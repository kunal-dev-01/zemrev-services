"""
============================================================================
FILE: app/services/optimizer.py
PURPOSE: Pure PyVIPS optimizer (JPEG, PNG, WebP only)
============================================================================
"""

import pyvips
import logging
from app.models.schemas import OptimizeRequest

logger = logging.getLogger(__name__)

class ImageOptimizer:
    """Pure PyVIPS optimizer"""
    
    @staticmethod
    def optimize(content: bytes, filename: str, options: OptimizeRequest) -> tuple[bytes, str]:
        """Optimize image (strip EXIF, fix orientation)"""
        
        try:
            fmt = ImageOptimizer._detect_format(filename)

            # Only web formats
            UNSUPPORTED = ["heif", "heic", "avif", "tiff"]
            if fmt in UNSUPPORTED:
                raise ValueError("Cannot optimize HEIF/HEIC/AVIF/TIFF. Convert to JPG/PNG/WebP first.")

            # Load
            if fmt in ["jpeg", "jpg"]:
                img = pyvips.Image.new_from_buffer(content, "", access="sequential", shrink=2)
            else:
                img = pyvips.Image.new_from_buffer(content, "", access="sequential")
            
            # Fix orientation
            if options.fix_orientation:
                img = ImageOptimizer._fix_orientation(img)
            
            # Save with stripping
            if fmt in ["jpeg", "jpg"]:
                output = img.jpegsave_buffer(Q=85, strip=options.strip_exif, optimize_coding=True)
            
            elif fmt == "png":
                output = img.pngsave_buffer(compression=9, strip=options.strip_exif)
            
            elif fmt == "webp":
                output = img.webpsave_buffer(Q=85, strip=options.strip_exif)
            
            else:
                output = img.write_to_buffer(f".{fmt}")
            
            reduction = (1 - len(output) / len(content)) * 100
            logger.info(f"Optimized {filename}: {reduction:.1f}% reduction")
            return output, filename
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            raise ValueError(f"Optimization error: {str(e)}")
    
    @staticmethod
    def _fix_orientation(img: pyvips.Image) -> pyvips.Image:
        try:
            orientation = img.get("orientation")
            
            if orientation == 3:
                img = img.rot180()
            elif orientation == 6:
                img = img.rot90()
            elif orientation == 8:
                img = img.rot270()
            
            img = img.copy()
            img.remove("orientation")
        except:
            pass
        
        return img
    
    @staticmethod
    def _detect_format(filename: str) -> str:
        ext = filename.rsplit(".", 1)[-1].lower()
        return "jpeg" if ext == "jpg" else ext

optimizer = ImageOptimizer()