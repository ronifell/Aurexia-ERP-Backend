"""
Utility functions for Aurexia ERP
"""
import qrcode
from io import BytesIO
import base64
from datetime import datetime
import uuid

def generate_qr_code(data: str) -> str:
    """Generate QR code and return as base64 string"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def generate_unique_number(prefix: str) -> str:
    """Generate a unique number with prefix"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"{prefix}-{timestamp}-{unique_id}"

def calculate_completion_percentage(completed: int, total: int) -> float:
    """Calculate completion percentage"""
    if total == 0:
        return 0.0
    return round((completed / total) * 100, 2)

def determine_risk_status(due_date, status: str) -> str:
    """Determine risk status based on due date and status"""
    if status in ['Completed', 'Shipped', 'Delivered']:
        return 'Green'
    
    if not due_date:
        return 'Yellow'
    
    from datetime import date, timedelta
    today = date.today()
    
    if due_date < today:
        return 'Red'
    elif due_date <= today + timedelta(days=3):
        return 'Yellow'
    else:
        return 'Green'
