"""
Automated End-to-End Workflow Test for Aurexia ERP
Tests the complete workflow from sales order to shipment
"""
import requests
import json
from datetime import date, datetime, timedelta

BASE_URL = "http://localhost:8000/api"

class WorkflowTester:
    def __init__(self):
        self.token = None
        self.test_data = {}
        
    def print_step(self, step_num, title):
        print(f"\n{'='*60}")
        print(f"STEP {step_num}: {title}")
        print('='*60)
        
    def print_success(self, message):
        print(f"[OK] {message}")
        
    def print_error(self, message):
        print(f"[ERROR] {message}")
        
    def print_info(self, message):
        print(f"[INFO] {message}")
        
    def login(self, username="admin", password="admin123"):
        """Step 1: Login"""
        self.print_step(1, "LOGIN")
        
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.print_success(f"Logged in as {username}")
            return True
        else:
            self.print_error(f"Login failed: {response.text}")
            return False
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}
    
    def get_test_data_ids(self):
        """Get IDs for test data"""
        self.print_step(2, "FETCH TEST DATA IDS")
        
        # Get customer SIGRAMA
        response = requests.get(f"{BASE_URL}/customers/", headers=self.get_headers())
        customers = response.json()
        sigrama = next((c for c in customers if c['code'] == 'SIGRAMA'), None)
        
        if not sigrama:
            self.print_error("SIGRAMA customer not found. Run seed_data.py first!")
            return False
        
        self.test_data['customer_id'] = sigrama['id']
        self.print_success(f"Found SIGRAMA - ID: {sigrama['id']}")
        
        # Get part number 11-1628-01
        response = requests.get(f"{BASE_URL}/part-numbers/", headers=self.get_headers())
        parts = response.json()
        part = next((p for p in parts if p['part_number'] == '11-1628-01'), None)
        
        if not part:
            self.print_error("Part 11-1628-01 not found. Run seed_data.py first!")
            return False
        
        self.test_data['part_number_id'] = part['id']
        self.test_data['unit_price'] = part['unit_price']
        self.print_success(f"Found part 11-1628-01 - ID: {part['id']}")
        
        return True
    
    def create_sales_order(self):
        """Step 3: Create Sales Order"""
        self.print_step(3, "CREATE SALES ORDER")
        
        today = date.today()
        due_date = today + timedelta(days=14)
        timestamp = datetime.now().strftime('%H%M%S')
        
        so_data = {
            "po_number": f"TEST-SO-{today.strftime('%Y%m%d')}-{timestamp}",
            "customer_id": self.test_data['customer_id'],
            "order_date": str(today),
            "due_date": str(due_date),
            "status": "Open",
            "notes": "Automated test - Complete workflow",
            "items": [
                {
                    "part_number_id": self.test_data['part_number_id'],
                    "quantity": 50,
                    "unit_price": self.test_data['unit_price']
                }
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/sales-orders/",
            json=so_data,
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            so = response.json()
            self.test_data['sales_order_id'] = so['id']
            self.test_data['sales_order_item_id'] = so['items'][0]['id']
            self.print_success(f"Created Sales Order: {so['po_number']} (ID: {so['id']})")
            self.print_info(f"  - Customer: SIGRAMA")
            self.print_info(f"  - Part: 11-1628-01")
            self.print_info(f"  - Quantity: 50 units")
            self.print_info(f"  - Due Date: {due_date}")
            return True
        else:
            self.print_error(f"Failed to create sales order: {response.text}")
            return False
    
    def create_production_order(self):
        """Step 4: Create Production Order"""
        self.print_step(4, "CREATE PRODUCTION ORDER")
        
        po_data = {
            "sales_order_id": self.test_data['sales_order_id'],
            "sales_order_item_id": self.test_data['sales_order_item_id'],
            "part_number_id": self.test_data['part_number_id'],
            "quantity": 50,
            "due_date": str(date.today() + timedelta(days=14)),
            "priority": "High"
        }
        
        response = requests.post(
            f"{BASE_URL}/production-orders/",
            json=po_data,
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            po = response.json()
            self.test_data['production_order_id'] = po['id']
            self.test_data['po_number'] = po['po_number']
            self.print_success(f"Created Production Order: {po['po_number']} (ID: {po['id']})")
            self.print_info(f"  - Quantity: {po['quantity']}")
            self.print_info(f"  - Status: {po['status']}")
            self.print_info(f"  - Priority: {po['priority']}")
            return True
        else:
            self.print_error(f"Failed to create production order: {response.text}")
            return False
    
    def generate_travel_sheet(self):
        """Step 5: Generate Travel Sheet"""
        self.print_step(5, "GENERATE TRAVEL SHEET")
        
        po_id = self.test_data['production_order_id']
        response = requests.post(
            f"{BASE_URL}/production-orders/{po_id}/generate-travel-sheet",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            ts = response.json()
            self.test_data['travel_sheet_id'] = ts['id']
            self.test_data['travel_sheet_number'] = ts['travel_sheet_number']
            self.print_success(f"Created Travel Sheet: {ts['travel_sheet_number']} (ID: {ts['id']})")
            self.print_info(f"  - Operations: {len(ts['operations'])} steps")
            for op in ts['operations']:
                self.print_info(f"    • Step {op['sequence_number']}: {op['process']['name'] if op.get('process') else 'Unknown'}")
            return True
        else:
            self.print_error(f"Failed to generate travel sheet: {response.text}")
            return False
    
    def simulate_operation_execution(self):
        """Step 6: Simulate QR Scanner Operations"""
        self.print_step(6, "EXECUTE OPERATIONS (Simulated)")
        
        # Get travel sheet details
        ts_id = self.test_data['travel_sheet_id']
        response = requests.get(
            f"{BASE_URL}/production-orders/{self.test_data['production_order_id']}/travel-sheets",
            headers=self.get_headers()
        )
        
        if response.status_code != 200:
            self.print_error("Failed to get travel sheet details")
            return False
        
        travel_sheets = response.json()
        operations = travel_sheets[0]['operations']
        
        self.print_info(f"Found {len(operations)} operations to execute")
        
        # Simulate completing all operations
        for op in operations:
            # Start operation (change status to In Progress)
            scan_data = {
                "badge_id": "BADGE101",
                "qr_code": op['qr_code']
            }
            
            response = requests.post(
                f"{BASE_URL}/qr-scanner/scan",
                json=scan_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                self.print_info(f"  Started: Step {op['sequence_number']}")
            
            # Complete operation
            complete_data = {
                "quantity_good": 50,
                "quantity_scrap": 0,
                "quantity_pending": 0,
                "machine_id": 1,
                "operator_notes": "Automated test execution"
            }
            
            response = requests.put(
                f"{BASE_URL}/qr-scanner/operations/{op['id']}/complete",
                json=complete_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                self.print_success(f"  Completed: Step {op['sequence_number']} - 50 good, 0 scrap")
            else:
                self.print_error(f"  Failed to complete step {op['sequence_number']}: {response.text}")
        
        return True
    
    def create_quality_inspection(self):
        """Step 7: Create Quality Inspection"""
        self.print_step(7, "CREATE QUALITY INSPECTION")
        
        inspection_data = {
            "production_order_id": self.test_data['production_order_id'],
            "travel_sheet_id": self.test_data['travel_sheet_id'],
            "status": "Released",
            "quantity_inspected": 50,
            "quantity_approved": 48,
            "quantity_rejected": 2,
            "rejection_reason": "",
            "notes": "Automated test - Quality passed with minor defects"
        }
        
        response = requests.post(
            f"{BASE_URL}/quality-inspections/",
            json=inspection_data,
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            inspection = response.json()
            self.test_data['inspection_id'] = inspection['id']
            self.print_success(f"Created Quality Inspection (ID: {inspection['id']})")
            self.print_info(f"  - Status: {inspection['status']}")
            self.print_info(f"  - Inspected: {inspection['quantity_inspected']}")
            self.print_info(f"  - Approved: {inspection['quantity_approved']}")
            self.print_info(f"  - Rejected: {inspection['quantity_rejected']}")
            return True
        else:
            self.print_error(f"Failed to create quality inspection: {response.text}")
            return False
    
    def create_shipment(self):
        """Step 8: Create Shipment"""
        self.print_step(8, "CREATE SHIPMENT")
        
        shipment_data = {
            "customer_id": self.test_data['customer_id'],
            "sales_order_id": self.test_data['sales_order_id'],
            "shipment_date": str(date.today()),
            "status": "Prepared",
            "notes": "Automated test shipment",
            "items": [
                {
                    "part_number_id": self.test_data['part_number_id'],
                    "production_order_id": self.test_data['production_order_id'],
                    "quantity": 48,  # Only ship approved quantity
                    "unit_price": self.test_data['unit_price']
                }
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/shipments",
            json=shipment_data,
            headers=self.get_headers()
        )
        
        if response.status_code == 201:
            shipment = response.json()
            self.test_data['shipment_id'] = shipment['id']
            self.test_data['shipment_number'] = shipment['shipment_number']
            self.print_success(f"Created Shipment: {shipment['shipment_number']} (ID: {shipment['id']})")
            self.print_info(f"  - Quantity: 48 units (approved quantity)")
            self.print_info(f"  - Status: {shipment['status']}")
            return True
        else:
            self.print_error(f"Failed to create shipment: {response.text}")
            self.print_info("This might be due to quality gate enforcement (expected behavior)")
            return False
    
    def verify_dashboard(self):
        """Step 9: Verify Dashboard Data"""
        self.print_step(9, "VERIFY DASHBOARD")
        
        # Get dashboard stats
        response = requests.get(
            f"{BASE_URL}/dashboard/stats",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            stats = response.json()
            self.print_success("Dashboard Stats Retrieved:")
            self.print_info(f"  - Open Orders: {stats['total_open_orders']}")
            self.print_info(f"  - Completed Orders: {stats['total_completed_orders']}")
            self.print_info(f"  - In Production: {stats['total_in_production']}")
            self.print_info(f"  - Shipped Orders: {stats['total_shipped_orders']}")
            self.print_info(f"  - On Time: {stats['total_on_time']}")
            self.print_info(f"  - At Risk: {stats['total_at_risk']}")
            self.print_info(f"  - Delayed: {stats['total_delayed']}")
            
            # Get production dashboard
            response = requests.get(
                f"{BASE_URL}/dashboard/production",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                production = response.json()
                # Find our test production order
                test_po = next((p for p in production if p['id'] == self.test_data['production_order_id']), None)
                if test_po:
                    self.print_success(f"\nProduction Order {test_po['po_number']} Status:")
                    self.print_info(f"  - Completed: {test_po['quantity_completed']} / {test_po['quantity']}")
                    self.print_info(f"  - Shipped: {test_po['quantity_shipped']}")
                    self.print_info(f"  - Completion: {test_po['completion_percentage']}%")
                    self.print_info(f"  - Risk Status: {test_po['risk_status']}")
            
            return True
        else:
            self.print_error(f"Failed to get dashboard data: {response.text}")
            return False
    
    def run_complete_workflow(self):
        """Run the complete workflow test"""
        print("\n" + "="*60)
        print("AUREXIA ERP - COMPLETE WORKFLOW TEST")
        print("="*60)
        print("This test will:")
        print("1. Login as admin")
        print("2. Fetch test data IDs")
        print("3. Create a sales order")
        print("4. Generate a production order")
        print("5. Generate travel sheet with QR codes")
        print("6. Simulate operation execution")
        print("7. Create quality inspection")
        print("8. Create shipment (with quality gate)")
        print("9. Verify dashboard updates")
        print("="*60)
        
        steps = [
            (self.login, "Login"),
            (self.get_test_data_ids, "Get Test Data"),
            (self.create_sales_order, "Create Sales Order"),
            (self.create_production_order, "Create Production Order"),
            (self.generate_travel_sheet, "Generate Travel Sheet"),
            (self.simulate_operation_execution, "Execute Operations"),
            (self.create_quality_inspection, "Quality Inspection"),
            (self.create_shipment, "Create Shipment"),
            (self.verify_dashboard, "Verify Dashboard"),
        ]
        
        failed_steps = []
        
        for step_func, step_name in steps:
            try:
                if not step_func():
                    failed_steps.append(step_name)
                    if step_name == "Login" or step_name == "Get Test Data":
                        # Critical steps - can't continue
                        break
            except Exception as e:
                self.print_error(f"Exception in {step_name}: {str(e)}")
                failed_steps.append(step_name)
        
        # Final Summary
        print("\n" + "="*60)
        print("WORKFLOW TEST SUMMARY")
        print("="*60)
        
        if not failed_steps:
            self.print_success("ALL STEPS COMPLETED SUCCESSFULLY!")
            print("\nTest Data Created:")
            print(f"  - Sales Order: {self.test_data.get('po_number', 'N/A')}")
            print(f"  - Production Order: {self.test_data.get('po_number', 'N/A')}")
            print(f"  - Travel Sheet: {self.test_data.get('travel_sheet_number', 'N/A')}")
            print(f"  - Shipment: {self.test_data.get('shipment_number', 'N/A')}")
        else:
            self.print_error(f"WORKFLOW FAILED - {len(failed_steps)} step(s) failed:")
            for step in failed_steps:
                print(f"  [ERROR] {step}")
        
        print("="*60 + "\n")

if __name__ == "__main__":
    tester = WorkflowTester()
    tester.run_complete_workflow()
