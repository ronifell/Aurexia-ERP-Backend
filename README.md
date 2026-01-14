# Aurexia ERP - Backend

FastAPI backend for Aurexia ERP system.

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Database

Make sure PostgreSQL is installed and create a database:

```sql
CREATE DATABASE aurexia_db;
CREATE USER aurexia_user WITH PASSWORD 'aurexia2024';
GRANT ALL PRIVILEGES ON DATABASE aurexia_db TO aurexia_user;
```

### 3. Update Configuration

Edit `config.py` to update the database connection string if needed:

```python
DATABASE_URL = "postgresql://aurexia_user:aurexia2024@localhost:5432/aurexia_db"
```

### 4. Initialize Database

Run the database initialization script:

```bash
python init_db.py
```

This will create all tables and seed default data including:
- Roles (Admin, Management, Quality, Operator, etc.)
- Default admin user (username: `admin`, password: `admin123`)
- Work centers and processes

### 5. Run the Server

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

## Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration settings
├── database.py          # Database connection and session management
├── models.py            # SQLAlchemy ORM models
├── schemas.py           # Pydantic schemas for validation
├── auth.py              # Authentication and authorization utilities
├── utils.py             # Utility functions
├── init_db.py           # Database initialization script
├── database_schema.sql  # SQL schema for reference
├── requirements.txt     # Python dependencies
└── routes/              # API route handlers
    ├── auth.py          # Authentication endpoints
    ├── users.py         # User management
    ├── customers.py     # Customer management
    ├── part_numbers.py  # Part number and routing management
    ├── sales_orders.py  # Sales order management
    ├── production_orders.py  # Production order management
    ├── qr_scanner.py    # QR code scanning and tracking
    └── dashboard.py     # Dashboard and analytics
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login
- `POST /api/auth/register` - Register new user
- `GET /api/auth/me` - Get current user

### Users
- `GET /api/users/` - List all users
- `GET /api/users/{id}` - Get user details
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user
- `GET /api/users/roles/` - Get all roles

### Customers
- `GET /api/customers/` - List customers
- `POST /api/customers/` - Create customer
- `GET /api/customers/{id}` - Get customer
- `PUT /api/customers/{id}` - Update customer
- `DELETE /api/customers/{id}` - Delete customer

### Part Numbers
- `GET /api/part-numbers/` - List part numbers
- `POST /api/part-numbers/` - Create part number with routing
- `GET /api/part-numbers/{id}` - Get part number
- `PUT /api/part-numbers/{id}` - Update part number
- `DELETE /api/part-numbers/{id}` - Delete part number

### Sales Orders
- `GET /api/sales-orders/` - List sales orders
- `POST /api/sales-orders/` - Create sales order
- `GET /api/sales-orders/{id}` - Get sales order
- `PUT /api/sales-orders/{id}` - Update sales order
- `DELETE /api/sales-orders/{id}` - Delete sales order

### Production Orders
- `GET /api/production-orders/` - List production orders
- `POST /api/production-orders/` - Create production order
- `GET /api/production-orders/{id}` - Get production order
- `PUT /api/production-orders/{id}` - Update production order
- `POST /api/production-orders/{id}/generate-travel-sheet` - Generate travel sheet
- `DELETE /api/production-orders/{id}` - Delete production order

### QR Scanner
- `POST /api/qr-scanner/scan` - Scan QR code
- `PUT /api/qr-scanner/operations/{id}/complete` - Complete operation
- `GET /api/qr-scanner/operations/{id}` - Get operation details

### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics
- `GET /api/dashboard/production` - Get production dashboard data
- `GET /api/dashboard/work-center-load` - Get work center load
- `GET /api/dashboard/daily-production` - Get daily production stats

## Default Credentials

After running `init_db.py`:

- **Username:** admin
- **Password:** admin123

## Database Schema

See `database_schema.sql` for the complete database schema.

## Notes

- All API endpoints (except `/api/auth/login` and `/api/auth/register`) require authentication
- Use Bearer token authentication: `Authorization: Bearer <token>`
- Price visibility is controlled by user roles
- QR codes are generated automatically for travel sheets and operations
