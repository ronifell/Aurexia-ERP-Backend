"""
Part Number management routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from database import get_db
from models import User, PartNumber, PartRouting, PartMaterial, PartSubAssembly, Customer, Material
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
    query = db.query(PartNumber).options(
        joinedload(PartNumber.materials).joinedload(PartMaterial.material),
        joinedload(PartNumber.sub_assemblies).joinedload(PartSubAssembly.child_part),
        joinedload(PartNumber.routings).joinedload(PartRouting.process),
        joinedload(PartNumber.customer)
    )
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
    part_number = db.query(PartNumber).options(
        joinedload(PartNumber.materials).joinedload(PartMaterial.material),
        joinedload(PartNumber.sub_assemblies).joinedload(PartSubAssembly.child_part),
        joinedload(PartNumber.routings).joinedload(PartRouting.process),
        joinedload(PartNumber.customer)
    ).filter(PartNumber.id == part_number_id).first()
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
    part_data = part_number.model_dump(exclude={'routings', 'materials', 'sub_assemblies'})
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
    
    # Create materials (BOM)
    if part_number.materials:
        # Check for duplicate materials
        material_ids = [m.material_id for m in part_number.materials]
        if len(material_ids) != len(set(material_ids)):
            raise HTTPException(status_code=400, detail="Duplicate materials are not allowed")
        
        # Validate materials exist and quantities
        for material in part_number.materials:
            # Validate material exists
            material_exists = db.query(Material).filter(Material.id == material.material_id).first()
            if not material_exists:
                raise HTTPException(status_code=400, detail=f"Material with ID {material.material_id} not found")
            
            # Validate quantity > 0
            if material.quantity <= 0:
                raise HTTPException(status_code=400, detail="Material quantity must be greater than 0")
        
        # Create materials
        for material in part_number.materials:
            db_material = PartMaterial(
                part_number_id=db_part.id,
                **material.model_dump()
            )
            db.add(db_material)
    
    # Create sub-assemblies
    if part_number.sub_assemblies:
        # Check for duplicate sub-assemblies
        child_part_ids = [sa.child_part_id for sa in part_number.sub_assemblies]
        if len(child_part_ids) != len(set(child_part_ids)):
            raise HTTPException(status_code=400, detail="Duplicate sub-assemblies are not allowed")
        
        # Validate sub-assemblies exist and prevent circular references
        for sub_assembly in part_number.sub_assemblies:
            # Prevent part from containing itself
            if sub_assembly.child_part_id == db_part.id:
                raise HTTPException(status_code=400, detail="A part cannot contain itself as a sub-assembly")
            
            # Validate child part exists
            child_part = db.query(PartNumber).filter(PartNumber.id == sub_assembly.child_part_id).first()
            if not child_part:
                raise HTTPException(status_code=400, detail=f"Part number with ID {sub_assembly.child_part_id} not found")
            
            # Validate quantity > 0 (handled by schema, but double-check)
            if sub_assembly.quantity <= 0:
                raise HTTPException(status_code=400, detail="Sub-assembly quantity must be greater than 0")
        
        # Create sub-assemblies
        for sub_assembly in part_number.sub_assemblies:
            db_sub_assembly = PartSubAssembly(
                parent_part_id=db_part.id,
                **sub_assembly.model_dump()
            )
            db.add(db_sub_assembly)
    
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
    part_number = db.query(PartNumber).options(
        joinedload(PartNumber.materials).joinedload(PartMaterial.material),
        joinedload(PartNumber.sub_assemblies).joinedload(PartSubAssembly.child_part),
        joinedload(PartNumber.routings).joinedload(PartRouting.process),
        joinedload(PartNumber.customer)
    ).filter(PartNumber.id == part_number_id).first()
    if not part_number:
        raise HTTPException(status_code=404, detail="Part number not found")
    
    update_data = part_number_update.model_dump(exclude_unset=True, exclude={'materials', 'sub_assemblies'})
    for field, value in update_data.items():
        setattr(part_number, field, value)
    
    # Update materials if provided (explicitly set in request)
    if part_number_update.materials is not None:
        # Delete existing materials
        db.query(PartMaterial).filter(PartMaterial.part_number_id == part_number_id).delete()
        
        # Validate and create new materials (if any)
        if part_number_update.materials:
            # Check for duplicate materials
            material_ids = [m.material_id for m in part_number_update.materials]
            if len(material_ids) != len(set(material_ids)):
                raise HTTPException(status_code=400, detail="Duplicate materials are not allowed")
            
            # Validate materials exist and quantities
            for material in part_number_update.materials:
                # Validate material exists
                material_exists = db.query(Material).filter(Material.id == material.material_id).first()
                if not material_exists:
                    raise HTTPException(status_code=400, detail=f"Material with ID {material.material_id} not found")
                
                # Validate quantity > 0
                if material.quantity <= 0:
                    raise HTTPException(status_code=400, detail="Material quantity must be greater than 0")
            
            # Create new materials
            for material in part_number_update.materials:
                db_material = PartMaterial(
                    part_number_id=part_number_id,
                    **material.model_dump()
                )
                db.add(db_material)
    
    # Update sub-assemblies if provided (explicitly set in request)
    if part_number_update.sub_assemblies is not None:
        # Delete existing sub-assemblies
        db.query(PartSubAssembly).filter(PartSubAssembly.parent_part_id == part_number_id).delete()
        
        # Validate and create new sub-assemblies (if any)
        if part_number_update.sub_assemblies:
            # Check for duplicate sub-assemblies
            child_part_ids = [sa.child_part_id for sa in part_number_update.sub_assemblies]
            if len(child_part_ids) != len(set(child_part_ids)):
                raise HTTPException(status_code=400, detail="Duplicate sub-assemblies are not allowed")
            
            # Validate sub-assemblies exist and prevent circular references
            for sub_assembly in part_number_update.sub_assemblies:
                # Prevent part from containing itself
                if sub_assembly.child_part_id == part_number_id:
                    raise HTTPException(status_code=400, detail="A part cannot contain itself as a sub-assembly")
                
                # Validate child part exists
                child_part = db.query(PartNumber).filter(PartNumber.id == sub_assembly.child_part_id).first()
                if not child_part:
                    raise HTTPException(status_code=400, detail=f"Part number with ID {sub_assembly.child_part_id} not found")
                
                # Validate quantity > 0
                if sub_assembly.quantity <= 0:
                    raise HTTPException(status_code=400, detail="Sub-assembly quantity must be greater than 0")
            
            # Create new sub-assemblies
            for sub_assembly in part_number_update.sub_assemblies:
                db_sub_assembly = PartSubAssembly(
                    parent_part_id=part_number_id,
                    **sub_assembly.model_dump()
                )
                db.add(db_sub_assembly)
    
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
