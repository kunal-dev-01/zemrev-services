from pathlib import Path
import subprocess
from app.core.logging import get_logger

logger = get_logger(__name__)


def convert_to_pdfa(
    input_path: Path,
    output_path: Path,
    version: str = "2b"
) -> None:

    try:
        original_size = input_path.stat().st_size / 1024
        
        logger.info(f"Converting to PDF/A-{version}: {original_size:.2f} KB")
        
        # Map version to PDFA level
        pdfa_level_map = {
            "1b": "1",
            "2b": "2",
            "3b": "3"
        }
        pdfa_level = pdfa_level_map.get(version, "2")
        
        # Build Ghostscript command for PDF/A conversion
        gs_command = [
            "gs",
            f"-dPDFA={pdfa_level}",
            "-dBATCH",
            "-dNOPAUSE",
            "-dQUIET",
            "-dUseCIEColor",
            "-sProcessColorModel=DeviceRGB",
            "-sDEVICE=pdfwrite",
            "-dPDFACompatibilityPolicy=1",
            f"-sOutputFile={output_path}",
            str(input_path)
        ]
        
        logger.info(f"Running Ghostscript: {' '.join(gs_command)}")
        
        result = subprocess.run(
            gs_command,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or "Unknown Ghostscript error"
            logger.error(f"Ghostscript error: {error_msg}")
            raise Exception(f"Ghostscript failed: {error_msg}")
        
        if not output_path.exists():
            raise Exception("Ghostscript did not create output file")
        
        converted_size = output_path.stat().st_size / 1024
        
        logger.info(
            f"Successfully converted to PDF/A-{version}: "
            f"{original_size:.2f} KB → {converted_size:.2f} KB"
        )
        
    except subprocess.TimeoutExpired:
        logger.error("PDF/A conversion timed out (300s)")
        raise Exception("PDF/A conversion timed out")
    except Exception as e:
        logger.error(f"Failed to convert to PDF/A: {e}")
        raise Exception(f"PDF/A conversion failed: {str(e)}")