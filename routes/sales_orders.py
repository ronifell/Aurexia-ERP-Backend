"""
Sales Order management routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import User, SalesOrder, SalesOrderItem, PartNumber
from schemas import SalesOrderResponse, SalesOrderCreate, SalesOrderUpdate
from auth import get_current_active_user, can_view_prices

router = APIRouter(prefix="/sales-orders", tags=["Sales Orders"])

@router.get("/", response_model=List[SalesOrderResponse])
async def get_sales_orders(
    skip: int = 0,
    limit: int = 100,
    customer_id: int = None,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all sales orders"""
    query = db.query(SalesOrder)
    if customer_id:
        query = query.filter(SalesOrder.customer_id == customer_id)
    if status:
        query = query.filter(SalesOrder.status == status)
    
    sales_orders = query.offset(skip).limit(limit).all()
    
    # Hide prices if user doesn't have permission
    if not can_view_prices(current_user):
        for order in sales_orders:
            for item in order.items:
                item.unit_price = None
                item.total_price = None
    
    return sales_orders

@router.get("/{order_id}", response_model=SalesOrderResponse)
async def get_sales_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific sales order"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    # Hide prices if user doesn't have permission
    if not can_view_prices(current_user):
        for item in order.items:
            item.unit_price = None
            item.total_price = None
    
    return order

@router.post("/", response_model=SalesOrderResponse)
async def create_sales_order(
    order: SalesOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new sales order"""
    # Check if PO number exists
    existing = db.query(SalesOrder).filter(SalesOrder.po_number == order.po_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="PO number already exists")
    
    # Create sales order
    order_data = order.model_dump(exclude={'items'})
    order_data['created_by'] = current_user.id
    db_order = SalesOrder(**order_data)
    db.add(db_order)
    db.flush()
    
    # Create order items
    for item in order.items:
        # Get part number to check price
        part_number = db.query(PartNumber).filter(PartNumber.id == item.part_number_id).first()
        if not part_number:
            raise HTTPException(status_code=400, detail=f"Part number {item.part_number_id} not found")
        
        unit_price = item.unit_price if item.unit_price else part_number.unit_price
        total_price = unit_price * item.quantity if unit_price else None
        
        db_item = SalesOrderItem(
            sales_order_id=db_order.id,
            part_number_id=item.part_number_id,
            quantity=item.quantity,
            unit_price=unit_price,
            total_price=total_price
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_order)
    return db_order

@router.put("/{order_id}", response_model=SalesOrderResponse)
async def update_sales_order(
    order_id: int,
    order_update: SalesOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a sales order"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    # Update basic order fields
    update_data = order_update.model_dump(exclude_unset=True, exclude={'items'})
    for field, value in update_data.items():
        setattr(order, field, value)
    
    # Update items if provided
    if order_update.items is not None:
        # Delete existing items
        db.query(SalesOrderItem).filter(SalesOrderItem.sales_order_id == order_id).delete()
        
        # Create new items
        for item in order_update.items:
            # Get part number to check price
            part_number = db.query(PartNumber).filter(PartNumber.id == item.part_number_id).first()
            if not part_number:
                raise HTTPException(status_code=400, detail=f"Part number {item.part_number_id} not found")
            
            unit_price = item.unit_price if item.unit_price else part_number.unit_price
            total_price = unit_price * item.quantity if unit_price else None
            
            db_item = SalesOrderItem(
                sales_order_id=order.id,
                part_number_id=item.part_number_id,
                quantity=item.quantity,
                unit_price=unit_price,
                total_price=total_price
            )
            db.add(db_item)
    
    db.commit()
    db.refresh(order)
    return order

@router.delete("/{order_id}")
async def delete_sales_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a sales order"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    db.delete(order)
    db.commit()
    return {"message": "Sales order deleted successfully"}
