"""
============================================================================
FILE: app/models/schemas.py
PURPOSE: Pydantic models (7 formats: JPEG, PNG, WebP, AVIF, HEIC, HEIF, TIFF)
============================================================================
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum

# ============================================================================
# ENUMS
# ============================================================================

class OutputFormat(str, Enum):
    """Supported formats (Pure PyVIPS)"""
    JPEG = "jpeg"
    JPG = "jpg"
    PNG = "png"
    WEBP = "webp"
    AVIF = "avif"
    HEIC = "heic"
    HEIF = "heif"
    TIFF = "tiff"

class ResizeMode(str, Enum):
    """Resize modes"""
    CONTAIN = "contain"
    COVER = "cover"
    STRETCH = "stretch"
    EXACT = "exact"

class WatermarkPosition(str, Enum):
    """Watermark positions"""
    TOP_LEFT = "top-left"
    TOP_RIGHT = "top-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_RIGHT = "bottom-right"
    CENTER = "center"


# ============================================================================
# REQUESTS
# ============================================================================

class ConvertRequest(BaseModel):
    """Format conversion"""
    format: OutputFormat = Field(default=OutputFormat.WEBP)
    quality: int = Field(default=75, ge=1, le=100)
    strip_metadata: bool = Field(default=True)

class CompressRequest(BaseModel):
    """Image compression"""
    quality: int = Field(default=75, ge=1, le=100)
    format: Optional[OutputFormat] = Field(default=None)

class ResizeRequest(BaseModel):
    """Resize"""
    width: Optional[int] = Field(default=None, ge=1, le=15000)
    height: Optional[int] = Field(default=None, ge=1, le=15000)
    mode: ResizeMode = Field(default=ResizeMode.CONTAIN)
    format: Optional[OutputFormat] = Field(default=None)
    
    @field_validator('height')
    def check_dimensions(cls, v, info):
        if v is None and info.data.get('width') is None:
            raise ValueError('At least width or height required')
        return v

class OptimizeRequest(BaseModel):
    """Optimization"""
    strip_exif: bool = Field(default=True)
    strip_gps: bool = Field(default=True)
    fix_orientation: bool = Field(default=True)

class CropRequest(BaseModel):
    """Cropping"""
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(ge=1, le=15000)
    height: int = Field(ge=1, le=15000)
    format: Optional[OutputFormat] = Field(default=None)

class TextWatermarkRequest(BaseModel):
    """Text watermark"""
    text: str = Field(max_length=200)
    font_size: int = Field(default=48, ge=10, le=200)
    color: str = Field(default="#FFFFFF")
    opacity: float = Field(default=0.5, ge=0.0, le=1.0)
    position: WatermarkPosition = Field(default=WatermarkPosition.BOTTOM_RIGHT)

class ImageWatermarkRequest(BaseModel):
    """Image watermark"""
    scale: float = Field(default=0.2, ge=0.01, le=1.0)
    opacity: float = Field(default=0.5, ge=0.0, le=1.0)
    position: WatermarkPosition = Field(default=WatermarkPosition.BOTTOM_RIGHT)

class MetadataRequest(BaseModel):
    """Metadata extraction"""

class PaletteRequest(BaseModel):
    """Color palette extraction"""
    num_colors: int = Field(default=5, ge=3, le=10)  

# ============================================================================
# RESPONSES
# ============================================================================

class ErrorResponse(BaseModel):
    """Error"""
    error: str
    detail: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check"""
    status: str
    redis: str
    queue_size: int
    workers: int