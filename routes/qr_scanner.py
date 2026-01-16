"""
QR Scanner routes for production tracking
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import User, TravelSheetOperation, TravelSheet, ProductionOrder
from schemas import QRScanRequest, QRScanResponse, TravelSheetOperationUpdate
from auth import get_current_active_user
import json
from datetime import datetime

router = APIRouter(prefix="/qr-scanner", tags=["QR Scanner"])

@router.post("/scan", response_model=QRScanResponse)
async def scan_qr_code(
    scan_request: QRScanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Process QR code scan"""
    # Verify operator badge
    operator = db.query(User).filter(User.badge_id == scan_request.badge_id).first()
    if not operator:
        return QRScanResponse(
            success=False,
            message="Invalid operator badge"
        )
    
    # Parse QR code data
    try:
        qr_data = json.loads(scan_request.qr_code)
    except:
        return QRScanResponse(
            success=False,
            message="Invalid QR code format"
        )
    
    # Handle operation QR code
    if qr_data.get("type") == "operation":
        operation = db.query(TravelSheetOperation).filter(
            TravelSheetOperation.qr_code == scan_request.qr_code
        ).first()
        
        if not operation:
            return QRScanResponse(
                success=False,
                message="Operation not found"
            )
        
        # Toggle operation status
        if operation.status == "Pending":
            # Start operation
            operation.status = "In Progress"
            operation.operator_id = operator.id
            operation.start_time = datetime.utcnow()
            message = f"Operation started: {operation.process.name if operation.process else 'Unknown'}"
        
        elif operation.status == "In Progress":
            # Operation is already in progress, this scan should be to complete it
            # Return operation info so frontend can show completion form
            return QRScanResponse(
                success=True,
                message="Ready to complete operation",
                operation_id=operation.id,
                travel_sheet_id=operation.travel_sheet_id,
                process_name=operation.process.name if operation.process else "Unknown",
                status="awaiting_completion"
            )
        
        else:
            return QRScanResponse(
                success=False,
                message=f"Operation already {operation.status}"
            )
        
        db.commit()
        db.refresh(operation)
        
        return QRScanResponse(
            success=True,
            message=message,
            operation_id=operation.id,
            travel_sheet_id=operation.travel_sheet_id,
            process_name=operation.process.name if operation.process else "Unknown",
            status=operation.status
        )
    
    return QRScanResponse(
        success=False,
        message="Unsupported QR code type"
    )

@router.put("/operations/{operation_id}/complete")
async def complete_operation(
    operation_id: int,
    operation_update: TravelSheetOperationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Complete an operation with quantities"""
    operation = db.query(TravelSheetOperation).filter(
        TravelSheetOperation.id == operation_id
    ).first()
    
    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")
    
    if operation.status != "In Progress":
        raise HTTPException(status_code=400, detail="Operation is not in progress")
    
    # Update operation
    operation.status = "Completed"
    operation.end_time = datetime.utcnow()
    
    if operation.start_time:
        duration = (operation.end_time - operation.start_time).total_seconds() / 60
        operation.duration_minutes = int(duration)
    
    update_data = operation_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field not in ['status', 'start_time', 'end_time']:
            setattr(operation, field, value)
    
    db.commit()
    db.refresh(operation)
    
    # Update production order quantities based on all completed operations
    travel_sheet = db.query(TravelSheet).filter(
        TravelSheet.id == operation.travel_sheet_id
    ).first()
    
    if travel_sheet and travel_sheet.production_order_id:
        production_order = db.query(ProductionOrder).filter(
            ProductionOrder.id == travel_sheet.production_order_id
        ).first()
        
        if production_order:
            # Get all travel sheets for this production order
            all_travel_sheets = db.query(TravelSheet).filter(
                TravelSheet.production_order_id == production_order.id
            ).all()
            
            travel_sheet_ids = [ts.id for ts in all_travel_sheets]
            
            # Sum all quantity_good and quantity_scrap from completed operations
            result = db.query(
                func.sum(TravelSheetOperation.quantity_good).label('total_good'),
                func.sum(TravelSheetOperation.quantity_scrap).label('total_scrap')
            ).filter(
                TravelSheetOperation.travel_sheet_id.in_(travel_sheet_ids),
                TravelSheetOperation.status == 'Completed'
            ).first()
            
            # Update production order quantities
            production_order.quantity_completed = int(result.total_good) if result.total_good else 0
            production_order.quantity_scrapped = int(result.total_scrap) if result.total_scrap else 0
            
            db.commit()
    
    return {
        "success": True,
        "message": "Operation completed successfully",
        "operation": operation
    }

@router.get("/operations/{operation_id}")
async def get_operation_details(
    operation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get operation details"""
    operation = db.query(TravelSheetOperation).filter(
        TravelSheetOperation.id == operation_id
    ).first()
    
    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")
    
    return operation
