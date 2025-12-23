from pathlib import Path
from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse
from concurrent.futures import ThreadPoolExecutor
import asyncio

from app.services.validator import validate_upload
from app.services.compress_pdf import compress_pdf_ghostscript
from app.services.flatten_pdf import flatten_pdf_ghostscript
from app.services.convert_pdfa import convert_to_pdfa
from app.models.ghostscript_schemas import (
    CompressPdfRequest, FlattenPdfRequest, ConvertToPdfARequest
)
from app.utils.file_io import create_temp_pdf_path, safe_remove
from app.core.logging import get_logger

logger = get_logger(__name__)

# Thread pool for blocking operations
executor = ThreadPoolExecutor(max_workers=2)


async def compress_pdf_handler(
    file: UploadFile,
    request: CompressPdfRequest
) -> FileResponse:
    """Handle PDF compression with Ghostscript."""
    input_path = None
    output_path = None
    
    try:
        input_path = await validate_upload(file)
        output_path = create_temp_pdf_path(prefix="compressed")
        loop = asyncio.get_event_loop()
        original_size, compressed_size = await loop.run_in_executor(
            executor,
            compress_pdf_ghostscript,
            input_path,
            output_path,
            request.level.value
        )
        
        return FileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename="compressed.pdf",
            background=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF compression failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if input_path:
            safe_remove(input_path)


async def flatten_pdf_handler(
    file: UploadFile,
    request: FlattenPdfRequest
) -> FileResponse:
    """Handle PDF flattening with Ghostscript."""
    input_path = None
    output_path = None
    
    try:
        input_path = await validate_upload(file)
        output_path = create_temp_pdf_path(prefix="flattened")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            executor,
            flatten_pdf_ghostscript,
            input_path,
            output_path
        )
        
        return FileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename="flattened.pdf",
            background=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF flattening failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if input_path:
            safe_remove(input_path)


async def convert_to_pdfa_handler(
    file: UploadFile,
    request: ConvertToPdfARequest
) -> FileResponse:
    """Handle PDF to PDF/A conversion with Ghostscript."""
    input_path = None
    output_path = None
    
    try:
        input_path = await validate_upload(file)
        output_path = create_temp_pdf_path(prefix=f"pdfa_{request.version}")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            executor,
            convert_to_pdfa,
            input_path,
            output_path,
            request.version
        )
        
        return FileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename=f"pdfa_{request.version}.pdf",
            background=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF/A conversion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if input_path:
            safe_remove(input_path)