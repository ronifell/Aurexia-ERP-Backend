"""
Script to verify quality inspection calculations for production orders
"""
from database import SessionLocal
from models import ProductionOrder, QualityInspection
from sqlalchemy import func

def verify_po_calculations(po_number: str):
    """Verify calculations for a specific PO number"""
    db = SessionLocal()
    
    try:
        # Get the production order
        po = db.query(ProductionOrder).filter(ProductionOrder.po_number == po_number).first()
        
        if not po:
            print(f"[ERROR] Production Order {po_number} not found")
            return
        
        print(f"\n[PRODUCTION ORDER]: {po_number}")
        print(f"   Part Number: {po.part_number.part_number if po.part_number else 'N/A'}")
        print(f"   Total Quantity: {po.quantity}")
        print(f"   Status: {po.status}")
        print(f"\n   Current Values in Database:")
        print(f"   - Completed: {po.quantity_completed}")
        print(f"   - Scrapped: {po.quantity_scrapped}")
        
        # Get all quality inspections for this PO
        inspections = db.query(QualityInspection).filter(
            QualityInspection.production_order_id == po.id
        ).all()
        
        print(f"\n[QUALITY INSPECTIONS] ({len(inspections)} total):")
        
        total_inspected = 0
        total_approved = 0
        total_rejected = 0
        
        for i, inspection in enumerate(inspections, 1):
            print(f"\n   Inspection #{i} (ID: {inspection.id})")
            print(f"   - Date: {inspection.inspection_date}")
            print(f"   - Status: {inspection.status}")
            print(f"   - Inspected: {inspection.quantity_inspected or 0}")
            print(f"   - Approved: {inspection.quantity_approved or 0}")
            print(f"   - Rejected: {inspection.quantity_rejected or 0}")
            
            if inspection.status == "Released":
                total_approved += (inspection.quantity_approved or 0)
                total_rejected += (inspection.quantity_rejected or 0)
            elif inspection.status == "Rejected":
                total_rejected += (inspection.quantity_rejected or 0)
            
            total_inspected += (inspection.quantity_inspected or 0)
        
        print(f"\n[CALCULATED TOTALS] (from Quality Inspections):")
        print(f"   - Total Inspected: {total_inspected}")
        print(f"   - Total Approved: {total_approved}")
        print(f"   - Total Rejected: {total_rejected}")
        
        print(f"\n[VERIFICATION]:")
        completed_match = po.quantity_completed == total_approved
        scrapped_match = po.quantity_scrapped == total_rejected
        
        print(f"   Production 'Completed' ({po.quantity_completed}) == Quality 'Approved' ({total_approved}): {'MATCH' if completed_match else 'MISMATCH'}")
        print(f"   Production 'Scrapped' ({po.quantity_scrapped}) == Quality 'Rejected' ({total_rejected}): {'MATCH' if scrapped_match else 'MISMATCH'}")
        
        if not completed_match or not scrapped_match:
            print(f"\n[WARNING] DATA INCONSISTENCY DETECTED!")
            print(f"   This may be due to:")
            print(f"   1. Inspections created before the logic fix")
            print(f"   2. Manual database changes")
            print(f"   3. Backend server not restarted after code update")
            print(f"\n   Recommended Actions:")
            print(f"   1. Restart the backend server")
            print(f"   2. Delete and recreate quality inspections for this PO")
            print(f"   3. Or manually fix production order quantities:")
            print(f"      - UPDATE production_orders SET quantity_completed = {total_approved}, quantity_scrapped = {total_rejected} WHERE po_number = '{po_number}'")
        else:
            print(f"\n[SUCCESS] ALL CALCULATIONS ARE CORRECT!")
        
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python verify_calculations.py <PO_NUMBER>")
        print("Example: python verify_calculations.py PO-20260115182748-28AEC6BB")
        sys.exit(1)
    
    po_number = sys.argv[1]
    verify_po_calculations(po_number)
