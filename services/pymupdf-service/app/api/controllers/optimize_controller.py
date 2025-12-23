from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse
from concurrent.futures import ThreadPoolExecutor
import asyncio

from app.services.validator import validate_upload
from app.services.optimize_pdf import optimize_pdf
from app.models.pymupdf_schemas import OptimizePdfRequest
from app.utils.file_io import (
    create_temp_pdf_path, safe_remove,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

executor = ThreadPoolExecutor(max_workers=2)


# ============================================================================
# OPTIMIZE PDF
# ============================================================================

async def optimize_pdf_handler(
    file: UploadFile,
    request: OptimizePdfRequest
) -> FileResponse:
    """Handle PDF optimization."""
    input_path = None
    output_path = None
    
    try:
        logger.info("Optimizing PDF...")
        input_path = await validate_upload(file)
        output_path = create_temp_pdf_path(prefix="optimized")
        loop = asyncio.get_event_loop()
        original_size, optimized_size = await loop.run_in_executor(
            executor,
            optimize_pdf,
            input_path,
            output_path,
            request.remove_metadata,
            request.remove_annotations,
            request.remove_javascript,
            request.remove_links,
            request.compress_images
        )
        
        reduction = ((original_size - optimized_size) / original_size) * 100
        logger.info(
            f"PDF optimized: {original_size/1024:.2f}KB → "
            f"{optimized_size/1024:.2f}KB ({reduction:.1f}% reduction)"
        )
        
        return FileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename="optimized.pdf",
            background=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF optimization failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if input_path:
            safe_remove(input_path)
