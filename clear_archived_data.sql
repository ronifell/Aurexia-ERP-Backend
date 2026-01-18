-- ============================================================
-- AUREXIA ERP - CLEAR ARCHIVED DATA (SQL Script)
-- ============================================================
-- This script deletes all transactional data while preserving
-- master data and database structure.
--
-- DELETES:
--   - Sales Orders & Items
--   - Production Orders
--   - Travel Sheets & Operations  
--   - Quality Inspections
--   - Shipments & Items
--   - Inventory Batches & Movements
--   - Audit Logs (optional - commented out by default)
--
-- PRESERVES:
--   - Users, Roles
--   - Customers, Suppliers, Materials
--   - Work Centers, Machines, Processes
--   - Part Numbers and Routings
--
-- USAGE:
--   1. Review the script carefully
--   2. Copy and paste into Supabase SQL Editor
--   3. Run the script
--   4. Check the results at the bottom
-- ============================================================

BEGIN;

-- Count records before deletion (optional - for reporting)
DO $$
DECLARE
    v_shipment_items INTEGER;
    v_shipments INTEGER;
    v_quality INTEGER;
    v_travel_ops INTEGER;
    v_travel_sheets INTEGER;
    v_production_orders INTEGER;
    v_sales_items INTEGER;
    v_sales_orders INTEGER;
    v_inventory_movements INTEGER;
    v_inventory_batches INTEGER;
    v_audit_logs INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_shipment_items FROM shipment_items;
    SELECT COUNT(*) INTO v_shipments FROM shipments;
    SELECT COUNT(*) INTO v_quality FROM quality_inspections;
    SELECT COUNT(*) INTO v_travel_ops FROM travel_sheet_operations;
    SELECT COUNT(*) INTO v_travel_sheets FROM travel_sheets;
    SELECT COUNT(*) INTO v_production_orders FROM production_orders;
    SELECT COUNT(*) INTO v_sales_items FROM sales_order_items;
    SELECT COUNT(*) INTO v_sales_orders FROM sales_orders;
    SELECT COUNT(*) INTO v_inventory_movements FROM inventory_movements;
    SELECT COUNT(*) INTO v_inventory_batches FROM inventory_batches;
    SELECT COUNT(*) INTO v_audit_logs FROM audit_log;
    
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'RECORDS TO BE DELETED:';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Shipment Items: %', v_shipment_items;
    RAISE NOTICE 'Shipments: %', v_shipments;
    RAISE NOTICE 'Quality Inspections: %', v_quality;
    RAISE NOTICE 'Travel Sheet Operations: %', v_travel_ops;
    RAISE NOTICE 'Travel Sheets: %', v_travel_sheets;
    RAISE NOTICE 'Production Orders: %', v_production_orders;
    RAISE NOTICE 'Sales Order Items: %', v_sales_items;
    RAISE NOTICE 'Sales Orders: %', v_sales_orders;
    RAISE NOTICE 'Inventory Movements: %', v_inventory_movements;
    RAISE NOTICE 'Inventory Batches: %', v_inventory_batches;
    RAISE NOTICE 'Audit Log Entries: % (will NOT be deleted by default)', v_audit_logs;
    RAISE NOTICE '============================================================';
END $$;

-- Delete data in reverse order of dependencies
-- 1. Shipment items (depends on shipments)
DELETE FROM shipment_items;

-- 2. Shipments
DELETE FROM shipments;

-- 3. Quality inspections
DELETE FROM quality_inspections;

-- 4. Travel sheet operations (depends on travel sheets)
DELETE FROM travel_sheet_operations;

-- 5. Travel sheets (depends on production orders)
DELETE FROM travel_sheets;

-- 6. Production orders
DELETE FROM production_orders;

-- 7. Sales order items (depends on sales orders)
DELETE FROM sales_order_items;

-- 8. Sales orders
DELETE FROM sales_orders;

-- 9. Inventory movements
DELETE FROM inventory_movements;

-- 10. Inventory batches
DELETE FROM inventory_batches;

-- 11. Audit log (OPTIONAL - uncomment the next line to delete audit logs)
-- DELETE FROM audit_log;

-- Commit the transaction
COMMIT;

-- Verify deletion and show what's preserved
SELECT 
    'DELETED: Sales Orders' as status, 
    COUNT(*) as remaining_records 
FROM sales_orders
UNION ALL
SELECT 
    'DELETED: Production Orders', 
    COUNT(*) 
FROM production_orders
UNION ALL
SELECT 
    'DELETED: Travel Sheets', 
    COUNT(*) 
FROM travel_sheets
UNION ALL
SELECT 
    'DELETED: Shipments', 
    COUNT(*) 
FROM shipments
UNION ALL
SELECT 
    'DELETED: Quality Inspections', 
    COUNT(*) 
FROM quality_inspections
UNION ALL
SELECT 
    'DELETED: Inventory Batches', 
    COUNT(*) 
FROM inventory_batches
UNION ALL
SELECT 
    '---PRESERVED: Customers---', 
    COUNT(*) 
FROM customers
UNION ALL
SELECT 
    'PRESERVED: Part Numbers', 
    COUNT(*) 
FROM part_numbers
UNION ALL
SELECT 
    'PRESERVED: Users', 
    COUNT(*) 
FROM users
UNION ALL
SELECT 
    'PRESERVED: Work Centers', 
    COUNT(*) 
FROM work_centers
UNION ALL
SELECT 
    'PRESERVED: Processes', 
    COUNT(*) 
FROM processes
ORDER BY status;
