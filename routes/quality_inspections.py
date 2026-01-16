"""
Quality Inspection management routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List
from datetime import datetime
from database import get_db
from models import User, QualityInspection, ProductionOrder, TravelSheet, PartNumber
from schemas import QualityInspectionResponse, QualityInspectionCreate
from auth import get_current_active_user

router = APIRouter(prefix="/quality-inspections", tags=["Quality Inspections"])

@router.get("/", response_model=List[QualityInspectionResponse])
async def get_quality_inspections(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    production_order_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all quality inspections"""
    query = db.query(QualityInspection).options(
        joinedload(QualityInspection.production_order).joinedload(ProductionOrder.part_number),
        joinedload(QualityInspection.travel_sheet),
        joinedload(QualityInspection.inspector)
    )
    if status:
        query = query.filter(QualityInspection.status == status)
    if production_order_id:
        query = query.filter(QualityInspection.production_order_id == production_order_id)
    
    inspections = query.order_by(desc(QualityInspection.inspection_date)).offset(skip).limit(limit).all()
    return inspections

@router.get("/{inspection_id}", response_model=QualityInspectionResponse)
async def get_quality_inspection(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific quality inspection"""
    inspection = db.query(QualityInspection).filter(QualityInspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Quality inspection not found")
    return inspection

@router.post("/", response_model=QualityInspectionResponse)
async def create_quality_inspection(
    inspection: QualityInspectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new quality inspection"""
    # Verify production order exists
    production_order = db.query(ProductionOrder).filter(ProductionOrder.id == inspection.production_order_id).first()
    if not production_order:
        raise HTTPException(status_code=400, detail="Production order not found")
    
    # Verify travel sheet if provided
    if inspection.travel_sheet_id:
        travel_sheet = db.query(TravelSheet).filter(TravelSheet.id == inspection.travel_sheet_id).first()
        if not travel_sheet:
            raise HTTPException(status_code=400, detail="Travel sheet not found")
        if travel_sheet.production_order_id != inspection.production_order_id:
            raise HTTPException(status_code=400, detail="Travel sheet does not belong to the specified production order")
    
    # Validate quantities
    if inspection.quantity_approved and inspection.quantity_rejected:
        total = inspection.quantity_approved + inspection.quantity_rejected
        if inspection.quantity_inspected and total > inspection.quantity_inspected:
            raise HTTPException(status_code=400, detail="Sum of approved and rejected quantities cannot exceed inspected quantity")
    
    # Create quality inspection
    db_inspection = QualityInspection(
        travel_sheet_id=inspection.travel_sheet_id,
        production_order_id=inspection.production_order_id,
        inspector_id=current_user.id,
        inspection_date=datetime.utcnow(),
        status=inspection.status,
        quantity_inspected=inspection.quantity_inspected,
        quantity_approved=inspection.quantity_approved,
        quantity_rejected=inspection.quantity_rejected,
        rejection_reason=inspection.rejection_reason,
        notes=inspection.notes
    )
    db.add(db_inspection)
    
    # Update production order based on inspection results
    if inspection.status == "Released":
        # Add approved quantity to completed quantity (these are the final good parts)
        if inspection.quantity_approved:
            production_order.quantity_completed += inspection.quantity_approved
        
        # Add rejected quantity to scrapped quantity
        if inspection.quantity_rejected:
            production_order.quantity_scrapped += inspection.quantity_rejected
        
        # Update production order status
        if production_order.quantity_completed >= production_order.quantity:
            production_order.status = "Completed"
        elif production_order.quantity_completed > 0:
            production_order.status = "In Progress"
    
    elif inspection.status == "Rejected":
        # If entire batch is rejected, add to scrap
        if inspection.quantity_rejected:
            production_order.quantity_scrapped += inspection.quantity_rejected
    
    db.commit()
    db.refresh(db_inspection)
    return db_inspection

@router.put("/{inspection_id}", response_model=QualityInspectionResponse)
async def update_quality_inspection(
    inspection_id: int,
    inspection_update: QualityInspectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a quality inspection"""
    inspection = db.query(QualityInspection).filter(QualityInspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Quality inspection not found")
    
    # Get the production order
    production_order = db.query(ProductionOrder).filter(ProductionOrder.id == inspection.production_order_id).first()
    if not production_order:
        raise HTTPException(status_code=404, detail="Production order not found")
    
    # Reverse the previous quantities if status was "Released"
    if inspection.status == "Released":
        if inspection.quantity_approved:
            production_order.quantity_completed -= inspection.quantity_approved
        if inspection.quantity_rejected:
            production_order.quantity_scrapped -= inspection.quantity_rejected
    elif inspection.status == "Rejected":
        if inspection.quantity_rejected:
            production_order.quantity_scrapped -= inspection.quantity_rejected
    
    # Update inspection fields
    update_data = inspection_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(inspection, field, value)
    
    # Apply new quantities based on updated status
    if inspection.status == "Released":
        if inspection.quantity_approved:
            production_order.quantity_completed += inspection.quantity_approved
        if inspection.quantity_rejected:
            production_order.quantity_scrapped += inspection.quantity_rejected
        
        # Update production order status
        if production_order.quantity_completed >= production_order.quantity:
            production_order.status = "Completed"
        elif production_order.quantity_completed > 0:
            production_order.status = "In Progress"
        else:
            production_order.status = "Released"
    
    elif inspection.status == "Rejected":
        if inspection.quantity_rejected:
            production_order.quantity_scrapped += inspection.quantity_rejected
    
    db.commit()
    db.refresh(inspection)
    return inspection

@router.delete("/{inspection_id}")
async def delete_quality_inspection(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a quality inspection"""
    # Check if user is admin or management
    if current_user.role.name not in ['Admin', 'Management']:
        raise HTTPException(status_code=403, detail="Only Admin or Management can delete quality inspections")
    
    inspection = db.query(QualityInspection).filter(QualityInspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Quality inspection not found")
    
    # Get the production order to reverse quantities
    production_order = db.query(ProductionOrder).filter(ProductionOrder.id == inspection.production_order_id).first()
    
    # Reverse the quantities before deleting
    if production_order:
        if inspection.status == "Released":
            if inspection.quantity_approved:
                production_order.quantity_completed -= inspection.quantity_approved
            if inspection.quantity_rejected:
                production_order.quantity_scrapped -= inspection.quantity_rejected
        elif inspection.status == "Rejected":
            if inspection.quantity_rejected:
                production_order.quantity_scrapped -= inspection.quantity_rejected
        
        # Update production order status
        if production_order.quantity_completed >= production_order.quantity:
            production_order.status = "Completed"
        elif production_order.quantity_completed > 0:
            production_order.status = "In Progress"
        else:
            production_order.status = "Released"
    
    db.delete(inspection)
    db.commit()
    return {"message": "Quality inspection deleted successfully"}

@router.get("/production-order/{production_order_id}/pending")
async def get_pending_inspections(
    production_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get production orders pending quality inspection"""
    production_order = db.query(ProductionOrder).filter(ProductionOrder.id == production_order_id).first()
    if not production_order:
        raise HTTPException(status_code=404, detail="Production order not found")
    
    # Get travel sheets for this production order
    travel_sheets = db.query(TravelSheet).filter(
        TravelSheet.production_order_id == production_order_id,
        TravelSheet.status == 'Completed'
    ).all()
    
    # Check which travel sheets haven't been inspected yet
    pending_sheets = []
    for sheet in travel_sheets:
        inspection = db.query(QualityInspection).filter(
            QualityInspection.travel_sheet_id == sheet.id
        ).first()
        if not inspection:
            pending_sheets.append({
                "travel_sheet_id": sheet.id,
                "travel_sheet_number": sheet.travel_sheet_number,
                "production_order_id": production_order_id,
                "po_number": production_order.po_number
            })
    
    return pending_sheets
