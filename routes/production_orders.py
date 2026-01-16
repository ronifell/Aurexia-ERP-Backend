"""
Production Order management routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import User, ProductionOrder, PartNumber, TravelSheet, TravelSheetOperation, PartRouting
from schemas import ProductionOrderResponse, ProductionOrderCreate, ProductionOrderUpdate, TravelSheetResponse
from auth import get_current_active_user
from utils import generate_unique_number, generate_qr_code
import json

router = APIRouter(prefix="/production-orders", tags=["Production Orders"])

@router.get("/", response_model=List[ProductionOrderResponse])
async def get_production_orders(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    part_number_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all production orders"""
    query = db.query(ProductionOrder)
    if status:
        query = query.filter(ProductionOrder.status == status)
    if part_number_id:
        query = query.filter(ProductionOrder.part_number_id == part_number_id)
    
    production_orders = query.offset(skip).limit(limit).all()
    return production_orders

@router.get("/{order_id}", response_model=ProductionOrderResponse)
async def get_production_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific production order"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Production order not found")
    return order

@router.post("/", response_model=ProductionOrderResponse)
async def create_production_order(
    order: ProductionOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new production order"""
    # Verify part number exists
    part_number = db.query(PartNumber).filter(PartNumber.id == order.part_number_id).first()
    if not part_number:
        raise HTTPException(status_code=400, detail="Part number not found")
    
    # Generate PO number
    po_number = generate_unique_number("PO")
    
    # Create production order
    db_order = ProductionOrder(
        po_number=po_number,
        sales_order_id=order.sales_order_id,
        sales_order_item_id=order.sales_order_item_id,
        part_number_id=order.part_number_id,
        quantity=order.quantity,
        due_date=order.due_date,
        priority=order.priority,
        created_by=current_user.id
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@router.put("/{order_id}", response_model=ProductionOrderResponse)
async def update_production_order(
    order_id: int,
    order_update: ProductionOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a production order"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Production order not found")
    
    update_data = order_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    
    db.commit()
    db.refresh(order)
    return order

@router.post("/{order_id}/generate-travel-sheet", response_model=TravelSheetResponse)
async def generate_travel_sheet(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate travel sheet for production order"""
    # Get production order
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Production order not found")
    
    # Get part number routings
    routings = db.query(PartRouting).filter(
        PartRouting.part_number_id == order.part_number_id
    ).order_by(PartRouting.sequence_number).all()
    
    if not routings:
        raise HTTPException(status_code=400, detail="No routing defined for this part number")
    
    # Generate travel sheet number
    travel_sheet_number = generate_unique_number("TS")
    
    # Generate QR code data
    qr_data = json.dumps({
        "type": "travel_sheet",
        "number": travel_sheet_number,
        "po": order.po_number,
        "part_number": order.part_number.part_number if order.part_number else None
    })
    
    # Create travel sheet
    travel_sheet = TravelSheet(
        travel_sheet_number=travel_sheet_number,
        production_order_id=order.id,
        qr_code=qr_data
    )
    db.add(travel_sheet)
    db.flush()
    
    # Create operations from routing
    for routing in routings:
        operation_qr_data = json.dumps({
            "type": "operation",
            "travel_sheet_id": travel_sheet.id,
            "sequence": routing.sequence_number,
            "process_id": routing.process_id
        })
        
        operation = TravelSheetOperation(
            travel_sheet_id=travel_sheet.id,
            process_id=routing.process_id,
            sequence_number=routing.sequence_number,
            qr_code=operation_qr_data,
            work_center_id=routing.process.work_center_id,
            quantity_pending=order.quantity
        )
        db.add(operation)
    
    db.commit()
    db.refresh(travel_sheet)
    return travel_sheet

@router.get("/{order_id}/travel-sheets", response_model=List[TravelSheetResponse])
async def get_travel_sheets(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all travel sheets for a production order"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Production order not found")
    
    travel_sheets = db.query(TravelSheet).filter(
        TravelSheet.production_order_id == order_id
    ).all()
    return travel_sheets

@router.delete("/{order_id}")
async def delete_production_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a production order"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Production order not found")
    
    db.delete(order)
    db.commit()
    return {"message": "Production order deleted successfully"}
