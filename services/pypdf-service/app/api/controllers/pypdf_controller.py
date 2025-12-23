from pathlib import Path
from typing import List
from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse
from concurrent.futures import ThreadPoolExecutor
import asyncio

from app.services.validator import validate_upload
from app.services.merge_service import merge_pdfs
from app.services.split_service import split_pdf
from app.services.rotate_service import rotate_pdf_pages
from app.services.encrypt_service import encrypt_pdf
from app.services.decrypt_service import decrypt_pdf
from app.models.pypdf_schemas import (
    SplitRequest, RotateRequest, EncryptRequest, DecryptRequest,
    parse_page_ranges, parse_rotations
)
from app.utils.file_io import (
    create_temp_pdf_path, safe_remove, safe_remove_multiple,
    create_zip_from_pdfs
)
from app.core.logging import get_logger

logger = get_logger(__name__)

executor = ThreadPoolExecutor(max_workers=2)


async def merge_pdfs_handler(files: List[UploadFile]) -> FileResponse:
    
    if len(files) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 PDF files required for merging"
        )
    
    temp_paths = []
    output_path = None
    
    try:
        for file in files:
            temp_path = await validate_upload(file)
            temp_paths.append(temp_path)
        
        output_path = create_temp_pdf_path(prefix="merged")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            executor,
            merge_pdfs,
            temp_paths,
            output_path
        )
        
        return FileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename="merged.pdf",
            background=None 
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Merge operation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Merge failed: {str(e)}")
    finally:
        safe_remove_multiple(temp_paths)


async def split_pdf_handler(
    file: UploadFile,
    request: SplitRequest
) -> FileResponse:

    input_path = None
    output_paths = []

    try:
        input_path = await validate_upload(file)
        ranges = parse_page_ranges(request.pages)
        logger.info(f"Split request: {len(ranges)} ranges from {request.pages}")
        loop = asyncio.get_event_loop()
        output_paths = await loop.run_in_executor(
            executor,
            split_pdf,
            input_path,
            ranges,
            Path(input_path.parent)
        )

        logger.info(f"Number of ranges: {len(ranges)}")
        logger.info(f"Number of output PDFs: {len(output_paths)}")
        logger.info(f"Output paths: {output_paths}")

        if len(ranges) == 1:
            single_pdf = output_paths[0]
            output_paths = []
            
            return FileResponse(
                path=str(single_pdf),
                media_type="application/pdf",
                filename="split.pdf",
                background=None
            )

        zip_path = create_zip_from_pdfs(output_paths, zip_prefix="split")
        safe_remove_multiple(output_paths)
        output_paths = []

        response = FileResponse(
            path=str(zip_path),
            media_type="application/zip",
            filename="split_pages.zip",
            background=None
        )

        response.headers["Content-Type"] = "application/zip"
        response.headers["Content-Disposition"] = 'attachment; filename="split_pages.zip"'

        return response

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Split operation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Split failed: {str(e)}")

    finally:
        if input_path:
            safe_remove(input_path)
        
        if output_paths:
            safe_remove_multiple(output_paths)



async def rotate_pdf_handler(
    file: UploadFile,
    request: RotateRequest
) -> FileResponse:
    
    input_path = None
    output_path = None
    
    try:
        input_path = await validate_upload(file)
        rotations = parse_rotations(request.rotations)
        logger.info(f"Rotate request: {len(rotations)} pages from {request.rotations}")
        
        output_path = create_temp_pdf_path(prefix="rotated")
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            executor,
            rotate_pdf_pages,
            input_path,
            rotations,
            output_path
        )
        
        return FileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename="rotated.pdf",
            background=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rotate operation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Rotation failed: {str(e)}")
    finally:
        if input_path:
            safe_remove(input_path)


async def encrypt_pdf_handler(
    file: UploadFile,
    request: EncryptRequest
) -> FileResponse:
    
    input_path = None
    output_path = None
    
    try:
        input_path = await validate_upload(file)
        output_path = create_temp_pdf_path(prefix="encrypted")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            executor,
            encrypt_pdf,
            input_path,
            output_path,
            request.user_password,
            request.owner_password
        )
        
        return FileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename="encrypted.pdf",
            background=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Encrypt operation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Encryption failed: {str(e)}")
    finally:
        if input_path:
            safe_remove(input_path)


async def decrypt_pdf_handler(
    file: UploadFile,
    request: DecryptRequest
) -> FileResponse:
    
    input_path = None
    output_path = None
    
    try:
        input_path = await validate_upload(file)
        output_path = create_temp_pdf_path(prefix="decrypted")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            executor,
            decrypt_pdf,
            input_path,
            output_path,
            request.password
        )
        
        return FileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename="decrypted.pdf",
            background=None
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Decrypt operation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Decryption failed: {str(e)}")
    finally:
        if input_path:
            safe_remove(input_path)