"""
Migration script to add part_sub_assemblies table
Run this script to add the sub-assemblies feature to the database
"""
from database import engine, Base
from models import PartSubAssembly
from sqlalchemy import text

def add_sub_assemblies_table():
    """Create the part_sub_assemblies table"""
    print("Creating part_sub_assemblies table...")
    
    # Create table using SQLAlchemy
    PartSubAssembly.__table__.create(engine, checkfirst=True)
    
    print("✓ part_sub_assemblies table created successfully!")
    print("\nTable structure:")
    print("  - id: Primary key")
    print("  - parent_part_id: Foreign key to part_numbers (parent)")
    print("  - child_part_id: Foreign key to part_numbers (child/sub-assembly)")
    print("  - quantity: Quantity of child part per unit of parent")
    print("  - unit: Unit of measurement")
    print("  - notes: Optional notes")
    print("  - created_at: Timestamp")

if __name__ == "__main__":
    try:
        add_sub_assemblies_table()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
