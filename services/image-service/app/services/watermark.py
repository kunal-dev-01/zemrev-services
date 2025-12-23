"""
============================================================================
FILE: app/services/watermark.py
PURPOSE: Pure PyVIPS watermark (JPEG, PNG, WebP only)
============================================================================
"""

import pyvips
import logging
from app.models.schemas import TextWatermarkRequest, ImageWatermarkRequest, WatermarkPosition

logger = logging.getLogger(__name__)

class Watermarker:
    """Pure PyVIPS watermark tool"""
    
    @staticmethod
    def add_text_watermark(content: bytes, filename: str, options: TextWatermarkRequest) -> tuple[bytes, str]:
        """Add text watermark"""
        
        try:
            ext = filename.rsplit(".", 1)[-1].lower()

            # Only web formats
            UNSUPPORTED = ["heif", "heic", "avif", "tiff"]
            if ext in UNSUPPORTED:
                raise ValueError("Cannot watermark HEIF/HEIC/AVIF/TIFF. Convert to JPG/PNG/WebP first.")

            # Load
            if ext in ["jpeg", "jpg"]:
                img = pyvips.Image.new_from_buffer(content, "", access="sequential", shrink=2)
            else:
                img = pyvips.Image.new_from_buffer(content, "", access="sequential")

            # Create text
            text = pyvips.Image.text(
                options.text,
                font=f"sans {options.font_size}",
                dpi=96
            ).colourspace("srgb")

            # Apply color
            r, g, b = Watermarker._hex_to_rgb(options.color)
            text = (text * [r/255, g/255, b/255]).cast("uchar")

            # Alpha
            alpha = (text[0] * options.opacity).cast("uchar")
            text = text.bandjoin(alpha)

            # Position
            x, y = Watermarker._calculate_position(
                img.width, img.height, text.width, text.height, options.position
            )

            # Ensure base has alpha
            if img.bands < 4:
                img = img.bandjoin(255)

            # Composite
            result = img.composite(text, "over", x=x, y=y)

            # Save
            fmt = Watermarker._detect_format(filename)
            output = Watermarker._save_image(result, fmt)

            logger.info(f"Added text watermark to {filename}")
            return output, filename

        except Exception as e:
            logger.error(f"Text watermark failed: {e}")
            raise ValueError(f"Watermark error: {str(e)}")

    @staticmethod
    def add_image_watermark(
        content: bytes, watermark_content: bytes, filename: str, options: ImageWatermarkRequest
    ) -> tuple[bytes, str]:
        """Add image watermark"""
        
        try:
            ext = filename.rsplit(".", 1)[-1].lower()

            # Only web formats
            UNSUPPORTED = ["heif", "heic", "avif", "tiff"]
            if ext in UNSUPPORTED:
                raise ValueError("Cannot watermark HEIF/HEIC/AVIF/TIFF. Convert to JPG/PNG/WebP first.")

            # Load base
            if ext in ["jpeg", "jpg"]:
                img = pyvips.Image.new_from_buffer(content, "", access="sequential", shrink=2)
            else:
                img = pyvips.Image.new_from_buffer(content, "", access="sequential")

            # Load watermark
            logo = pyvips.Image.new_from_buffer(watermark_content, "", access="sequential")

            # Resize watermark
            target_width = int(img.width * options.scale)
            logo = logo.thumbnail_image(target_width, height=9999)

            # Apply opacity
            if logo.bands < 4:
                alpha = logo.bandjoin(255)[-1]
            else:
                alpha = logo[-1]

            alpha = (alpha * options.opacity).cast("uchar")
            logo = logo.extract_band(0, n=3).bandjoin(alpha)

            # Position
            x, y = Watermarker._calculate_position(
                img.width, img.height, logo.width, logo.height, options.position
            )

            # Ensure base has alpha
            if img.bands < 4:
                img = img.bandjoin(255)

            # Composite
            result = img.composite(logo, "over", x=x, y=y)

            # Save
            fmt = Watermarker._detect_format(filename)
            output = Watermarker._save_image(result, fmt)

            logger.info(f"Added image watermark to {filename}")
            return output, filename

        except Exception as e:
            logger.error(f"Image watermark failed: {e}")
            raise ValueError(f"Watermark error: {str(e)}")

    @staticmethod
    def _calculate_position(img_w: int, img_h: int, wm_w: int, wm_h: int, position: WatermarkPosition) -> tuple[int, int]:
        padding = 20
        
        if position == WatermarkPosition.TOP_LEFT:
            return padding, padding
        if position == WatermarkPosition.TOP_RIGHT:
            return img_w - wm_w - padding, padding
        if position == WatermarkPosition.BOTTOM_LEFT:
            return padding, img_h - wm_h - padding
        if position == WatermarkPosition.BOTTOM_RIGHT:
            return img_w - wm_w - padding, img_h - wm_h - padding
        if position == WatermarkPosition.CENTER:
            return (img_w - wm_w) // 2, (img_h - wm_h) // 2
        
        return padding, img_h - wm_h - padding

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    @staticmethod
    def _detect_format(filename: str) -> str:
        ext = filename.rsplit(".", 1)[-1].lower()
        return "jpeg" if ext == "jpg" else ext

    @staticmethod
    def _save_image(img: pyvips.Image, fmt: str) -> bytes:
        if fmt in ["jpeg", "jpg"]:
            return img.jpegsave_buffer(Q=85, strip=True)
        if fmt == "png":
            return img.pngsave_buffer(compression=9, strip=True)
        if fmt == "webp":
            return img.webpsave_buffer(Q=85, strip=True)
        return img.write_to_buffer(f".{fmt}")

watermarker = Watermarker()