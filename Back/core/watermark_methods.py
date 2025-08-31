import numpy as np
import cv2
from scipy.fft import dct, idct
from datetime import datetime
import json
from PIL import Image
from utils.logger import get_logger

logger = get_logger(__name__)

class WatermarkMethods:
    """Collection of watermark embedding methods with user key support"""
    
    @staticmethod
    def embed_lsb_with_key(img_array, binary_data, strength, seed):
        """Embed data using LSB steganography with user-specific seed"""
        height, width = img_array.shape[:2]
        strength_factor = strength / 100.0
        modified_pixels = 0
        binary_index = 0
        
        # Use user-specific seed for deterministic randomness
        np.random.seed(seed)
        
        for i in range(height):
            for j in range(width):
                if binary_index < len(binary_data):
                    # Only modify pixel if random check passes (based on strength)
                    if np.random.random() < strength_factor:
                        bit_to_embed = int(binary_data[binary_index])
                        
                        if len(img_array.shape) == 3:  # Color image
                            pixel_val = img_array[i, j, 2]  # Blue channel
                            img_array[i, j, 2] = (pixel_val & 0xFE) | bit_to_embed
                        else:  # Grayscale
                            pixel_val = img_array[i, j]
                            img_array[i, j] = (pixel_val & 0xFE) | bit_to_embed
                        
                        modified_pixels += 1
                        binary_index += 1
        
        logger.info(f"Modified {modified_pixels} pixels for watermark with seed {seed}")
        return img_array
    
    @staticmethod
    def embed_lsb(img_array, binary_data, strength=50):
        """Legacy method - use embed_lsb_with_key instead"""
        # Fallback to fixed seed for backward compatibility
        return WatermarkMethods.embed_lsb_with_key(img_array, binary_data, strength, seed=42)
    
    @staticmethod
    def embed_frequency_domain_with_key(img_array, text, strength, seed):
        """Embed watermark in frequency domain using user-specific seed"""
        height, width = img_array.shape[:2]
        
        # Work with luminance channel
        yuv = cv2.cvtColor(img_array, cv2.COLOR_RGB2YUV)
        y_channel = yuv[:, :, 0].astype(np.float32)
        
        # Apply DCT
        dct_coeffs = dct(dct(y_channel.T, norm='ortho').T, norm='ortho')
        
        # Generate pseudo-random pattern based on user seed and text
        combined_seed = seed + hash(text) % 1000000
        np.random.seed(combined_seed % (2**32))
        pattern = np.random.randn(*dct_coeffs.shape) * (strength / 100.0)
        
        # Embed in mid-frequency coefficients
        mid_freq_mask = np.zeros_like(dct_coeffs)
        h, w = dct_coeffs.shape
        mid_freq_mask[h//4:3*h//4, w//4:3*w//4] = 1
        
        # Apply watermark
        watermarked_dct = dct_coeffs + pattern * mid_freq_mask * 10
        
        # Inverse DCT
        watermarked_y = idct(idct(watermarked_dct.T, norm='ortho').T, norm='ortho')
        watermarked_y = np.clip(watermarked_y, 0, 255).astype(np.uint8)
        
        # Reconstruct image
        yuv[:, :, 0] = watermarked_y
        watermarked_rgb = cv2.cvtColor(yuv, cv2.COLOR_YUV2RGB)
        
        logger.info(f"Applied frequency domain watermark with seed {combined_seed}")
        return watermarked_rgb
    
    @staticmethod
    def embed_frequency_domain(img_array, text, strength=50):
        """Legacy method - use embed_frequency_domain_with_key instead"""
        # Fallback to text-based seed for backward compatibility
        return WatermarkMethods.embed_frequency_domain_with_key(
            img_array, text, strength, seed=hash(text) % (2**32)
        )
    
    @staticmethod
    def embed_with_redundancy_and_key(img_array, binary_data, redundancy, seed):
        """Embed data with redundancy using user-specific seed"""
        # Add redundancy
        redundant_binary = ''.join(bit * redundancy for bit in binary_data)
        
        height, width = img_array.shape[:2]
        binary_index = 0
        
        # Use user-specific seed for channel selection pattern
        np.random.seed(seed)
        channel_pattern = np.random.randint(0, 3, size=len(redundant_binary))
        
        for i in range(height):
            for j in range(width):
                if binary_index < len(redundant_binary):
                    bit_to_embed = int(redundant_binary[binary_index])
                    
                    if len(img_array.shape) == 3:
                        # Use seed-based channel selection
                        channel = channel_pattern[binary_index] if binary_index < len(channel_pattern) else 0
                        pixel_val = img_array[i, j, channel]
                        img_array[i, j, channel] = (pixel_val & 0xFE) | bit_to_embed
                    else:
                        pixel_val = img_array[i, j]
                        img_array[i, j] = (pixel_val & 0xFE) | bit_to_embed
                    
                    binary_index += 1
        
        logger.info(f"Embedded {binary_index} bits with redundancy {redundancy} using seed {seed}")
        return img_array
    
    @staticmethod
    def embed_with_redundancy(img_array, binary_data, redundancy=1):
        """Legacy method - use embed_with_redundancy_and_key instead"""
        # Fallback to fixed seed for backward compatibility
        return WatermarkMethods.embed_with_redundancy_and_key(
            img_array, binary_data, redundancy, seed=42
        )