from pathlib import Path
from typing import List
from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse
from concurrent.futures import ThreadPoolExecutor
import asyncio
import tempfile
import json

from app.services.validator import validate_upload
from app.services.sign_pdf import sign_pdf
from app.models.pymupdf_schemas import SignPdfRequest, SignatureItem
from app.utils.file_io import create_temp_pdf_path, safe_remove
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

executor = ThreadPoolExecutor(max_workers=2)


async def sign_pdf_handler(
    file: UploadFile,
    signatures_json: str,
    signature_image_files: List[UploadFile]
) -> FileResponse:

    input_path = None
    output_path = None
    temp_image_paths = []
    
    try:
        # ====================================================================
        # STEP 1: Validate PDF File
        # ====================================================================
        logger.info("Validating PDF file...")
        input_path = await validate_upload(file)
        output_path = create_temp_pdf_path(prefix="signed")
        
        # ====================================================================
        # STEP 2: Parse Signatures JSON
        # ====================================================================
        logger.info("Parsing signatures JSON...")
        try:
            signatures_data = json.loads(signatures_json)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid signatures_json format: {str(e)}"
            )
        
        if not isinstance(signatures_data, list):
            raise HTTPException(status_code=400, detail="signatures_json must be a JSON array")
            
        if len(signatures_data) == 0:
            raise HTTPException(status_code=400, detail="At least one signature is required")

        # ====================================================================
        # STEP 3: Validate Signature Items
        # ====================================================================
        logger.info(f"Validating {len(signatures_data)} signatures...")
        validated_signatures = []
        
        for idx, sig_data in enumerate(signatures_data):
            try:
                # Pydantic handles types, defaults, and rotation validation
                sig = SignatureItem(**sig_data)
                validated_signatures.append(sig)
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid signature at index {idx}: {str(e)}"
                )
        
        # ====================================================================
        # STEP 4: Process Image Files
        # ====================================================================
        signature_images = {}
        
        # Filter signatures that require an image
        image_signatures = [sig for sig in validated_signatures if sig.type == 'image']
        
        if image_signatures:
            uploaded_files = signature_image_files or []
            
            logger.info(f"Processing images. Expected: {len(image_signatures)}, Received: {len(uploaded_files)}")
            
            if len(uploaded_files) != len(image_signatures):
                error_msg = f"Expected {len(image_signatures)} image files, but received {len(uploaded_files)}. Please try again."
                logger.error(error_msg)
                raise HTTPException(status_code=400, detail=error_msg)
            
            # Save uploaded images to temp and map them
            for idx, img_file in enumerate(uploaded_files):
                if not img_file or not img_file.filename:
                    continue
                
                if not img_file.content_type or not img_file.content_type.startswith('image/'):
                    raise HTTPException(
                        status_code=400,
                        detail=f"File {img_file.filename} is not a valid image. Type: {img_file.content_type}"
                    )
                
                content = await img_file.read()
                temp_file = tempfile.NamedTemporaryFile(
                    mode='wb',
                    delete=False,
                    suffix=Path(img_file.filename).suffix,
                    dir=settings.UPLOAD_DIR
                )
                temp_file.write(content)
                temp_file.close()
                
                temp_path = Path(temp_file.name)
                temp_image_paths.append(temp_path)
                
                signature_id = image_signatures[idx].id
                signature_images[signature_id] = temp_path
                logger.info(f"Mapped image {img_file.filename} to signature {signature_id}")
        
        # ====================================================================
        # STEP 5: Build Signature Data for Processing
        # ====================================================================
        logger.info("Building final signature data...")
        signatures_for_processing = []
        
        for sig in validated_signatures:
            sig_dict = {
                'id': sig.id,
                'type': sig.type,
                'x': sig.x,
                'y': sig.y,
                'width': sig.width,
                'height': sig.height,
                'page': sig.page,
                'color': sig.color if sig.color else "#000000",
                'opacity': sig.opacity if sig.opacity is not None else 1.0,
                'rotation': sig.rotation if sig.rotation is not None else 0,
            }
            
            if sig.type == 'text':
                sig_dict['text'] = sig.text or 'Signature'
                sig_dict['font'] = sig.font or 'Dancing Script'
            elif sig.type == 'image':
                if sig.id not in signature_images:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Image file missing for signature ID: {sig.id}"
                    )
                sig_dict['image_path'] = str(signature_images[sig.id])
            
            signatures_for_processing.append(sig_dict)
        
        # ====================================================================
        # STEP 6: Process PDF
        # ====================================================================
        logger.info(f"Processing PDF with {len(signatures_for_processing)} signatures...")
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            executor,
            sign_pdf,
            input_path,
            output_path,
            signatures_for_processing
        )
        
        logger.info(f"Successfully signed PDF: {output_path}")
        
        # ====================================================================
        # STEP 7: Return Result
        # ====================================================================
        return FileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename="signed.pdf",
            background=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF signing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"PDF signing failed: {str(e)}"
        )
    finally:
        # Cleanup temporary files
        if input_path:
            safe_remove(input_path)
        for temp_path in temp_image_paths:
            safe_remove(temp_path)