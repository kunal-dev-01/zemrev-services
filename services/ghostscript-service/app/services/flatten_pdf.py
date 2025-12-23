from pathlib import Path
import subprocess
from app.core.logging import get_logger

logger = get_logger(__name__)


def flatten_pdf_ghostscript(input_path: Path, output_path: Path) -> None:
    try:
        logger.info(f"Flattening PDF with Ghostscript: {input_path.name}")
        
        # Build Ghostscript command
        gs_command = [
            "gs",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.3", 
            "-dPDFSETTINGS=/prepress",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            "-dNoOutputFonts",         
            "-dAutoRotatePages=/None",
            "-dPreserveAnnots=false",  
            "-dFlattenTransparency=true",
            "-dHaveTransparency=false",
            "-dDetectDuplicateImages=true",
            "-sColorConversionStrategy=RGB",
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
        
        # Log success with file size comparison
        original_size = input_path.stat().st_size / 1024
        flattened_size = output_path.stat().st_size / 1024
        
        logger.info(
            f"Successfully flattened PDF: "
            f"{original_size:.2f} KB → {flattened_size:.2f} KB"
        )
        
    except subprocess.TimeoutExpired:
        logger.error("Ghostscript flattening timed out")
        raise Exception("PDF flattening timed out (file too large)")
    except Exception as e:
        logger.error(f"Failed to flatten PDF: {e}")
        raise Exception(f"PDF flattening failed: {str(e)}")