from pathlib import Path
from typing import List, Dict, Any
import fitz 
from PIL import Image, ImageDraw, ImageFont, ImageColor
import io
from app.core.logging import get_logger

logger = get_logger(__name__)

def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex string to RGB tuple"""
    try:
        if hex_color.startswith('#'):
            return ImageColor.getrgb(hex_color)
        return (0, 0, 0)
    except:
        return (0, 0, 0)

def sign_pdf(
    input_path: Path,
    output_path: Path,
    signatures: List[Dict[str, Any]]
) -> None:

    try:
        doc = fitz.open(input_path)
        logger.info(f"Processing {len(signatures)} signatures for PDF with {len(doc)} pages")
        
        # ====================================================================
        # STEP 1: Expand page: -1 to actual page numbers
        # ====================================================================
        expanded_signatures = []
        for sig in signatures:
            page_num = sig.get('page', 0)
            
            # If page is -1, apply to ALL pages
            if page_num == -1:
                for page_idx in range(len(doc)):
                    sig_copy = sig.copy()
                    sig_copy['page'] = page_idx
                    expanded_signatures.append(sig_copy)
                logger.info(f"Expanded page: -1 to {len(doc)} pages")
            else:
                # Validate specific page exists
                if page_num >= len(doc):
                    doc.close()
                    raise ValueError(
                        f"Signature on page {page_num + 1} failed: PDF has only {len(doc)} pages"
                    )
                expanded_signatures.append(sig)
        
        # ====================================================================
        # STEP 2: Group signatures by page
        # ====================================================================
        signatures_by_page: Dict[int, List[Dict[str, Any]]] = {}
        for sig in expanded_signatures:
            page_num = sig.get('page', 0)
            if page_num not in signatures_by_page:
                signatures_by_page[page_num] = []
            signatures_by_page[page_num].append(sig)
        
        # ====================================================================
        # STEP 3: Process each page
        # ====================================================================
        for page_num, page_signatures in signatures_by_page.items():
            page = doc[page_num]
            page_rect = page.rect
            
            logger.info(f"Adding {len(page_signatures)} signatures to page {page_num + 1}")
            
            for sig in page_signatures:
                x = sig.get('x', 50)
                y = sig.get('y', 50)
                width = sig.get('width', 200)
                height = sig.get('height', 80)
                rotation = sig.get('rotation', 0)
                sig_type = sig.get('type', 'text')
                color_hex = sig.get('color', '#000000')
                opacity = float(sig.get('opacity', 1.0))
                rgb_color = hex_to_rgb(color_hex)
                
                # To store the final PIL Image before saving
                final_pil_image = None

                # =========================================================
                # 1. PROCESS IMAGE (PNG/JPEG ONLY)
                # =========================================================
                if sig_type == 'image' and 'image_path' in sig:
                    image_path = sig['image_path']
                    logger.info(f"Processing image: {image_path}")
                    
                    try:
                        # Only support PNG/JPEG
                        if str(image_path).lower().endswith(('.png', '.jpg', '.jpeg')):
                            img = Image.open(image_path)
                            
                            # Scaling logic
                            if img.width <= width and img.height <= height:
                                width = img.width
                                height = img.height
                            else:
                                aspect = img.width / img.height
                                target_aspect = width / height
                                if aspect > target_aspect:
                                    new_width = width
                                    new_height = int(width / aspect)
                                else:
                                    new_height = height
                                    new_width = int(height * aspect)
                                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                                width = new_width
                                height = new_height
                            
                            if img.mode != 'RGBA':
                                img = img.convert('RGBA')
                            
                            # Apply opacity
                            if opacity < 1.0:
                                alpha = img.split()[3]
                                alpha = alpha.point(lambda p: int(p * opacity))
                                img.putalpha(alpha)
                                
                            final_pil_image = img
                        
                        else:
                            logger.warning(f"Unsupported image format: {image_path}. Only PNG/JPEG supported.")
                            continue
                            
                    except Exception as img_err:
                        logger.error(f"Error processing image: {img_err}")
                        continue

                # =========================================================
                # 2. GENERATE TEXT SIGNATURE
                # =========================================================
                else:
                    text = sig.get('text', 'Signature')
                    font_name = sig.get('font', 'Dancing Script')
                    
                    scale = 2
                    canvas_width = int(width * scale)
                    canvas_height = int(height * scale)
                    
                    sig_img = Image.new('RGBA', (canvas_width, canvas_height), (255, 255, 255, 0))
                    draw = ImageDraw.Draw(sig_img)
                    
                    font_paths = {
                        'Dancing Script': 'app/fonts/DancingScript-Bold.ttf',
                        'Great Vibes': 'app/fonts/GreatVibes-Regular.ttf',
                        'Sacramento': 'app/fonts/Sacramento-Regular.ttf',
                        'Allura': 'app/fonts/Allura-Regular.ttf',
                        'Homemade Apple': 'app/fonts/HomemadeApple-Regular.ttf',
                        'Caveat': 'app/fonts/Caveat-VariableFont_wght.ttf', 
                        'Reenie Beanie': 'app/fonts/ReenieBeanie-Regular.ttf',
                        'Bebas Neue': 'app/fonts/BebasNeue-Regular.ttf',
                        'Oswald': 'app/fonts/Oswald-VariableFont_wght.ttf',
                        'Righteous': 'app/fonts/Righteous-Regular.ttf',
                        'Anton': 'app/fonts/Anton-Regular.ttf',
                        'Permanent Marker': 'app/fonts/PermanentMarker-Regular.ttf',
                        'Roboto Condensed': 'app/fonts/RobotoCondensed-VariableFont_wght.ttf',
                        'Russo One': 'app/fonts/RussoOne-Regular.ttf',
                        'Arial': '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                    }
                    
                    font_path = font_paths.get(font_name, font_paths['Dancing Script'])
                    target_font_size = min(int(canvas_height * 0.7), 160)
                    
                    try:
                        font = ImageFont.truetype(font_path, target_font_size)
                    except:
                        font = ImageFont.load_default()
                    
                    text_fill = (rgb_color[0], rgb_color[1], rgb_color[2], int(255 * opacity))
                    
                    try:
                        bbox = draw.textbbox((0, 0), text, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                    except:
                        text_width, text_height = draw.textsize(text, font=font)
                    
                    text_x = (canvas_width - text_width) // 2
                    text_y = (canvas_height - text_height) // 2
                    
                    draw.text((text_x, text_y), text, fill=text_fill, font=font)
                    
                    final_pil_image = sig_img.resize((width, height), Image.Resampling.LANCZOS)

                # =========================================================
                # 3. APPLY ROTATION
                # =========================================================
                if final_pil_image and rotation != 0:
                    cx = x + (width / 2)
                    cy = y + (height / 2)
                    
                    final_pil_image = final_pil_image.rotate(-rotation, expand=True, resample=Image.BICUBIC)
                    
                    width = final_pil_image.width
                    height = final_pil_image.height
                    
                    x = cx - (width / 2)
                    y = cy - (height / 2)

                # =========================================================
                # 4. SAVE AND INSERT
                # =========================================================
                if final_pil_image:
                    img_bytes_io = io.BytesIO()
                    final_pil_image.save(
                        img_bytes_io, 
                        format='PNG',
                        compress_level=0,
                        optimize=False
                    )
                    img_bytes_io.seek(0)
                    png_data = img_bytes_io.getvalue()
                    
                    sig_rect = fitz.Rect(x, y, x + width, y + height)
                    
                    # Bounds check - clamp to page if needed
                    if sig_rect.x0 < page_rect.x0: x = page_rect.x0
                    if sig_rect.y0 < page_rect.y0: y = page_rect.y0
                    if sig_rect.x1 > page_rect.x1: x = page_rect.x1 - width
                    if sig_rect.y1 > page_rect.y1: y = page_rect.y1 - height
                    sig_rect = fitz.Rect(x, y, x + width, y + height)

                    page.insert_image(
                        sig_rect,
                        stream=png_data,
                        keep_proportion=False,
                        overlay=True,
                        oc=0
                    )
        
        # Save PDF
        doc.save(
            output_path,
            garbage=4,
            deflate=True,
            clean=True,
            pretty=True
        )
        doc.close()
        
        logger.info(f"Successfully signed PDF -> {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to sign PDF: {e}")
        if 'doc' in locals():
            doc.close()
        raise Exception(f"PDF signing failed: {str(e)}")