"""
Initialize database with default data
"""
from database import SessionLocal, engine, Base
from models import Role, User, WorkCenter, Machine, Process
from auth import get_password_hash

def init_database():
    """Initialize database with default data"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if roles already exist
        existing_roles = db.query(Role).count()
        if existing_roles == 0:
            print("Creating default roles...")
            roles = [
                Role(name="Admin", can_view_prices=True, description="System administrator"),
                Role(name="Management", can_view_prices=True, description="Management and direction"),
                Role(name="Quality", can_view_prices=False, description="Quality control personnel"),
                Role(name="Operator", can_view_prices=False, description="Production operators"),
                Role(name="Supervisor", can_view_prices=False, description="Production supervisors"),
                Role(name="Planner", can_view_prices=False, description="Production planners"),
                Role(name="Warehouse", can_view_prices=True, description="Warehouse personnel"),
                Role(name="Shipping", can_view_prices=True, description="Shipping personnel"),
            ]
            db.add_all(roles)
            db.commit()
            print("Roles created successfully")
        
        # Check if admin user exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("Creating admin user...")
            admin_role = db.query(Role).filter(Role.name == "Admin").first()
            admin = User(
                username="admin",
                email="admin@aurexia.com",
                password_hash=get_password_hash("admin123"),
                full_name="System Administrator",
                badge_id="ADMIN001",
                role_id=admin_role.id if admin_role else None,
                is_active=True
            )
            db.add(admin)
            db.commit()
            print("Admin user created successfully")
            print("Username: admin")
            print("Password: admin123")
        
        # Create default work centers
        existing_work_centers = db.query(WorkCenter).count()
        if existing_work_centers == 0:
            print("Creating default work centers...")
            work_centers = [
                WorkCenter(code="LASER", name="Laser Cutting", description="Laser cutting station"),
                WorkCenter(code="BEND", name="Bending", description="Bending station"),
                WorkCenter(code="MACH", name="Machining", description="Machining station"),
                WorkCenter(code="WELD", name="Welding", description="Welding station"),
                WorkCenter(code="PAINT", name="Painting", description="Painting station"),
                WorkCenter(code="GALV", name="Galvanizing", description="Galvanizing station"),
                WorkCenter(code="CLEAN", name="Cleaning", description="Cleaning station"),
                WorkCenter(code="QC", name="Quality Control", description="Quality inspection"),
            ]
            db.add_all(work_centers)
            db.commit()
            print("Work centers created successfully")
            
            # Create processes
            print("Creating default processes...")
            laser_wc = db.query(WorkCenter).filter(WorkCenter.code == "LASER").first()
            bend_wc = db.query(WorkCenter).filter(WorkCenter.code == "BEND").first()
            mach_wc = db.query(WorkCenter).filter(WorkCenter.code == "MACH").first()
            paint_wc = db.query(WorkCenter).filter(WorkCenter.code == "PAINT").first()
            galv_wc = db.query(WorkCenter).filter(WorkCenter.code == "GALV").first()
            clean_wc = db.query(WorkCenter).filter(WorkCenter.code == "CLEAN").first()
            qc_wc = db.query(WorkCenter).filter(WorkCenter.code == "QC").first()
            
            processes = [
                Process(code="LASER_CUT", name="Laser Cut", work_center_id=laser_wc.id if laser_wc else None),
                Process(code="DOBLEZ", name="Doblez", work_center_id=bend_wc.id if bend_wc else None),
                Process(code="MACHINING", name="Machining", work_center_id=mach_wc.id if mach_wc else None),
                Process(code="CLEANING", name="Cleaning", work_center_id=clean_wc.id if clean_wc else None),
                Process(code="BENDING", name="Bending", work_center_id=bend_wc.id if bend_wc else None),
                Process(code="ASSEMBLY", name="Assembly", work_center_id=mach_wc.id if mach_wc else None),
                Process(code="PAINTING", name="Painting", work_center_id=paint_wc.id if paint_wc else None),
                Process(code="GALVANIZING", name="Galvanizing", work_center_id=galv_wc.id if galv_wc else None),
                Process(code="QC_FINAL", name="Final Quality Control", work_center_id=qc_wc.id if qc_wc else None),
            ]
            db.add_all(processes)
            db.commit()
            print("Processes created successfully")
        
        print("\nDatabase initialization completed successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
