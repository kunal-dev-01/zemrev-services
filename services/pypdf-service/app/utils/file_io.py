"""
============================================================================
FILE: services/pdf-service/app/utils/file_io.py
PURPOSE: File I/O utilities for PDF operations
============================================================================
"""

from pathlib import Path
import tempfile
import shutil
from typing import List
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_temp_pdf_path(prefix: str = "output") -> Path:

    temp_file = tempfile.NamedTemporaryFile(
        mode='wb',
        delete=False,
        suffix='.pdf',
        prefix=f"{prefix}_",
        dir=settings.UPLOAD_DIR
    )
    temp_file.close()
    return Path(temp_file.name)


def safe_remove(path: Path) -> None:

    try:
        if path.exists():
            path.unlink()
            logger.debug(f"Removed temp file: {path}")
    except Exception as e:
        logger.warning(f"Failed to remove temp file {path}: {e}")


def safe_remove_multiple(paths: List[Path]) -> None:

    for path in paths:
        safe_remove(path)


def create_zip_from_pdfs(pdf_paths: List[Path], zip_prefix: str = "split") -> Path:

    temp_dir = tempfile.mkdtemp(dir=settings.UPLOAD_DIR)
    temp_dir_path = Path(temp_dir)
    
    try:
        # Copy PDFs to temp directory with sequential names
        for idx, pdf_path in enumerate(pdf_paths, start=1):
            dest = temp_dir_path / f"page_{idx}.pdf"
            shutil.copy2(pdf_path, dest)
            logger.debug(f"Copied {pdf_path} -> {dest}")
        
        # Create ZIP archive
        zip_base = tempfile.mktemp(dir=settings.UPLOAD_DIR, prefix=f"{zip_prefix}_")
        zip_path = shutil.make_archive(
            base_name=zip_base,
            format='zip',
            root_dir=temp_dir_path
        )
        
        logger.info(f"Created ZIP archive: {zip_path} ({len(pdf_paths)} files)")
        return Path(zip_path)
        
    except Exception as e:
        logger.error(f"Failed to create ZIP: {e}")
        raise
        
    finally:
        # Clean up temp directory
        try:
            shutil.rmtree(temp_dir_path)
            logger.debug(f"Cleaned up temp directory: {temp_dir_path}")
        except Exception as e:
            logger.warning(f"Failed to remove temp directory {temp_dir_path}: {e}")


def create_zip_from_files(file_paths: List[Path], zip_prefix: str = "files") -> Path:

    temp_dir = tempfile.mkdtemp(dir=settings.UPLOAD_DIR)
    temp_dir_path = Path(temp_dir)
    
    try:
        # Copy files to temp directory with original names
        for file_path in file_paths:
            dest = temp_dir_path / file_path.name
            shutil.copy2(file_path, dest)
            logger.debug(f"Copied {file_path} -> {dest}")
        
        # Create ZIP archive
        zip_base = tempfile.mktemp(dir=settings.UPLOAD_DIR, prefix=f"{zip_prefix}_")
        zip_path = shutil.make_archive(
            base_name=zip_base,
            format='zip',
            root_dir=temp_dir_path
        )
        
        logger.info(f"Created ZIP archive: {zip_path} ({len(file_paths)} files)")
        return Path(zip_path)
        
    except Exception as e:
        logger.error(f"Failed to create ZIP: {e}")
        raise
        
    finally:
        # Clean up temp directory
        try:
            shutil.rmtree(temp_dir_path)
            logger.debug(f"Cleaned up temp directory: {temp_dir_path}")
        except Exception as e:
            logger.warning(f"Failed to remove temp directory {temp_dir_path}: {e}")