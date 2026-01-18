"""
Dashboard and analytics routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List
from database import get_db
from models import User, ProductionOrder, SalesOrder, TravelSheetOperation, PartNumber, Customer
from schemas import DashboardStats, ProductionDashboardItem
from auth import get_current_active_user
from utils import determine_risk_status, calculate_completion_percentage
from datetime import date, timedelta

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get dashboard statistics"""
    today = date.today()
    risk_date = today + timedelta(days=3)
    
    # Total open sales orders (Open + Partial)
    total_open_orders = db.query(SalesOrder).filter(
        SalesOrder.status.in_(['Open', 'Partial'])
    ).count()
    
    # Total completed sales orders
    total_completed_orders = db.query(SalesOrder).filter(
        SalesOrder.status == 'Completed'
    ).count()
    
    # Total shipped orders (orders with at least one shipment)
    from models import Shipment
    # Count distinct sales orders that have shipments
    total_shipped_orders = db.query(
        func.count(func.distinct(Shipment.sales_order_id))
    ).filter(
        Shipment.sales_order_id.isnot(None)
    ).scalar() or 0
    
    # Total production orders in production
    total_in_production = db.query(ProductionOrder).filter(
        ProductionOrder.status == 'In Progress'
    ).count()
    
    # Count delayed, at risk, and on time
    production_orders = db.query(ProductionOrder).filter(
        ProductionOrder.status.notin_(['Completed', 'Cancelled'])
    ).all()
    
    total_delayed = 0
    total_at_risk = 0
    total_on_time = 0
    
    for po in production_orders:
        risk_status = determine_risk_status(po.due_date, po.status)
        if risk_status == 'Red':
            total_delayed += 1
        elif risk_status == 'Yellow':
            total_at_risk += 1
        else:
            total_on_time += 1
    
    return DashboardStats(
        total_open_orders=total_open_orders,
        total_completed_orders=total_completed_orders,
        total_shipped_orders=total_shipped_orders,
        total_in_production=total_in_production,
        total_delayed=total_delayed,
        total_at_risk=total_at_risk,
        total_on_time=total_on_time
    )

@router.get("/production", response_model=List[ProductionDashboardItem])
async def get_production_dashboard(
    status: str = None,
    risk_status: str = None,
    customer_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get production dashboard data"""
    query = db.query(ProductionOrder).join(PartNumber)
    
    if status:
        query = query.filter(ProductionOrder.status == status)
    
    production_orders = query.offset(skip).limit(limit).all()
    
    dashboard_items = []
    for po in production_orders:
        # Get sales order info
        sales_order_number = None
        customer_name = None
        if po.sales_order_id:
            sales_order = db.query(SalesOrder).filter(SalesOrder.id == po.sales_order_id).first()
            if sales_order:
                sales_order_number = sales_order.po_number
                if sales_order.customer:
                    customer_name = sales_order.customer.name
        
        # Calculate risk status
        risk = determine_risk_status(po.due_date, po.status)
        
        # Calculate completion percentage
        completion = calculate_completion_percentage(po.quantity_completed, po.quantity)
        
        # Calculate shipped quantity for this production order
        from models import ShipmentItem
        shipped_quantity = db.query(
            func.sum(ShipmentItem.quantity)
        ).filter(
            ShipmentItem.production_order_id == po.id
        ).scalar() or 0
        
        # Apply filter
        if risk_status and risk != risk_status:
            continue
        
        if customer_id and sales_order and sales_order.customer_id != customer_id:
            continue
        
        dashboard_items.append(ProductionDashboardItem(
            id=po.id,
            po_number=po.po_number,
            sales_order_number=sales_order_number,
            customer_name=customer_name,
            part_number=po.part_number.part_number if po.part_number else "",
            part_description=po.part_number.description if po.part_number else None,
            quantity=po.quantity,
            quantity_completed=po.quantity_completed,
            quantity_shipped=int(shipped_quantity),
            quantity_scrapped=po.quantity_scrapped,
            status=po.status,
            due_date=po.due_date,
            risk_status=risk,
            completion_percentage=completion
        ))
    
    return dashboard_items

@router.get("/work-center-load")
async def get_work_center_load(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get work center load data"""
    # Count operations by work center and status
    from models import WorkCenter
    
    work_centers = db.query(WorkCenter).all()
    
    load_data = []
    for wc in work_centers:
        pending = db.query(TravelSheetOperation).filter(
            TravelSheetOperation.work_center_id == wc.id,
            TravelSheetOperation.status == 'Pending'
        ).count()
        
        in_progress = db.query(TravelSheetOperation).filter(
            TravelSheetOperation.work_center_id == wc.id,
            TravelSheetOperation.status == 'In Progress'
        ).count()
        
        completed = db.query(TravelSheetOperation).filter(
            TravelSheetOperation.work_center_id == wc.id,
            TravelSheetOperation.status == 'Completed'
        ).count()
        
        load_data.append({
            "work_center_id": wc.id,
            "work_center_name": wc.name,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "total": pending + in_progress + completed
        })
    
    return load_data

@router.get("/daily-production")
async def get_daily_production(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get daily production statistics"""
    from datetime import datetime, timedelta
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Get completed operations by day
    operations = db.query(
        func.date(TravelSheetOperation.end_time).label('date'),
        func.sum(TravelSheetOperation.quantity_good).label('good'),
        func.sum(TravelSheetOperation.quantity_scrap).label('scrap')
    ).filter(
        TravelSheetOperation.status == 'Completed',
        TravelSheetOperation.end_time >= start_date
    ).group_by(func.date(TravelSheetOperation.end_time)).all()
    
    daily_data = []
    for op in operations:
        daily_data.append({
            "date": str(op.date),
            "good": int(op.good) if op.good else 0,
            "scrap": int(op.scrap) if op.scrap else 0
        })
    
    return daily_data
