"""
Script to import data from Excel spreadsheet into Aurexia database
Based on the client's existing Excel database structure
"""
import pandas as pd
from database import SessionLocal
from models import Customer, PartNumber, Process, PartRouting, Material
from sqlalchemy.exc import IntegrityError
import sys

def import_excel_data(excel_file_path):
    """
    Import data from Excel file to database
    Expected columns: Part Number, Customer, Description, Material, 
                     Laser Cut, Machining, Cleaning, Bending, Assembly, Painting, Galvanizing
    """
    db = SessionLocal()
    
    try:
        # Read Excel file
        print(f"Reading Excel file: {excel_file_path}")
        df = pd.read_excel(excel_file_path)
        
        print(f"Found {len(df)} rows")
        
        # Get or create processes
        process_map = {
            'Laser Cut': get_or_create_process(db, 'LASER_CUT', 'Laser Cut'),
            'Machining': get_or_create_process(db, 'MACHINING', 'Machining'),
            'Cleaning': get_or_create_process(db, 'CLEANING', 'Cleaning'),
            'Bending': get_or_create_process(db, 'BENDING', 'Bending'),
            'Assembly': get_or_create_process(db, 'ASSEMBLY', 'Assembly'),
            'Painting': get_or_create_process(db, 'PAINTING', 'Painting'),
            'Galvanizing': get_or_create_process(db, 'GALVANIZING', 'Galvanizing'),
        }
        
        # Process each row
        for index, row in df.iterrows():
            try:
                # Get or create customer
                customer_name = str(row.get('Customer', '')).strip()
                if customer_name and customer_name != 'nan':
                    customer = get_or_create_customer(db, customer_name)
                    customer_id = customer.id
                else:
                    customer_id = None
                
                # Create or update part number
                part_number = str(row.get('Part Number', '')).strip()
                if not part_number or part_number == 'nan':
                    print(f"Row {index + 2}: Skipping - no part number")
                    continue
                
                description = str(row.get('Description', '')).strip()
                if description == 'nan':
                    description = None
                
                material_type = str(row.get('Material', '')).strip()
                if material_type == 'nan':
                    material_type = None
                
                # Check if part number exists
                existing_part = db.query(PartNumber).filter(
                    PartNumber.part_number == part_number
                ).first()
                
                if existing_part:
                    print(f"Row {index + 2}: Updating existing part {part_number}")
                    db_part = existing_part
                    db_part.description = description
                    db_part.material_type = material_type
                    if customer_id:
                        db_part.customer_id = customer_id
                    
                    # Delete existing routings
                    db.query(PartRouting).filter(
                        PartRouting.part_number_id == db_part.id
                    ).delete()
                else:
                    print(f"Row {index + 2}: Creating new part {part_number}")
                    db_part = PartNumber(
                        part_number=part_number,
                        description=description,
                        material_type=material_type,
                        customer_id=customer_id
                    )
                    db.add(db_part)
                    db.flush()
                
                # Create routings based on process times
                sequence = 1
                for process_name, process in process_map.items():
                    time_value = row.get(process_name, 0)
                    
                    # Handle different time formats
                    if pd.isna(time_value) or time_value == '' or time_value == 0:
                        continue
                    
                    try:
                        time_minutes = float(time_value)
                        if time_minutes > 0:
                            routing = PartRouting(
                                part_number_id=db_part.id,
                                process_id=process.id,
                                sequence_number=sequence,
                                standard_time_minutes=time_minutes
                            )
                            db.add(routing)
                            sequence += 1
                    except (ValueError, TypeError):
                        print(f"  Warning: Invalid time value for {process_name}: {time_value}")
                        continue
                
                db.commit()
                print(f"  ✓ Successfully imported {part_number} with {sequence - 1} processes")
                
            except IntegrityError as e:
                db.rollback()
                print(f"Row {index + 2}: IntegrityError - {str(e)}")
                continue
            except Exception as e:
                db.rollback()
                print(f"Row {index + 2}: Error - {str(e)}")
                continue
        
        print("\n" + "="*50)
        print("Import completed!")
        print("="*50)
        
        # Print summary
        total_parts = db.query(PartNumber).count()
        total_customers = db.query(Customer).count()
        total_routings = db.query(PartRouting).count()
        
        print(f"\nDatabase Summary:")
        print(f"  Total Part Numbers: {total_parts}")
        print(f"  Total Customers: {total_customers}")
        print(f"  Total Routings: {total_routings}")
        
    except FileNotFoundError:
        print(f"Error: File not found - {excel_file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

def get_or_create_customer(db, customer_name):
    """Get existing customer or create new one"""
    # Generate code from name
    code = customer_name.replace(' ', '_').upper()[:50]
    
    customer = db.query(Customer).filter(Customer.code == code).first()
    if not customer:
        customer = db.query(Customer).filter(Customer.name == customer_name).first()
    
    if not customer:
        customer = Customer(
            code=code,
            name=customer_name,
            is_active=True
        )
        db.add(customer)
        db.flush()
        print(f"  Created customer: {customer_name}")
    
    return customer

def get_or_create_process(db, code, name):
    """Get existing process or create new one"""
    process = db.query(Process).filter(Process.code == code).first()
    
    if not process:
        # Get default work center
        from models import WorkCenter
        work_center = db.query(WorkCenter).first()
        
        if not work_center:
            print("Error: No work centers found. Run init_db.py first!")
            sys.exit(1)
        
        process = Process(
            code=code,
            name=name,
            work_center_id=work_center.id
        )
        db.add(process)
        db.flush()
    
    return process

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_excel_data.py <path_to_excel_file>")
        print("\nExample:")
        print("  python import_excel_data.py ../data/part_numbers.xlsx")
        print("\nExpected Excel columns:")
        print("  - Part Number (required)")
        print("  - Customer")
        print("  - Description")
        print("  - Material")
        print("  - Laser Cut (time in minutes)")
        print("  - Machining (time in minutes)")
        print("  - Cleaning (time in minutes)")
        print("  - Bending (time in minutes)")
        print("  - Assembly (time in minutes)")
        print("  - Painting (time in minutes)")
        print("  - Galvanizing (time in minutes)")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    import_excel_data(excel_file)
