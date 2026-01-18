"""
Materials and Inventory management routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import User, Material, Supplier, InventoryBatch, InventoryMovement
from schemas import (
    MaterialResponse, MaterialCreate, MaterialUpdate,
    SupplierResponse, SupplierCreate, SupplierUpdate,
    InventoryBatchResponse, InventoryBatchCreate,
    InventoryMovementResponse, InventoryMovementCreate
)
from auth import get_current_active_user

router = APIRouter(prefix="/materials", tags=["Materials & Inventory"])

# ============================================
# MATERIALS ENDPOINTS
# ============================================

@router.get("/list", response_model=List[MaterialResponse])
async def get_materials(
    skip: int = 0,
    limit: int = 100,
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all materials"""
    query = db.query(Material)
    if type:
        query = query.filter(Material.type == type)
    
    materials = query.offset(skip).limit(limit).all()
    return materials

@router.get("/{material_id}", response_model=MaterialResponse)
async def get_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific material"""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material

@router.post("/", response_model=MaterialResponse)
async def create_material(
    material: MaterialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new material"""
    db_material = Material(**material.model_dump())
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material

@router.put("/{material_id}", response_model=MaterialResponse)
async def update_material(
    material_id: int,
    material_update: MaterialUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a material"""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    update_data = material_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(material, field, value)
    
    db.commit()
    db.refresh(material)
    return material

@router.delete("/{material_id}")
async def delete_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a material"""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    db.delete(material)
    db.commit()
    return {"message": "Material deleted successfully"}

# ============================================
# SUPPLIERS ENDPOINTS
# ============================================

@router.get("/suppliers/list", response_model=List[SupplierResponse])
async def get_suppliers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all suppliers"""
    suppliers = db.query(Supplier).offset(skip).limit(limit).all()
    return suppliers

@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific supplier"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier

@router.post("/suppliers/", response_model=SupplierResponse)
async def create_supplier(
    supplier: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new supplier"""
    # Check if code exists
    existing = db.query(Supplier).filter(Supplier.code == supplier.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Supplier code already exists")
    
    db_supplier = Supplier(**supplier.model_dump())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: int,
    supplier_update: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a supplier"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    update_data = supplier_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)
    
    db.commit()
    db.refresh(supplier)
    return supplier

@router.delete("/suppliers/{supplier_id}")
async def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a supplier"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    db.delete(supplier)
    db.commit()
    return {"message": "Supplier deleted successfully"}

# ============================================
# INVENTORY BATCHES ENDPOINTS
# ============================================

@router.get("/batches/list", response_model=List[InventoryBatchResponse])
async def get_inventory_batches(
    skip: int = 0,
    limit: int = 100,
    material_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all inventory batches"""
    query = db.query(InventoryBatch)
    if material_id:
        query = query.filter(InventoryBatch.material_id == material_id)
    
    batches = query.offset(skip).limit(limit).all()
    return batches

@router.get("/batches/{batch_id}", response_model=InventoryBatchResponse)
async def get_inventory_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific inventory batch"""
    batch = db.query(InventoryBatch).filter(InventoryBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Inventory batch not found")
    return batch

@router.post("/batches/", response_model=InventoryBatchResponse)
async def create_inventory_batch(
    batch: InventoryBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new inventory batch (material receipt)"""
    # Verify material exists
    material = db.query(Material).filter(Material.id == batch.material_id).first()
    if not material:
        raise HTTPException(status_code=400, detail="Material not found")
    
    # Check if batch number exists
    existing = db.query(InventoryBatch).filter(InventoryBatch.batch_number == batch.batch_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Batch number already exists")
    
    # Create batch
    db_batch = InventoryBatch(
        **batch.model_dump(),
        remaining_quantity=batch.quantity,
        created_by=current_user.id
    )
    db.add(db_batch)
    db.flush()
    
    # Update material stock
    material.current_stock += batch.quantity
    
    # Create inventory movement record
    movement = InventoryMovement(
        movement_type='Receipt',
        batch_id=db_batch.id,
        material_id=batch.material_id,
        quantity=batch.quantity,
        reference_type='InventoryBatch',
        reference_id=db_batch.id,
        notes=f"Material receipt - Batch {batch.batch_number}",
        created_by=current_user.id
    )
    db.add(movement)
    
    db.commit()
    db.refresh(db_batch)
    return db_batch

# ============================================
# INVENTORY MOVEMENTS ENDPOINTS
# ============================================

@router.get("/movements/list", response_model=List[InventoryMovementResponse])
async def get_inventory_movements(
    skip: int = 0,
    limit: int = 100,
    material_id: Optional[int] = None,
    movement_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all inventory movements"""
    query = db.query(InventoryMovement)
    if material_id:
        query = query.filter(InventoryMovement.material_id == material_id)
    if movement_type:
        query = query.filter(InventoryMovement.movement_type == movement_type)
    
    movements = query.order_by(InventoryMovement.created_at.desc()).offset(skip).limit(limit).all()
    return movements

@router.post("/movements/", response_model=InventoryMovementResponse)
async def create_inventory_movement(
    movement: InventoryMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new inventory movement"""
    # Verify material exists
    material = db.query(Material).filter(Material.id == movement.material_id).first()
    if not material:
        raise HTTPException(status_code=400, detail="Material not found")
    
    # Verify batch if provided
    if movement.batch_id:
        batch = db.query(InventoryBatch).filter(InventoryBatch.id == movement.batch_id).first()
        if not batch:
            raise HTTPException(status_code=400, detail="Batch not found")
        
        # Check if batch has enough quantity for Issue/Return movements
        if movement.movement_type in ['Issue', 'Adjustment'] and batch.remaining_quantity < movement.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient quantity in batch. Available: {batch.remaining_quantity}")
    
    # Create movement
    db_movement = InventoryMovement(
        **movement.model_dump(),
        created_by=current_user.id
    )
    db.add(db_movement)
    
    # Update material stock and batch quantities based on movement type
    if movement.movement_type == 'Receipt':
        material.current_stock += movement.quantity
        if movement.batch_id:
            batch.remaining_quantity += movement.quantity
    elif movement.movement_type == 'Issue':
        material.current_stock -= movement.quantity
        if movement.batch_id:
            batch.remaining_quantity -= movement.quantity
    elif movement.movement_type == 'Return':
        material.current_stock += movement.quantity
        if movement.batch_id:
            batch.remaining_quantity += movement.quantity
    elif movement.movement_type == 'Adjustment':
        # Adjustment can be positive or negative
        material.current_stock += movement.quantity
        if movement.batch_id:
            batch.remaining_quantity += movement.quantity
    
    db.commit()
    db.refresh(db_movement)
    return db_movement

@router.post("/movements/issue-to-production", response_model=InventoryMovementResponse)
async def issue_material_to_production(
    production_order_id: int,
    material_id: int,
    batch_id: int,
    quantity: float,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Issue material from a batch to a production order
    This creates a traceability link between raw material and production
    """
    from models import ProductionOrder
    
    # Verify production order exists
    po = db.query(ProductionOrder).filter(ProductionOrder.id == production_order_id).first()
    if not po:
        raise HTTPException(status_code=400, detail="Production order not found")
    
    # Verify material and batch
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=400, detail="Material not found")
    
    batch = db.query(InventoryBatch).filter(InventoryBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=400, detail="Batch not found")
    
    if batch.remaining_quantity < quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient quantity in batch. Available: {batch.remaining_quantity}, Requested: {quantity}"
        )
    
    # Create movement
    movement = InventoryMovement(
        movement_type='Issue',
        batch_id=batch_id,
        material_id=material_id,
        quantity=quantity,
        reference_type='ProductionOrder',
        reference_id=production_order_id,
        notes=notes or f"Material issued to PO {po.po_number}",
        created_by=current_user.id
    )
    db.add(movement)
    
    # Update quantities
    material.current_stock -= quantity
    batch.remaining_quantity -= quantity
    
    db.commit()
    db.refresh(movement)
    return movement
