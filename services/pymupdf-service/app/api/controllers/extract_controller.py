from pathlib import Path
from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse
from concurrent.futures import ThreadPoolExecutor
import asyncio
import tempfile

from app.services.validator import validate_upload
from app.services.extract_text import extract_text_from_pdf
from app.services.extract_images import extract_images_from_pdf
from app.models.pymupdf_schemas import (
    ExtractTextRequest,ExtractImagesRequest,ExtractTextResponse
)
from app.utils.file_io import (
    safe_remove, safe_remove_multiple,
    create_zip_from_files
)
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Thread pool for blocking operations
executor = ThreadPoolExecutor(max_workers=2)


# ============================================================================
# EXTRACT TEXT
# ============================================================================

async def extract_text_handler(
    file: UploadFile,
    request: ExtractTextRequest
) -> ExtractTextResponse:
    """Handle text extraction from PDF."""
    input_path = None
    
    try:
        logger.info("Extracting text from PDF...")
        
        # Validate upload
        input_path = await validate_upload(file)
        
        # Extract text
        loop = asyncio.get_event_loop()
        text, page_count = await loop.run_in_executor(
            executor,
            extract_text_from_pdf,
            input_path,
            request.page_range,
            request.preserve_layout
        )
        
        logger.info(f"Extracted {len(text)} characters from {page_count} pages")
        
        return ExtractTextResponse(
            text=text,
            page_count=page_count,
            char_count=len(text)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text extraction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if input_path:
            safe_remove(input_path)


# ============================================================================
# EXTRACT IMAGES
# ============================================================================

async def extract_images_handler(
    file: UploadFile,
    request: ExtractImagesRequest
) -> FileResponse:
    """Handle image extraction from PDF."""
    input_path = None
    output_paths = []
    output_dir = None
    
    try:
        logger.info("Extracting images from PDF...")
        
        # Validate upload
        input_path = await validate_upload(file)
        
        # Create temp output directory
        output_dir = Path(tempfile.mkdtemp(dir=settings.UPLOAD_DIR))
        
        # Extract images
        loop = asyncio.get_event_loop()
        output_paths = await loop.run_in_executor(
            executor,
            extract_images_from_pdf,
            input_path,
            output_dir,
            request.page_range,
            request.min_width,
            request.min_height
        )
        
        if not output_paths:
            raise HTTPException(
                status_code=404,
                detail="No images found in PDF matching the size criteria"
            )
        
        # Create ZIP
        zip_path = create_zip_from_files(output_paths, zip_prefix="extracted_images")
        
        logger.info(f"Extracted {len(output_paths)} images from PDF")
        
        return FileResponse(
            path=str(zip_path),
            media_type="application/zip",
            filename="extracted_images.zip",
            background=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image extraction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if input_path:
            safe_remove(input_path)
        safe_remove_multiple(output_paths)
        if output_dir and output_dir.exists():
            try:
                output_dir.rmdir()
            except:
                pass
