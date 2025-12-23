from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Tuple, Dict

# ============================================================================
# PARSER HELPERS
# ============================================================================

def parse_page_ranges(pages_str: str) -> List[Tuple[int, int]]:
    # Parse page ranges
    ranges = []
    parts = pages_str.strip().split(',')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        if '-' in part:
            start, end = part.split('-', 1)
            start_idx = int(start.strip()) - 1  # Convert to 0-indexed
            end_idx = int(end.strip()) - 1
            
            if start_idx < 0 or end_idx < 0:
                raise ValueError(f"Page numbers must be positive: {part}")
            if start_idx > end_idx:
                raise ValueError(f"Invalid range (start > end): {part}")
                
            ranges.append((start_idx, end_idx))
        else:
            page_num = int(part) - 1  # Convert to 0-indexed
            if page_num < 0:
                raise ValueError(f"Page number must be positive: {part}")
            ranges.append((page_num, page_num))
    
    if not ranges:
        raise ValueError("No valid page ranges provided")
    
    return ranges


def parse_rotations(rotations_str: str) -> Dict[int, int]:
 
    rotations = {}
    parts = rotations_str.strip().split(',')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        if ':' not in part:
            raise ValueError(f"Invalid rotation format (expected 'page:degrees'): {part}")
        
        page_str, degrees_str = part.split(':', 1)
        page_num = int(page_str.strip()) - 1  # Convert to 0-indexed
        degrees = int(degrees_str.strip())
        
        if page_num < 0:
            raise ValueError(f"Page number must be positive: {page_str}")
        
        if degrees not in [90, 180, 270]:
            raise ValueError(f"Rotation must be 90, 180, or 270 degrees, got: {degrees}")
        
        rotations[page_num] = degrees
    
    if not rotations:
        raise ValueError("No valid rotations provided")
    
    return rotations


# ============================================================================
# REQUEST MODELS
# ============================================================================

class SplitRequest(BaseModel):
    """Split PDF request"""
    pages: str = Field(..., description="Page ranges like '1-3,5,8-10'")
    
    @field_validator('pages')
    @classmethod
    def validate_pages(cls, v: str) -> str:
        """Validate page range format"""
        try:
            parse_page_ranges(v)
        except ValueError as e:
            raise ValueError(f"Invalid page ranges: {str(e)}")
        return v


class RotateRequest(BaseModel):
    """Rotate PDF pages request"""
    rotations: str = Field(..., description="Rotations like '1:90,3:270'")
    
    @field_validator('rotations')
    @classmethod
    def validate_rotations(cls, v: str) -> str:
        """Validate rotation format"""
        try:
            parse_rotations(v)
        except ValueError as e:
            raise ValueError(f"Invalid rotations: {str(e)}")
        return v


class EncryptRequest(BaseModel):
    """Encrypt PDF request"""
    user_password: Optional[str] = Field(None, description="User password (for opening)")
    owner_password: Optional[str] = Field(None, description="Owner password (for permissions)")
    
    @field_validator('user_password', 'owner_password')
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Password cannot be empty")
        return v


class DecryptRequest(BaseModel):
    """Decrypt PDF request"""
    password: str = Field(..., description="Password to decrypt PDF")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v.strip()) == 0:
            raise ValueError("Password cannot be empty")
        return v


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str