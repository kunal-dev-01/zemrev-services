"""
============================================================================
FILE: app/services/cropper.py
PURPOSE: Pure PyVIPS cropper (JPEG, PNG, WebP only)
============================================================================
"""

import pyvips
import logging
from app.models.schemas import CropRequest

logger = logging.getLogger(__name__)

class ImageCropper:
    """Pure PyVIPS cropper"""
    
    @staticmethod
    def crop(content: bytes, filename: str, options: CropRequest) -> tuple[bytes, str]:
        """Crop image"""
        
        try:
            ext = filename.rsplit(".", 1)[-1].lower()

            # Only web formats
            UNSUPPORTED = ["heif", "heic", "avif", "tiff"]
            if ext in UNSUPPORTED:
                raise ValueError("Cannot crop HEIF/HEIC/AVIF/TIFF. Convert to JPG/PNG/WebP first.")

            # Load
            if ext in ["jpeg", "jpg"]:
                img = pyvips.Image.new_from_buffer(content, "", access="sequential", shrink=2)
            else:
                img = pyvips.Image.new_from_buffer(content, "", access="sequential")
            
            # Validate bounds
            if options.x + options.width > img.width:
                raise ValueError(f"Crop exceeds width ({img.width}px)")
            
            if options.y + options.height > img.height:
                raise ValueError(f"Crop exceeds height ({img.height}px)")
            
            # Crop
            cropped = img.crop(options.x, options.y, options.width, options.height)
            
            # Output
            target_fmt = options.format.value if options.format else ImageCropper._detect_format(filename)
            
            if target_fmt in ["jpeg", "jpg"]:
                output = cropped.jpegsave_buffer(Q=85, strip=True, optimize_coding=True)
            
            elif target_fmt == "png":
                output = cropped.pngsave_buffer(compression=9, strip=True)
            
            elif target_fmt == "webp":
                output = cropped.webpsave_buffer(Q=85, strip=True)
            
            else:
                output = cropped.write_to_buffer(f".{target_fmt}")
            
            logger.info(f"Cropped {filename} to {options.width}x{options.height}")
            return output, filename
        
        except Exception as e:
            logger.error(f"Crop failed: {e}")
            raise ValueError(f"Crop error: {str(e)}")
    
    @staticmethod
    def _detect_format(filename: str) -> str:
        ext = filename.rsplit(".", 1)[-1].lower()
        return "jpeg" if ext == "jpg" else ext

cropper = ImageCropper()