from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class ImageFormat(str, Enum):
    PNG = "png"
    JPEG = "jpeg"
    JPG = "jpg"


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class PdfToImagesRequest(BaseModel):
    format: ImageFormat = Field(default=ImageFormat.PNG, description="Output image format")
    dpi: int = Field(default=150, ge=72, le=300, description="DPI for rendering (72-300)")
    page_range: Optional[str] = Field(None, description="Page range like '1-3,5' (optional, default: all)")
    
    @field_validator('page_range')
    @classmethod
    def validate_page_range(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.strip():
            return None
        return v.strip()


class ImagesToPdfRequest(BaseModel):
    pass


class ExtractTextRequest(BaseModel):
    page_range: Optional[str] = Field(None, description="Page range like '1-3,5' (optional, default: all)")
    preserve_layout: bool = Field(default=False, description="Preserve text layout")
    
    @field_validator('page_range')
    @classmethod
    def validate_page_range(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.strip():
            return None
        return v.strip()


class ExtractImagesRequest(BaseModel):
    page_range: Optional[str] = Field(None, description="Page range like '1-3,5' (optional, default: all)")
    min_width: int = Field(default=100, ge=10, description="Minimum image width in pixels")
    min_height: int = Field(default=100, ge=10, description="Minimum image height in pixels")
    
    @field_validator('page_range')
    @classmethod
    def validate_page_range(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.strip():
            return None
        return v.strip()



class OptimizePdfRequest(BaseModel):
    remove_metadata: bool = Field(default=True, description="Remove PDF metadata")
    remove_annotations: bool = Field(default=True, description="Remove annotations")
    remove_javascript: bool = Field(default=True, description="Remove JavaScript")
    remove_links: bool = Field(default=True, description="Remove hyperlinks")
    compress_images: bool = Field(default=False, description="Compress embedded images")

# ============================================================================
# SIGN PDF - UPDATED FOR MULTIPLE SIGNATURES
# ============================================================================

class SignatureItem(BaseModel):
    id: str = Field(..., description="Unique signature ID")
    type: str = Field(..., description="'text' or 'image'")
    text: Optional[str] = Field(None, description="Text for text signatures")
    font: Optional[str] = Field(None, description="Font name for text signatures")
    rotation: int = Field(default=0, ge=-360, le=360, description="Rotation angle in degrees")
    color: Optional[str] = Field(default="#000000", description="Hex color code")
    opacity: Optional[float] = Field(default=1.0, ge=0.0, le=1.0, description="Opacity")
    x: int = Field(..., ge=0, description="X position")
    y: int = Field(..., ge=0, description="Y position")
    width: int = Field(..., ge=10, le=500, description="Signature width")
    height: int = Field(..., ge=10, le=300, description="Signature height")
    page: int = Field(..., ge=-1, lt=100, description="Page number")

class SignPdfRequest(BaseModel):
    signatures: List[SignatureItem] = Field(..., min_items=1, max_items=100)

# ============================================================================
# CROP PDF
# ============================================================================

class CropPdfRequest(BaseModel):
    x: int = Field(..., ge=0, description="X position")
    y: int = Field(..., ge=0, description="Y position")
    width: int = Field(..., ge=10, description="Crop width")
    height: int = Field(..., ge=10, description="Crop height")    
    page_range: Optional[str] = Field(
       None,
       description="Page range like '1-3,5' (optional, default: all)"
    )

    @field_validator("page_range")
    @classmethod
    def validate_page_range(cls, v):
        if v is None or not v.strip():
            return None
        return v.strip()  


class RemovePagesRequest(BaseModel):
    pages_to_remove: str = Field(
        ..., 
        description="Pages to remove like '1,3,5-7' or '2-4,10'"
    )
    
    @field_validator('pages_to_remove')
    @classmethod
    def validate_pages_format(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("pages_to_remove cannot be empty")
        # Check for valid characters only: digits, comma, hyphen, spaces
        import re
        if not re.match(r'^[\d,\s-]+$', v.strip()):
            raise ValueError(
                "Invalid format. Use format like '1,3,5-7' with only numbers, commas, and hyphens"
            )
        
        return v.strip()    


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class ExtractTextResponse(BaseModel):
    text: str
    page_count: int
    char_count: int


class ExtractImagesResponse(BaseModel):
    image_count: int
    message: str


class OptimizePdfResponse(BaseModel):
    message: str
    original_size_kb: float
    optimized_size_kb: float
    reduction_percent: float


class RemovePagesResponse(BaseModel):
    """Remove pages response"""
    message: str
    original_pages: int
    removed_pages: int
    remaining_pages: int
    original_size_kb: float
    new_size_kb: float    

  