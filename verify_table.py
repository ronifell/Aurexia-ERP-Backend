"""Verify part_materials table exists"""
from database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()

print("Database tables:")
for table in sorted(tables):
    print(f"  - {table}")

if 'part_materials' in tables:
    print("\nSUCCESS: part_materials table exists!")
    # Check columns
    columns = inspector.get_columns('part_materials')
    print("\nTable columns:")
    for col in columns:
        print(f"  - {col['name']} ({col['type']})")
else:
    print("\nWARNING: part_materials table NOT found")
    print("The table will be created when the server starts")
