
from pathlib import Path
import fitz
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


def parse_page_range(page_range: str | None, total_pages: int) -> list[int]:
    if not page_range:
        return list(range(total_pages))

    pages = set()
    for part in page_range.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-")
            pages.update(range(int(start) - 1, int(end)))
        else:
            pages.add(int(part) - 1)

    return sorted(p for p in pages if 0 <= p < total_pages)


def crop_pdf(
    input_path: Path,
    output_path: Path,
    x: int,
    y: int,
    width: int,
    height: int,
    page_range: str | None = None
) -> None:
    try:
        doc = fitz.open(input_path)
        total_pages = len(doc)

        if total_pages > settings.MAX_PAGES:
            doc.close()
            raise ValueError(
                f"PDF has too many pages. Max: {settings.MAX_PAGES}, got: {total_pages}"
            )

        target_pages = parse_page_range(page_range, total_pages)

        logger.info(
            f"Cropping pages: {target_pages if page_range else 'ALL'} "
            f"to region ({x},{y},{width},{height})"
        )

        output_doc = fitz.open()

        for page_num in target_pages:
            page = doc[page_num]
            page_rect = page.rect

            crop_rect = fitz.Rect(
                x,
                y,
                min(x + width, page_rect.x1),
                min(y + height, page_rect.y1)
            )

            page.set_cropbox(crop_rect)
            output_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

        doc.close()

        output_doc.save(output_path, garbage=4, deflate=True)
        output_doc.close()

        logger.info(f"Successfully cropped PDF -> {output_path}")

    except Exception as e:
        logger.error(f"Failed to crop PDF: {e}")
        raise Exception(f"PDF cropping failed: {str(e)}")
