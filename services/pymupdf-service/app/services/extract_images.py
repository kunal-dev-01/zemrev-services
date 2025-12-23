from pathlib import Path
from typing import List, Optional
import fitz 
from PIL import Image
import io

from app.core.logging import get_logger
from app.core.config import settings
from app.services.pdf_to_images import parse_page_range

logger = get_logger(__name__)


def extract_images_from_pdf(
    pdf_path: Path,
    output_dir: Path,
    page_range: Optional[str] = None,
    min_width: int = 100,
    min_height: int = 100
) -> List[Path]:

    output_paths = []
    image_counter = 1
    
    try:
        # Open PDF
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        logger.info(f"Extracting images from PDF: {total_pages} pages")
        
        if total_pages > settings.MAX_PAGES:
            doc.close()
            raise ValueError(f"PDF has too many pages. Max: {settings.MAX_PAGES}, got: {total_pages}")
        
        pages_to_extract = parse_page_range(page_range, total_pages)
        logger.info(f"Scanning {len(pages_to_extract)} pages for images")
        
        for page_num in pages_to_extract:
            page = doc[page_num]
            
            image_list = page.get_images(full=True)
            
            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]  # Image xref
                
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                img = Image.open(io.BytesIO(image_bytes))
                width, height = img.size
                
                if width < min_width or height < min_height:
                    logger.debug(
                        f"Skipping small image on page {page_num + 1}: "
                        f"{width}x{height}px (min: {min_width}x{min_height})"
                    )
                    continue
                
                output_path = output_dir / f"image_{image_counter:03d}.{image_ext}"
                
                with open(output_path, 'wb') as f:
                    f.write(image_bytes)
                
                output_paths.append(output_path)
                logger.debug(
                    f"Extracted image {image_counter} from page {page_num + 1}: "
                    f"{width}x{height}px -> {output_path.name}"
                )
                
                image_counter += 1
        
        doc.close()
        
        logger.info(f"Successfully extracted {len(output_paths)} images")
        
        return output_paths
        
    except Exception as e:
        logger.error(f"Failed to extract images from PDF: {e}")
        
        for path in output_paths:
            try:
                path.unlink()
            except:
                pass
        raise Exception(f"Image extraction failed: {str(e)}")