"""
Clear Archived Data Script for Aurexia ERP
Deletes all transactional data and most master data
Preserves only: Admin user, Roles, Work Centers, Machines, Processes, Materials, Suppliers
"""
from sqlalchemy.orm import Session
from database import SessionLocal
from models import (
    ShipmentItem, Shipment, QualityInspection,
    TravelSheetOperation, TravelSheet, ProductionOrder,
    SalesOrderItem, SalesOrder, InventoryMovement, InventoryBatch,
    AuditLog, Customer, PartNumber, PartRouting, User
)

def clear_archived_data(db: Session, clear_audit_log=False):
    """
    Clear all transactional data and most master data
    
    Keeps:
    - Admin user (username: admin)
    - Roles
    - Work centers, machines, processes
    - Suppliers, materials
    
    Deletes:
    - All orders, shipments, production data, quality inspections
    - Inventory transactions and batches
    - Customers
    - Part numbers and routings
    - Users (except admin)
    - Optionally: audit logs
    """
    try:
        print("\n" + "="*60)
        print("CLEARING ALL DATA (EXCEPT ADMIN & CORE CONFIG)")
        print("="*60)
        
        # Count records before deletion
        shipment_items_count = db.query(ShipmentItem).count()
        shipments_count = db.query(Shipment).count()
        quality_count = db.query(QualityInspection).count()
        travel_ops_count = db.query(TravelSheetOperation).count()
        travel_sheets_count = db.query(TravelSheet).count()
        production_orders_count = db.query(ProductionOrder).count()
        sales_items_count = db.query(SalesOrderItem).count()
        sales_orders_count = db.query(SalesOrder).count()
        inventory_movements_count = db.query(InventoryMovement).count()
        inventory_batches_count = db.query(InventoryBatch).count()
        audit_log_count = db.query(AuditLog).count()
        
        # Master data counts
        part_routings_count = db.query(PartRouting).count()
        part_numbers_count = db.query(PartNumber).count()
        customers_count = db.query(Customer).count()
        users_count = db.query(User).filter(User.username != 'admin').count()
        
        print("\n[INFO] Transactional data to be deleted:")
        print(f"   - Shipment Items: {shipment_items_count}")
        print(f"   - Shipments: {shipments_count}")
        print(f"   - Quality Inspections: {quality_count}")
        print(f"   - Travel Sheet Operations: {travel_ops_count}")
        print(f"   - Travel Sheets: {travel_sheets_count}")
        print(f"   - Production Orders: {production_orders_count}")
        print(f"   - Sales Order Items: {sales_items_count}")
        print(f"   - Sales Orders: {sales_orders_count}")
        print(f"   - Inventory Movements: {inventory_movements_count}")
        print(f"   - Inventory Batches: {inventory_batches_count}")
        
        print("\n[INFO] Master data to be deleted:")
        print(f"   - Part Routings: {part_routings_count}")
        print(f"   - Part Numbers: {part_numbers_count}")
        print(f"   - Customers: {customers_count}")
        print(f"   - Users (except admin): {users_count}")
        
        if clear_audit_log:
            print(f"\n[INFO] Audit log entries: {audit_log_count}")
        
        total_records = (shipment_items_count + shipments_count + quality_count + 
                        travel_ops_count + travel_sheets_count + production_orders_count +
                        sales_items_count + sales_orders_count + inventory_movements_count +
                        inventory_batches_count + part_routings_count + part_numbers_count +
                        customers_count + users_count)
        
        if clear_audit_log:
            total_records += audit_log_count
        
        if total_records == 0:
            print("\n[OK] No data to delete.")
            return
        
        print(f"\n[WARNING] Total records to delete: {total_records}")
        print("[INFO] Admin user will be PRESERVED")
        
        # Ask for confirmation
        response = input("\nAre you sure you want to delete all this data? (yes/no): ")
        if response.lower() != 'yes':
            print("[ERROR] Operation cancelled.")
            return
        
        print("\n[INFO] Deleting data in proper order...")
        
        # Delete in reverse order of dependencies
        # 1. Shipment items (depends on shipments)
        deleted = db.query(ShipmentItem).delete()
        print(f"   [OK] Deleted {deleted} shipment items")
        
        # 2. Shipments
        deleted = db.query(Shipment).delete()
        print(f"   [OK] Deleted {deleted} shipments")
        
        # 3. Quality inspections
        deleted = db.query(QualityInspection).delete()
        print(f"   [OK] Deleted {deleted} quality inspections")
        
        # 4. Travel sheet operations (depends on travel sheets)
        deleted = db.query(TravelSheetOperation).delete()
        print(f"   [OK] Deleted {deleted} travel sheet operations")
        
        # 5. Travel sheets (depends on production orders)
        deleted = db.query(TravelSheet).delete()
        print(f"   [OK] Deleted {deleted} travel sheets")
        
        # 6. Production orders
        deleted = db.query(ProductionOrder).delete()
        print(f"   [OK] Deleted {deleted} production orders")
        
        # 7. Sales order items (depends on sales orders)
        deleted = db.query(SalesOrderItem).delete()
        print(f"   [OK] Deleted {deleted} sales order items")
        
        # 8. Sales orders
        deleted = db.query(SalesOrder).delete()
        print(f"   [OK] Deleted {deleted} sales orders")
        
        # 9. Inventory movements
        deleted = db.query(InventoryMovement).delete()
        print(f"   [OK] Deleted {deleted} inventory movements")
        
        # 10. Inventory batches
        deleted = db.query(InventoryBatch).delete()
        print(f"   [OK] Deleted {deleted} inventory batches")
        
        # MASTER DATA
        print("\n[INFO] Deleting master data...")
        
        # 11. Part routings (depends on part numbers)
        deleted = db.query(PartRouting).delete()
        print(f"   [OK] Deleted {deleted} part routings")
        
        # 12. Part numbers
        deleted = db.query(PartNumber).delete()
        print(f"   [OK] Deleted {deleted} part numbers")
        
        # 13. Customers
        deleted = db.query(Customer).delete()
        print(f"   [OK] Deleted {deleted} customers")
        
        # 14. Users (except admin)
        deleted = db.query(User).filter(User.username != 'admin').delete(synchronize_session=False)
        print(f"   [OK] Deleted {deleted} users (admin preserved)")
        
        # 15. Audit log (optional)
        if clear_audit_log:
            deleted = db.query(AuditLog).delete()
            print(f"   [OK] Deleted {deleted} audit log entries")
        
        # Commit the transaction
        db.commit()
        
        print("\n" + "="*60)
        print("[OK] ALL DATA DELETED SUCCESSFULLY!")
        print("="*60)
        print("\n[INFO] Preserved data:")
        print("   [OK] Admin user (username: admin)")
        print("   [OK] Roles")
        print("   [OK] Suppliers, Materials")
        print("   [OK] Work Centers, Machines, Processes")
        print("\n[INFO] Deleted data:")
        print("   [OK] All customers, part numbers, and routings")
        print("   [OK] All users (except admin)")
        print("   [OK] All transactional data")
        print("\n[INFO] Your database is clean and ready for test data.")
        
    except Exception as e:
        print(f"\n[ERROR] Error clearing archived data: {str(e)}")
        db.rollback()
        raise


def main():
    """Main function with menu"""
    print("\n" + "="*60)
    print("AUREXIA ERP - CLEAR ALL DATA")
    print("="*60)
    print("\nThis script will delete ALL transactional data:")
    print("  - Sales Orders")
    print("  - Production Orders")
    print("  - Travel Sheets")
    print("  - Quality Inspections")
    print("  - Shipments")
    print("  - Inventory Batches and Movements")
    print("\nAnd also delete most master data:")
    print("  - Customers")
    print("  - Part Numbers and Routings")
    print("  - Users (except admin)")
    print("\nData that will be PRESERVED:")
    print("  - Admin user (username: admin)")
    print("  - Roles")
    print("  - Suppliers, Materials")
    print("  - Work Centers, Machines, Processes")
    
    print("\n" + "-"*60)
    response = input("\nDo you also want to clear audit logs? (yes/no): ")
    clear_audit = response.lower() == 'yes'
    
    db = SessionLocal()
    try:
        clear_archived_data(db, clear_audit_log=clear_audit)
    finally:
        db.close()


if __name__ == "__main__":
    main()
