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
# Explicitly set allowed origins for local development
cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

# Add any additional origins from environment variable (comma-separated)
if settings.ALLOWED_ORIGINS:
    for origin in settings.ALLOWED_ORIGINS.split(","):
        origin = origin.strip()
        # Only add if it's a valid URL and not already in the list
        if origin and origin.startswith("http") and origin not in cors_origins:
            cors_origins.append(origin)

print(f"CORS: Allowing origins: {cors_origins}")

# Add CORS middleware with explicit configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,  # Set to False since we're not using cookies
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],  # Explicit methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Add middleware to log requests (always log for debugging CORS issues)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Always log requests to help debug CORS issues
    origin = request.headers.get('origin', 'N/A')
    print(f"[{request.method}] {request.url.path} - Origin: {origin}")
    response = await call_next(request)
    cors_header = response.headers.get('access-control-allow-origin', 'NOT SET')
    print(f"[{response.status_code}] {request.url.path} - Access-Control-Allow-Origin: {cors_header}")
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

@app.get("/api/test-cors")
async def test_cors():
    """Test endpoint to verify CORS is working"""
    return {"message": "CORS is working!", "status": "ok"}

if __name__ == "__main__":
    import uvicorn
    # Use PORT environment variable for Render (Render sets this automatically)
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=settings.DEBUG_BOOL)
