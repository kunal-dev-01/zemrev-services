from pathlib import Path
from typing import List
from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse
from concurrent.futures import ThreadPoolExecutor
import asyncio
import tempfile

from app.services.validator import validate_upload
from app.services.pdf_to_images import pdf_to_images
from app.services.images_to_pdf import images_to_pdf

from app.models.pymupdf_schemas import PdfToImagesRequest

from app.utils.file_io import (
    create_temp_pdf_path, safe_remove, safe_remove_multiple,
    create_zip_from_files
)
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Thread pool for blocking operations
executor = ThreadPoolExecutor(max_workers=2)


# ============================================================================
# PDF TO IMAGES
# ============================================================================

async def pdf_to_images_handler(
    file: UploadFile,
    request: PdfToImagesRequest
) -> FileResponse:
    input_path = None
    output_paths = []
    output_dir = None
    
    try:
        logger.info("Starting PDF to images conversion...")
        input_path = await validate_upload(file)
        output_dir = Path(tempfile.mkdtemp(dir=settings.UPLOAD_DIR))
        loop = asyncio.get_event_loop()
        output_paths = await loop.run_in_executor(
            executor,
            pdf_to_images,
            input_path,
            output_dir,
            request.format.value,
            request.dpi,
            request.page_range
        )
        
        zip_path = create_zip_from_files(output_paths, zip_prefix="pdf_images")
        
        logger.info(f"Successfully converted PDF to {len(output_paths)} images")
        
        return FileResponse(
            path=str(zip_path),
            media_type="application/zip",
            filename="pdf_images.zip",
            background=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF to images failed: {e}", exc_info=True)
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


# ============================================================================
# IMAGES TO PDF
# ============================================================================

async def images_to_pdf_handler(files: List[UploadFile]) -> FileResponse:
    temp_paths = []
    output_path = None
    
    try:
        logger.info(f"Converting {len(files)} images to PDF...")
        
        if len(files) < 1:
            raise HTTPException(status_code=400, detail="At least 1 image required")
        
        for file in files:
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} is not an image"
                )
            
            content = await file.read()
            temp_file = tempfile.NamedTemporaryFile(
                mode='wb',
                delete=False,
                suffix=Path(file.filename).suffix,
                dir=settings.UPLOAD_DIR
            )
            temp_file.write(content)
            temp_file.close()
            temp_paths.append(Path(temp_file.name))
        
        output_path = create_temp_pdf_path(prefix="images_to_pdf")
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            executor,
            images_to_pdf,
            temp_paths,
            output_path
        )
        
        logger.info("Successfully converted images to PDF")
        
        return FileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename="images_to_pdf.pdf",
            background=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Images to PDF failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        safe_remove_multiple(temp_paths)