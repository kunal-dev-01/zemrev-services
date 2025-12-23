"""
============================================================================
FILE: app/services/resizer.py
PURPOSE: Pure PyVIPS resizer (JPEG, PNG, WebP only for editing)
============================================================================
"""

import pyvips
import logging
from app.models.schemas import ResizeRequest, ResizeMode

logger = logging.getLogger(__name__)

class ImageResizer:
    """Pure PyVIPS resizer"""
    
    @staticmethod
    def resize(content: bytes, filename: str, options: ResizeRequest) -> tuple[bytes, str, tuple[int, int]]:
        """Resize image"""
        
        try:
            ext = filename.rsplit(".", 1)[-1].lower()

            # Only web formats can be edited
            UNSUPPORTED = ["heif", "heic", "avif", "tiff"]
            if ext in UNSUPPORTED:
                raise ValueError("Cannot resize HEIF/HEIC/AVIF/TIFF. Convert to JPG/PNG/WebP first.")

            # Load
            if ext in ["jpeg", "jpg"]:
                img = pyvips.Image.new_from_buffer(content, "", access="sequential", shrink=2)
            else:
                img = pyvips.Image.new_from_buffer(content, "", access="sequential")
            
            target_width, target_height = ImageResizer._calculate_dimensions(
                img.width, img.height, options
            )
            
            # Resize by mode
            if options.mode == ResizeMode.CONTAIN:
                resized = img.thumbnail_image(target_width, height=target_height, size=pyvips.Size.DOWN)
            
            elif options.mode == ResizeMode.COVER:
                resized = img.thumbnail_image(
                    target_width, height=target_height,
                    size=pyvips.Size.BOTH, crop=pyvips.Interesting.ATTENTION
                )
            
            elif options.mode in [ResizeMode.STRETCH, ResizeMode.EXACT]:
                scale_w = target_width / img.width
                scale_h = target_height / img.height
                resized = img.resize(scale_w, vscale=scale_h)
            
            else:
                raise ValueError(f"Unknown mode: {options.mode}")
            
            # Output format
            target_fmt = options.format.value if options.format else ImageResizer._detect_format(filename)
            
            # Save
            if target_fmt in ["jpeg", "jpg"]:
                output = resized.jpegsave_buffer(Q=85, strip=True, optimize_coding=True)
            
            elif target_fmt == "png":
                output = resized.pngsave_buffer(compression=9, strip=True)
            
            elif target_fmt == "webp":
                output = resized.webpsave_buffer(Q=85, strip=True)
            
            else:
                output = resized.write_to_buffer(f".{target_fmt}")
            
            logger.info(f"Resized {filename} to {resized.width}x{resized.height}")
            return output, filename, (resized.width, resized.height)
        
        except Exception as e:
            logger.error(f"Resize failed: {e}")
            raise ValueError(f"Resize error: {str(e)}")
    
    @staticmethod
    def _calculate_dimensions(orig_w: int, orig_h: int, options: ResizeRequest) -> tuple[int, int]:
        if options.width and options.height:
            return options.width, options.height
        elif options.width:
            scale = options.width / orig_w
            return options.width, int(orig_h * scale)
        elif options.height:
            scale = options.height / orig_h
            return int(orig_w * scale), options.height
        else:
            raise ValueError("Width or height required")
    
    @staticmethod
    def _detect_format(filename: str) -> str:
        ext = filename.rsplit(".", 1)[-1].lower()
        return "jpeg" if ext == "jpg" else ext

resizer = ImageResizer()