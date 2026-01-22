"""
Migration script to add scrap_percentage column to part_materials table
"""
import sys
from sqlalchemy import text
from database import SessionLocal, engine

def add_scrap_percentage_column():
    """Add scrap_percentage column to part_materials table if it doesn't exist"""
    db = SessionLocal()
    try:
        # Check if column already exists
        result = db.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'part_materials' 
            AND column_name = 'scrap_percentage'
        """))
        
        column_exists = result.scalar() > 0
        
        if column_exists:
            print("✓ Column 'scrap_percentage' already exists in 'part_materials' table")
            return
        
        # Add the column
        print("Adding 'scrap_percentage' column to 'part_materials' table...")
        db.execute(text("""
            ALTER TABLE part_materials 
            ADD COLUMN scrap_percentage NUMERIC(5, 2) DEFAULT 0
        """))
        db.commit()
        print("✓ Successfully added 'scrap_percentage' column to 'part_materials' table")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error adding column: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Adding scrap_percentage column to part_materials table")
    print("=" * 60)
    add_scrap_percentage_column()
    print("=" * 60)
    print("Migration completed!")
    print("=" * 60)
