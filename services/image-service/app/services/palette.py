"""
============================================================================
FILE: app/services/palette.py
PURPOSE: Pure PyVIPS color palette extractor
============================================================================
"""

import pyvips
import logging
from typing import Dict, List, Any
from collections import Counter

logger = logging.getLogger(__name__)

class ColorPaletteGenerator:
    """Pure PyVIPS dominant color palette extractor"""
    
    @staticmethod
    def extract_palette(content: bytes, filename: str, num_colors: int = 5) -> tuple[Dict[str, Any], bytes, str]:
        """
        Extract dominant color palette from image
        
        Returns:
            tuple: (palette_data_dict, preview_image_bytes, preview_filename)
        """
        
        try:
            ext = filename.rsplit(".", 1)[-1].lower()
            
            # Load image with sequential access for memory efficiency
            if ext in ["jpeg", "jpg"]:
                img = pyvips.Image.new_from_buffer(content, "", access="sequential", shrink=2)
            else:
                img = pyvips.Image.new_from_buffer(content, "", access="sequential")
            
            # Ensure RGB
            if img.interpretation != "srgb":
                img = img.colourspace("srgb")
            
            # Remove alpha if present
            if img.bands == 4:
                img = img.flatten(background=[255, 255, 255])
            
            # Resize FIRST (while still sequential for speed)
            scale = 1.0
            target_size = 200
            if img.width > target_size or img.height > target_size:
                scale = min(target_size / img.width, target_size / img.height)
                img = img.resize(scale, kernel="nearest")
            
            # Apply median filter
            if img.width > 50 and img.height > 50:
                img = img.median(3)
            
            # Convert to memory for random access using copy_memory()
            img = img.copy_memory()
            
            # Validate num_colors
            num_colors = max(3, min(10, num_colors))
            
            # Extract dominant colors
            palette_colors = ColorPaletteGenerator._extract_dominant_colors(img, num_colors)
            
            # Generate preview image
            preview_bytes, preview_filename = ColorPaletteGenerator._generate_preview(
                palette_colors, filename
            )
            
            # Prepare response data
            palette_data = {
                "total_colors": num_colors,
                "palette": palette_colors,
                "preview_available": True
            }
            
            logger.info(f"Extracted {num_colors} colors from {filename}")
            
            return palette_data, preview_bytes, preview_filename
            
        except Exception as e:
            logger.error(f"Palette extraction failed: {e}")
            raise ValueError(f"Palette error: {str(e)}")
    
    @staticmethod
    def _extract_dominant_colors(img: pyvips.Image, num_colors: int) -> List[Dict[str, Any]]:
        """
        Extract dominant colors using simple sampling and clustering
        
        Returns:
            list: [{"hex": "#RRGGBB", "rgb": [r, g, b], "percentage": 0.0}, ...]
        """
        
        # Image is already resized and in memory from extract_palette()
        # Get image dimensions
        width = img.width
        height = img.height
        
        # Sample colors from grid
        step = max(1, min(width, height) // 20)
        color_samples = []
        
        for y in range(0, height, step):
            for x in range(0, width, step):
                try:
                    pixel = img.getpoint(x, y)
                    if len(pixel) >= 3:
                        r = int(pixel[0])
                        g = int(pixel[1])
                        b = int(pixel[2])
                        color_samples.append((r, g, b))
                except:
                    continue
        
        if not color_samples:
            # Fallback to basic colors
            return ColorPaletteGenerator._get_fallback_palette(num_colors)
        
        # Cluster colors into bins (32x32x32 = 32768 possible bins)
        bin_size = 32
        color_bins = {}
        
        for r, g, b in color_samples:
            # Create bin key
            bin_r = (r // bin_size) * bin_size + bin_size // 2
            bin_g = (g // bin_size) * bin_size + bin_size // 2
            bin_b = (b // bin_size) * bin_size + bin_size // 2
            
            # Clamp to valid range
            bin_r = max(0, min(255, bin_r))
            bin_g = max(0, min(255, bin_g))
            bin_b = max(0, min(255, bin_b))
            
            bin_key = (bin_r, bin_g, bin_b)
            
            if bin_key not in color_bins:
                color_bins[bin_key] = 0
            color_bins[bin_key] += 1
        
        # Get top N colors by frequency
        sorted_colors = sorted(color_bins.items(), key=lambda x: x[1], reverse=True)
        top_colors = sorted_colors[:num_colors]
        
        # Calculate percentages
        total_count = sum(count for _, count in top_colors)
        
        results = []
        for (r, g, b), count in top_colors:
            percentage = (count / total_count) * 100.0
            hex_color = ColorPaletteGenerator._rgb_to_hex(r, g, b)
            
            results.append({
                "hex": hex_color,
                "rgb": [r, g, b],
                "percentage": round(percentage, 1)
            })
        
        return results
    
    @staticmethod
    def _get_fallback_palette(num_colors: int) -> List[Dict[str, Any]]:
        """Fallback palette if extraction fails"""
        
        fallback_colors = [
            (128, 128, 128),  # Gray
            (255, 0, 0),      # Red
            (0, 255, 0),      # Green
            (0, 0, 255),      # Blue
            (255, 255, 0),    # Yellow
            (255, 0, 255),    # Magenta
            (0, 255, 255),    # Cyan
            (255, 128, 0),    # Orange
            (128, 0, 255),    # Purple
            (0, 128, 128),    # Teal
        ]
        
        percentage = 100.0 / num_colors
        results = []
        
        for i in range(num_colors):
            r, g, b = fallback_colors[i % len(fallback_colors)]
            hex_color = ColorPaletteGenerator._rgb_to_hex(r, g, b)
            
            results.append({
                "hex": hex_color,
                "rgb": [r, g, b],
                "percentage": round(percentage, 1)
            })
        
        return results
    
    @staticmethod
    def _generate_preview(palette_data: List[Dict[str, Any]], filename: str) -> tuple[bytes, str]:
        """
        Generate palette preview image (horizontal color bars)
        
        Returns:
            tuple: (preview_bytes, preview_filename)
        """
        
        preview_width = 800
        preview_height = 200
        
        # Create color bands
        bands = []
        
        for color_info in palette_data:
            r, g, b = color_info["rgb"]
            percentage = color_info["percentage"]
            
            # Calculate band width
            band_width = int((percentage / 100.0) * preview_width)
            
            if band_width > 0:
                # Create solid color rectangle
                band = pyvips.Image.black(band_width, preview_height)
                band = band.new_from_image([r, g, b])
                bands.append(band)
        
        # Join all bands horizontally
        if bands:
            preview_img = bands[0]
            for band in bands[1:]:
                preview_img = preview_img.join(band, "horizontal")
        else:
            # Fallback - gray image
            preview_img = pyvips.Image.black(preview_width, preview_height)
            preview_img = preview_img.new_from_image([128, 128, 128])
        
        # Ensure correct size
        if preview_img.width < preview_width:
            # Add filler with last color
            remaining = preview_width - preview_img.width
            if palette_data:
                r, g, b = palette_data[-1]["rgb"]
            else:
                r, g, b = 128, 128, 128
            
            filler = pyvips.Image.black(remaining, preview_height)
            filler = filler.new_from_image([r, g, b])
            preview_img = preview_img.join(filler, "horizontal")
        elif preview_img.width > preview_width:
            # Crop if too wide
            preview_img = preview_img.crop(0, 0, preview_width, preview_height)
        
        # Save as PNG
        preview_bytes = preview_img.pngsave_buffer(compression=6)
        
        base = filename.rsplit(".", 1)[0]
        preview_filename = f"{base}_palette_preview.png"
        
        return preview_bytes, preview_filename
    
    @staticmethod
    def _rgb_to_hex(r: int, g: int, b: int) -> str:
        """Convert RGB to hex color"""
        return f"#{r:02X}{g:02X}{b:02X}"

color_palette_generator = ColorPaletteGenerator()