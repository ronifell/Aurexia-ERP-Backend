"""
Comprehensive End-to-End Workflow Test for Aurexia ERP
Tests multiple scenarios to demonstrate all system capabilities
"""
import requests
import json
from datetime import date, datetime, timedelta

BASE_URL = "http://localhost:8000/api"

class ComprehensiveWorkflowTester:
    def __init__(self):
        self.token = None
        self.test_data = {}
        self.scenarios = []
        
    def print_step(self, step_num, title):
        print(f"\n{'='*70}")
        print(f"SCENARIO {step_num}: {title}")
        print('='*70)
        
    def print_success(self, message):
        print(f"[OK] {message}")
        
    def print_error(self, message):
        print(f"[ERROR] {message}")
        
    def print_info(self, message):
        print(f"  {message}")
        
    def login(self, username="admin", password="admin123"):
        """Login"""
        print(f"\n{'='*70}")
        print("AUTHENTICATING")
        print('='*70)
        
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
    
    def create_test_data(self):
        """Create test customers and part numbers"""
        print(f"\n{'='*70}")
        print("CREATING TEST DATA")
        print('='*70)
        
        self.test_data['customers'] = {}
        self.test_data['parts'] = {}
        
        # Create test customers
        customers_data = [
            {
                "code": "SIGRAMA",
                "name": "Sigrama GmbH",
                "address": "Test Address 1, Germany",
                "contact_person": "Test Contact 1",
                "phone": "+49-123-456789",
                "email": "test1@sigrama.de",
                "delivery_frequency": "Weekly",
                "is_active": True
            },
            {
                "code": "AKZONOBEL",
                "name": "AkzoNobel Coatings",
                "address": "Test Address 2, Germany",
                "contact_person": "Test Contact 2",
                "phone": "+49-987-654321",
                "email": "test2@akzonobel.de",
                "delivery_frequency": "Bi-weekly",
                "is_active": True
            },
            {
                "code": "CROMAX",
                "name": "Cromax Industries",
                "address": "Test Address 3, Germany",
                "contact_person": "Test Contact 3",
                "phone": "+49-555-123456",
                "email": "test3@cromax.de",
                "delivery_frequency": "Monthly",
                "is_active": True
            }
        ]
        
        for cust_data in customers_data:
            response = requests.post(
                f"{BASE_URL}/customers/",
                json=cust_data,
                headers=self.get_headers()
            )
            if response.status_code == 200:
                customer = response.json()
                self.test_data['customers'][cust_data['code']] = customer['id']
                self.print_success(f"Created customer: {cust_data['code']} - ID: {customer['id']}")
            else:
                self.print_error(f"Failed to create customer {cust_data['code']}: {response.text}")
                return False
        
        # Get first customer ID for part numbers
        first_customer_id = self.test_data['customers']['SIGRAMA']
        
        # Get processes first - needed for routings
        response = requests.get(f"{BASE_URL}/processes/", headers=self.get_headers())
        if response.status_code != 200:
            self.print_error("Failed to get processes. Make sure seed_data.py was run for base config (roles, work centers, processes, etc).")
            return False
        
        processes = response.json()
        if len(processes) < 4:
            self.print_error("Not enough processes found. Need at least 4 processes. Run seed_data.py first.")
            return False
        
        # Create routings data (4 operations per part)
        routings = [
            {
                "process_id": processes[0]['id'],
                "sequence_number": 1,
                "standard_time_minutes": 30.0
            },
            {
                "process_id": processes[1]['id'],
                "sequence_number": 2,
                "standard_time_minutes": 30.0
            },
            {
                "process_id": processes[2]['id'],
                "sequence_number": 3,
                "standard_time_minutes": 30.0
            },
            {
                "process_id": processes[3]['id'],
                "sequence_number": 4,
                "standard_time_minutes": 30.0
            }
        ]
        
        # Create test part numbers WITH routings
        parts_data = [
            {
                "part_number": "11-1628-01",
                "customer_id": first_customer_id,
                "description": "Test Part 1 - Automotive Component",
                "material_type": "Steel",
                "unit_price": 25.50,
                "is_active": True,
                "routings": routings
            },
            {
                "part_number": "11-1630-01",
                "customer_id": first_customer_id,
                "description": "Test Part 2 - Industrial Component",
                "material_type": "Aluminum",
                "unit_price": 32.75,
                "is_active": True,
                "routings": routings
            },
            {
                "part_number": "11-1750-01",
                "customer_id": first_customer_id,
                "description": "Test Part 3 - Special Component",
                "material_type": "Stainless Steel",
                "unit_price": 45.00,
                "is_active": True,
                "routings": routings
            }
        ]
        
        for part_data in parts_data:
            response = requests.post(
                f"{BASE_URL}/part-numbers/",
                json=part_data,
                headers=self.get_headers()
            )
            if response.status_code == 200:
                part = response.json()
                self.test_data['parts'][part_data['part_number']] = {
                    'id': part['id'],
                    'unit_price': part['unit_price']
                }
                self.print_success(f"Created part: {part_data['part_number']} with 4 routings - ID: {part['id']}")
            else:
                self.print_error(f"Failed to create part {part_data['part_number']}: {response.text}")
                return False
        
        return True
    
    def scenario_1_completed_order_with_full_shipment(self):
        """
        Scenario 1: Perfect Execution
        - Sales Order → Production → Quality (100% approved) → Full Shipment
        - This creates: Completed Order, Shipped Order
        """
        self.print_step(1, "COMPLETED ORDER WITH FULL SHIPMENT")
        
        today = date.today()
        timestamp = datetime.now().strftime('%H%M%S')
        
        # Create Sales Order
        so_data = {
            "po_number": f"SO-COMPLETE-{timestamp}",
            "customer_id": self.test_data['customers']['SIGRAMA'],
            "order_date": str(today - timedelta(days=10)),
            "due_date": str(today - timedelta(days=1)),
            "status": "Open",
            "notes": "Scenario 1: Completed order",
            "items": [{
                "part_number_id": self.test_data['parts']['11-1628-01']['id'],
                "quantity": 100,
                "unit_price": self.test_data['parts']['11-1628-01']['unit_price']
            }]
        }
        
        response = requests.post(f"{BASE_URL}/sales-orders/", json=so_data, headers=self.get_headers())
        so = response.json()
        self.print_info(f"Created Sales Order: {so['po_number']}")
        
        # Create Production Order
        po_data = {
            "sales_order_id": so['id'],
            "sales_order_item_id": so['items'][0]['id'],
            "part_number_id": self.test_data['parts']['11-1628-01']['id'],
            "quantity": 100,
            "due_date": str(today - timedelta(days=1)),
            "priority": "High"
        }
        
        response = requests.post(f"{BASE_URL}/production-orders/", json=po_data, headers=self.get_headers())
        po = response.json()
        self.print_info(f"Created Production Order: {po['po_number']}")
        
        # Generate Travel Sheet
        response = requests.post(
            f"{BASE_URL}/production-orders/{po['id']}/generate-travel-sheet",
            headers=self.get_headers()
        )
        ts = response.json()
        self.print_info(f"Generated Travel Sheet: {ts['travel_sheet_number']}")
        
        # Complete all operations
        response = requests.get(
            f"{BASE_URL}/production-orders/{po['id']}/travel-sheets",
            headers=self.get_headers()
        )
        operations = response.json()[0]['operations']
        
        for op in operations:
            # Start operation
            requests.post(
                f"{BASE_URL}/qr-scanner/scan",
                json={"badge_id": "BADGE101", "qr_code": op['qr_code']},
                headers=self.get_headers()
            )
            # Complete operation
            requests.put(
                f"{BASE_URL}/qr-scanner/operations/{op['id']}/complete",
                json={
                    "quantity_good": 100,
                    "quantity_scrap": 0,
                    "quantity_pending": 0,
                    "machine_id": 1,
                    "operator_notes": "Completed"
                },
                headers=self.get_headers()
            )
        self.print_info(f"Completed {len(operations)} operations")
        
        # Quality Inspection - 100% approved
        inspection_data = {
            "production_order_id": po['id'],
            "travel_sheet_id": ts['id'],
            "status": "Released",
            "quantity_inspected": 100,
            "quantity_approved": 100,
            "quantity_rejected": 0,
            "rejection_reason": "",
            "notes": "Perfect quality - all approved"
        }
        
        response = requests.post(f"{BASE_URL}/quality-inspections/", json=inspection_data, headers=self.get_headers())
        self.print_info("Quality: 100% APPROVED")
        
        # Create Shipment
        shipment_data = {
            "customer_id": self.test_data['customers']['SIGRAMA'],
            "sales_order_id": so['id'],
            "shipment_date": str(today),
            "status": "Shipped",
            "notes": "Full shipment",
            "items": [{
                "part_number_id": self.test_data['parts']['11-1628-01']['id'],
                "production_order_id": po['id'],
                "quantity": 100,
                "unit_price": self.test_data['parts']['11-1628-01']['unit_price']
            }]
        }
        
        response = requests.post(f"{BASE_URL}/shipments", json=shipment_data, headers=self.get_headers())
        if response.status_code == 201:
            shipment = response.json()
            self.print_success(f"Shipped: {shipment['shipment_number']} (100 units)")
        
        self.scenarios.append("[OK] Scenario 1: Completed & Shipped")
        return True
    
    def scenario_2_in_progress_order_with_partial_completion(self):
        """
        Scenario 2: Work In Progress
        - Production started but not finished
        - Creates: In Production, Pending Operations
        """
        self.print_step(2, "IN PROGRESS ORDER (PARTIAL COMPLETION)")
        
        today = date.today()
        timestamp = datetime.now().strftime('%H%M%S')
        
        # Create Sales Order
        so_data = {
            "po_number": f"SO-INPROGRESS-{timestamp}",
            "customer_id": self.test_data['customers']['AKZONOBEL'],
            "order_date": str(today - timedelta(days=5)),
            "due_date": str(today + timedelta(days=5)),
            "status": "Open",
            "notes": "Scenario 2: In progress order",
            "items": [{
                "part_number_id": self.test_data['parts']['11-1630-01']['id'],
                "quantity": 200,
                "unit_price": self.test_data['parts']['11-1630-01']['unit_price']
            }]
        }
        
        response = requests.post(f"{BASE_URL}/sales-orders/", json=so_data, headers=self.get_headers())
        so = response.json()
        self.print_info(f"Created Sales Order: {so['po_number']}")
        
        # Create Production Order
        po_data = {
            "sales_order_id": so['id'],
            "sales_order_item_id": so['items'][0]['id'],
            "part_number_id": self.test_data['parts']['11-1630-01']['id'],
            "quantity": 200,
            "due_date": str(today + timedelta(days=5)),
            "priority": "Medium"
        }
        
        response = requests.post(f"{BASE_URL}/production-orders/", json=po_data, headers=self.get_headers())
        po = response.json()
        self.print_info(f"Created Production Order: {po['po_number']}")
        
        # Generate Travel Sheet
        response = requests.post(
            f"{BASE_URL}/production-orders/{po['id']}/generate-travel-sheet",
            headers=self.get_headers()
        )
        ts = response.json()
        self.print_info(f"Generated Travel Sheet: {ts['travel_sheet_number']}")
        
        # Complete only FIRST TWO operations (leave rest pending)
        response = requests.get(
            f"{BASE_URL}/production-orders/{po['id']}/travel-sheets",
            headers=self.get_headers()
        )
        operations = response.json()[0]['operations']
        
        completed_ops = 0
        for i, op in enumerate(operations):
            if i < 2:  # Only complete first 2 operations
                # Start operation
                requests.post(
                    f"{BASE_URL}/qr-scanner/scan",
                    json={"badge_id": "BADGE102", "qr_code": op['qr_code']},
                    headers=self.get_headers()
                )
                # Complete operation
                requests.put(
                    f"{BASE_URL}/qr-scanner/operations/{op['id']}/complete",
                    json={
                        "quantity_good": 200,
                        "quantity_scrap": 0,
                        "quantity_pending": 0,
                        "machine_id": 1,
                        "operator_notes": "In progress"
                    },
                    headers=self.get_headers()
                )
                completed_ops += 1
        
        self.print_info(f"Completed {completed_ops}/{len(operations)} operations (IN PROGRESS)")
        self.print_success(f"Order Status: IN PROGRESS - {len(operations) - completed_ops} operations pending")
        
        self.scenarios.append("[OK] Scenario 2: In Progress")
        return True
    
    def scenario_3_order_with_quality_rejection(self):
        """
        Scenario 3: Quality Issues
        - Production completed but quality rejected some parts
        - Creates: Scrap, Partial approval
        """
        self.print_step(3, "ORDER WITH QUALITY REJECTION")
        
        today = date.today()
        timestamp = datetime.now().strftime('%H%M%S')
        
        # Create Sales Order
        so_data = {
            "po_number": f"SO-QUALITY-{timestamp}",
            "customer_id": self.test_data['customers']['CROMAX'],
            "order_date": str(today - timedelta(days=7)),
            "due_date": str(today + timedelta(days=2)),
            "status": "Open",
            "notes": "Scenario 3: Quality rejection",
            "items": [{
                "part_number_id": self.test_data['parts']['11-1750-01']['id'],
                "quantity": 150,
                "unit_price": self.test_data['parts']['11-1750-01']['unit_price']
            }]
        }
        
        response = requests.post(f"{BASE_URL}/sales-orders/", json=so_data, headers=self.get_headers())
        so = response.json()
        self.print_info(f"Created Sales Order: {so['po_number']}")
        
        # Create Production Order
        po_data = {
            "sales_order_id": so['id'],
            "sales_order_item_id": so['items'][0]['id'],
            "part_number_id": self.test_data['parts']['11-1750-01']['id'],
            "quantity": 150,
            "due_date": str(today + timedelta(days=2)),
            "priority": "High"
        }
        
        response = requests.post(f"{BASE_URL}/production-orders/", json=po_data, headers=self.get_headers())
        po = response.json()
        self.print_info(f"Created Production Order: {po['po_number']}")
        
        # Generate Travel Sheet
        response = requests.post(
            f"{BASE_URL}/production-orders/{po['id']}/generate-travel-sheet",
            headers=self.get_headers()
        )
        ts = response.json()
        
        # Complete all operations
        response = requests.get(
            f"{BASE_URL}/production-orders/{po['id']}/travel-sheets",
            headers=self.get_headers()
        )
        operations = response.json()[0]['operations']
        
        for op in operations:
            requests.post(
                f"{BASE_URL}/qr-scanner/scan",
                json={"badge_id": "BADGE103", "qr_code": op['qr_code']},
                headers=self.get_headers()
            )
            requests.put(
                f"{BASE_URL}/qr-scanner/operations/{op['id']}/complete",
                json={
                    "quantity_good": 150,
                    "quantity_scrap": 0,
                    "quantity_pending": 0,
                    "machine_id": 1,
                    "operator_notes": "Completed"
                },
                headers=self.get_headers()
            )
        
        # Quality Inspection - PARTIAL REJECTION
        inspection_data = {
            "production_order_id": po['id'],
            "travel_sheet_id": ts['id'],
            "status": "Released",
            "quantity_inspected": 150,
            "quantity_approved": 130,  # 20 rejected
            "quantity_rejected": 20,
            "rejection_reason": "Surface defects detected",
            "notes": "Partial rejection - 20 units scrapped"
        }
        
        response = requests.post(f"{BASE_URL}/quality-inspections/", json=inspection_data, headers=self.get_headers())
        self.print_info("Quality: 130 APPROVED, 20 REJECTED")
        self.print_success("Scrap recorded: 20 units")
        
        self.scenarios.append("[OK] Scenario 3: Quality Issues (Scrap)")
        return True
    
    def scenario_4_delayed_order_at_risk(self):
        """
        Scenario 4: At-Risk Order
        - Order due soon but not started
        - Creates: At Risk status (Yellow)
        """
        self.print_step(4, "AT-RISK ORDER (DUE SOON, NOT STARTED)")
        
        today = date.today()
        timestamp = datetime.now().strftime('%H%M%S')
        
        # Create Sales Order
        so_data = {
            "po_number": f"SO-ATRISK-{timestamp}",
            "customer_id": self.test_data['customers']['SIGRAMA'],
            "order_date": str(today - timedelta(days=3)),
            "due_date": str(today + timedelta(days=2)),  # Due in 2 days
            "status": "Open",
            "notes": "Scenario 4: At-risk order",
            "items": [{
                "part_number_id": self.test_data['parts']['11-1628-01']['id'],
                "quantity": 75,
                "unit_price": self.test_data['parts']['11-1628-01']['unit_price']
            }]
        }
        
        response = requests.post(f"{BASE_URL}/sales-orders/", json=so_data, headers=self.get_headers())
        so = response.json()
        self.print_info(f"Created Sales Order: {so['po_number']}")
        
        # Create Production Order - NOT STARTED
        po_data = {
            "sales_order_id": so['id'],
            "sales_order_item_id": so['items'][0]['id'],
            "part_number_id": self.test_data['parts']['11-1628-01']['id'],
            "quantity": 75,
            "due_date": str(today + timedelta(days=2)),
            "priority": "High"
        }
        
        response = requests.post(f"{BASE_URL}/production-orders/", json=po_data, headers=self.get_headers())
        po = response.json()
        self.print_info(f"Created Production Order: {po['po_number']}")
        
        # Generate Travel Sheet but DON'T START
        response = requests.post(
            f"{BASE_URL}/production-orders/{po['id']}/generate-travel-sheet",
            headers=self.get_headers()
        )
        ts = response.json()
        
        self.print_info(f"Generated Travel Sheet: {ts['travel_sheet_number']}")
        self.print_success("Status: AT RISK (Due in 2 days, not started)")
        
        self.scenarios.append("[OK] Scenario 4: At Risk")
        return True
    
    def scenario_5_delayed_overdue_order(self):
        """
        Scenario 5: Multiple Delayed Orders
        - Orders past due date
        - Creates: Delayed status (Red) - ensures delayed count > 0
        """
        self.print_step(5, "DELAYED ORDERS (PAST DUE)")
        
        today = date.today()
        
        # Create MULTIPLE delayed orders to ensure visible count
        delayed_configs = [
            {"days_overdue": 5, "customer": "AKZONOBEL", "part": "11-1630-01", "qty": 120, "started": True},
            {"days_overdue": 8, "customer": "CROMAX", "part": "11-1750-01", "qty": 90, "started": False},
            {"days_overdue": 3, "customer": "SIGRAMA", "part": "11-1628-01", "qty": 150, "started": True},
        ]
        
        delayed_count = 0
        for config in delayed_configs:
            timestamp = datetime.now().strftime('%H%M%S') + str(delayed_count)
            
            # Create Sales Order
            so_data = {
                "po_number": f"SO-DELAYED-{timestamp}",
                "customer_id": self.test_data['customers'][config['customer']],
                "order_date": str(today - timedelta(days=15)),
                "due_date": str(today - timedelta(days=config['days_overdue'])),
                "status": "Open",
                "notes": f"Delayed by {config['days_overdue']} days",
                "items": [{
                    "part_number_id": self.test_data['parts'][config['part']]['id'],
                    "quantity": config['qty'],
                    "unit_price": self.test_data['parts'][config['part']]['unit_price']
                }]
            }
            
            response = requests.post(f"{BASE_URL}/sales-orders/", json=so_data, headers=self.get_headers())
            if response.status_code != 200:
                continue
            so = response.json()
            
            # Create Production Order
            po_data = {
                "sales_order_id": so['id'],
                "sales_order_item_id": so['items'][0]['id'],
                "part_number_id": self.test_data['parts'][config['part']]['id'],
                "quantity": config['qty'],
                "due_date": str(today - timedelta(days=config['days_overdue'])),
                "priority": "High"
            }
            
            response = requests.post(f"{BASE_URL}/production-orders/", json=po_data, headers=self.get_headers())
            if response.status_code != 200:
                continue
            po = response.json()
            
            # Generate Travel Sheet
            response = requests.post(
                f"{BASE_URL}/production-orders/{po['id']}/generate-travel-sheet",
                headers=self.get_headers()
            )
            if response.status_code != 200:
                continue
            
            # Optionally start (but not complete) to show in-progress delayed work
            if config['started']:
                response = requests.get(
                    f"{BASE_URL}/production-orders/{po['id']}/travel-sheets",
                    headers=self.get_headers()
                )
                if response.status_code == 200:
                    operations = response.json()[0]['operations']
                    if operations:
                        requests.post(
                            f"{BASE_URL}/qr-scanner/scan",
                            json={"badge_id": "BADGE107", "qr_code": operations[0]['qr_code']},
                            headers=self.get_headers()
                        )
            
            self.print_info(f"Created delayed order: {po['po_number']} ({config['days_overdue']} days overdue)")
            delayed_count += 1
        
        self.print_success(f"Created {delayed_count} DELAYED orders (Red status)")
        
        self.scenarios.append("[OK] Scenario 5: Delayed Orders")
        return True
    
    def scenario_6_partial_shipment(self):
        """
        Scenario 6: Partial Shipment
        - Order partially shipped (Partial status)
        """
        self.print_step(6, "PARTIAL SHIPMENT")
        
        today = date.today()
        timestamp = datetime.now().strftime('%H%M%S')
        
        # Create Sales Order
        so_data = {
            "po_number": f"SO-PARTIAL-{timestamp}",
            "customer_id": self.test_data['customers']['CROMAX'],
            "order_date": str(today - timedelta(days=8)),
            "due_date": str(today + timedelta(days=7)),
            "status": "Open",
            "notes": "Scenario 6: Partial shipment",
            "items": [{
                "part_number_id": self.test_data['parts']['11-1750-01']['id'],
                "quantity": 300,
                "unit_price": self.test_data['parts']['11-1750-01']['unit_price']
            }]
        }
        
        response = requests.post(f"{BASE_URL}/sales-orders/", json=so_data, headers=self.get_headers())
        so = response.json()
        self.print_info(f"Created Sales Order: {so['po_number']}")
        
        # Create Production Order
        po_data = {
            "sales_order_id": so['id'],
            "sales_order_item_id": so['items'][0]['id'],
            "part_number_id": self.test_data['parts']['11-1750-01']['id'],
            "quantity": 300,
            "due_date": str(today + timedelta(days=7)),
            "priority": "Medium"
        }
        
        response = requests.post(f"{BASE_URL}/production-orders/", json=po_data, headers=self.get_headers())
        po = response.json()
        self.print_info(f"Created Production Order: {po['po_number']}")
        
        # Generate Travel Sheet
        response = requests.post(
            f"{BASE_URL}/production-orders/{po['id']}/generate-travel-sheet",
            headers=self.get_headers()
        )
        ts = response.json()
        
        # Complete all operations
        response = requests.get(
            f"{BASE_URL}/production-orders/{po['id']}/travel-sheets",
            headers=self.get_headers()
        )
        operations = response.json()[0]['operations']
        
        for op in operations:
            requests.post(
                f"{BASE_URL}/qr-scanner/scan",
                json={"badge_id": "BADGE104", "qr_code": op['qr_code']},
                headers=self.get_headers()
            )
            requests.put(
                f"{BASE_URL}/qr-scanner/operations/{op['id']}/complete",
                json={
                    "quantity_good": 300,
                    "quantity_scrap": 0,
                    "quantity_pending": 0,
                    "machine_id": 1,
                    "operator_notes": "Completed"
                },
                headers=self.get_headers()
            )
        
        # Quality Inspection
        inspection_data = {
            "production_order_id": po['id'],
            "travel_sheet_id": ts['id'],
            "status": "Released",
            "quantity_inspected": 300,
            "quantity_approved": 300,
            "quantity_rejected": 0,
            "rejection_reason": "",
            "notes": "All approved"
        }
        requests.post(f"{BASE_URL}/quality-inspections/", json=inspection_data, headers=self.get_headers())
        
        # Ship only 150 out of 300 (PARTIAL)
        shipment_data = {
            "customer_id": self.test_data['customers']['CROMAX'],
            "sales_order_id": so['id'],
            "shipment_date": str(today),
            "status": "Shipped",
            "notes": "Partial shipment - first batch",
            "items": [{
                "part_number_id": self.test_data['parts']['11-1750-01']['id'],
                "production_order_id": po['id'],
                "quantity": 150,  # Only 150 out of 300
                "unit_price": self.test_data['parts']['11-1750-01']['unit_price']
            }]
        }
        
        response = requests.post(f"{BASE_URL}/shipments", json=shipment_data, headers=self.get_headers())
        if response.status_code == 201:
            self.print_success("Partial Shipment: 150/300 units shipped")
        
        self.scenarios.append("[OK] Scenario 6: Partial Shipment")
        return True
    
    def scenario_7_multiple_production_orders_same_sales_order(self):
        """
        Scenario 7: Multiple Production Orders for One Sales Order
        - One sales order with multiple items
        """
        self.print_step(7, "MULTIPLE PRODUCTION ORDERS (ONE SALES ORDER)")
        
        today = date.today()
        timestamp = datetime.now().strftime('%H%M%S')
        
        # Create Sales Order with MULTIPLE ITEMS
        so_data = {
            "po_number": f"SO-MULTI-{timestamp}",
            "customer_id": self.test_data['customers']['SIGRAMA'],
            "order_date": str(today - timedelta(days=4)),
            "due_date": str(today + timedelta(days=10)),
            "status": "Open",
            "notes": "Scenario 7: Multiple items",
            "items": [
                {
                    "part_number_id": self.test_data['parts']['11-1628-01']['id'],
                    "quantity": 80,
                    "unit_price": self.test_data['parts']['11-1628-01']['unit_price']
                },
                {
                    "part_number_id": self.test_data['parts']['11-1630-01']['id'],
                    "quantity": 90,
                    "unit_price": self.test_data['parts']['11-1630-01']['unit_price']
                }
            ]
        }
        
        response = requests.post(f"{BASE_URL}/sales-orders/", json=so_data, headers=self.get_headers())
        so = response.json()
        self.print_info(f"Created Sales Order: {so['po_number']} (2 items)")
        
        # Create Production Orders for EACH item
        for i, item in enumerate(so['items']):
            po_data = {
                "sales_order_id": so['id'],
                "sales_order_item_id": item['id'],
                "part_number_id": item['part_number_id'],
                "quantity": item['quantity'],
                "due_date": str(today + timedelta(days=10)),
                "priority": "Normal"
            }
            
            response = requests.post(f"{BASE_URL}/production-orders/", json=po_data, headers=self.get_headers())
            po = response.json()
            self.print_info(f"  Production Order {i+1}: {po['po_number']} ({item['quantity']} units)")
        
        self.print_success("Created 2 production orders for 1 sales order")
        self.scenarios.append("[OK] Scenario 7: Multiple POs")
        return True
    
    def scenario_8_order_with_scrap_during_operations(self):
        """
        Scenario 8: Scrap During Operations
        - Operations completed with scrap
        """
        self.print_step(8, "ORDER WITH SCRAP DURING OPERATIONS")
        
        today = date.today()
        timestamp = datetime.now().strftime('%H%M%S')
        
        # Create Sales Order
        so_data = {
            "po_number": f"SO-SCRAP-{timestamp}",
            "customer_id": self.test_data['customers']['AKZONOBEL'],
            "order_date": str(today - timedelta(days=6)),
            "due_date": str(today + timedelta(days=4)),
            "status": "Open",
            "notes": "Scenario 8: Scrap during operations",
            "items": [{
                "part_number_id": self.test_data['parts']['11-1628-01']['id'],
                "quantity": 100,
                "unit_price": self.test_data['parts']['11-1628-01']['unit_price']
            }]
        }
        
        response = requests.post(f"{BASE_URL}/sales-orders/", json=so_data, headers=self.get_headers())
        so = response.json()
        self.print_info(f"Created Sales Order: {so['po_number']}")
        
        # Create Production Order
        po_data = {
            "sales_order_id": so['id'],
            "sales_order_item_id": so['items'][0]['id'],
            "part_number_id": self.test_data['parts']['11-1628-01']['id'],
            "quantity": 100,
            "due_date": str(today + timedelta(days=4)),
            "priority": "Medium"
        }
        
        response = requests.post(f"{BASE_URL}/production-orders/", json=po_data, headers=self.get_headers())
        po = response.json()
        self.print_info(f"Created Production Order: {po['po_number']}")
        
        # Generate Travel Sheet
        response = requests.post(
            f"{BASE_URL}/production-orders/{po['id']}/generate-travel-sheet",
            headers=self.get_headers()
        )
        ts = response.json()
        
        # Complete operations WITH SCRAP
        response = requests.get(
            f"{BASE_URL}/production-orders/{po['id']}/travel-sheets",
            headers=self.get_headers()
        )
        operations = response.json()[0]['operations']
        
        total_scrap = 0
        for op in operations:
            requests.post(
                f"{BASE_URL}/qr-scanner/scan",
                json={"badge_id": "BADGE105", "qr_code": op['qr_code']},
                headers=self.get_headers()
            )
            # Each operation has some scrap
            requests.put(
                f"{BASE_URL}/qr-scanner/operations/{op['id']}/complete",
                json={
                    "quantity_good": 95,
                    "quantity_scrap": 5,  # 5 units scrapped per operation
                    "quantity_pending": 0,
                    "machine_id": 1,
                    "operator_notes": "Some scrap generated"
                },
                headers=self.get_headers()
            )
            total_scrap += 5
        
        self.print_info(f"Completed {len(operations)} operations with scrap")
        self.print_success(f"Total scrap during operations: {total_scrap} units")
        
        self.scenarios.append("[OK] Scenario 8: Scrap During Ops")
        return True
    
    def scenario_9_prepared_shipment_not_shipped(self):
        """
        Scenario 9: Prepared But Not Shipped
        - Shipment prepared but not yet shipped
        """
        self.print_step(9, "PREPARED SHIPMENT (NOT YET SHIPPED)")
        
        today = date.today()
        timestamp = datetime.now().strftime('%H%M%S')
        
        # Create Sales Order
        so_data = {
            "po_number": f"SO-PREPARED-{timestamp}",
            "customer_id": self.test_data['customers']['CROMAX'],
            "order_date": str(today - timedelta(days=9)),
            "due_date": str(today + timedelta(days=1)),
            "status": "Open",
            "notes": "Scenario 9: Prepared shipment",
            "items": [{
                "part_number_id": self.test_data['parts']['11-1750-01']['id'],
                "quantity": 60,
                "unit_price": self.test_data['parts']['11-1750-01']['unit_price']
            }]
        }
        
        response = requests.post(f"{BASE_URL}/sales-orders/", json=so_data, headers=self.get_headers())
        so = response.json()
        self.print_info(f"Created Sales Order: {so['po_number']}")
        
        # Create Production Order
        po_data = {
            "sales_order_id": so['id'],
            "sales_order_item_id": so['items'][0]['id'],
            "part_number_id": self.test_data['parts']['11-1750-01']['id'],
            "quantity": 60,
            "due_date": str(today + timedelta(days=1)),
            "priority": "High"
        }
        
        response = requests.post(f"{BASE_URL}/production-orders/", json=po_data, headers=self.get_headers())
        po = response.json()
        
        # Generate and complete
        response = requests.post(
            f"{BASE_URL}/production-orders/{po['id']}/generate-travel-sheet",
            headers=self.get_headers()
        )
        ts = response.json()
        
        response = requests.get(
            f"{BASE_URL}/production-orders/{po['id']}/travel-sheets",
            headers=self.get_headers()
        )
        operations = response.json()[0]['operations']
        
        for op in operations:
            requests.post(
                f"{BASE_URL}/qr-scanner/scan",
                json={"badge_id": "BADGE106", "qr_code": op['qr_code']},
                headers=self.get_headers()
            )
            requests.put(
                f"{BASE_URL}/qr-scanner/operations/{op['id']}/complete",
                json={
                    "quantity_good": 60,
                    "quantity_scrap": 0,
                    "quantity_pending": 0,
                    "machine_id": 1,
                    "operator_notes": "Done"
                },
                headers=self.get_headers()
            )
        
        # Quality
        inspection_data = {
            "production_order_id": po['id'],
            "travel_sheet_id": ts['id'],
            "status": "Released",
            "quantity_inspected": 60,
            "quantity_approved": 60,
            "quantity_rejected": 0,
            "rejection_reason": "",
            "notes": "Approved"
        }
        requests.post(f"{BASE_URL}/quality-inspections/", json=inspection_data, headers=self.get_headers())
        
        # Create Shipment as PREPARED (not shipped yet)
        shipment_data = {
            "customer_id": self.test_data['customers']['CROMAX'],
            "sales_order_id": so['id'],
            "shipment_date": str(today),
            "status": "Prepared",  # NOT SHIPPED YET
            "notes": "Prepared but waiting for pickup",
            "items": [{
                "part_number_id": self.test_data['parts']['11-1750-01']['id'],
                "production_order_id": po['id'],
                "quantity": 60,
                "unit_price": self.test_data['parts']['11-1750-01']['unit_price']
            }]
        }
        
        response = requests.post(f"{BASE_URL}/shipments", json=shipment_data, headers=self.get_headers())
        if response.status_code == 201:
            self.print_success("Shipment PREPARED (awaiting pickup)")
        
        self.scenarios.append("[OK] Scenario 9: Prepared Shipment")
        return True
    
    def scenario_10_on_time_order(self):
        """
        Scenario 10: On-Time Order
        - Order with plenty of time (Green status)
        """
        self.print_step(10, "ON-TIME ORDER (GREEN STATUS)")
        
        today = date.today()
        timestamp = datetime.now().strftime('%H%M%S')
        
        # Create Sales Order
        so_data = {
            "po_number": f"SO-ONTIME-{timestamp}",
            "customer_id": self.test_data['customers']['SIGRAMA'],
            "order_date": str(today),
            "due_date": str(today + timedelta(days=20)),  # 20 days - plenty of time
            "status": "Open",
            "notes": "Scenario 10: On-time order",
            "items": [{
                "part_number_id": self.test_data['parts']['11-1628-01']['id'],
                "quantity": 180,
                "unit_price": self.test_data['parts']['11-1628-01']['unit_price']
            }]
        }
        
        response = requests.post(f"{BASE_URL}/sales-orders/", json=so_data, headers=self.get_headers())
        so = response.json()
        self.print_info(f"Created Sales Order: {so['po_number']}")
        
        # Create Production Order
        po_data = {
            "sales_order_id": so['id'],
            "sales_order_item_id": so['items'][0]['id'],
            "part_number_id": self.test_data['parts']['11-1628-01']['id'],
            "quantity": 180,
            "due_date": str(today + timedelta(days=20)),
            "priority": "Low"
        }
        
        response = requests.post(f"{BASE_URL}/production-orders/", json=po_data, headers=self.get_headers())
        po = response.json()
        self.print_info(f"Created Production Order: {po['po_number']}")
        
        # Generate Travel Sheet
        response = requests.post(
            f"{BASE_URL}/production-orders/{po['id']}/generate-travel-sheet",
            headers=self.get_headers()
        )
        
        self.print_success("Status: ON TIME (20 days remaining)")
        self.scenarios.append("[OK] Scenario 10: On Time")
        return True
    
    def scenario_11_historical_production_data(self):
        """
        Scenario 11: Historical Production Data
        - Create operations completed over the past 7 days with varying scrap
        - This will populate the Daily Production chart with red bars
        """
        self.print_step(11, "HISTORICAL PRODUCTION DATA (7 DAYS)")
        
        today = date.today()
        
        # Create multiple small orders completed on different days
        for days_ago in [6, 5, 4, 3, 2, 1, 0]:
            timestamp = datetime.now().strftime('%H%M%S') + str(days_ago)
            completion_date = today - timedelta(days=days_ago)
            
            # Create Sales Order
            so_data = {
                "po_number": f"SO-HIST-{timestamp}",
                "customer_id": list(self.test_data['customers'].values())[days_ago % 3],
                "order_date": str(completion_date - timedelta(days=2)),
                "due_date": str(completion_date),
                "status": "Open",
                "notes": f"Historical data - day {days_ago}",
                "items": [{
                    "part_number_id": list(self.test_data['parts'].values())[days_ago % 3]['id'],
                    "quantity": 50 + (days_ago * 10),
                    "unit_price": list(self.test_data['parts'].values())[days_ago % 3]['unit_price']
                }]
            }
            
            response = requests.post(f"{BASE_URL}/sales-orders/", json=so_data, headers=self.get_headers())
            if response.status_code != 200:
                continue
            so = response.json()
            
            # Create Production Order
            quantity = 50 + (days_ago * 10)
            po_data = {
                "sales_order_id": so['id'],
                "sales_order_item_id": so['items'][0]['id'],
                "part_number_id": so['items'][0]['part_number_id'],
                "quantity": quantity,
                "due_date": str(completion_date),
                "priority": "Normal"
            }
            
            response = requests.post(f"{BASE_URL}/production-orders/", json=po_data, headers=self.get_headers())
            if response.status_code != 200:
                continue
            po = response.json()
            
            # Generate Travel Sheet
            response = requests.post(
                f"{BASE_URL}/production-orders/{po['id']}/generate-travel-sheet",
                headers=self.get_headers()
            )
            if response.status_code != 200:
                continue
            
            # Get operations
            response = requests.get(
                f"{BASE_URL}/production-orders/{po['id']}/travel-sheets",
                headers=self.get_headers()
            )
            if response.status_code != 200:
                continue
            
            operations = response.json()[0]['operations']
            
            # Varying scrap rates for different days
            scrap_amounts = [0, 5, 10, 8, 3, 12, 6]
            scrap = scrap_amounts[days_ago]
            
            # Complete operations and manually update end_time via direct DB update
            for op in operations:
                # Start operation
                requests.post(
                    f"{BASE_URL}/qr-scanner/scan",
                    json={"badge_id": "BADGE_HIST", "qr_code": op['qr_code']},
                    headers=self.get_headers()
                )
                # Complete operation
                requests.put(
                    f"{BASE_URL}/qr-scanner/operations/{op['id']}/complete",
                    json={
                        "quantity_good": quantity - scrap,
                        "quantity_scrap": scrap,
                        "quantity_pending": 0,
                        "machine_id": 1,
                        "operator_notes": f"Historical - {days_ago} days ago"
                    },
                    headers=self.get_headers()
                )
            
            # Update operation end_time to historical date (direct DB update)
            try:
                import psycopg2
                conn = psycopg2.connect(
                    dbname="aurexia_db",
                    user="aurexia_user",
                    password="aurexia2024",
                    host="localhost",
                    port="5432"
                )
                cursor = conn.cursor()
                
                # Update all operations for this travel sheet to have the historical end_time
                historical_datetime = datetime.combine(completion_date, datetime.now().time())
                for op in operations:
                    cursor.execute(
                        "UPDATE travel_sheet_operations SET end_time = %s WHERE id = %s",
                        (historical_datetime, op['id'])
                    )
                
                conn.commit()
                conn.close()
            except Exception as e:
                self.print_info(f"Note: Could not update historical dates (operations will show on today): {e}")
            
            self.print_info(f"Day {days_ago}: {quantity - scrap} good, {scrap} scrap")
        
        self.print_success("Created 7 days of historical production data with varying scrap")
        self.scenarios.append("[OK] Scenario 11: Historical Data")
        return True
    
    def verify_dashboard(self):
        """Verify Dashboard Data"""
        print(f"\n{'='*70}")
        print("DASHBOARD VERIFICATION")
        print('='*70)
        
        # Get dashboard stats
        response = requests.get(f"{BASE_URL}/dashboard/stats", headers=self.get_headers())
        
        if response.status_code == 200:
            stats = response.json()
            self.print_success("Dashboard Statistics:")
            print(f"\n  Sales Orders:")
            print(f"     - Open Orders: {stats['total_open_orders']}")
            print(f"     - Completed Orders: {stats['total_completed_orders']}")
            print(f"     - Shipped Orders: {stats['total_shipped_orders']}")
            
            print(f"\n  Production:")
            print(f"     - In Production: {stats['total_in_production']}")
            
            print(f"\n  Timeline Status:")
            print(f"     - [GREEN] On Time: {stats['total_on_time']}")
            print(f"     - [YELLOW] At Risk: {stats['total_at_risk']}")
            print(f"     - [RED] Delayed: {stats['total_delayed']}")
            
            # Get work center load
            response = requests.get(f"{BASE_URL}/dashboard/work-center-load", headers=self.get_headers())
            if response.status_code == 200:
                work_centers = response.json()
                print(f"\n  Work Center Load:")
                for wc in work_centers:
                    if wc['total'] > 0:
                        print(f"     - {wc['work_center_name']}: "
                              f"Pending={wc['pending']}, "
                              f"In Progress={wc['in_progress']}, "
                              f"Completed={wc['completed']}")
            
            # Get daily production
            response = requests.get(f"{BASE_URL}/dashboard/daily-production?days=7", headers=self.get_headers())
            if response.status_code == 200:
                daily = response.json()
                if daily:
                    print(f"\n  Daily Production (last 7 days):")
                    for day in daily[-3:]:  # Show last 3 days
                        print(f"     - {day['date']}: Good={day['good']}, Scrap={day['scrap']}")
            
            return True
        else:
            self.print_error(f"Failed to get dashboard data: {response.text}")
            return False
    
    def run_comprehensive_test(self):
        """Run all test scenarios"""
        print("\n" + "="*70)
        print("AUREXIA ERP - COMPREHENSIVE WORKFLOW TEST")
        print("="*70)
        print("This test will create test data and 11 different scenarios")
        print("to demonstrate all capabilities of the system:")
        print()
        print("  0. Create test customers and part numbers")
        print("  1. Completed order with full shipment")
        print("  2. In-progress order (partial completion)")
        print("  3. Order with quality rejection (scrap)")
        print("  4. At-risk order (due soon, not started)")
        print("  5. Delayed orders (past due)")
        print("  6. Partial shipment")
        print("  7. Multiple production orders (one sales order)")
        print("  8. Scrap during operations")
        print("  9. Prepared shipment (not yet shipped)")
        print(" 10. On-time order (plenty of time)")
        print(" 11. Historical production data (7 days with scrap)")
        print()
        print("NOTE: Run clear_archived_data.py first for best results!")
        print("="*70)
        
        # Login
        if not self.login():
            return
        
        # Create test data (customers, part numbers, routings)
        if not self.create_test_data():
            return
        
        # Run all scenarios
        scenarios = [
            self.scenario_1_completed_order_with_full_shipment,
            self.scenario_2_in_progress_order_with_partial_completion,
            self.scenario_3_order_with_quality_rejection,
            self.scenario_4_delayed_order_at_risk,
            self.scenario_5_delayed_overdue_order,
            self.scenario_6_partial_shipment,
            self.scenario_7_multiple_production_orders_same_sales_order,
            self.scenario_8_order_with_scrap_during_operations,
            self.scenario_9_prepared_shipment_not_shipped,
            self.scenario_10_on_time_order,
            self.scenario_11_historical_production_data,
        ]
        
        for scenario in scenarios:
            try:
                scenario()
            except Exception as e:
                self.print_error(f"Exception in scenario: {str(e)}")
        
        # Verify dashboard
        self.verify_dashboard()
        
        # Final Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        for scenario in self.scenarios:
            print(f"  {scenario}")
        print()
        self.print_success(f"Successfully created {len(self.scenarios)} test scenarios!")
        print()
        print("Dashboard should now show:")
        print("   - Multiple chart bars with different colors")
        print("   - Non-zero values for ALL metrics (including Delayed)")
        print("   - Mix of green, yellow, and RED statuses")
        print("   - Various production stages (Pending, In Progress, Completed)")
        print("   - Quality data (approved and rejected quantities)")
        print("   - Shipment data (prepared and shipped)")
        print("   - [RED] RED BARS in Daily Production chart (scrap data over 7 days)")
        print("   - [RED] Delayed orders count should be > 0")
        print("="*70 + "\n")

if __name__ == "__main__":
    tester = ComprehensiveWorkflowTester()
    tester.run_comprehensive_test()
