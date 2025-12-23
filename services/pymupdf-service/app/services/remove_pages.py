import fitz 
from pathlib import Path
from typing import Set, Tuple
from fastapi import HTTPException


def parse_page_range(page_range: str, total_pages: int) -> Set[int]:

    pages_to_remove = set()

    parts = page_range.split(',')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        if '-' in part:
            try:
                start, end = part.split('-', 1)
                start = int(start.strip())
                end = int(end.strip())
                
                # Validation
                if start < 1 or end < 1:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Page numbers must be >= 1. Got: {part}"
                    )
                
                if start > end:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid range '{part}': start > end"
                    )
                
                if start > total_pages or end > total_pages:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Page range '{part}' exceeds PDF pages (max: {total_pages})"
                    )
                
                for page_num in range(start, end + 1):
                    pages_to_remove.add(page_num - 1)
                    
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid range format: '{part}'. Use format like '5-7'"
                )
        else:
            # Single page number
            try:
                page_num = int(part)
                
                if page_num < 1:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Page number must be >= 1. Got: {page_num}"
                    )
                
                if page_num > total_pages:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Page {page_num} exceeds PDF pages (max: {total_pages})"
                    )
                
                # Convert to 0-indexed
                pages_to_remove.add(page_num - 1)
                
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid page number: '{part}'"
                )
    
    if not pages_to_remove:
        raise HTTPException(
            status_code=400,
            detail="No valid pages specified for removal"
        )
    
    return pages_to_remove


def remove_pages_from_pdf(
    input_path: Path,
    output_path: Path,
    pages_to_remove: str
) -> Tuple[int, int, int, float, float]:

    doc = None
    
    try:
        # Open PDF
        doc = fitz.open(str(input_path))
        original_pages = len(doc)
        
        if original_pages == 0:
            raise HTTPException(
                status_code=400,
                detail="PDF has no pages"
            )
        
        pages_set = parse_page_range(pages_to_remove, original_pages)

        if len(pages_set) >= original_pages:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot remove all pages. PDF has {original_pages} pages, trying to remove {len(pages_set)}"
            )
        
        original_size = input_path.stat().st_size
        
        pages_to_delete = sorted(pages_set, reverse=True)
        
        for page_num in pages_to_delete:
            doc.delete_page(page_num)
        
        doc.save(
            str(output_path),
            garbage=4,  # Maximum garbage collection
            deflate=True,  # Compress streams
            clean=True  # Clean up PDF structure
        )
        
        remaining_pages = len(doc)
        removed_count = len(pages_set)
        
        doc.close()
        doc = None
        
        new_size = output_path.stat().st_size
        
        return (
            original_pages,
            removed_count,
            remaining_pages,
            original_size / 1024,  # KB
            new_size / 1024  # KB
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove pages: {str(e)}"
        )
        
    finally:
        if doc:
            try:
                doc.close()
            except:
                pass