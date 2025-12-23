"""
============================================================================
FILE: app/api/controllers/image_controller.py
PURPOSE: Business logic for all image operations
============================================================================
"""

from fastapi import UploadFile
from fastapi.responses import Response
import logging

from app.models.schemas import (
    ConvertRequest,
    CompressRequest,
    ResizeRequest,
    OptimizeRequest,
    CropRequest,
    TextWatermarkRequest,
    ImageWatermarkRequest,
    MetadataRequest,
    PaletteRequest,
)

from app.services.validator import validator
from app.services.converter import converter
from app.services.compressor import compressor
from app.services.resizer import resizer
from app.services.optimizer import optimizer
from app.services.cropper import cropper
from app.services.watermark import watermarker
from app.services.metadata import metadata_extractor
from app.services.palette import color_palette_generator

logger = logging.getLogger(__name__)


class ImageController:
    """Controller for image operations (FILE ONLY MODE)"""

    # ============================================================
    # CONVERT
    # ============================================================

    @staticmethod
    async def convert_image(file: UploadFile, options: ConvertRequest):
        content = await validator.validate_file(file)
        filename = file.filename

        output, new_filename = converter.convert(content, filename, options)

        return ImageController._single_response(
            output, new_filename, f"image/{options.format.value}"
        )

    # ============================================================
    # COMPRESS
    # ============================================================

    @staticmethod
    async def compress_image(file: UploadFile, options: CompressRequest):
        content = await validator.validate_file(file)
        filename = file.filename

        output, new_filename = compressor.compress(content, filename, options)
        ext = new_filename.split(".")[-1]

        return ImageController._single_response(output, new_filename, f"image/{ext}")

    # ============================================================
    # RESIZE
    # ============================================================

    @staticmethod
    async def resize_image(file: UploadFile, options: ResizeRequest):
        content = await validator.validate_file(file)
        filename = file.filename

        output, new_filename, _ = resizer.resize(content, filename, options)
        ext = new_filename.split(".")[-1]

        return ImageController._single_response(output, new_filename, f"image/{ext}")

    # ============================================================
    # OPTIMIZE
    # ============================================================

    @staticmethod
    async def optimize_image(file: UploadFile, options: OptimizeRequest):
        content = await validator.validate_file(file)
        filename = file.filename

        output, new_filename = optimizer.optimize(content, filename, options)
        ext = new_filename.split(".")[-1]

        return ImageController._single_response(output, new_filename, f"image/{ext}")

    # ============================================================
    # CROP
    # ============================================================

    @staticmethod
    async def crop_image(file: UploadFile, options: CropRequest):
        content = await validator.validate_file(file)
        filename = file.filename

        output, new_filename = cropper.crop(content, filename, options)
        ext = new_filename.split(".")[-1]

        return ImageController._single_response(output, new_filename, f"image/{ext}")

    # ============================================================
    # TEXT WATERMARK
    # ============================================================

    @staticmethod
    async def add_text_watermark(file: UploadFile, options: TextWatermarkRequest):
        content = await validator.validate_file(file)
        filename = file.filename

        output, new_filename = watermarker.add_text_watermark(content, filename, options)
        ext = new_filename.split(".")[-1]

        return ImageController._single_response(output, new_filename, f"image/{ext}")

    # ============================================================
    # IMAGE WATERMARK
    # ============================================================

    @staticmethod
    async def add_image_watermark(file: UploadFile, watermark: UploadFile, options: ImageWatermarkRequest):
        content = await validator.validate_file(file)
        mark_bytes = await validator.validate_file(watermark)

        filename = file.filename

        output, new_filename = watermarker.add_image_watermark(
            content, mark_bytes, filename, options
        )

        ext = new_filename.split(".")[-1]
        return ImageController._single_response(output, new_filename, f"image/{ext}")

    # ============================================================
    # METADATA
    # ============================================================

    @staticmethod
    async def extract_metadata(file: UploadFile):
        content = await validator.validate_file(file)
        filename = file.filename

        metadata = metadata_extractor.extract_metadata(content, filename)
        from fastapi.responses import JSONResponse

        return JSONResponse(
            content={
                "success": True,
                "filename": filename,
                "metadata": metadata
            }
        )

    # ============================================================
    # PALETTE
    # ============================================================

    @staticmethod
    async def extract_palette(file: UploadFile, options: PaletteRequest):
        content = await validator.validate_file(file)
        filename = file.filename

        palette_data, preview_bytes, preview_filename = color_palette_generator.extract_palette(
            content, filename, options.num_colors
        )

        import base64
        preview_base64 = base64.b64encode(preview_bytes).decode("utf-8")

        from fastapi.responses import JSONResponse

        return JSONResponse(
            content={
                "success": True,
                "filename": filename,
                "palette": palette_data["palette"],
                "total_colors": palette_data["total_colors"],
                "preview_image": {
                    "filename": preview_filename,
                    "data": f"data:image/png;base64,{preview_base64}",
                    "size": len(preview_bytes)
                }
            }
        )

    # ============================================================
    # HELPER
    # ============================================================

    @staticmethod
    def _single_response(data: bytes, filename: str, media_type: str) -> Response:
        return Response(
            content=data,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )


image_controller = ImageController()
