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
    ALLOWED_ORIGINS: str = "https://www.zemrev.com,https://zemrev.com,https://api.zemrev.com,http://api.zemrev.com/"
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

    def get_allowed_origins(self) -> List[str]:
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]
    
    def ensure_upload_dir(self):
        """Create upload directory if it doesn't exist"""
        Path(self.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_upload_dir()