"""
============================================================================
FILE: services/pymupdf-service/app/core/config.py
PURPOSE: PyMuPDF Service configuration
============================================================================
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pathlib import Path

class Settings(BaseSettings):
    # ========================================================================
    # SERVICE CONFIG ONLY (Queue config handled by zemrev-queue package)
    # ========================================================================
    
    WORKERS: int = 1
    LOG_LEVEL: str = "info"
    HOST: str = "0.0.0.0"
    PORT: int = 8002
    UPLOAD_DIR: str = "/tmp/zemrev_pymupdf_uploads"
    
    # ========================================================================
    # TOOL-SPECIFIC LIMITS
    # ========================================================================
    
    MAX_FILE_SIZE: int = 62914560         # 60MB
    MAX_PAGES: int = 300
    TOOL_TIMEOUT: int = 300               # 5 minutes
    
    # ========================================================================
    # QUEUE-RELATED (Service uses this, .env provides value)
    # ========================================================================
    
    QUEUE_MAX_WORKERS: int = 2
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    def ensure_upload_dir(self):
        """Create upload directory if it doesn't exist"""
        Path(self.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_upload_dir()