"""
============================================================================
FILE: app/api/routes/image_routes.py
PURPOSE: FastAPI route definitions
============================================================================
"""

from fastapi import APIRouter, UploadFile, File, Form, Response
from app.api.controllers.image_controller import image_controller

from app.models.schemas import (
    OutputFormat,
    ResizeMode,
    ConvertRequest,
    CompressRequest,
    ResizeRequest,
    OptimizeRequest,
    CropRequest,
    TextWatermarkRequest,
    ImageWatermarkRequest,
    PaletteRequest,
)

router = APIRouter(prefix="/api/v1/image", tags=["Image Tools"])


# ============================================================
# CONVERT
# ============================================================

@router.post("/convert", response_class=Response)
async def convert(
    file: UploadFile = File(...),
    format: OutputFormat = Form(OutputFormat.WEBP),
    quality: int = Form(75),
    strip_metadata: bool = Form(True),
):
    options = ConvertRequest(format=format, quality=quality, strip_metadata=strip_metadata)
    return await image_controller.convert_image(file, options)


# ============================================================
# COMPRESS
# ============================================================

@router.post("/compress", response_class=Response)
async def compress(
    file: UploadFile = File(...),
    quality: int = Form(75),
    format: OutputFormat = Form(None),
):
    options = CompressRequest(quality=quality, format=format)
    return await image_controller.compress_image(file, options)


# ============================================================
# RESIZE
# ============================================================

@router.post("/resize", response_class=Response)
async def resize(
    file: UploadFile = File(...),
    width: int = Form(None),
    height: int = Form(None),
    mode: ResizeMode = Form(ResizeMode.CONTAIN),
    format: OutputFormat = Form(None),
):
    options = ResizeRequest(
        width=width,
        height=height,
        mode=mode,
        format=format
    )
    return await image_controller.resize_image(file, options)


# ============================================================
# OPTIMIZE
# ============================================================

@router.post("/optimize", response_class=Response)
async def optimize(
    file: UploadFile = File(...),
    strip_exif: bool = Form(True),
    strip_gps: bool = Form(True),
    fix_orientation: bool = Form(True),
):
    options = OptimizeRequest(
        strip_exif=strip_exif,
        strip_gps=strip_gps,
        fix_orientation=fix_orientation,
    )
    return await image_controller.optimize_image(file, options)


# ============================================================
# CROP
# ============================================================

@router.post("/crop", response_class=Response)
async def crop(
    file: UploadFile = File(...),
    x: int = Form(...),
    y: int = Form(...),
    width: int = Form(...),
    height: int = Form(...),
    format: OutputFormat = Form(None),
):
    options = CropRequest(x=x, y=y, width=width, height=height, format=format)
    return await image_controller.crop_image(file, options)


# ============================================================
# TEXT WATERMARK
# ============================================================

@router.post("/watermark/text", response_class=Response)
async def watermark_text(
    file: UploadFile = File(...),
    text: str = Form(...),
    font_size: int = Form(48),
    color: str = Form("#FFFFFF"),
    opacity: float = Form(0.5),
    position: str = Form("bottom-right"),
):
    options = TextWatermarkRequest(
        text=text,
        font_size=font_size,
        color=color,
        opacity=opacity,
        position=position,
    )
    return await image_controller.add_text_watermark(file, options)


# ============================================================
# IMAGE WATERMARK
# ============================================================

@router.post("/watermark/image", response_class=Response)
async def watermark_image(
    file: UploadFile = File(...),
    watermark: UploadFile = File(...),
    scale: float = Form(0.2),
    opacity: float = Form(0.5),
    position: str = Form("bottom-right"),
):
    options = ImageWatermarkRequest(
        scale=scale,
        opacity=opacity,
        position=position,
    )
    return await image_controller.add_image_watermark(file, watermark, options)


# ============================================================
# METADATA
# ============================================================

@router.post("/metadata")
async def extract_metadata(file: UploadFile = File(...)):
    return await image_controller.extract_metadata(file)


# ============================================================
# PALETTE
# ============================================================

@router.post("/palette")
async def palette(
    file: UploadFile = File(...),
    num_colors: int = Form(5),
):
    options = PaletteRequest(num_colors=num_colors)
    return await image_controller.extract_palette(file, options)
