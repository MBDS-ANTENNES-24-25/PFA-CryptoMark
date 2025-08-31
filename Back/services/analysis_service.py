import numpy as np
from PIL import Image, ExifTags
from utils.logger import get_logger

logger = get_logger(__name__)

class ImageAnalysisService:
    """Service for analyzing image properties and detecting tampering"""
    
    @staticmethod
    def analyze_image(image, file_size=None):
        """Analyze image properties"""
        try:
            img_array = np.array(image)
            
            # Basic analysis
            analysis = {
                'dimensions': f"{image.width}x{image.height}",
                'format': image.format,
                'mode': image.mode,
                'size_bytes': file_size,
                'channels': len(img_array.shape) if len(img_array.shape) > 2 else 1,
                'bit_depth': 8
            }
            
            # Statistical analysis
            if len(img_array.shape) == 3:
                # Color image analysis
                analysis['color_stats'] = {
                    'mean_rgb': [float(np.mean(img_array[:,:,i])) for i in range(3)],
                    'std_rgb': [float(np.std(img_array[:,:,i])) for i in range(3)]
                }
            else:
                # Grayscale analysis
                analysis['grayscale_stats'] = {
                    'mean': float(np.mean(img_array)),
                    'std': float(np.std(img_array))
                }
            
            # EXIF data analysis
            exif_data = ImageAnalysisService.extract_exif_data(image)
            analysis['exif_data'] = exif_data
            analysis['has_exif'] = len(exif_data) > 0
            
            return analysis, None
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return None, str(e)
    
    @staticmethod
    def extract_exif_data(image):
        """Extract EXIF data from image"""
        exif_data = {}
        try:
            if hasattr(image, '_getexif') and image._getexif():
                exif_dict = image._getexif()
                for tag, value in exif_dict.items():
                    tag_name = ExifTags.TAGS.get(tag, tag)
                    exif_data[tag_name] = str(value)
        except Exception as e:
            logger.warning(f"Could not extract EXIF data: {str(e)}")
        
        return exif_data
    
    @staticmethod
    def detect_tampering(image):
        """Detect potential image tampering"""
        # This is a placeholder for more sophisticated tampering detection
        # In production, you might use:
        # - Error Level Analysis (ELA)
        # - Copy-move detection
        # - JPEG compression artifacts analysis
        # - Metadata consistency checks
        
        tampering_indicators = []
        
        # Check for unusual patterns in LSB
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            lsb_variance = np.var(img_array[:,:,2] & 1)
            if lsb_variance < 0.2:
                tampering_indicators.append("Low LSB variance detected")
        
        return {
            'tampering_detected': len(tampering_indicators) > 0,
            'indicators': tampering_indicators
        }