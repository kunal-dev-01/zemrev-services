from pydantic import BaseModel, Field, field_validator
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class CompressionLevel(str, Enum):
    SCREEN = "screen"  
    EBOOK = "ebook"    
    PRINTER = "printer"  
    PREPRESS = "prepress"


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class CompressPdfRequest(BaseModel):
    level: CompressionLevel = Field(
        default=CompressionLevel.EBOOK,
        description="Compression level (screen/ebook/printer/prepress)"
    )


class FlattenPdfRequest(BaseModel):
    pass


class ConvertToPdfARequest(BaseModel):
    version: str = Field(
        default="2b",
        description="PDF/A version: 1b, 2b, or 3b"
    )
    
    @field_validator('version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        if v not in ['1b', '2b', '3b']:
            raise ValueError("Version must be 1b, 2b, or 3b")
        return v

# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class CompressPdfResponse(BaseModel):
    original_size_kb: float
    compressed_size_kb: float
    reduction_percent: float
    compression_level: str