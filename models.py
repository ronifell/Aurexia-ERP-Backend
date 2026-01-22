"""
SQLAlchemy ORM Models for Aurexia ERP
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Numeric, Text, ForeignKey, TIMESTAMP, func, JSON
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    can_view_prices = Column(Boolean, default=False)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"))
    badge_id = Column(String(50), unique=True, index=True)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    role = relationship("Role", back_populates="users")

class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    table_name = Column(String(50))
    record_id = Column(Integer)
    details = Column(JSON)
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(Text)
    contact_person = Column(String(100))
    phone = Column(String(50))
    email = Column(String(100))
    delivery_frequency = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    part_numbers = relationship("PartNumber", back_populates="customer")
    sales_orders = relationship("SalesOrder", back_populates="customer")

class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(Text)
    contact_person = Column(String(100))
    phone = Column(String(50))
    email = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Material(Base):
    __tablename__ = "materials"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50))
    unit = Column(String(20))
    current_stock = Column(Numeric(10, 2), default=0)
    minimum_stock = Column(Numeric(10, 2))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class WorkCenter(Base):
    __tablename__ = "work_centers"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    machines = relationship("Machine", back_populates="work_center")
    processes = relationship("Process", back_populates="work_center")

class Machine(Base):
    __tablename__ = "machines"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    work_center_id = Column(Integer, ForeignKey("work_centers.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    work_center = relationship("WorkCenter", back_populates="machines")

class Process(Base):
    __tablename__ = "processes"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    work_center_id = Column(Integer, ForeignKey("work_centers.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    work_center = relationship("WorkCenter", back_populates="processes")
    part_routings = relationship("PartRouting", back_populates="process")

class PartNumber(Base):
    __tablename__ = "part_numbers"
    
    id = Column(Integer, primary_key=True, index=True)
    part_number = Column(String(100), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    description = Column(Text)
    material_type = Column(String(100))
    unit_price = Column(Numeric(10, 2))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    customer = relationship("Customer", back_populates="part_numbers")
    routings = relationship("PartRouting", back_populates="part_number", cascade="all, delete-orphan")
    materials = relationship("PartMaterial", back_populates="part_number", cascade="all, delete-orphan")
    sub_assemblies = relationship(
        "PartSubAssembly",
        primaryjoin="PartNumber.id == PartSubAssembly.parent_part_id",
        back_populates="parent_part",
        cascade="all, delete-orphan"
    )

class PartRouting(Base):
    __tablename__ = "part_routings"
    
    id = Column(Integer, primary_key=True, index=True)
    part_number_id = Column(Integer, ForeignKey("part_numbers.id", ondelete="CASCADE"))
    process_id = Column(Integer, ForeignKey("processes.id"))
    sequence_number = Column(Integer, nullable=False)
    standard_time_minutes = Column(Numeric(8, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    part_number = relationship("PartNumber", back_populates="routings")
    process = relationship("Process", back_populates="part_routings")

class PartMaterial(Base):
    __tablename__ = "part_materials"
    
    id = Column(Integer, primary_key=True, index=True)
    part_number_id = Column(Integer, ForeignKey("part_numbers.id", ondelete="CASCADE"))
    material_id = Column(Integer, ForeignKey("materials.id"))
    quantity = Column(Numeric(10, 4), nullable=False)  # Quantity per unit of part
    unit = Column(String(20))  # Unit of measurement (kg, m, pcs, etc.)
    scrap_percentage = Column(Numeric(5, 2), default=0)  # Scrap percentage (0-100)
    notes = Column(Text)  # Optional notes about this material requirement
    created_at = Column(DateTime, default=datetime.utcnow)
    
    part_number = relationship("PartNumber", back_populates="materials")
    material = relationship("Material")

class PartSubAssembly(Base):
    __tablename__ = "part_sub_assemblies"
    
    id = Column(Integer, primary_key=True, index=True)
    parent_part_id = Column(Integer, ForeignKey("part_numbers.id", ondelete="CASCADE"), nullable=False)
    child_part_id = Column(Integer, ForeignKey("part_numbers.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Numeric(10, 4), nullable=False)  # Quantity of child part per unit of parent part
    unit = Column(String(20))  # Unit of measurement (pcs, units, etc.)
    notes = Column(Text)  # Optional notes about this sub-assembly requirement
    created_at = Column(DateTime, default=datetime.utcnow)
    
    parent_part = relationship("PartNumber", foreign_keys=[parent_part_id], back_populates="sub_assemblies")
    child_part = relationship("PartNumber", foreign_keys=[child_part_id])

class SalesOrder(Base):
    __tablename__ = "sales_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(100), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    order_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(20), default='Open', index=True)
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    customer = relationship("Customer", back_populates="sales_orders")
    items = relationship("SalesOrderItem", back_populates="sales_order", cascade="all, delete-orphan")

class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id", ondelete="CASCADE"))
    part_number_id = Column(Integer, ForeignKey("part_numbers.id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2))
    total_price = Column(Numeric(12, 2))
    quantity_produced = Column(Integer, default=0)
    quantity_shipped = Column(Integer, default=0)
    status = Column(String(20), default='Pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sales_order = relationship("SalesOrder", back_populates="items")
    part_number = relationship("PartNumber")

class InventoryBatch(Base):
    __tablename__ = "inventory_batches"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_number = Column(String(100), unique=True, nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"))
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    heat_number = Column(String(100), index=True)
    lot_number = Column(String(100))
    quantity = Column(Numeric(10, 2), nullable=False)
    remaining_quantity = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(20))
    received_date = Column(Date)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    movement_type = Column(String(20), nullable=False)
    batch_id = Column(Integer, ForeignKey("inventory_batches.id"))
    material_id = Column(Integer, ForeignKey("materials.id"))
    quantity = Column(Numeric(10, 2), nullable=False)
    reference_type = Column(String(50))
    reference_id = Column(Integer)
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class ProductionOrder(Base):
    __tablename__ = "production_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(100), unique=True, nullable=False, index=True)
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"))
    sales_order_item_id = Column(Integer, ForeignKey("sales_order_items.id"))
    part_number_id = Column(Integer, ForeignKey("part_numbers.id"), index=True)
    quantity = Column(Integer, nullable=False)
    quantity_completed = Column(Integer, default=0)
    quantity_scrapped = Column(Integer, default=0)
    status = Column(String(20), default='Created', index=True)
    start_date = Column(Date)
    due_date = Column(Date)
    priority = Column(String(20), default='Normal')
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    travel_sheets = relationship("TravelSheet", back_populates="production_order", cascade="all, delete-orphan")
    part_number = relationship("PartNumber")

class TravelSheet(Base):
    __tablename__ = "travel_sheets"
    
    id = Column(Integer, primary_key=True, index=True)
    travel_sheet_number = Column(String(100), unique=True, nullable=False)
    production_order_id = Column(Integer, ForeignKey("production_orders.id", ondelete="CASCADE"))
    qr_code = Column(Text, unique=True, nullable=False)
    batch_number = Column(String(100))
    status = Column(String(20), default='Active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    production_order = relationship("ProductionOrder", back_populates="travel_sheets")
    operations = relationship("TravelSheetOperation", back_populates="travel_sheet", cascade="all, delete-orphan")

class TravelSheetOperation(Base):
    __tablename__ = "travel_sheet_operations"
    
    id = Column(Integer, primary_key=True, index=True)
    travel_sheet_id = Column(Integer, ForeignKey("travel_sheets.id", ondelete="CASCADE"))
    process_id = Column(Integer, ForeignKey("processes.id"))
    sequence_number = Column(Integer, nullable=False)
    qr_code = Column(Text, unique=True, nullable=False)
    work_center_id = Column(Integer, ForeignKey("work_centers.id"))
    status = Column(String(20), default='Pending', index=True)
    operator_id = Column(Integer, ForeignKey("users.id"), index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    quantity_good = Column(Integer, default=0)
    quantity_scrap = Column(Integer, default=0)
    quantity_pending = Column(Integer)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_minutes = Column(Integer)
    operator_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    travel_sheet = relationship("TravelSheet", back_populates="operations")
    process = relationship("Process")
    work_center = relationship("WorkCenter")
    operator = relationship("User", foreign_keys=[operator_id])
    machine = relationship("Machine")

class QualityInspection(Base):
    __tablename__ = "quality_inspections"
    
    id = Column(Integer, primary_key=True, index=True)
    travel_sheet_id = Column(Integer, ForeignKey("travel_sheets.id"))
    production_order_id = Column(Integer, ForeignKey("production_orders.id"))
    inspector_id = Column(Integer, ForeignKey("users.id"))
    inspection_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), nullable=False)
    quantity_inspected = Column(Integer)
    quantity_approved = Column(Integer)
    quantity_rejected = Column(Integer)
    rejection_reason = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    travel_sheet = relationship("TravelSheet")
    production_order = relationship("ProductionOrder")
    inspector = relationship("User", foreign_keys=[inspector_id])

class Shipment(Base):
    __tablename__ = "shipments"
    
    id = Column(Integer, primary_key=True, index=True)
    shipment_number = Column(String(100), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"))
    shipment_date = Column(Date, nullable=False)
    status = Column(String(20), default='Prepared')
    tracking_number = Column(String(100))
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer")
    sales_order = relationship("SalesOrder")
    items = relationship("ShipmentItem", back_populates="shipment", cascade="all, delete-orphan")

class ShipmentItem(Base):
    __tablename__ = "shipment_items"
    
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id", ondelete="CASCADE"))
    sales_order_item_id = Column(Integer, ForeignKey("sales_order_items.id"))
    part_number_id = Column(Integer, ForeignKey("part_numbers.id"))
    production_order_id = Column(Integer, ForeignKey("production_orders.id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    shipment = relationship("Shipment", back_populates="items")
    part_number = relationship("PartNumber")
    production_order = relationship("ProductionOrder")