from pathlib import Path
from typing import Optional, Tuple
import fitz 

from app.core.logging import get_logger
from app.core.config import settings
from app.services.pdf_to_images import parse_page_range

logger = get_logger(__name__)


def extract_text_from_pdf(
    pdf_path: Path,
    page_range: Optional[str] = None,
    preserve_layout: bool = False
) -> Tuple[str, int]:

    try:
        # Open PDF
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        logger.info(f"Extracting text from PDF: {total_pages} pages")
        
        if total_pages > settings.MAX_PAGES:
            doc.close()
            raise ValueError(f"PDF has too many pages. Max: {settings.MAX_PAGES}, got: {total_pages}")
        
        pages_to_extract = parse_page_range(page_range, total_pages)
        logger.info(f"Extracting text from {len(pages_to_extract)} pages")

        extracted_text = []
        
        for page_num in pages_to_extract:
            page = doc[page_num]
            
            if preserve_layout:
                text = page.get_text("text", sort=True)
            else:
                text = page.get_text()
            
            if text.strip():
                extracted_text.append(f"--- Page {page_num + 1} ---\n{text}\n")
        
        doc.close()
        
        full_text = "\n".join(extracted_text)
        
        logger.info(
            f"Successfully extracted {len(full_text)} characters "
            f"from {len(pages_to_extract)} pages"
        )
        
        return full_text, len(pages_to_extract)
        
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        raise Exception(f"Text extraction failed: {str(e)}")