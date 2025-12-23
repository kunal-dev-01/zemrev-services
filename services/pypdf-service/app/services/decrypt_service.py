from pathlib import Path
from pypdf import PdfWriter, PdfReader
from app.core.logging import get_logger

logger = get_logger(__name__)


def decrypt_pdf(
    input_path: Path,
    output_path: Path,
    password: str
) -> None:

    if not password:
        raise ValueError("Password is required for decryption")
    
    try:
        with open(input_path, 'rb') as f:
            reader = PdfReader(f, strict=False)
            # Check if PDF is encrypted
            if not reader.is_encrypted:
                raise ValueError("PDF is not encrypted")
            
            # Try to decrypt
            decrypt_result = reader.decrypt(password)
            
            
            if decrypt_result == 0:
                raise ValueError("Incorrect password or decryption failed")
            
            logger.debug(f"Decryption successful (mode: {decrypt_result})")
            
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            logger.info(f"Successfully decrypted PDF -> {output_path}")
        
    except ValueError as e:
        logger.warning(f"Decryption validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to decrypt PDF: {e}")
        raise Exception(f"PDF decryption failed: {str(e)}")