"""
QR Scanner routes for production tracking
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, TravelSheetOperation, TravelSheet
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
    
    # Handle travel sheet QR code - find first pending operation
    if qr_data.get("type") == "travel_sheet":
        # Find travel sheet by QR code or travel sheet number
        travel_sheet = None
        if "number" in qr_data:
            travel_sheet = db.query(TravelSheet).filter(
                TravelSheet.travel_sheet_number == qr_data["number"]
            ).first()
        else:
            travel_sheet = db.query(TravelSheet).filter(
                TravelSheet.qr_code == scan_request.qr_code
            ).first()
        
        if not travel_sheet:
            return QRScanResponse(
                success=False,
                message="Travel sheet not found"
            )
        
        # Find first pending operation in sequence order
        first_pending_operation = db.query(TravelSheetOperation).filter(
            TravelSheetOperation.travel_sheet_id == travel_sheet.id,
            TravelSheetOperation.status == "Pending"
        ).order_by(TravelSheetOperation.sequence_number).first()
        
        if not first_pending_operation:
            # Check if there are any in-progress operations
            in_progress_operation = db.query(TravelSheetOperation).filter(
                TravelSheetOperation.travel_sheet_id == travel_sheet.id,
                TravelSheetOperation.status == "In Progress"
            ).order_by(TravelSheetOperation.sequence_number).first()
            
            if in_progress_operation:
                # Return the in-progress operation for completion
                return QRScanResponse(
                    success=True,
                    message="Ready to complete operation",
                    operation_id=in_progress_operation.id,
                    travel_sheet_id=in_progress_operation.travel_sheet_id,
                    process_name=in_progress_operation.process.name if in_progress_operation.process else "Unknown",
                    status="awaiting_completion"
                )
            else:
                return QRScanResponse(
                    success=False,
                    message="No pending operations found in this travel sheet. All operations may be completed."
                )
        
        # Start the first pending operation
        first_pending_operation.status = "In Progress"
        first_pending_operation.operator_id = operator.id
        first_pending_operation.start_time = datetime.utcnow()
        message = f"Operation started: {first_pending_operation.process.name if first_pending_operation.process else 'Unknown'}"
        
        db.commit()
        db.refresh(first_pending_operation)
        
        return QRScanResponse(
            success=True,
            message=message,
            operation_id=first_pending_operation.id,
            travel_sheet_id=first_pending_operation.travel_sheet_id,
            process_name=first_pending_operation.process.name if first_pending_operation.process else "Unknown",
            status=first_pending_operation.status
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
        message=f"Unsupported QR code type: {qr_data.get('type', 'unknown')}. Expected 'operation' or 'travel_sheet'."
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
    
    # Check if all operations in the travel sheet are completed
    travel_sheet = db.query(TravelSheet).filter(
        TravelSheet.id == operation.travel_sheet_id
    ).first()
    
    if travel_sheet:
        # Count total operations and completed operations
        total_ops = db.query(TravelSheetOperation).filter(
            TravelSheetOperation.travel_sheet_id == operation.travel_sheet_id
        ).count()
        
        completed_ops = db.query(TravelSheetOperation).filter(
            TravelSheetOperation.travel_sheet_id == operation.travel_sheet_id,
            TravelSheetOperation.status == "Completed"
        ).count()
        
        # Update travel sheet status if all operations are completed
        if completed_ops >= total_ops and travel_sheet.status != "Completed":
            travel_sheet.status = "Completed"
    
    db.commit()
    db.refresh(operation)
    
    # NOTE: Production order quantities (quantity_completed, quantity_scrapped) 
    # should ONLY be updated by Quality Inspections after parts are approved.
    # This prevents double-counting and ensures the dashboard shows final approved quantities.
    # Operation-level quantities (quantity_good, quantity_scrap) are tracked separately
    # for production tracking purposes.
    
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
