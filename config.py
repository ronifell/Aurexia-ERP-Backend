"""
Aurexia ERP Configuration
"""
import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database - use DATABASE_URL from environment (Render provides this automatically for PostgreSQL)
    DATABASE_URL: str = "postgresql://aurexia_user:aurexia2024@localhost:5432/aurexia_db"
    
    # Security - SECRET_KEY must be set via environment variable in production
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Application
    APP_NAME: str = "Aurexia ERP"
    APP_VERSION: str = "1.0.0"
    # DEBUG should be False in production
    DEBUG: str = "False"
    
    # CORS - allow frontend URL from environment, with fallback for local development
    # For Render: set FRONTEND_URL environment variable (e.g., https://your-app.onrender.com)
    # ALLOWED_ORIGINS should be comma-separated string (not JSON array)
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: str = ""  # Comma-separated string, not JSON
    
    @property
    def ALLOWED_ORIGINS_LIST(self) -> List[str]:
        """Parse ALLOWED_ORIGINS from comma-separated string to list"""
        if self.ALLOWED_ORIGINS:
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
        # Default fallback if not set
        return [self.FRONTEND_URL, "http://localhost:3000", "http://localhost:3001"]
    
    @property
    def DEBUG_BOOL(self) -> bool:
        """Convert DEBUG string to boolean"""
        return self.DEBUG.lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
