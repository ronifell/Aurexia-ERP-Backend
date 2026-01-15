"""
Process management routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import User, Process
from schemas import ProcessResponse
from auth import get_current_active_user

router = APIRouter(prefix="/processes", tags=["Processes"])

@router.get("/", response_model=List[ProcessResponse])
async def get_processes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all processes"""
    processes = db.query(Process).all()
    return processes
