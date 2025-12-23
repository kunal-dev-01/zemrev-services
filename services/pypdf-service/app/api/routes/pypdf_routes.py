from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from typing import List

from app.api.controllers.pypdf_controller import (
    merge_pdfs_handler,
    split_pdf_handler,
    rotate_pdf_handler,
    encrypt_pdf_handler,
    decrypt_pdf_handler
)
from app.models.pypdf_schemas import (
    SplitRequest, RotateRequest, EncryptRequest, DecryptRequest
)

router = APIRouter(prefix="/api/v1/pdf", tags=["PDF Tools"])


@router.post("/merge", response_class=FileResponse)
async def merge_pdfs_endpoint(
    files: List[UploadFile] = File(..., description="PDF files to merge (minimum 2)")
) -> FileResponse:
   
    return await merge_pdfs_handler(files)


@router.post("/split", response_class=FileResponse)
async def split_pdf_endpoint(
    file: UploadFile = File(..., description="PDF file to split"),
    pages: str = Form(..., description="Page ranges like '1-3,5,8-10'")
) -> FileResponse:
    
    request = SplitRequest(pages=pages)
    return await split_pdf_handler(file, request)


@router.post("/rotate", response_class=FileResponse)
async def rotate_pdf_endpoint(
    file: UploadFile = File(..., description="PDF file to rotate"),
    rotations: str = Form(..., description="Rotations like '1:90,3:270'")
) -> FileResponse:
    
    request = RotateRequest(rotations=rotations)
    return await rotate_pdf_handler(file, request)


@router.post("/encrypt", response_class=FileResponse)
async def encrypt_pdf_endpoint(
    file: UploadFile = File(..., description="PDF file to encrypt"),
    user_password: str = Form(None, description="Password for opening PDF"),
    owner_password: str = Form(None, description="Password for permissions")
) -> FileResponse:
    
    # Validate at least one password
    if not user_password and not owner_password:
        raise HTTPException(
            status_code=400,
            detail="At least one password (user_password or owner_password) must be provided"
        )
    
    request = EncryptRequest(
        user_password=user_password,
        owner_password=owner_password
    )
    return await encrypt_pdf_handler(file, request)


@router.post("/decrypt", response_class=FileResponse)
async def decrypt_pdf_endpoint(
    file: UploadFile = File(..., description="Encrypted PDF file"),
    password: str = Form(..., description="Password to decrypt")
) -> FileResponse:
    
    request = DecryptRequest(password=password)
    return await decrypt_pdf_handler(file, request)