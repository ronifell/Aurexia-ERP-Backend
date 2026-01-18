"""
Aurexia ERP Configuration
"""
import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database - use DATABASE_URL from environment (Render provides this automatically for PostgreSQL)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://aurexia_user:aurexia2024@localhost:5432/aurexia_db")
    
    # Security - SECRET_KEY must be set via environment variable in production
    SECRET_KEY: str = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Application
    APP_NAME: str = "Aurexia ERP"
    APP_VERSION: str = "1.0.0"
    # DEBUG should be False in production
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS - allow frontend URL from environment, with fallback for local development
    # For Render: set FRONTEND_URL environment variable (e.g., https://your-app.onrender.com)
    _frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    _allowed_origins_str = os.getenv(
        "ALLOWED_ORIGINS",
        f"{_frontend_url},http://localhost:3000,http://localhost:3001"
    )
    ALLOWED_ORIGINS: List[str] = [origin.strip() for origin in _allowed_origins_str.split(",") if origin.strip()]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
