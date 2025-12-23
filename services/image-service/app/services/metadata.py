"""
============================================================================
FILE: app/services/metadata.py
PURPOSE: Pure PyVIPS image metadata extractor
============================================================================
"""

import pyvips
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MetadataExtractor:
    """Pure PyVIPS metadata extractor"""
    
    @staticmethod
    def extract_metadata(content: bytes, filename: str) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from image
        
        Returns:
            dict: Complete metadata including EXIF, file info, image properties
        """
        
        try:
            # Load image
            img = pyvips.Image.new_from_buffer(content, "")
            
            # Extract all metadata
            metadata = {
                "file": MetadataExtractor._get_file_info(content, filename),
                "image": MetadataExtractor._get_image_properties(img),
                "exif": MetadataExtractor._get_exif_data(img),
                "technical": MetadataExtractor._get_technical_info(img),
                "color": MetadataExtractor._get_color_info(img)
            }
            
            logger.info(f"Extracted metadata from {filename}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            raise ValueError(f"Metadata error: {str(e)}")
    
    @staticmethod
    def _get_file_info(content: bytes, filename: str) -> Dict[str, Any]:
        """Extract file-level information"""
        
        file_size = len(content)
        
        # Detect format from magic bytes
        format_info = MetadataExtractor._detect_format(content)
        
        return {
            "filename": filename,
            "size_bytes": file_size,
            "size_kb": round(file_size / 1024, 2),
            "size_mb": round(file_size / (1024 * 1024), 2),
            "format": format_info["format"],
            "mime_type": format_info["mime_type"],
            "extension": filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"
        }
    
    @staticmethod
    def _detect_format(content: bytes) -> Dict[str, str]:
        """Detect image format from magic bytes"""
        
        if content.startswith(b'\xFF\xD8\xFF'):
            return {"format": "JPEG", "mime_type": "image/jpeg"}
        elif content.startswith(b'\x89PNG\r\n\x1a\n'):
            return {"format": "PNG", "mime_type": "image/png"}
        elif content.startswith(b'RIFF') and content[8:12] == b'WEBP':
            return {"format": "WebP", "mime_type": "image/webp"}
        elif content[4:8] == b'ftyp':
            # HEIF/HEIC/AVIF
            if b'heic' in content[8:20] or b'heix' in content[8:20]:
                return {"format": "HEIC", "mime_type": "image/heic"}
            elif b'avif' in content[8:20] or b'avis' in content[8:20]:
                return {"format": "AVIF", "mime_type": "image/avif"}
            else:
                return {"format": "HEIF", "mime_type": "image/heif"}
        elif content.startswith(b'II*\x00') or content.startswith(b'MM\x00*'):
            return {"format": "TIFF", "mime_type": "image/tiff"}
        elif content.startswith(b'GIF87a') or content.startswith(b'GIF89a'):
            return {"format": "GIF", "mime_type": "image/gif"}
        elif content.startswith(b'BM'):
            return {"format": "BMP", "mime_type": "image/bmp"}
        else:
            return {"format": "Unknown", "mime_type": "application/octet-stream"}
    
    @staticmethod
    def _get_image_properties(img: pyvips.Image) -> Dict[str, Any]:
        """Extract basic image properties"""
        
        # Calculate aspect ratio
        gcd_val = MetadataExtractor._gcd(img.width, img.height)
        aspect_w = img.width // gcd_val
        aspect_h = img.height // gcd_val
        
        # Determine orientation
        if img.width > img.height:
            orientation = "landscape"
        elif img.height > img.width:
            orientation = "portrait"
        else:
            orientation = "square"
        
        # Calculate megapixels
        megapixels = round((img.width * img.height) / 1_000_000, 2)
        
        return {
            "width": img.width,
            "height": img.height,
            "dimensions": f"{img.width}x{img.height}",
            "aspect_ratio": f"{aspect_w}:{aspect_h}",
            "orientation": orientation,
            "megapixels": megapixels,
            "bands": img.bands,
            "has_alpha": img.bands == 4 or img.bands == 2,
            "format": img.format
        }
    
    @staticmethod
    def _gcd(a: int, b: int) -> int:
        """Calculate greatest common divisor"""
        while b:
            a, b = b, a % b
        return a
    
    @staticmethod
    def _get_exif_data(img: pyvips.Image) -> Dict[str, Any]:
        """Extract EXIF metadata"""
        
        exif_data = {
            "has_exif": False,
            "camera": {},
            "settings": {},
            "location": {},
            "datetime": {},
            "other": {}
        }
        
        try:
            # Get all field names
            fields = img.get_fields()
            
            if not fields:
                return exif_data
            
            exif_data["has_exif"] = True
            
            # Camera information
            camera_fields = {
                "exif-ifd0-Make": "make",
                "exif-ifd0-Model": "model",
                "exif-ifd0-Software": "software",
                "exif-ifd2-LensModel": "lens_model"
            }
            
            for field, key in camera_fields.items():
                if field in fields:
                    try:
                        value = img.get(field)
                        if isinstance(value, bytes):
                            value = value.decode('utf-8', errors='ignore').strip('\x00')
                        exif_data["camera"][key] = value
                    except:
                        pass
            
            # Camera settings
            settings_fields = {
                "exif-ifd2-FNumber": "f_number",
                "exif-ifd2-ExposureTime": "exposure_time",
                "exif-ifd2-ISOSpeedRatings": "iso",
                "exif-ifd2-FocalLength": "focal_length",
                "exif-ifd2-Flash": "flash",
                "exif-ifd2-WhiteBalance": "white_balance",
                "exif-ifd2-ExposureProgram": "exposure_program",
                "exif-ifd2-MeteringMode": "metering_mode"
            }
            
            for field, key in settings_fields.items():
                if field in fields:
                    try:
                        value = img.get(field)
                        if isinstance(value, bytes):
                            value = value.decode('utf-8', errors='ignore').strip('\x00')
                        exif_data["settings"][key] = value
                    except:
                        pass
            
            # GPS Location
            gps_fields = {
                "exif-ifd0-GPSLatitude": "latitude",
                "exif-ifd0-GPSLongitude": "longitude",
                "exif-ifd0-GPSAltitude": "altitude"
            }
            
            for field, key in gps_fields.items():
                if field in fields:
                    try:
                        value = img.get(field)
                        exif_data["location"][key] = value
                    except:
                        pass
            
            # DateTime
            datetime_fields = {
                "exif-ifd0-DateTime": "datetime",
                "exif-ifd2-DateTimeOriginal": "datetime_original",
                "exif-ifd2-DateTimeDigitized": "datetime_digitized"
            }
            
            for field, key in datetime_fields.items():
                if field in fields:
                    try:
                        value = img.get(field)
                        if isinstance(value, bytes):
                            value = value.decode('utf-8', errors='ignore').strip('\x00')
                        exif_data["datetime"][key] = value
                    except:
                        pass
            
            # Other useful fields
            other_fields = {
                "exif-ifd0-Copyright": "copyright",
                "exif-ifd0-Artist": "artist",
                "exif-ifd0-ImageDescription": "description",
                "exif-ifd0-Orientation": "orientation"
            }
            
            for field, key in other_fields.items():
                if field in fields:
                    try:
                        value = img.get(field)
                        if isinstance(value, bytes):
                            value = value.decode('utf-8', errors='ignore').strip('\x00')
                        exif_data["other"][key] = value
                    except:
                        pass
        
        except Exception as e:
            logger.warning(f"EXIF extraction warning: {e}")
        
        return exif_data
    
    @staticmethod
    def _get_technical_info(img: pyvips.Image) -> Dict[str, Any]:
        """Extract technical image information"""
        
        # Color space / interpretation
        interpretation_map = {
            "error": "Error",
            "multiband": "Multiband",
            "b-w": "Black & White",
            "histogram": "Histogram",
            "xyz": "XYZ",
            "lab": "LAB",
            "cmyk": "CMYK",
            "labq": "LABQ",
            "rgb": "RGB",
            "cmc": "CMC",
            "lch": "LCH",
            "labs": "LABS",
            "srgb": "sRGB",
            "yxy": "YXY",
            "fourier": "Fourier",
            "rgb16": "RGB16",
            "grey16": "Grey16",
            "matrix": "Matrix",
            "scrgb": "scRGB",
            "hsv": "HSV"
        }
        
        interpretation = interpretation_map.get(img.interpretation, img.interpretation)
        
        # Bit depth
        format_map = {
            "uchar": 8,
            "char": 8,
            "ushort": 16,
            "short": 16,
            "uint": 32,
            "int": 32,
            "float": 32,
            "double": 64,
            "complex": 64,
            "dpcomplex": 128
        }
        
        bit_depth = format_map.get(img.format, "unknown")
        
        return {
            "color_space": interpretation,
            "bit_depth": bit_depth,
            "coding": img.coding if hasattr(img, 'coding') else "none",
            "bands": img.bands,
            "format": img.format,
            "x_resolution": img.xres if hasattr(img, 'xres') else None,
            "y_resolution": img.yres if hasattr(img, 'yres') else None,
            "x_offset": img.xoffset if hasattr(img, 'xoffset') else 0,
            "y_offset": img.yoffset if hasattr(img, 'yoffset') else 0
        }
    
    @staticmethod
    def _get_color_info(img: pyvips.Image) -> Dict[str, Any]:
        """Extract color information"""
        
        color_info = {
            "has_alpha": img.bands == 4 or img.bands == 2,
            "is_grayscale": img.bands == 1,
            "is_rgb": img.bands == 3 or img.bands == 4
        }
        
        # Calculate basic statistics if not too large
        if img.width * img.height < 1_000_000:  # Only for images < 1MP
            try:
                # Get min/max for each band
                stats = img.stats()
                
                if img.bands >= 3:
                    color_info["brightness"] = {
                        "min": round(stats(1, 0)[0], 2),
                        "max": round(stats(1, 1)[0], 2),
                        "avg": round(stats(1, 2)[0], 2)
                    }
            except:
                pass
        
        return color_info

metadata_extractor = MetadataExtractor()