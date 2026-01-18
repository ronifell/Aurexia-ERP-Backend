"""
Data Seeding Script for Aurexia ERP
Creates test data for complete workflow testing
"""
import sys
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import (
    Role, User, Customer, Supplier, Material, WorkCenter, Machine, 
    Process, PartNumber, PartRouting, SalesOrder, SalesOrderItem
)
from auth import get_password_hash

def seed_database():
    """Populate database with test data"""
    db = SessionLocal()
    try:
        print("🌱 Starting database seeding...")
        
        # Check if data already exists
        if db.query(Customer).filter(Customer.code == "SIGRAMA").first():
            print("⚠️  Test data already exists. Skipping seeding.")
            response = input("Do you want to clear and reseed? (yes/no): ")
            if response.lower() != 'yes':
                return
            print("🗑️  Clearing existing test data...")
            clear_test_data(db)
        
        # 1. Create Roles (if not exist)
        print("\n📋 Creating roles...")
        roles_data = [
            {'name': 'Admin', 'can_view_prices': True, 'description': 'System administrator with full access'},
            {'name': 'Management', 'can_view_prices': True, 'description': 'Management and general direction'},
            {'name': 'Quality', 'can_view_prices': False, 'description': 'Quality control personnel'},
            {'name': 'Operator', 'can_view_prices': False, 'description': 'Production operators'},
            {'name': 'Supervisor', 'can_view_prices': False, 'description': 'Production supervisors'},
            {'name': 'Planner', 'can_view_prices': False, 'description': 'Production planners'},
            {'name': 'Warehouse', 'can_view_prices': True, 'description': 'Warehouse personnel'},
            {'name': 'Shipping', 'can_view_prices': True, 'description': 'Shipping personnel'},
        ]
        
        roles = {}
        for role_data in roles_data:
            role = db.query(Role).filter(Role.name == role_data['name']).first()
            if not role:
                role = Role(**role_data)
                db.add(role)
                db.flush()
            roles[role_data['name']] = role
            print(f"   ✓ {role_data['name']}")
        
        # 2. Create Test Users
        print("\n👥 Creating users...")
        users_data = [
            {'username': 'admin', 'password': 'admin123', 'email': 'admin@aurexia.com', 'role': 'Admin', 'badge_id': 'BADGE001', 'full_name': 'System Administrator'},
            {'username': 'operator1', 'password': 'operator123', 'email': 'operator1@aurexia.com', 'role': 'Operator', 'badge_id': 'BADGE101', 'full_name': 'Juan Pérez'},
            {'username': 'operator2', 'password': 'operator123', 'email': 'operator2@aurexia.com', 'role': 'Operator', 'badge_id': 'BADGE102', 'full_name': 'María García'},
            {'username': 'operator3', 'password': 'operator123', 'email': 'operator3@aurexia.com', 'role': 'Operator', 'badge_id': 'BADGE103', 'full_name': 'Pedro Gómez'},
            {'username': 'operator4', 'password': 'operator123', 'email': 'operator4@aurexia.com', 'role': 'Operator', 'badge_id': 'BADGE104', 'full_name': 'Laura Torres'},
            {'username': 'operator5', 'password': 'operator123', 'email': 'operator5@aurexia.com', 'role': 'Operator', 'badge_id': 'BADGE105', 'full_name': 'Diego Vargas'},
            {'username': 'operator6', 'password': 'operator123', 'email': 'operator6@aurexia.com', 'role': 'Operator', 'badge_id': 'BADGE106', 'full_name': 'Sofia Castro'},
            {'username': 'operator7', 'password': 'operator123', 'email': 'operator7@aurexia.com', 'role': 'Operator', 'badge_id': 'BADGE107', 'full_name': 'Roberto Jiménez'},
            {'username': 'operator_hist', 'password': 'operator123', 'email': 'operator_hist@aurexia.com', 'role': 'Operator', 'badge_id': 'BADGE_HIST', 'full_name': 'Historical Operator'},
            {'username': 'quality1', 'password': 'quality123', 'email': 'quality1@aurexia.com', 'role': 'Quality', 'badge_id': 'BADGE201', 'full_name': 'Carlos Rodríguez'},
            {'username': 'planner1', 'password': 'planner123', 'email': 'planner1@aurexia.com', 'role': 'Planner', 'badge_id': None, 'full_name': 'Ana Martínez'},
            {'username': 'shipping1', 'password': 'shipping123', 'email': 'shipping1@aurexia.com', 'role': 'Shipping', 'badge_id': 'BADGE301', 'full_name': 'Luis Sánchez'},
        ]
        
        users = {}
        for user_data in users_data:
            user = db.query(User).filter(User.username == user_data['username']).first()
            if not user:
                user = User(
                    username=user_data['username'],
                    password_hash=get_password_hash(user_data['password']),
                    email=user_data['email'],
                    role_id=roles[user_data['role']].id,
                    badge_id=user_data['badge_id'],
                    full_name=user_data['full_name'],
                    is_active=True
                )
                db.add(user)
                db.flush()
            users[user_data['username']] = user
            print(f"   ✓ {user_data['username']} ({user_data['role']}) - password: {user_data['password']}")
        
        # 3. Create Customers
        print("\n🏢 Creating customers...")
        customers_data = [
            {'code': 'SIGRAMA', 'name': 'SIGRAMA Industrial', 'address': 'Av. Industrial 123, Monterrey', 'contact_person': 'Roberto López', 'phone': '+52-81-1234-5678', 'email': 'compras@sigrama.com', 'delivery_frequency': 'weekly'},
            {'code': 'TECDEL', 'name': 'TECDEL Manufacturing', 'address': 'Blvd. Tecnológico 456, Guadalajara', 'contact_person': 'Patricia Fernández', 'phone': '+52-33-2345-6789', 'email': 'procurement@tecdel.com', 'delivery_frequency': 'daily'},
            {'code': 'INDMEX', 'name': 'Industrias Mexicanas SA', 'address': 'Calle Reforma 789, Ciudad de México', 'contact_person': 'Miguel Hernández', 'phone': '+52-55-3456-7890', 'email': 'compras@indmex.com.mx', 'delivery_frequency': 'weekly'},
        ]
        
        customers = {}
        for customer_data in customers_data:
            customer = Customer(**customer_data, is_active=True)
            db.add(customer)
            db.flush()
            customers[customer_data['code']] = customer
            print(f"   ✓ {customer_data['code']} - {customer_data['name']}")
        
        # 4. Create Suppliers
        print("\n📦 Creating suppliers...")
        suppliers_data = [
            {'code': 'ALMEX', 'name': 'Aluminios de México', 'address': 'Zona Industrial, Monterrey', 'contact_person': 'Jorge Ramírez', 'phone': '+52-81-9999-0001', 'email': 'ventas@almex.com'},
            {'code': 'GALVAN', 'name': 'Galvanizados del Norte', 'address': 'Parque Industrial, Saltillo', 'contact_person': 'Sandra Torres', 'phone': '+52-84-8888-0002', 'email': 'comercial@galvan.com'},
            {'code': 'ACEROMEX', 'name': 'Aceros Mexicanos SA', 'address': 'Complejo Industrial, Puebla', 'contact_person': 'Fernando Ruiz', 'phone': '+52-22-7777-0003', 'email': 'ventas@aceromex.com'},
        ]
        
        suppliers = {}
        for supplier_data in suppliers_data:
            supplier = Supplier(**supplier_data, is_active=True)
            db.add(supplier)
            db.flush()
            suppliers[supplier_data['code']] = supplier
            print(f"   ✓ {supplier_data['code']} - {supplier_data['name']}")
        
        # 5. Create Materials
        print("\n🔩 Creating materials...")
        materials_data = [
            {'name': 'Aluminio 6063', 'type': 'Aluminio', 'unit': 'kg', 'current_stock': 5000, 'minimum_stock': 1000},
            {'name': 'Lámina Galvanizada Cal 20', 'type': 'Galvanizado', 'unit': 'kg', 'current_stock': 3000, 'minimum_stock': 500},
            {'name': 'Acero 1045', 'type': 'Acero', 'unit': 'kg', 'current_stock': 2000, 'minimum_stock': 800},
            {'name': 'Tubo Aluminio 2" x 1/8"', 'type': 'Aluminio', 'unit': 'pcs', 'current_stock': 500, 'minimum_stock': 100},
        ]
        
        materials = {}
        for material_data in materials_data:
            material = Material(**material_data, is_active=True)
            db.add(material)
            db.flush()
            materials[material_data['name']] = material
            print(f"   ✓ {material_data['name']}")
        
        # 6. Create Work Centers
        print("\n🏭 Creating work centers...")
        work_centers_data = [
            {'code': 'WC-CUT', 'name': 'Corte', 'description': 'Centro de corte de materiales'},
            {'code': 'WC-BEND', 'name': 'Doblado', 'description': 'Centro de doblado y conformado'},
            {'code': 'WC-WELD', 'name': 'Soldadura', 'description': 'Centro de soldadura'},
            {'code': 'WC-PAINT', 'name': 'Pintura', 'description': 'Centro de pintura y acabado'},
            {'code': 'WC-ASSY', 'name': 'Ensamble', 'description': 'Centro de ensamble final'},
            {'code': 'WC-PKG', 'name': 'Empaque', 'description': 'Centro de empaque'},
        ]
        
        work_centers = {}
        for wc_data in work_centers_data:
            wc = WorkCenter(**wc_data, is_active=True)
            db.add(wc)
            db.flush()
            work_centers[wc_data['code']] = wc
            print(f"   ✓ {wc_data['code']} - {wc_data['name']}")
        
        # 7. Create Machines
        print("\n⚙️  Creating machines...")
        machines_data = [
            {'code': 'CUT-01', 'name': 'Sierra CNC 1', 'work_center': 'WC-CUT'},
            {'code': 'CUT-02', 'name': 'Sierra CNC 2', 'work_center': 'WC-CUT'},
            {'code': 'BEND-01', 'name': 'Dobladora Hidráulica 1', 'work_center': 'WC-BEND'},
            {'code': 'WELD-01', 'name': 'Soldadora MIG 1', 'work_center': 'WC-WELD'},
            {'code': 'WELD-02', 'name': 'Soldadora TIG 1', 'work_center': 'WC-WELD'},
            {'code': 'PAINT-01', 'name': 'Cabina de Pintura 1', 'work_center': 'WC-PAINT'},
        ]
        
        machines = {}
        for machine_data in machines_data:
            machine = Machine(
                code=machine_data['code'],
                name=machine_data['name'],
                work_center_id=work_centers[machine_data['work_center']].id,
                is_active=True
            )
            db.add(machine)
            db.flush()
            machines[machine_data['code']] = machine
            print(f"   ✓ {machine_data['code']} - {machine_data['name']}")
        
        # 8. Create Processes
        print("\n🔄 Creating processes...")
        processes_data = [
            {'code': 'PROC-CUT', 'name': 'Corte de Material', 'work_center': 'WC-CUT', 'description': 'Cortar material a medida'},
            {'code': 'PROC-BEND', 'name': 'Doblado', 'work_center': 'WC-BEND', 'description': 'Doblar piezas según especificaciones'},
            {'code': 'PROC-WELD', 'name': 'Soldadura', 'work_center': 'WC-WELD', 'description': 'Soldar componentes'},
            {'code': 'PROC-PAINT', 'name': 'Pintura', 'work_center': 'WC-PAINT', 'description': 'Aplicar pintura y acabado'},
            {'code': 'PROC-ASSY', 'name': 'Ensamble', 'work_center': 'WC-ASSY', 'description': 'Ensamblar componentes finales'},
            {'code': 'PROC-PKG', 'name': 'Empaque', 'work_center': 'WC-PKG', 'description': 'Empacar producto terminado'},
        ]
        
        processes = {}
        for process_data in processes_data:
            process = Process(
                code=process_data['code'],
                name=process_data['name'],
                description=process_data['description'],
                work_center_id=work_centers[process_data['work_center']].id
            )
            db.add(process)
            db.flush()
            processes[process_data['code']] = process
            print(f"   ✓ {process_data['code']} - {process_data['name']}")
        
        # 9. Create Part Numbers with Routings
        print("\n🔢 Creating part numbers with routings...")
        parts_data = [
            {
                'part_number': '11-1628-01',
                'customer': 'SIGRAMA',
                'description': 'Soporte Lateral Aluminio',
                'material_type': 'Aluminio 6063',
                'unit_price': 45.50,
                'routing': [
                    {'process': 'PROC-CUT', 'sequence': 10, 'time': 5.0},
                    {'process': 'PROC-BEND', 'sequence': 20, 'time': 8.0},
                    {'process': 'PROC-WELD', 'sequence': 30, 'time': 12.0},
                    {'process': 'PROC-PAINT', 'sequence': 40, 'time': 15.0},
                ]
            },
            {
                'part_number': '22-3456-02',
                'customer': 'TECDEL',
                'description': 'Bracket de Montaje Galvanizado',
                'material_type': 'Lámina Galvanizada Cal 20',
                'unit_price': 28.75,
                'routing': [
                    {'process': 'PROC-CUT', 'sequence': 10, 'time': 3.0},
                    {'process': 'PROC-BEND', 'sequence': 20, 'time': 5.0},
                    {'process': 'PROC-PKG', 'sequence': 30, 'time': 2.0},
                ]
            },
            {
                'part_number': '33-7890-03',
                'customer': 'INDMEX',
                'description': 'Base de Acero con Ensamble',
                'material_type': 'Acero 1045',
                'unit_price': 125.00,
                'routing': [
                    {'process': 'PROC-CUT', 'sequence': 10, 'time': 8.0},
                    {'process': 'PROC-WELD', 'sequence': 20, 'time': 20.0},
                    {'process': 'PROC-PAINT', 'sequence': 30, 'time': 18.0},
                    {'process': 'PROC-ASSY', 'sequence': 40, 'time': 10.0},
                    {'process': 'PROC-PKG', 'sequence': 50, 'time': 5.0},
                ]
            },
        ]
        
        part_numbers = {}
        for part_data in parts_data:
            part = PartNumber(
                part_number=part_data['part_number'],
                customer_id=customers[part_data['customer']].id,
                description=part_data['description'],
                material_type=part_data['material_type'],
                unit_price=part_data['unit_price'],
                is_active=True
            )
            db.add(part)
            db.flush()
            part_numbers[part_data['part_number']] = part
            print(f"   ✓ {part_data['part_number']} - {part_data['description']}")
            
            # Create routing
            for routing_step in part_data['routing']:
                routing = PartRouting(
                    part_number_id=part.id,
                    process_id=processes[routing_step['process']].id,
                    sequence_number=routing_step['sequence'],
                    standard_time_minutes=routing_step['time']
                )
                db.add(routing)
            print(f"      → {len(part_data['routing'])} routing steps created")
        
        # 10. Create Sample Sales Orders
        print("\n📋 Creating sample sales orders...")
        today = date.today()
        
        # Sales Order 1 - SIGRAMA
        so1 = SalesOrder(
            po_number='SO-2026-0001',
            customer_id=customers['SIGRAMA'].id,
            order_date=today,
            due_date=today + timedelta(days=14),
            status='Open',
            notes='Pedido urgente para proyecto nuevo',
            created_by=users['admin'].id
        )
        db.add(so1)
        db.flush()
        
        so1_item1 = SalesOrderItem(
            sales_order_id=so1.id,
            part_number_id=part_numbers['11-1628-01'].id,
            quantity=50,
            unit_price=45.50,
            total_price=50 * 45.50,
            status='Pending'
        )
        db.add(so1_item1)
        print(f"   ✓ SO-2026-0001 (SIGRAMA) - 50 units of 11-1628-01")
        
        # Sales Order 2 - TECDEL
        so2 = SalesOrder(
            po_number='SO-2026-0002',
            customer_id=customers['TECDEL'].id,
            order_date=today,
            due_date=today + timedelta(days=7),
            status='Open',
            notes='Reorden mensual',
            created_by=users['admin'].id
        )
        db.add(so2)
        db.flush()
        
        so2_item1 = SalesOrderItem(
            sales_order_id=so2.id,
            part_number_id=part_numbers['22-3456-02'].id,
            quantity=100,
            unit_price=28.75,
            total_price=100 * 28.75,
            status='Pending'
        )
        db.add(so2_item1)
        print(f"   ✓ SO-2026-0002 (TECDEL) - 100 units of 22-3456-02")
        
        # Sales Order 3 - INDMEX
        so3 = SalesOrder(
            po_number='SO-2026-0003',
            customer_id=customers['INDMEX'].id,
            order_date=today,
            due_date=today + timedelta(days=21),
            status='Open',
            notes='Proyecto especial - alta prioridad',
            created_by=users['admin'].id
        )
        db.add(so3)
        db.flush()
        
        so3_item1 = SalesOrderItem(
            sales_order_id=so3.id,
            part_number_id=part_numbers['33-7890-03'].id,
            quantity=25,
            unit_price=125.00,
            total_price=25 * 125.00,
            status='Pending'
        )
        db.add(so3_item1)
        print(f"   ✓ SO-2026-0003 (INDMEX) - 25 units of 33-7890-03")
        
        db.commit()
        print("\n✅ Database seeding completed successfully!")
        print("\n" + "="*60)
        print("TEST CREDENTIALS:")
        print("="*60)
        print("Admin:     username: admin     password: admin123")
        print("Operator:  username: operator1 password: operator123")
        print("           username: operator2 password: operator123")
        print("Quality:   username: quality1  password: quality123")
        print("Planner:   username: planner1  password: planner123")
        print("Shipping:  username: shipping1 password: shipping123")
        print("="*60)
        print("\nYou can now test the complete workflow:")
        print("1. Login as admin")
        print("2. View Sales Order SO-2026-0001 (SIGRAMA - Part 11-1628-01)")
        print("3. Create Production Order from this sales order")
        print("4. Generate Travel Sheet")
        print("5. Execute operations via QR Scanner (use BADGE101 or BADGE102)")
        print("6. Create Quality Inspection")
        print("7. Create Shipment")
        print("8. View Dashboard for updates")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error seeding database: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def clear_test_data(db: Session):
    """Clear test data from database"""
    try:
        # Clear in reverse order of dependencies
        db.query(SalesOrderItem).delete()
        db.query(SalesOrder).delete()
        db.query(PartRouting).delete()
        db.query(PartNumber).delete()
        db.query(Process).delete()
        db.query(Machine).delete()
        db.query(WorkCenter).delete()
        db.query(Material).delete()
        db.query(Supplier).delete()
        db.query(Customer).delete()
        
        # Clear test users (but keep admin if it exists)
        db.query(User).filter(User.username != 'admin').delete()
        
        db.commit()
        print("   ✓ Test data cleared")
    except Exception as e:
        print(f"   ✗ Error clearing test data: {str(e)}")
        db.rollback()

if __name__ == "__main__":
    print("="*60)
    print("AUREXIA ERP - DATABASE SEEDING SCRIPT")
    print("="*60)
    seed_database()
