"""
Aurexia ERP - Main FastAPI Application
"""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from database import engine, Base

# Import all models to ensure they are registered
import models

# Import routers
from routes import auth, users, customers, part_numbers, sales_orders, production_orders, qr_scanner, dashboard, processes, quality_inspections, shipments, exports, materials

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Manufacturing ERP system for metal-mechanical companies"
)

# Configure CORS - MUST be added first!
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add middleware to log requests (only in debug mode to reduce overhead)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    if settings.DEBUG_BOOL:
        # Only log basic request info in debug mode
        print(f"[{request.method}] {request.url.path}")
    response = await call_next(request)
    if settings.DEBUG_BOOL:
        print(f"[{response.status_code}] {request.url.path}")
    return response

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(customers.router, prefix="/api")
app.include_router(part_numbers.router, prefix="/api")
app.include_router(sales_orders.router, prefix="/api")
app.include_router(production_orders.router, prefix="/api")
app.include_router(qr_scanner.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(processes.router, prefix="/api")
app.include_router(quality_inspections.router, prefix="/api")
app.include_router(shipments.router, prefix="/api")
app.include_router(exports.router, prefix="/api")
app.include_router(materials.router, prefix="/api")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Aurexia ERP API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    # Use PORT environment variable for Render (Render sets this automatically)
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=settings.DEBUG_BOOL)
