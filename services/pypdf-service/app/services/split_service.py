from pathlib import Path
from typing import List, Tuple
from pypdf import PdfWriter, PdfReader
from app.core.config import settings
from app.core.logging import get_logger
from app.utils.file_io import create_temp_pdf_path

logger = get_logger(__name__)


def split_pdf(
    input_path: Path,
    ranges: List[Tuple[int, int]],
    output_dir: Path
) -> List[Path]:

    output_paths = []
    
    try:
        with open(input_path, 'rb') as f:
            reader = PdfReader(f, strict=False)
            total_pages = len(reader.pages)
            
            logger.debug(f"Input PDF has {total_pages} pages")
            
            if total_pages > settings.MAX_PAGES:
                raise ValueError(
                    f"PDF has too many pages. Max: {settings.MAX_PAGES}, got: {total_pages}"
                )
            
            for idx, (start_page, end_page) in enumerate(ranges, start=1):
                if start_page >= total_pages:
                    raise ValueError(
                        f"Range {idx}: start page {start_page + 1} exceeds total pages {total_pages}"
                    )
                if end_page >= total_pages:
                    raise ValueError(
                        f"Range {idx}: end page {end_page + 1} exceeds total pages {total_pages}"
                    )
                
                writer = PdfWriter()
                
                for page_num in range(start_page, end_page + 1):
                    page = reader.pages[page_num]
                    writer.add_page(page)
                
                output_path = create_temp_pdf_path(prefix=f"split_{idx}")
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)
                
                output_paths.append(output_path)
                page_count = end_page - start_page + 1
                logger.debug(
                    f"Created split {idx}: pages {start_page + 1}-{end_page + 1} "
                    f"({page_count} pages) -> {output_path}"
                )
        
        logger.info(f"Successfully split PDF into {len(output_paths)} files")
        return output_paths
        
    except Exception as e:
        logger.error(f"Failed to split PDF: {e}")
        for path in output_paths:
            try:
                path.unlink()
            except:
                pass
        raise Exception(f"PDF split failed: {str(e)}")