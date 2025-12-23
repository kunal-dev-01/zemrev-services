from pathlib import Path
from typing import List, Optional, Tuple
import fitz  
from PIL import Image
import io

from app.core.logging import get_logger
from app.core.config import settings
from app.utils.file_io import create_temp_pdf_path

logger = get_logger(__name__)


def parse_page_range(page_range_str: Optional[str], total_pages: int) -> List[int]:

    if not page_range_str:
        return list(range(total_pages))
    
    pages = set()
    parts = page_range_str.split(',')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        if '-' in part:
            start, end = part.split('-', 1)
            start_idx = int(start.strip()) - 1 
            end_idx = int(end.strip()) - 1
            
            if start_idx < 0 or end_idx >= total_pages:
                raise ValueError(f"Page range {part} out of bounds (1-{total_pages})")
            
            pages.update(range(start_idx, end_idx + 1))
        else:
            page_num = int(part) - 1 
            if page_num < 0 or page_num >= total_pages:
                raise ValueError(f"Page {int(part)} out of bounds (1-{total_pages})")
            pages.add(page_num)
    
    return sorted(list(pages))


def pdf_to_images(
    pdf_path: Path,
    output_dir: Path,
    image_format: str = "png",
    dpi: int = 150,
    page_range: Optional[str] = None
) -> List[Path]:

    output_paths = []
    
    try:
        # Open PDF
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        logger.info(f"PDF opened: {total_pages} pages")
        
        if total_pages > settings.MAX_PAGES:
            doc.close()
            raise ValueError(f"PDF has too many pages. Max: {settings.MAX_PAGES}, got: {total_pages}")
        
        pages_to_convert = parse_page_range(page_range, total_pages)
        logger.info(f"Converting {len(pages_to_convert)} pages at {dpi} DPI")
        
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        
        for idx, page_num in enumerate(pages_to_convert, start=1):
            page = doc[page_num]
            
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            output_path = output_dir / f"page_{idx:03d}.{image_format}"
            
            if image_format.lower() in ['jpg', 'jpeg']:
                # Convert RGBA to RGB for JPEG
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                img.save(output_path, 'JPEG', quality=95, optimize=True)
            else:
                img.save(output_path, 'PNG', optimize=True)
            
            output_paths.append(output_path)
            logger.debug(f"Converted page {page_num + 1} -> {output_path.name}")
        
        doc.close()
        logger.info(f"Successfully converted {len(output_paths)} pages to {image_format}")
        
        return output_paths
        
    except Exception as e:
        logger.error(f"Failed to convert PDF to images: {e}")
        # Cleanup any created files
        for path in output_paths:
            try:
                path.unlink()
            except:
                pass
        raise Exception(f"PDF to images conversion failed: {str(e)}")