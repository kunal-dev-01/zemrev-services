from pathlib import Path
from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse
from concurrent.futures import ThreadPoolExecutor
import asyncio

from app.services.validator import validate_upload
from app.services.crop_pdf import crop_pdf
from app.services.remove_pages import remove_pages_from_pdf
from app.models.pymupdf_schemas import (
    RemovePagesRequest,CropPdfRequest
)
from app.utils.file_io import (
    create_temp_pdf_path, safe_remove,
)
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Thread pool for blocking operations
executor = ThreadPoolExecutor(max_workers=2)

# ============================================================================
# CROP PDF
# ============================================================================

async def crop_pdf_handler(
    file: UploadFile,
    request: CropPdfRequest
) -> FileResponse:
    """Handle PDF cropping."""
    input_path = None
    output_path = None
    
    try:
        logger.info("Cropping PDF...")
        
        input_path = await validate_upload(file)
        output_path = create_temp_pdf_path(prefix="cropped")
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            executor,
            crop_pdf,
            input_path,
            output_path,
            request.x,
            request.y,
            request.width,
            request.height,
            request.page_range
        )
        
        logger.info("Successfully cropped PDF")
        
        return FileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename="cropped.pdf",
            background=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF cropping failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if input_path:
            safe_remove(input_path)


# ============================================================================
# REMOVE PAGES
# ============================================================================

async def remove_pages_handler(
    file: UploadFile,
    request: RemovePagesRequest
) -> FileResponse:
    """Handle PDF page removal."""
    input_path = None
    output_path = None
    
    try:
        logger.info(f"Removing pages from PDF: {request.pages_to_remove}")
        
        # Validate upload
        input_path = await validate_upload(file)
        
        # Create output path
        output_path = create_temp_pdf_path(prefix="pages_removed")
        
        # Remove pages in thread pool (blocking operation)
        loop = asyncio.get_event_loop()
        original_pages, removed_count, remaining_pages, original_size_kb, new_size_kb = await loop.run_in_executor(
            executor,
            remove_pages_from_pdf,
            input_path,
            output_path,
            request.pages_to_remove
        )
        
        reduction_percent = ((original_size_kb - new_size_kb) / original_size_kb) * 100 if original_size_kb > 0 else 0
        
        logger.info(
            f"Successfully removed {removed_count} pages. "
            f"Original: {original_pages} pages ({original_size_kb:.2f}KB) → "
            f"New: {remaining_pages} pages ({new_size_kb:.2f}KB) "
            f"[{reduction_percent:.1f}% size reduction]"
        )
        
        return FileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename="pages_removed.pdf",
            background=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Page removal failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if input_path:
            safe_remove(input_path)            