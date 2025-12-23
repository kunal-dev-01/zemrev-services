from pathlib import Path
from typing import Optional
from pypdf import PdfWriter, PdfReader
from app.core.logging import get_logger

logger = get_logger(__name__)


def encrypt_pdf(
    input_path: Path,
    output_path: Path,
    user_password: Optional[str] = None,
    owner_password: Optional[str] = None
) -> None:

    if not user_password and not owner_password:
        raise ValueError("At least one password (user or owner) must be provided")
    
    if user_password and not owner_password:
        owner_password = user_password
    elif owner_password and not user_password:
        user_password = ""  
    
    try:
        with open(input_path, 'rb') as f:
            reader = PdfReader(f, strict=False)
            writer = PdfWriter()
            
            for page in reader.pages:
                writer.add_page(page)
            
            writer.encrypt(
                user_password=user_password,
                owner_password=owner_password,
                permissions_flag=0b0000 
            )
            
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            logger.info(f"Successfully encrypted PDF -> {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to encrypt PDF: {e}")
        raise Exception(f"PDF encryption failed: {str(e)}")