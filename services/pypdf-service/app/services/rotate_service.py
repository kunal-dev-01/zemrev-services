from pathlib import Path
from typing import Dict
from pypdf import PdfWriter, PdfReader
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def rotate_pdf_pages(
    input_path: Path,
    rotations: Dict[int, int],
    output_path: Path
) -> None:

    if not rotations:
        raise ValueError("No rotations specified")
    
    for page_idx, degrees in rotations.items():
        if degrees not in [90, 180, 270]:
            raise ValueError(
                f"Invalid rotation for page {page_idx + 1}: {degrees}. "
                "Must be 90, 180, or 270"
            )
    
    try:
        with open(input_path, 'rb') as f:
            reader = PdfReader(f, strict=False)
            total_pages = len(reader.pages)
            
            logger.debug(f"Input PDF has {total_pages} pages")
            
            if total_pages > settings.MAX_PAGES:
                raise ValueError(
                    f"PDF has too many pages. Max: {settings.MAX_PAGES}, got: {total_pages}"
                )
            
            for page_idx in rotations.keys():
                if page_idx >= total_pages:
                    raise ValueError(
                        f"Page index {page_idx + 1} exceeds total pages {total_pages}"
                    )
            
            writer = PdfWriter()
            
            for page_num in range(total_pages):
                page = reader.pages[page_num]
                
                if page_num in rotations:
                    degrees = rotations[page_num]
                    page.rotate(degrees)
                    logger.debug(f"Rotated page {page_num + 1} by {degrees}°")
                
                writer.add_page(page)
            
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            logger.info(
                f"Successfully rotated {len(rotations)} pages in PDF -> {output_path}"
            )
        
    except Exception as e:
        logger.error(f"Failed to rotate PDF: {e}")
        raise Exception(f"PDF rotation failed: {str(e)}")