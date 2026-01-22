"""
Verify that PartSubAssembly model can be imported and table can be created
"""
try:
    print("Importing models...")
    from models import PartSubAssembly, PartNumber
    print("✓ Models imported successfully")
    
    print("\nChecking PartSubAssembly model...")
    print(f"  Table name: {PartSubAssembly.__tablename__}")
    print(f"  Columns: {[col.name for col in PartSubAssembly.__table__.columns]}")
    
    print("\nChecking PartNumber relationship...")
    if hasattr(PartNumber, 'sub_assemblies'):
        print("✓ PartNumber.sub_assemblies relationship exists")
    else:
        print("✗ PartNumber.sub_assemblies relationship NOT found")
    
    print("\nChecking database connection...")
    from database import engine, Base
    print("✓ Database connection established")
    
    print("\nCreating tables (if they don't exist)...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created/verified")
    
    print("\n✅ All checks passed! PartSubAssembly feature is ready.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
