"""
Part Number management routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import User, PartNumber, PartRouting, Customer
from schemas import PartNumberResponse, PartNumberCreate, PartNumberUpdate
from auth import get_current_active_user

router = APIRouter(prefix="/part-numbers", tags=["Part Numbers"])

@router.get("/", response_model=List[PartNumberResponse])
async def get_part_numbers(
    skip: int = 0,
    limit: int = 500,
    customer_id: int = None,
    is_active: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all part numbers"""
    query = db.query(PartNumber)
    if customer_id:
        query = query.filter(PartNumber.customer_id == customer_id)
    if is_active is not None:
        query = query.filter(PartNumber.is_active == is_active)
    part_numbers = query.offset(skip).limit(limit).all()
    return part_numbers

@router.get("/{part_number_id}", response_model=PartNumberResponse)
async def get_part_number(
    part_number_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific part number"""
    part_number = db.query(PartNumber).filter(PartNumber.id == part_number_id).first()
    if not part_number:
        raise HTTPException(status_code=404, detail="Part number not found")
    return part_number

@router.post("/", response_model=PartNumberResponse)
async def create_part_number(
    part_number: PartNumberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new part number with routing"""
    # Check if part number exists
    existing = db.query(PartNumber).filter(PartNumber.part_number == part_number.part_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Part number already exists")
    
    # Create part number
    part_data = part_number.model_dump(exclude={'routings'})
    db_part = PartNumber(**part_data)
    db.add(db_part)
    db.flush()  # Get the ID without committing
    
    # Create routings
    if part_number.routings:
        for routing in part_number.routings:
            db_routing = PartRouting(
                part_number_id=db_part.id,
                **routing.model_dump()
            )
            db.add(db_routing)
    
    db.commit()
    db.refresh(db_part)
    return db_part

@router.put("/{part_number_id}", response_model=PartNumberResponse)
async def update_part_number(
    part_number_id: int,
    part_number_update: PartNumberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a part number"""
    part_number = db.query(PartNumber).filter(PartNumber.id == part_number_id).first()
    if not part_number:
        raise HTTPException(status_code=404, detail="Part number not found")
    
    update_data = part_number_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(part_number, field, value)
    
    db.commit()
    db.refresh(part_number)
    return part_number

@router.delete("/{part_number_id}")
async def delete_part_number(
    part_number_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a part number"""
    part_number = db.query(PartNumber).filter(PartNumber.id == part_number_id).first()
    if not part_number:
        raise HTTPException(status_code=404, detail="Part number not found")
    
    db.delete(part_number)
    db.commit()
    return {"message": "Part number deleted successfully"}
