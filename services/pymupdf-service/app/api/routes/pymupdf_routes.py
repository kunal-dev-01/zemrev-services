from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import FileResponse
from typing import List, Optional

from app.api.controllers.convert_controller import (
    pdf_to_images_handler,
    images_to_pdf_handler    
)
from app.api.controllers.edit_controller import (
    crop_pdf_handler,
    remove_pages_handler
)
from app.api.controllers.extract_controller import (
    extract_text_handler,
    extract_images_handler
)
from app.api.controllers.optimize_controller import optimize_pdf_handler
from app.api.controllers.sign_pdf_controller import sign_pdf_handler

from app.models.pymupdf_schemas import (
    PdfToImagesRequest, ExtractTextRequest,
    ExtractImagesRequest, OptimizePdfRequest,
    ExtractTextResponse, ImageFormat, CropPdfRequest,RemovePagesRequest
)

router = APIRouter(prefix="/api/v1/pymupdf", tags=["PyMuPDF Tools"])

# ============================================================================
# PDF TO IMAGES
# ============================================================================

@router.post("/pdf-to-images", response_class=FileResponse)
async def pdf_to_images_endpoint(
    file: UploadFile = File(..., description="PDF file to convert"),
    format: ImageFormat = Form(
        default=ImageFormat.PNG, 
        description="Output image format"
    ),
    dpi: int = Form(
        default=150, 
        ge=72, 
        le=300, 
        description="DPI (72-300)"
    ),
    page_range: Optional[str] = Form(
        None, 
        description="Page range like '1-3,5'"
    )
) -> FileResponse:
    """Convert PDF pages to images."""
    request = PdfToImagesRequest(
        format=format,
        dpi=dpi,
        page_range=page_range
    )
    return await pdf_to_images_handler(file, request)


# ============================================================================
# IMAGES TO PDF
# ============================================================================

@router.post("/images-to-pdf", response_class=FileResponse)
async def images_to_pdf_endpoint(
    files: List[UploadFile] = File(..., description="Image files to convert")
) -> FileResponse:
    """Convert multiple images into a single PDF."""
    return await images_to_pdf_handler(files)


# ============================================================================
# EXTRACT TEXT
# ============================================================================

@router.post("/extract-text", response_model=ExtractTextResponse)
async def extract_text_endpoint(
    file: UploadFile = File(..., description="PDF file"),
    page_range: Optional[str] = Form(
        None, 
        description="Page range like '1-3,5'"
    ),
    preserve_layout: bool = Form(
        default=False, 
        description="Preserve layout"
    )
) -> ExtractTextResponse:
    """Extract text from PDF."""
    request = ExtractTextRequest(
        page_range=page_range,
        preserve_layout=preserve_layout
    )
    return await extract_text_handler(file, request)


# ============================================================================
# EXTRACT IMAGES
# ============================================================================

@router.post("/extract-images", response_class=FileResponse)
async def extract_images_endpoint(
    file: UploadFile = File(..., description="PDF file"),
    page_range: Optional[str] = Form(
        None, 
        description="Page range like '1-3,5'"
    ),
    min_width: int = Form(
        default=100, 
        ge=10, 
        description="Min image width"
    ),
    min_height: int = Form(
        default=100, 
        ge=10, 
        description="Min image height"
    )
) -> FileResponse:
    """Extract images from PDF."""
    request = ExtractImagesRequest(
        page_range=page_range,
        min_width=min_width,
        min_height=min_height
    )
    return await extract_images_handler(file, request)


# ============================================================================
# OPTIMIZE PDF
# ============================================================================

@router.post("/optimize", response_class=FileResponse)
async def optimize_pdf_endpoint(
    file: UploadFile = File(..., description="PDF file to optimize"),
    remove_metadata: bool = Form(
        default=True, 
        description="Remove metadata"
    ),
    remove_annotations: bool = Form(
        default=True, 
        description="Remove annotations"
    ),
    remove_javascript: bool = Form(
        default=True, 
        description="Remove JavaScript"
    ),
    remove_links: bool = Form(
        default=True, 
        description="Remove links"
    ),
    compress_images: bool = Form(
        default=False, 
        description="Compress images"
    )
) -> FileResponse:
    """Optimize PDF by removing unnecessary elements."""
    request = OptimizePdfRequest(
        remove_metadata=remove_metadata,
        remove_annotations=remove_annotations,
        remove_javascript=remove_javascript,
        remove_links=remove_links,
        compress_images=compress_images
    )
    return await optimize_pdf_handler(file, request)


# ============================================================================
# SIGN PDF (UPDATED - MULTIPLE SIGNATURES)
# ============================================================================

@router.post("/sign", response_class=FileResponse)
async def sign_pdf_endpoint(
    file: UploadFile = File(..., description="PDF file to sign"),
    signatures_json: str = Form(..., description="JSON array of signature objects"),
    # --- FIX HERE: Use List[UploadFile] with default=[] ---
    signature_image_files: List[UploadFile] = File(default=[], description="Image files")
) -> FileResponse:
    """
    Add multiple signatures to a PDF document.
    """
    return await sign_pdf_handler(file, signatures_json, signature_image_files)


# ============================================================================
# CROP PDF
# ============================================================================

@router.post("/crop", response_class=FileResponse)
async def crop_pdf_endpoint(
    file: UploadFile = File(..., description="PDF file to crop"),
    x: int = Form(..., ge=0, description="X coordinate (left)"),
    y: int = Form(..., ge=0, description="Y coordinate (top)"),
    width: int = Form(..., ge=10, description="Crop width"),
    height: int = Form(..., ge=10, description="Crop height"),
    page_range: Optional[str] = Form(
        None,
        description="Page range like '1-3,5'"
    )
) -> FileResponse:
    """
    Crop all pages of a PDF to specified dimensions.
    Coordinates are in points (1/72 inch).
    """
    request = CropPdfRequest(
        x=x,
        y=y,
        width=width,
        height=height,
        page_range=page_range
    )
    return await crop_pdf_handler(file, request)

# ============================================================================
# REMOVE PAGES
# ============================================================================

@router.post("/remove-pages", response_class=FileResponse)
async def remove_pages_endpoint(
    file: UploadFile = File(..., description="PDF file"),
    pages_to_remove: str = Form(
        ..., 
        description="Pages to remove (e.g., '1,3,5-7,10')"
    )
) -> FileResponse:
    """
    Remove specific pages from PDF.
    
    **Page Format Examples:**
    - Single pages: `"1,3,5"`
    - Ranges: `"2-5"`
    - Combined: `"1,3-5,7,10-12"`
    
    **Notes:**
    - Page numbers start from 1
    - Cannot remove all pages
    - Duplicate pages are automatically handled
    
    **Example:**
    - Input: 10-page PDF, remove `"2,4-6,9"`
    - Output: 5-page PDF (pages 1,3,7,8,10 remain)
    """
    request = RemovePagesRequest(pages_to_remove=pages_to_remove)
    return await remove_pages_handler(file, request)    