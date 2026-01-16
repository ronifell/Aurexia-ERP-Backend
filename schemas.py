"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

# ============================================
# Authentication Schemas
# ============================================

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class Login(BaseModel):
    username: str
    password: str

# ============================================
# User and Role Schemas
# ============================================

class RoleBase(BaseModel):
    name: str
    can_view_prices: bool = False
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    badge_id: Optional[str] = None
    role_id: Optional[int] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    badge_id: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    role: Optional[RoleResponse] = None
    
    class Config:
        from_attributes = True

# ============================================
# Customer Schemas
# ============================================

class CustomerBase(BaseModel):
    code: str
    name: str
    address: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    delivery_frequency: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    delivery_frequency: Optional[str] = None
    is_active: Optional[bool] = None

class CustomerResponse(CustomerBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============================================
# Supplier Schemas
# ============================================

class SupplierBase(BaseModel):
    code: str
    name: str
    address: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class SupplierCreate(SupplierBase):
    pass

class SupplierResponse(SupplierBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============================================
# Material Schemas
# ============================================

class MaterialBase(BaseModel):
    name: str
    type: Optional[str] = None
    unit: Optional[str] = None
    minimum_stock: Optional[Decimal] = None

class MaterialCreate(MaterialBase):
    pass

class MaterialResponse(MaterialBase):
    id: int
    current_stock: Decimal
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============================================
# Work Center and Machine Schemas
# ============================================

class WorkCenterBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None

class WorkCenterCreate(WorkCenterBase):
    pass

class WorkCenterResponse(WorkCenterBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class MachineBase(BaseModel):
    code: str
    name: str
    work_center_id: int

class MachineCreate(MachineBase):
    pass

class MachineResponse(MachineBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============================================
# Process Schemas
# ============================================

class ProcessBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    work_center_id: int

class ProcessCreate(ProcessBase):
    pass

class ProcessResponse(ProcessBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============================================
# Part Number Schemas
# ============================================

class PartRoutingBase(BaseModel):
    process_id: int
    sequence_number: int
    standard_time_minutes: Optional[Decimal] = None

class PartRoutingCreate(PartRoutingBase):
    pass

class PartRoutingResponse(PartRoutingBase):
    id: int
    process: Optional[ProcessResponse] = None
    
    class Config:
        from_attributes = True

class PartNumberBase(BaseModel):
    part_number: str
    customer_id: Optional[int] = None
    description: Optional[str] = None
    material_type: Optional[str] = None
    unit_price: Optional[Decimal] = None

class PartNumberCreate(PartNumberBase):
    routings: Optional[List[PartRoutingCreate]] = []

class PartNumberUpdate(BaseModel):
    description: Optional[str] = None
    material_type: Optional[str] = None
    unit_price: Optional[Decimal] = None
    is_active: Optional[bool] = None

class PartNumberResponse(PartNumberBase):
    id: int
    is_active: bool
    created_at: datetime
    customer: Optional[CustomerResponse] = None
    routings: List[PartRoutingResponse] = []
    
    class Config:
        from_attributes = True

# ============================================
# Sales Order Schemas
# ============================================

class SalesOrderItemBase(BaseModel):
    part_number_id: int
    quantity: int
    unit_price: Optional[Decimal] = None

class SalesOrderItemCreate(SalesOrderItemBase):
    pass

class SalesOrderItemResponse(SalesOrderItemBase):
    id: int
    total_price: Optional[Decimal] = None
    quantity_produced: int
    quantity_shipped: int
    status: str
    part_number: Optional[PartNumberResponse] = None
    
    class Config:
        from_attributes = True

class SalesOrderBase(BaseModel):
    po_number: str
    customer_id: int
    order_date: date
    due_date: date
    status: Optional[str] = 'Open'
    notes: Optional[str] = None

class SalesOrderCreate(SalesOrderBase):
    items: List[SalesOrderItemCreate]

class SalesOrderUpdate(BaseModel):
    po_number: Optional[str] = None
    customer_id: Optional[int] = None
    order_date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[SalesOrderItemCreate]] = None

class SalesOrderResponse(SalesOrderBase):
    id: int
    status: str
    created_at: datetime
    customer: Optional[CustomerResponse] = None
    items: List[SalesOrderItemResponse] = []
    
    class Config:
        from_attributes = True

# ============================================
# Inventory Schemas
# ============================================

class InventoryBatchBase(BaseModel):
    batch_number: str
    material_id: int
    supplier_id: Optional[int] = None
    heat_number: Optional[str] = None
    lot_number: Optional[str] = None
    quantity: Decimal
    unit: Optional[str] = None
    received_date: Optional[date] = None

class InventoryBatchCreate(InventoryBatchBase):
    pass

class InventoryBatchResponse(InventoryBatchBase):
    id: int
    remaining_quantity: Decimal
    created_at: datetime
    
    class Config:
        from_attributes = True

class InventoryMovementBase(BaseModel):
    movement_type: str
    material_id: int
    quantity: Decimal
    batch_id: Optional[int] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    notes: Optional[str] = None

class InventoryMovementCreate(InventoryMovementBase):
    pass

class InventoryMovementResponse(InventoryMovementBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============================================
# Production Order Schemas
# ============================================

class ProductionOrderBase(BaseModel):
    part_number_id: int
    quantity: int
    due_date: Optional[date] = None
    priority: Optional[str] = "Normal"

class ProductionOrderCreate(ProductionOrderBase):
    sales_order_id: Optional[int] = None
    sales_order_item_id: Optional[int] = None

class ProductionOrderUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None

class ProductionOrderResponse(ProductionOrderBase):
    id: int
    po_number: str
    status: str
    quantity_completed: int
    quantity_scrapped: int
    start_date: Optional[date] = None
    created_at: datetime
    part_number: Optional[PartNumberResponse] = None
    
    class Config:
        from_attributes = True

# ============================================
# Travel Sheet Schemas
# ============================================

class TravelSheetOperationBase(BaseModel):
    process_id: int
    sequence_number: int

class TravelSheetOperationCreate(TravelSheetOperationBase):
    pass

class TravelSheetOperationUpdate(BaseModel):
    status: Optional[str] = None
    operator_id: Optional[int] = None
    machine_id: Optional[int] = None
    quantity_good: Optional[int] = None
    quantity_scrap: Optional[int] = None
    quantity_pending: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    operator_notes: Optional[str] = None

class TravelSheetOperationResponse(TravelSheetOperationBase):
    id: int
    qr_code: str
    status: str
    operator_id: Optional[int] = None
    machine_id: Optional[int] = None
    quantity_good: int
    quantity_scrap: int
    quantity_pending: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    operator_notes: Optional[str] = None
    process: Optional[ProcessResponse] = None
    
    class Config:
        from_attributes = True

class TravelSheetBase(BaseModel):
    production_order_id: int
    batch_number: Optional[str] = None

class TravelSheetCreate(TravelSheetBase):
    pass

class TravelSheetResponse(TravelSheetBase):
    id: int
    travel_sheet_number: str
    qr_code: str
    status: str
    created_at: datetime
    operations: List[TravelSheetOperationResponse] = []
    
    class Config:
        from_attributes = True

# ============================================
# Quality Inspection Schemas
# ============================================

class QualityInspectionBase(BaseModel):
    travel_sheet_id: Optional[int] = None
    production_order_id: int
    status: str
    quantity_inspected: Optional[int] = None
    quantity_approved: Optional[int] = None
    quantity_rejected: Optional[int] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None

class QualityInspectionCreate(QualityInspectionBase):
    pass

class QualityInspectionResponse(QualityInspectionBase):
    id: int
    inspector_id: Optional[int] = None
    inspection_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============================================
# Shipment Schemas
# ============================================

class ShipmentItemBase(BaseModel):
    sales_order_item_id: int
    part_number_id: int
    production_order_id: Optional[int] = None
    quantity: int
    unit_price: Optional[Decimal] = None

class ShipmentItemCreate(ShipmentItemBase):
    pass

class ShipmentItemResponse(ShipmentItemBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ShipmentBase(BaseModel):
    customer_id: int
    sales_order_id: Optional[int] = None
    shipment_date: date
    tracking_number: Optional[str] = None
    notes: Optional[str] = None

class ShipmentCreate(ShipmentBase):
    items: List[ShipmentItemCreate]

class ShipmentResponse(ShipmentBase):
    id: int
    shipment_number: str
    status: str
    created_at: datetime
    items: List[ShipmentItemResponse] = []
    
    class Config:
        from_attributes = True

# ============================================
# Dashboard Schemas
# ============================================

class DashboardStats(BaseModel):
    total_open_orders: int
    total_in_production: int
    total_delayed: int
    total_at_risk: int
    total_on_time: int

class ProductionDashboardItem(BaseModel):
    id: int
    po_number: str
    sales_order_number: Optional[str] = None
    customer_name: Optional[str] = None
    part_number: str
    part_description: Optional[str] = None
    quantity: int
    quantity_completed: int
    quantity_scrapped: int
    status: str
    due_date: Optional[date] = None
    risk_status: str
    completion_percentage: float
    
    class Config:
        from_attributes = True

# ============================================
# QR Scan Schemas
# ============================================

class QRScanRequest(BaseModel):
    qr_code: str
    badge_id: str

class QRScanResponse(BaseModel):
    success: bool
    message: str
    operation_id: Optional[int] = None
    travel_sheet_id: Optional[int] = None
    process_name: Optional[str] = None
    status: Optional[str] = None
