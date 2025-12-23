from pathlib import Path
from typing import List
from pypdf import PdfWriter, PdfReader
from app.core.logging import get_logger

logger = get_logger(__name__)


def merge_pdfs(input_paths: List[Path], output_path: Path) -> None:

    if len(input_paths) < 2:
        raise ValueError("At least 2 PDF files required for merging")
    
    writer = PdfWriter()
    
    try:
        for pdf_path in input_paths:
            logger.debug(f"Processing PDF: {pdf_path}")
            
            with open(pdf_path, 'rb') as f:
                reader = PdfReader(f, strict=False)
                page_count = len(reader.pages)
                
                for page_num in range(page_count):
                    page = reader.pages[page_num]
                    writer.add_page(page)
                
                logger.debug(f"Added {page_count} pages from {pdf_path.name}")
        
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        total_pages = len(writer.pages)
        logger.info(f"Successfully merged {len(input_paths)} PDFs into {output_path} ({total_pages} pages)")
        
    except Exception as e:
        logger.error(f"Failed to merge PDFs: {e}")
        raise Exception(f"PDF merge failed: {str(e)}")