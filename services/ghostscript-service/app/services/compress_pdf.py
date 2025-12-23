from pathlib import Path
from typing import Tuple
import subprocess

from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


# Ghostscript compression settings
GS_SETTINGS = {
    "screen": {
        "dpi": 72,
        "description": "Low quality, smallest size (for screen viewing)"
    },
    "ebook": {
        "dpi": 150,
        "description": "Medium quality (good for e-readers)"
    },
    "printer": {
        "dpi": 300,
        "description": "High quality (suitable for printing)"
    },
    "prepress": {
        "dpi": 300,
        "description": "Very high quality (color preserving for professional printing)"
    }
}


def compress_pdf_ghostscript(
    input_path: Path,
    output_path: Path,
    compression_level: str = "ebook"
) -> Tuple[float, float]:

    try:
        # Get original file size
        original_size = input_path.stat().st_size / 1024  # KB
        
        logger.info(
            f"Compressing PDF with Ghostscript: {original_size:.2f} KB, "
            f"level: {compression_level}"
        )
        
        # Build Ghostscript command
        gs_command = [
            "gs",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS=/{compression_level}",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            "-dDetectDuplicateImages=true",
            "-dCompressFonts=true",
            "-dCompressPages=true",
            "-dDownsampleColorImages=true",
            "-dDownsampleGrayImages=true",
            "-dDownsampleMonoImages=true",
            "-dAutoRotatePages=/None",
            f"-sOutputFile={output_path}",
            str(input_path)
        ]
        
        # Run Ghostscript
        result = subprocess.run(
            gs_command,
            capture_output=True,
            text=True,
            timeout=300 
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or "Unknown Ghostscript error"
            raise Exception(f"Ghostscript failed: {error_msg}")
        
        # Check if output file was created
        if not output_path.exists():
            raise Exception("Ghostscript did not create output file")
        
        # Get compressed file size
        compressed_size = output_path.stat().st_size / 1024  # KB
        
        reduction = ((original_size - compressed_size) / original_size) * 100 if original_size > 0 else 0
        
        logger.info(
            f"Successfully compressed PDF: "
            f"{original_size:.2f} KB → {compressed_size:.2f} KB "
            f"({reduction:.1f}% reduction)"
        )
        
        return original_size, compressed_size
        
    except subprocess.TimeoutExpired:
        logger.error("Ghostscript compression timed out")
        raise Exception("PDF compression timed out (file too large)")
    except Exception as e:
        logger.error(f"Failed to compress PDF with Ghostscript: {e}")
        raise Exception(f"PDF compression failed: {str(e)}")