from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pathlib import Path

class Settings(BaseSettings):
    
    # ========================================================================
    # SERVICE CONFIG
    # ========================================================================
    
    WORKERS: int = 1
    LOG_LEVEL: str = "info"
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    UPLOAD_DIR: str = "/tmp/zemrev_ghostscript_uploads"
    
    # ========================================================================
    # TOOL-SPECIFIC LIMITS
    # ========================================================================
    
    MAX_FILE_SIZE: int = 83886080   
    MAX_PAGES: int = 250        
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