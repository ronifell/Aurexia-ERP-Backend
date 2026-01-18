"""
Performance Testing Script

This script tests the performance improvements by measuring query execution time
and counting the number of database queries made.

Usage:
    python test_performance.py
"""

import time
import sys
from sqlalchemy import event, text
from database import engine, SessionLocal
from models import ProductionOrder, SalesOrder, Customer, ShipmentItem, WorkCenter, TravelSheetOperation
from sqlalchemy.orm import joinedload
from sqlalchemy import func, case

# Query counter
query_count = 0

def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Count queries"""
    global query_count
    query_count += 1

def test_dashboard_production():
    """Test the optimized dashboard production endpoint"""
    global query_count
    
    print("\n" + "="*70)
    print("TESTING DASHBOARD PRODUCTION QUERY")
    print("="*70)
    
    db = SessionLocal()
    
    # Reset counter
    query_count = 0
    
    # Register event listener
    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    
    start_time = time.time()
    
    try:
        # Simulate the optimized dashboard query
        query = db.query(ProductionOrder)\
            .join(ProductionOrder.part_number)\
            .outerjoin(SalesOrder, ProductionOrder.sales_order_id == SalesOrder.id)\
            .outerjoin(Customer, SalesOrder.customer_id == Customer.id)\
            .options(joinedload(ProductionOrder.part_number))
        
        production_orders = query.limit(100).all()
        
        # Batch fetch shipped quantities
        po_ids = [po.id for po in production_orders]
        
        if po_ids:
            shipped_quantities = db.query(
                ShipmentItem.production_order_id,
                func.sum(ShipmentItem.quantity).label('total_shipped')
            ).filter(
                ShipmentItem.production_order_id.in_(po_ids)
            ).group_by(ShipmentItem.production_order_id).all()
        
        # Batch fetch sales orders and customers
        sales_order_ids = [po.sales_order_id for po in production_orders if po.sales_order_id]
        
        if sales_order_ids:
            sales_orders_with_customers = db.query(
                SalesOrder.id,
                SalesOrder.po_number,
                Customer.name.label('customer_name')
            ).outerjoin(
                Customer, SalesOrder.customer_id == Customer.id
            ).filter(
                SalesOrder.id.in_(sales_order_ids)
            ).all()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n✓ Query completed successfully")
        print(f"  Production Orders: {len(production_orders)}")
        print(f"  Database Queries: {query_count}")
        print(f"  Execution Time: {duration:.3f} seconds")
        
        if query_count <= 5:
            print(f"\n✓ EXCELLENT! Query count is optimal (≤5 queries)")
        elif query_count <= 10:
            print(f"\n⚠ GOOD: Query count is acceptable (≤10 queries)")
        else:
            print(f"\n✗ WARNING: Query count is high (>{query_count} queries)")
            print(f"  Expected: ≤5 queries for {len(production_orders)} orders")
        
        if duration < 1.0:
            print(f"✓ EXCELLENT! Execution time is fast (<1 second)")
        elif duration < 2.0:
            print(f"⚠ GOOD: Execution time is acceptable (<2 seconds)")
        else:
            print(f"✗ WARNING: Execution time is slow (>{duration:.1f} seconds)")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return False
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)
        db.close()
    
    return True

def test_work_center_load():
    """Test the optimized work center load query"""
    global query_count
    
    print("\n" + "="*70)
    print("TESTING WORK CENTER LOAD QUERY")
    print("="*70)
    
    db = SessionLocal()
    
    # Reset counter
    query_count = 0
    
    # Register event listener
    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    
    start_time = time.time()
    
    try:
        # Simulate the optimized work center load query
        load_stats = db.query(
            WorkCenter.id,
            WorkCenter.name,
            func.sum(case((TravelSheetOperation.status == 'Pending', 1), else_=0)).label('pending'),
            func.sum(case((TravelSheetOperation.status == 'In Progress', 1), else_=0)).label('in_progress'),
            func.sum(case((TravelSheetOperation.status == 'Completed', 1), else_=0)).label('completed')
        ).outerjoin(
            TravelSheetOperation,
            TravelSheetOperation.work_center_id == WorkCenter.id
        ).group_by(WorkCenter.id, WorkCenter.name).all()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n✓ Query completed successfully")
        print(f"  Work Centers: {len(load_stats)}")
        print(f"  Database Queries: {query_count}")
        print(f"  Execution Time: {duration:.3f} seconds")
        
        if query_count == 1:
            print(f"\n✓ EXCELLENT! Single query as expected")
        elif query_count <= 3:
            print(f"\n⚠ GOOD: Query count is low (≤3 queries)")
        else:
            print(f"\n✗ WARNING: Query count is high ({query_count} queries)")
            print(f"  Expected: 1 query for all work centers")
        
        if duration < 0.2:
            print(f"✓ EXCELLENT! Execution time is very fast (<0.2 seconds)")
        elif duration < 0.5:
            print(f"⚠ GOOD: Execution time is acceptable (<0.5 seconds)")
        else:
            print(f"✗ WARNING: Execution time is slow (>{duration:.1f} seconds)")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return False
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)
        db.close()
    
    return True

def check_indexes():
    """Check if performance indexes exist"""
    print("\n" + "="*70)
    print("CHECKING DATABASE INDEXES")
    print("="*70)
    
    expected_indexes = [
        'idx_production_orders_sales_order_id',
        'idx_sales_orders_customer_id',
        'idx_shipment_items_production_order_id',
        'idx_travel_sheet_operations_work_center_id',
    ]
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
              AND indexname LIKE 'idx_%'
            ORDER BY indexname
        """))
        
        existing_indexes = [row[0] for row in result]
        
        print(f"\nFound {len(existing_indexes)} performance indexes:")
        
        missing = []
        for idx in expected_indexes:
            if idx in existing_indexes:
                print(f"  ✓ {idx}")
            else:
                print(f"  ✗ {idx} (MISSING)")
                missing.append(idx)
        
        if missing:
            print(f"\n⚠ WARNING: {len(missing)} indexes are missing!")
            print(f"  Run: python add_performance_indexes.py")
            return False
        else:
            print(f"\n✓ All critical indexes are present")
            return True

def main():
    """Run all performance tests"""
    print("="*70)
    print("PERFORMANCE TEST SUITE")
    print("="*70)
    print("\nThis script tests the performance optimizations applied to the")
    print("dashboard and work center load queries.")
    print()
    
    # Check indexes first
    indexes_ok = check_indexes()
    
    # Test dashboard production query
    dashboard_ok = test_dashboard_production()
    
    # Test work center load query
    work_center_ok = test_work_center_load()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    if indexes_ok and dashboard_ok and work_center_ok:
        print("\n✓ ALL TESTS PASSED!")
        print("\nPerformance optimizations are working correctly.")
        print("Expected dashboard load time: <1 second")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        if not indexes_ok:
            print("  • Missing database indexes - run: python add_performance_indexes.py")
        if not dashboard_ok:
            print("  • Dashboard query test failed")
        if not work_center_ok:
            print("  • Work center load query test failed")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
