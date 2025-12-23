"""
============================================================================
FILE: app/services/compressor.py
PURPOSE: Pure PyVIPS compressor (JPEG, PNG, WebP only)
============================================================================
"""

import pyvips
import logging
from app.models.schemas import CompressRequest

logger = logging.getLogger(__name__)

class ImageCompressor:
    """Pure PyVIPS compressor"""
    
    @staticmethod
    def compress(content: bytes, filename: str, options: CompressRequest) -> tuple[bytes, str]:
        """Compress image"""
        
        try:
            ext = filename.rsplit(".", 1)[-1].lower()
            
            # Load image
            if ext in ["jpeg", "jpg"]:
                img = pyvips.Image.new_from_buffer(content, "", access="sequential", shrink=2)
            else:
                img = pyvips.Image.new_from_buffer(content, "", access="sequential")
            
            current_fmt = ImageCompressor._detect_format(filename)
            target_fmt = options.format.value if options.format else current_fmt
            quality = options.quality

            # Only allow web-friendly formats for compression
            UNSUPPORTED = ["heif", "heic", "avif", "tiff"]
            if target_fmt in UNSUPPORTED:
                raise ValueError("Cannot compress HEIF/HEIC/AVIF/TIFF. Convert to JPG/PNG/WebP first.")

            # Compress
            if target_fmt in ["jpeg", "jpg"]:
                output = img.jpegsave_buffer(Q=quality, strip=True, optimize_coding=True)
            
            elif target_fmt == "png":
                output = img.pngsave_buffer(compression=9, strip=True)
            
            elif target_fmt == "webp":
                output = img.webpsave_buffer(Q=quality, lossless=False, effort=4, strip=True)
            
            else:
                raise ValueError(f"Unsupported compression format: {target_fmt}")
            
            compression_ratio = (1 - len(output) / len(content)) * 100
            logger.info(f"Compressed {filename}: {compression_ratio:.1f}% reduction")
            
            return output, filename
        
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            raise ValueError(f"Compression error: {str(e)}")
    
    @staticmethod
    def _detect_format(filename: str) -> str:
        ext = filename.rsplit(".", 1)[-1].lower()
        return "jpeg" if ext == "jpg" else ext

compressor = ImageCompressor()