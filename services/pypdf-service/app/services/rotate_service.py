from pathlib import Path
from typing import Dict
from pypdf import PdfReader, PdfWriter
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def rotate_pdf_pages(
    input_path: Path,
    rotations: Dict[int, int],
    output_path: Path
) -> None:

    try:
        with open(input_path, "rb") as f:
            reader = PdfReader(f, strict=False)
            total_pages = len(reader.pages)

            logger.debug(f"PDF pages: {total_pages}")

            if total_pages > settings.MAX_PAGES:
                raise ValueError(
                    f"PDF has too many pages. Max: {settings.MAX_PAGES}, got: {total_pages}"
                )

            writer = PdfWriter()

            # ✅ CASE 1: No rotation requested → return same PDF
            if not rotations:
                with open(input_path, "rb") as src, open(output_path, "wb") as dst:
                    dst.write(src.read())
                return

            # ✅ CASE 2: Rotate all pages
            if "all" in rotations:
                degree = rotations["all"]
                for page in reader.pages:
                    page.rotate(degree)
                    writer.add_page(page)

            # ✅ CASE 3: Rotate selected pages
            else:
                for page_index in range(total_pages):
                    page = reader.pages[page_index]

                    if page_index in rotations:
                        page.rotate(rotations[page_index])

                    writer.add_page(page)

            with open(output_path, "wb") as out:
                writer.write(out)

            logger.info("PDF rotation completed successfully")

    except Exception as e:
        logger.error(f"PDF rotation failed: {e}")
        raise Exception(f"PDF rotation failed: {str(e)}")
