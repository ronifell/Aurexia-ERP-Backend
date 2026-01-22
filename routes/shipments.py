from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List
from datetime import datetime, date

from database import get_db
from auth import get_current_user
from models import Shipment, ShipmentItem, User, Customer, SalesOrder, SalesOrderItem, PartNumber, ProductionOrder, QualityInspection
from schemas import ShipmentCreate, ShipmentResponse, ShipmentItemResponse

router = APIRouter(prefix="/shipments", tags=["Shipments"])


def generate_shipment_number(db: Session) -> str:
    """Generate a unique shipment number in format SHIP-YYYY-NNNN"""
    year = datetime.now().year
    prefix = f"SHIP-{year}-"
    
    last_shipment = (
        db.query(Shipment)
        .filter(Shipment.shipment_number.like(f"{prefix}%"))
        .order_by(Shipment.shipment_number.desc())
        .first()
    )
    
    if last_shipment:
        last_number = int(last_shipment.shipment_number.split("-")[-1])
        new_number = last_number + 1
    else:
        new_number = 1
    
    return f"{prefix}{new_number:04d}"


def update_sales_order_status(db: Session, sales_order_id: int):
    """Update sales order status based on shipped quantities"""
    sales_order = db.query(SalesOrder).filter(SalesOrder.id == sales_order_id).first()
    if not sales_order:
        return
    
    # Get all items for this order
    items = db.query(SalesOrderItem).filter(
        SalesOrderItem.sales_order_id == sales_order_id
    ).all()
    
    if not items:
        return
    
    # Calculate totals
    total_ordered = sum(item.quantity for item in items)
    total_shipped = sum(item.quantity_shipped or 0 for item in items)
    
    # Update status based on fulfillment
    if total_shipped == 0:
        new_status = "Open"
    elif total_shipped >= total_ordered:
        new_status = "Completed"
    else:
        new_status = "Partial"
    
    # Only update if status changed
    if sales_order.status != new_status:
        sales_order.status = new_status


def update_sales_order_quantities(
    db: Session,
    shipment_items: List[ShipmentItem],
    operation: str = "add"
):
    """Update quantity_shipped in SalesOrderItem based on shipment items"""
    multiplier = 1 if operation == "add" else -1
    sales_order_ids = set()  # Track which orders need status update
    
    for item in shipment_items:
        if item.sales_order_item_id:
            sales_order_item = db.query(SalesOrderItem).filter(
                SalesOrderItem.id == item.sales_order_item_id
            ).first()
            
            if sales_order_item:
                current_shipped = sales_order_item.quantity_shipped or 0
                new_shipped = current_shipped + (item.quantity * multiplier)
                # Ensure quantity_shipped doesn't go negative
                sales_order_item.quantity_shipped = max(0, new_shipped)
                
                # Track the sales order for status update
                sales_order_ids.add(sales_order_item.sales_order_id)
    
    # Update status for all affected sales orders
    for sales_order_id in sales_order_ids:
        update_sales_order_status(db, sales_order_id)


def validate_quality_constraints(
    db: Session,
    production_order_id: int,
    quantity_to_ship: int
) -> dict:
    """
    Validate that a production order has passed quality inspection
    and has enough approved quantity available for shipping.
    
    Returns dict with:
        - is_valid: bool
        - error_message: str (if not valid)
        - approved_quantity: int
        - already_shipped: int
        - available_to_ship: int
    """
    # Get the production order
    production_order = db.query(ProductionOrder).filter(
        ProductionOrder.id == production_order_id
    ).first()
    
    if not production_order:
        return {
            "is_valid": False,
            "error_message": "Production order not found",
            "approved_quantity": 0,
            "already_shipped": 0,
            "available_to_ship": 0
        }
    
    # Get all quality inspections for this production order
    inspections = db.query(QualityInspection).filter(
        QualityInspection.production_order_id == production_order_id
    ).all()
    
    # Check if there are any quality inspections
    if not inspections:
        return {
            "is_valid": False,
            "error_message": f"Production order {production_order.po_number} has not been quality inspected yet. Cannot ship uninspected items.",
            "approved_quantity": 0,
            "already_shipped": 0,
            "available_to_ship": 0
        }
    
    # Calculate total approved and rejected quantities
    total_approved = sum(
        inspection.quantity_approved or 0 
        for inspection in inspections 
        if inspection.status == "Released"
    )
    
    total_rejected = sum(
        inspection.quantity_rejected or 0
        for inspection in inspections
    )
    
    # Check if any inspection has "Rejected" status (entire batch rejected)
    has_rejected_status = any(
        inspection.status == "Rejected" 
        for inspection in inspections
    )
    
    if has_rejected_status:
        return {
            "is_valid": False,
            "error_message": f"Production order {production_order.po_number} has been rejected by quality control. Cannot ship rejected items.",
            "approved_quantity": total_approved,
            "already_shipped": 0,
            "available_to_ship": 0
        }
    
    # Calculate how much has already been shipped from this production order
    already_shipped = db.query(ShipmentItem).filter(
        ShipmentItem.production_order_id == production_order_id
    ).with_entities(
        func.sum(ShipmentItem.quantity)
    ).scalar() or 0
    
    # Calculate available quantity to ship
    available_to_ship = total_approved - already_shipped
    
    # Validate requested quantity
    if quantity_to_ship > available_to_ship:
        return {
            "is_valid": False,
            "error_message": f"Cannot ship {quantity_to_ship} units. Only {available_to_ship} approved units available (Total approved: {total_approved}, Already shipped: {already_shipped}).",
            "approved_quantity": total_approved,
            "already_shipped": already_shipped,
            "available_to_ship": available_to_ship
        }
    
    # All checks passed
    return {
        "is_valid": True,
        "error_message": None,
        "approved_quantity": total_approved,
        "already_shipped": already_shipped,
        "available_to_ship": available_to_ship
    }


@router.get("", response_model=List[ShipmentResponse])
def get_shipments(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    customer_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all shipments with optional filtering"""
    query = db.query(Shipment).options(
        joinedload(Shipment.customer),
        joinedload(Shipment.sales_order),
        joinedload(Shipment.items)
    )
    
    if status:
        query = query.filter(Shipment.status == status)
    
    if customer_id:
        query = query.filter(Shipment.customer_id == customer_id)
    
    shipments = query.order_by(Shipment.created_at.desc()).offset(skip).limit(limit).all()
    return shipments


@router.get("/{shipment_id}", response_model=ShipmentResponse)
def get_shipment(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific shipment by ID"""
    shipment = (
        db.query(Shipment)
        .options(
            joinedload(Shipment.customer),
            joinedload(Shipment.sales_order),
            joinedload(Shipment.items).joinedload(ShipmentItem.part_number),
            joinedload(Shipment.items).joinedload(ShipmentItem.production_order)
        )
        .filter(Shipment.id == shipment_id)
        .first()
    )
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    return shipment


@router.post("", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
def create_shipment(
    shipment_data: ShipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new shipment"""
    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == shipment_data.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Verify sales order exists if provided
    if shipment_data.sales_order_id:
        sales_order = db.query(SalesOrder).filter(SalesOrder.id == shipment_data.sales_order_id).first()
        if not sales_order:
            raise HTTPException(status_code=404, detail="Sales order not found")
    
    # Generate shipment number
    shipment_number = generate_shipment_number(db)
    
    # Create shipment
    new_shipment = Shipment(
        shipment_number=shipment_number,
        customer_id=shipment_data.customer_id,
        sales_order_id=shipment_data.sales_order_id,
        shipment_date=shipment_data.shipment_date,
        status=shipment_data.status or "Prepared",
        tracking_number=shipment_data.tracking_number,
        notes=shipment_data.notes,
        created_by=current_user.id
    )
    
    db.add(new_shipment)
    db.flush()  # Get the shipment ID
    
    # Create shipment items
    for item_data in shipment_data.items:
        # Verify part number exists
        part_number = db.query(PartNumber).filter(PartNumber.id == item_data.part_number_id).first()
        if not part_number:
            raise HTTPException(status_code=404, detail=f"Part number with ID {item_data.part_number_id} not found")
        
        # Verify production order exists if provided
        if item_data.production_order_id:
            production_order = db.query(ProductionOrder).filter(ProductionOrder.id == item_data.production_order_id).first()
            if not production_order:
                raise HTTPException(status_code=404, detail=f"Production order with ID {item_data.production_order_id} not found")
            
            # QUALITY GATE: Validate quality constraints before allowing shipment
            validation_result = validate_quality_constraints(
                db,
                item_data.production_order_id,
                item_data.quantity
            )
            
            if not validation_result["is_valid"]:
                raise HTTPException(
                    status_code=400,
                    detail=validation_result["error_message"]
                )
        
        # Auto-match sales_order_item_id
        sales_order_item_id = item_data.sales_order_item_id
        if not sales_order_item_id:
            if shipment_data.sales_order_id:
                # If sales order is provided, find matching item by part number in that order
                matching_item = db.query(SalesOrderItem).filter(
                    SalesOrderItem.sales_order_id == shipment_data.sales_order_id,
                    SalesOrderItem.part_number_id == item_data.part_number_id
                ).first()
                if matching_item:
                    sales_order_item_id = matching_item.id
            else:
                # If no sales order is selected, find any open/partial sales order for this customer and part
                # that still has unshipped quantities
                matching_item = db.query(SalesOrderItem).join(SalesOrder).filter(
                    SalesOrder.customer_id == shipment_data.customer_id,
                    SalesOrder.status.in_(['Open', 'Partial']),
                    SalesOrderItem.part_number_id == item_data.part_number_id,
                    SalesOrderItem.quantity > SalesOrderItem.quantity_shipped
                ).order_by(SalesOrder.due_date.asc()).first()
                if matching_item:
                    sales_order_item_id = matching_item.id
        
        shipment_item = ShipmentItem(
            shipment_id=new_shipment.id,
            sales_order_item_id=sales_order_item_id,
            part_number_id=item_data.part_number_id,
            production_order_id=item_data.production_order_id,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price
        )
        db.add(shipment_item)
    
    db.flush()  # Get shipment item IDs
    
    # Update sales order quantities
    new_shipment_items = db.query(ShipmentItem).filter(
        ShipmentItem.shipment_id == new_shipment.id
    ).all()
    update_sales_order_quantities(db, new_shipment_items, operation="add")
    
    db.commit()
    db.refresh(new_shipment)
    
    # Load relationships
    shipment = (
        db.query(Shipment)
        .options(
            joinedload(Shipment.customer),
            joinedload(Shipment.sales_order),
            joinedload(Shipment.items).joinedload(ShipmentItem.part_number),
            joinedload(Shipment.items).joinedload(ShipmentItem.production_order)
        )
        .filter(Shipment.id == new_shipment.id)
        .first()
    )
    
    return shipment


@router.put("/{shipment_id}", response_model=ShipmentResponse)
def update_shipment(
    shipment_id: int,
    shipment_data: ShipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing shipment"""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    # Update shipment fields
    shipment.customer_id = shipment_data.customer_id
    shipment.sales_order_id = shipment_data.sales_order_id
    shipment.shipment_date = shipment_data.shipment_date
    shipment.status = shipment_data.status or shipment.status
    shipment.tracking_number = shipment_data.tracking_number
    shipment.notes = shipment_data.notes
    
    # Get old shipment items before deletion to subtract quantities
    old_shipment_items = db.query(ShipmentItem).filter(
        ShipmentItem.shipment_id == shipment_id
    ).all()
    
    # Subtract old quantities from sales order items
    update_sales_order_quantities(db, old_shipment_items, operation="subtract")
    
    # Delete existing items
    db.query(ShipmentItem).filter(ShipmentItem.shipment_id == shipment_id).delete()
    
    # Create new items
    for item_data in shipment_data.items:
        # Verify production order and quality constraints if provided
        if item_data.production_order_id:
            production_order = db.query(ProductionOrder).filter(
                ProductionOrder.id == item_data.production_order_id
            ).first()
            if not production_order:
                raise HTTPException(
                    status_code=404,
                    detail=f"Production order with ID {item_data.production_order_id} not found"
                )
            
            # QUALITY GATE: Validate quality constraints before allowing shipment
            validation_result = validate_quality_constraints(
                db,
                item_data.production_order_id,
                item_data.quantity
            )
            
            if not validation_result["is_valid"]:
                raise HTTPException(
                    status_code=400,
                    detail=validation_result["error_message"]
                )
        
        # Auto-match sales_order_item_id
        sales_order_item_id = item_data.sales_order_item_id
        if not sales_order_item_id:
            if shipment_data.sales_order_id:
                # If sales order is provided, find matching item by part number in that order
                matching_item = db.query(SalesOrderItem).filter(
                    SalesOrderItem.sales_order_id == shipment_data.sales_order_id,
                    SalesOrderItem.part_number_id == item_data.part_number_id
                ).first()
                if matching_item:
                    sales_order_item_id = matching_item.id
            else:
                # If no sales order is selected, find any open/partial sales order for this customer and part
                # that still has unshipped quantities
                matching_item = db.query(SalesOrderItem).join(SalesOrder).filter(
                    SalesOrder.customer_id == shipment_data.customer_id,
                    SalesOrder.status.in_(['Open', 'Partial']),
                    SalesOrderItem.part_number_id == item_data.part_number_id,
                    SalesOrderItem.quantity > SalesOrderItem.quantity_shipped
                ).order_by(SalesOrder.due_date.asc()).first()
                if matching_item:
                    sales_order_item_id = matching_item.id
        
        shipment_item = ShipmentItem(
            shipment_id=shipment.id,
            sales_order_item_id=sales_order_item_id,
            part_number_id=item_data.part_number_id,
            production_order_id=item_data.production_order_id,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price
        )
        db.add(shipment_item)
    
    db.flush()  # Get new shipment item IDs
    
    # Add new quantities to sales order items
    new_shipment_items = db.query(ShipmentItem).filter(
        ShipmentItem.shipment_id == shipment_id
    ).all()
    update_sales_order_quantities(db, new_shipment_items, operation="add")
    
    db.commit()
    db.refresh(shipment)
    
    # Load relationships
    shipment = (
        db.query(Shipment)
        .options(
            joinedload(Shipment.customer),
            joinedload(Shipment.sales_order),
            joinedload(Shipment.items).joinedload(ShipmentItem.part_number),
            joinedload(Shipment.items).joinedload(ShipmentItem.production_order)
        )
        .filter(Shipment.id == shipment_id)
        .first()
    )
    
    return shipment


@router.delete("/{shipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shipment(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a shipment"""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    # Get shipment items before deletion to subtract quantities
    shipment_items = db.query(ShipmentItem).filter(
        ShipmentItem.shipment_id == shipment_id
    ).all()
    
    # Subtract quantities from sales order items
    update_sales_order_quantities(db, shipment_items, operation="subtract")
    
    db.delete(shipment)
    db.commit()
    
    return None


@router.patch("/{shipment_id}/status", response_model=ShipmentResponse)
def update_shipment_status(
    shipment_id: int,
    status: str,
    tracking_number: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update shipment status (Prepared, Shipped, Delivered)"""
    valid_statuses = ["Prepared", "Shipped", "Delivered"]
    
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    shipment.status = status
    if tracking_number:
        shipment.tracking_number = tracking_number
    
    db.commit()
    db.refresh(shipment)
    
    # Load relationships
    shipment = (
        db.query(Shipment)
        .options(
            joinedload(Shipment.customer),
            joinedload(Shipment.sales_order),
            joinedload(Shipment.items).joinedload(ShipmentItem.part_number)
        )
        .filter(Shipment.id == shipment_id)
        .first()
    )
    
    return shipment


@router.get("/sales-order/{sales_order_id}/approved-quantities")
def get_approved_quantities_for_sales_order(
    sales_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get approved quantities available for shipping for each part number in a sales order"""
    sales_order = db.query(SalesOrder).filter(SalesOrder.id == sales_order_id).first()
    if not sales_order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    result = []
    
    for item in sales_order.items:
        part_number_id = item.part_number_id
        
        # Find all production orders for this part number that are linked to this sales order
        production_orders = db.query(ProductionOrder).filter(
            ProductionOrder.part_number_id == part_number_id,
            ProductionOrder.sales_order_id == sales_order_id
        ).all()
        
        total_approved = 0
        total_shipped = 0
        
        for po in production_orders:
            # Get quality inspections for this production order
            inspections = db.query(QualityInspection).filter(
                QualityInspection.production_order_id == po.id,
                QualityInspection.status == "Released"
            ).all()
            
            approved_qty = sum(inspection.quantity_approved or 0 for inspection in inspections)
            total_approved += approved_qty
            
            # Calculate already shipped from this production order
            shipped = db.query(ShipmentItem).filter(
                ShipmentItem.production_order_id == po.id
            ).with_entities(
                func.sum(ShipmentItem.quantity)
            ).scalar() or 0
            
            total_shipped += shipped
        
        available = total_approved - total_shipped
        
        result.append({
            "part_number_id": part_number_id,
            "part_number": item.part_number.part_number if item.part_number else None,
            "ordered_quantity": item.quantity,
            "already_shipped": item.quantity_shipped or 0,
            "approved_quantity": total_approved,
            "available_to_ship": max(0, available),
            "remaining_to_fulfill": max(0, item.quantity - (item.quantity_shipped or 0))
        })
    
    return result