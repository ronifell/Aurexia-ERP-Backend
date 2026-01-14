-- Aurexia ERP Database Schema
-- PostgreSQL Database Schema for MVP
-- Designed to support Excel data migration from existing database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USERS AND ROLES (RBAC)
-- ============================================

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    can_view_prices BOOLEAN DEFAULT FALSE,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default roles
INSERT INTO roles (name, can_view_prices, description) VALUES
('Admin', TRUE, 'System administrator with full access'),
('Management', TRUE, 'Management and general direction'),
('Quality', FALSE, 'Quality control personnel'),
('Operator', FALSE, 'Production operators'),
('Supervisor', FALSE, 'Production supervisors'),
('Planner', FALSE, 'Production planners'),
('Warehouse', TRUE, 'Warehouse personnel'),
('Shipping', TRUE, 'Shipping personnel');

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role_id INTEGER REFERENCES roles(id),
    badge_id VARCHAR(50) UNIQUE, -- For QR scanning
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(50),
    record_id INTEGER,
    details JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- MASTER DATA
-- ============================================

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    contact_person VARCHAR(100),
    phone VARCHAR(50),
    email VARCHAR(100),
    delivery_frequency VARCHAR(20), -- 'daily', 'weekly'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    contact_person VARCHAR(100),
    phone VARCHAR(50),
    email VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE materials (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50), -- 'Aluminio', 'Galvanizado', etc.
    unit VARCHAR(20), -- 'kg', 'pcs', etc.
    current_stock DECIMAL(10, 2) DEFAULT 0,
    minimum_stock DECIMAL(10, 2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE work_centers (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE machines (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    work_center_id INTEGER REFERENCES work_centers(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE processes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    work_center_id INTEGER REFERENCES work_centers(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- PART NUMBERS AND ROUTINGS
-- ============================================

CREATE TABLE part_numbers (
    id SERIAL PRIMARY KEY,
    part_number VARCHAR(100) UNIQUE NOT NULL,
    customer_id INTEGER REFERENCES customers(id),
    description TEXT,
    material_type VARCHAR(100), -- From Excel: 'Aluminio', 'Galvanizado'
    unit_price DECIMAL(10, 2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE part_routings (
    id SERIAL PRIMARY KEY,
    part_number_id INTEGER REFERENCES part_numbers(id) ON DELETE CASCADE,
    process_id INTEGER REFERENCES processes(id),
    sequence_number INTEGER NOT NULL,
    standard_time_minutes DECIMAL(8, 2), -- Standard time for the process
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(part_number_id, sequence_number)
);

-- ============================================
-- SALES ORDERS (CUSTOMER POs)
-- ============================================

CREATE TABLE sales_orders (
    id SERIAL PRIMARY KEY,
    po_number VARCHAR(100) UNIQUE NOT NULL,
    customer_id INTEGER REFERENCES customers(id),
    order_date DATE NOT NULL,
    due_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'Open', -- 'Open', 'Partial', 'Completed', 'Cancelled'
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sales_order_items (
    id SERIAL PRIMARY KEY,
    sales_order_id INTEGER REFERENCES sales_orders(id) ON DELETE CASCADE,
    part_number_id INTEGER REFERENCES part_numbers(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2),
    total_price DECIMAL(12, 2),
    quantity_produced INTEGER DEFAULT 0,
    quantity_shipped INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'Pending', -- 'Pending', 'In Production', 'Completed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INVENTORY AND RAW MATERIALS
-- ============================================

CREATE TABLE inventory_batches (
    id SERIAL PRIMARY KEY,
    batch_number VARCHAR(100) UNIQUE NOT NULL,
    material_id INTEGER REFERENCES materials(id),
    supplier_id INTEGER REFERENCES suppliers(id),
    heat_number VARCHAR(100), -- Colada for steel tracking
    lot_number VARCHAR(100),
    quantity DECIMAL(10, 2) NOT NULL,
    remaining_quantity DECIMAL(10, 2) NOT NULL,
    unit VARCHAR(20),
    received_date DATE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inventory_movements (
    id SERIAL PRIMARY KEY,
    movement_type VARCHAR(20) NOT NULL, -- 'Receipt', 'Issue', 'Return', 'Adjustment'
    batch_id INTEGER REFERENCES inventory_batches(id),
    material_id INTEGER REFERENCES materials(id),
    quantity DECIMAL(10, 2) NOT NULL,
    reference_type VARCHAR(50), -- 'PurchaseOrder', 'ProductionOrder', etc.
    reference_id INTEGER,
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- PRODUCTION ORDERS AND TRAVEL SHEETS
-- ============================================

CREATE TABLE production_orders (
    id SERIAL PRIMARY KEY,
    po_number VARCHAR(100) UNIQUE NOT NULL,
    sales_order_id INTEGER REFERENCES sales_orders(id),
    sales_order_item_id INTEGER REFERENCES sales_order_items(id),
    part_number_id INTEGER REFERENCES part_numbers(id),
    quantity INTEGER NOT NULL,
    quantity_completed INTEGER DEFAULT 0,
    quantity_scrapped INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'Created', -- 'Created', 'Released', 'In Progress', 'Completed', 'Cancelled'
    start_date DATE,
    due_date DATE,
    priority VARCHAR(20) DEFAULT 'Normal', -- 'Low', 'Normal', 'High', 'Critical'
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE travel_sheets (
    id SERIAL PRIMARY KEY,
    travel_sheet_number VARCHAR(100) UNIQUE NOT NULL,
    production_order_id INTEGER REFERENCES production_orders(id) ON DELETE CASCADE,
    qr_code TEXT UNIQUE NOT NULL, -- QR code for the entire travel sheet
    batch_number VARCHAR(100), -- Links to raw material batch
    status VARCHAR(20) DEFAULT 'Active', -- 'Active', 'Completed', 'Cancelled'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE travel_sheet_operations (
    id SERIAL PRIMARY KEY,
    travel_sheet_id INTEGER REFERENCES travel_sheets(id) ON DELETE CASCADE,
    process_id INTEGER REFERENCES processes(id),
    sequence_number INTEGER NOT NULL,
    qr_code TEXT UNIQUE NOT NULL, -- QR code for this specific operation
    work_center_id INTEGER REFERENCES work_centers(id),
    status VARCHAR(20) DEFAULT 'Pending', -- 'Pending', 'In Progress', 'Completed', 'Skipped'
    operator_id INTEGER REFERENCES users(id),
    machine_id INTEGER REFERENCES machines(id),
    quantity_good INTEGER DEFAULT 0,
    quantity_scrap INTEGER DEFAULT 0,
    quantity_pending INTEGER,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_minutes INTEGER,
    operator_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- QUALITY CONTROL
-- ============================================

CREATE TABLE quality_inspections (
    id SERIAL PRIMARY KEY,
    travel_sheet_id INTEGER REFERENCES travel_sheets(id),
    production_order_id INTEGER REFERENCES production_orders(id),
    inspector_id INTEGER REFERENCES users(id),
    inspection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL, -- 'Released', 'Rejected', 'On Hold'
    quantity_inspected INTEGER,
    quantity_approved INTEGER,
    quantity_rejected INTEGER,
    rejection_reason TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- SHIPPING AND DELIVERY
-- ============================================

CREATE TABLE shipments (
    id SERIAL PRIMARY KEY,
    shipment_number VARCHAR(100) UNIQUE NOT NULL,
    customer_id INTEGER REFERENCES customers(id),
    sales_order_id INTEGER REFERENCES sales_orders(id),
    shipment_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'Prepared', -- 'Prepared', 'Shipped', 'Delivered'
    tracking_number VARCHAR(100),
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE shipment_items (
    id SERIAL PRIMARY KEY,
    shipment_id INTEGER REFERENCES shipments(id) ON DELETE CASCADE,
    sales_order_item_id INTEGER REFERENCES sales_order_items(id),
    part_number_id INTEGER REFERENCES part_numbers(id),
    production_order_id INTEGER REFERENCES production_orders(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

CREATE INDEX idx_users_badge_id ON users(badge_id);
CREATE INDEX idx_users_role_id ON users(role_id);
CREATE INDEX idx_part_numbers_customer ON part_numbers(customer_id);
CREATE INDEX idx_sales_orders_customer ON sales_orders(customer_id);
CREATE INDEX idx_sales_orders_status ON sales_orders(status);
CREATE INDEX idx_production_orders_status ON production_orders(status);
CREATE INDEX idx_production_orders_part_number ON production_orders(part_number_id);
CREATE INDEX idx_travel_sheet_operations_status ON travel_sheet_operations(status);
CREATE INDEX idx_travel_sheet_operations_operator ON travel_sheet_operations(operator_id);
CREATE INDEX idx_inventory_batches_material ON inventory_batches(material_id);
CREATE INDEX idx_shipments_customer ON shipments(customer_id);
CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);

-- ============================================
-- VIEWS FOR REPORTING
-- ============================================

-- View for production dashboard
CREATE VIEW v_production_dashboard AS
SELECT 
    po.id,
    po.po_number,
    so.po_number as sales_order_number,
    c.name as customer_name,
    pn.part_number,
    pn.description as part_description,
    po.quantity,
    po.quantity_completed,
    po.quantity_scrapped,
    po.status,
    po.due_date,
    CASE 
        WHEN po.due_date < CURRENT_DATE THEN 'Red'
        WHEN po.due_date <= CURRENT_DATE + INTERVAL '3 days' THEN 'Yellow'
        ELSE 'Green'
    END as risk_status,
    po.created_at
FROM production_orders po
JOIN part_numbers pn ON po.part_number_id = pn.id
LEFT JOIN sales_orders so ON po.sales_order_id = so.id
LEFT JOIN customers c ON so.customer_id = c.id
WHERE po.status != 'Cancelled';

-- View for sales order progress
CREATE VIEW v_sales_order_progress AS
SELECT 
    so.id,
    so.po_number,
    c.name as customer_name,
    so.order_date,
    so.due_date,
    so.status,
    COUNT(soi.id) as total_items,
    SUM(soi.quantity) as total_quantity,
    SUM(soi.quantity_produced) as total_produced,
    SUM(soi.quantity_shipped) as total_shipped,
    ROUND(100.0 * SUM(soi.quantity_produced) / NULLIF(SUM(soi.quantity), 0), 2) as completion_percentage
FROM sales_orders so
JOIN customers c ON so.customer_id = c.id
LEFT JOIN sales_order_items soi ON so.id = soi.sales_order_id
GROUP BY so.id, c.name;

-- ============================================
-- TRIGGER FOR UPDATED_AT TIMESTAMPS
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_part_numbers_updated_at BEFORE UPDATE ON part_numbers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sales_orders_updated_at BEFORE UPDATE ON sales_orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_production_orders_updated_at BEFORE UPDATE ON production_orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_travel_sheets_updated_at BEFORE UPDATE ON travel_sheets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_travel_sheet_operations_updated_at BEFORE UPDATE ON travel_sheet_operations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
