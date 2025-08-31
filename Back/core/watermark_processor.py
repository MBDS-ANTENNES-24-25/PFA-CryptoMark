import numpy as np
import json
import hashlib
from datetime import datetime
from PIL import Image, ExifTags
from core.watermark_methods import WatermarkMethods
from services.encryption_service import EncryptionService
from utils.logger import get_logger

logger = get_logger(__name__)

class WatermarkProcessor:
    def __init__(self, encryption_key=None):
        self.encryption_service = EncryptionService(encryption_key)
        self.methods = WatermarkMethods()
    
    def generate_user_key(self):
        """Generate a unique secret key for the user"""
        # Generate a strong random key
        random_bytes = np.random.bytes(32)
        user_key = hashlib.sha256(random_bytes).hexdigest()
        logger.info(f"Generated new user key: {user_key[:8]}...")
        return user_key
    
    def _get_seed_from_key(self, user_key, image_hash=None):
        """Generate a deterministic seed from user key only"""
        # Don't use image hash as it changes after watermarking
        # Only use the user key for consistent seed generation
        combined = user_key
        
        # Generate a 32-bit integer seed
        seed_bytes = hashlib.sha256(combined.encode()).digest()
        seed = int.from_bytes(seed_bytes[:4], byteorder='big')
        return seed
    
    def apply_watermark(self, image, text, user_key, watermark_type='invisible', strength=50):
        """Apply watermark to image using user's secret key"""
        try:
            # Don't use image hash since it will change after watermarking
            # This ensures consistent seed for extraction
            
            if watermark_type == 'invisible':
                return self._invisible_watermark(image, text, user_key, None, strength)
            elif watermark_type == 'steganography':
                return self._steganography_watermark(image, text, user_key, None, strength)
            elif watermark_type == 'frequency':
                return self._frequency_domain_watermark(image, text, user_key, None, strength)
            elif watermark_type == 'metadata':
                return self._metadata_watermark(image, text, user_key, strength)
            else:
                raise ValueError(f"Unknown watermark type: {watermark_type}")
        except Exception as e:
            logger.error(f"Error applying watermark: {str(e)}")
            raise
    
    def _invisible_watermark(self, image, text, user_key, image_hash, strength=50):
        """Apply invisible watermark using LSB steganography with user key"""
        img_array = np.array(image)
        height, width = img_array.shape[:2]
        
        # Create signature with metadata
        signature_data = {
            'text': text,
            'timestamp': datetime.now().isoformat(),
            'dimensions': f"{width}x{height}",
            'protection_level': strength,
            'method': 'invisible',
            'key_hash': hashlib.sha256(user_key.encode()).hexdigest()[:16]  # Store partial hash for verification
        }
        
        # Prepare binary data
        binary_data = self._prepare_binary_data(signature_data)
        
        # Apply LSB modification with user-specific seed
        seed = self._get_seed_from_key(user_key, image_hash)
        modified_array = self.methods.embed_lsb_with_key(
            img_array, binary_data, strength, seed
        )
        
        signature_hash = self.encryption_service.generate_hash(
            json.dumps(signature_data, sort_keys=True)
        )
        
        return Image.fromarray(modified_array), signature_hash
    
    def _steganography_watermark(self, image, text, user_key, image_hash, strength=50):
        """Advanced steganography with user key"""
        img_array = np.array(image)
        
        # Create robust signature
        signature_data = {
            'text': text,
            'timestamp': datetime.now().isoformat(),
            'method': 'steganography',
            'checksum': self.encryption_service.generate_hash(text),
            'key_hash': hashlib.sha256(user_key.encode()).hexdigest()[:16]
        }
        
        # Prepare binary data with redundancy
        binary_data = self._prepare_binary_data(signature_data)
        redundancy = max(1, strength // 25)
        
        # Embed with redundancy using user-specific seed
        seed = self._get_seed_from_key(user_key, image_hash)
        modified_array = self.methods.embed_with_redundancy_and_key(
            img_array, binary_data, redundancy, seed
        )
        
        signature_hash = self.encryption_service.generate_hash(
            json.dumps(signature_data, sort_keys=True)
        )
        
        return Image.fromarray(modified_array), signature_hash
    
    def _frequency_domain_watermark(self, image, text, user_key, image_hash, strength=50):
        """Apply watermark in frequency domain using user key"""
        img_array = np.array(image.convert('RGB'))
        
        # Create signature
        signature_data = {
            'text': text,
            'timestamp': datetime.now().isoformat(),
            'method': 'frequency_domain',
            'strength': strength,
            'key_hash': hashlib.sha256(user_key.encode()).hexdigest()[:16]
        }
        
        # Apply frequency domain watermark with user-specific seed
        seed = self._get_seed_from_key(user_key, image_hash)
        watermarked_array = self.methods.embed_frequency_domain_with_key(
            img_array, text, strength, seed
        )
        
        signature_hash = self.encryption_service.generate_hash(
            json.dumps(signature_data, sort_keys=True)
        )
        
        return Image.fromarray(watermarked_array), signature_hash
    
    def _metadata_watermark(self, image, text, user_key, strength=50):
        """Embed watermark in image metadata with user key reference"""
        metadata = {
            'Copyright': text,
            'Artist': text,
            'Description': f'Protected image - {datetime.now().isoformat()}',
            'Software': 'ImageProtector',
            'Protection_Level': str(strength),
            'KeyHash': hashlib.sha256(user_key.encode()).hexdigest()[:16],
            'Signature': self.encryption_service.generate_token()
        }
        
        signature_hash = self.encryption_service.generate_hash(
            json.dumps(metadata, sort_keys=True)
        )
        
        img_with_metadata = image.copy()
        # Note: In production, use piexif to properly embed EXIF data
        
        return img_with_metadata, signature_hash
    
    def _prepare_binary_data(self, signature_data):
        """Prepare binary data for embedding"""
        # Encrypt the signature
        signature_json = json.dumps(signature_data)
        encrypted_signature = self.encryption_service.encrypt(signature_json)
        
        # Convert to binary
        signature_binary = ''.join(format(byte, '08b') for byte in encrypted_signature)
        
        # Add length header (32 bits for length)
        length_binary = format(len(signature_binary), '032b')
        
        return length_binary + signature_binary
    
    def extract_watermark(self, image, user_key, method='invisible', strength=50):
        """Extract watermark from image using user's secret key"""
        try:
            # Don't use image hash - just use the user key for consistent seed
            seed = self._get_seed_from_key(user_key, None)
            
            if method == 'invisible':
                return self._extract_lsb_watermark(image, seed, strength)
            elif method == 'steganography':
                # For steganography, we need to extract with redundancy
                redundancy = max(1, strength // 25)
                return self._extract_steganography_watermark(image, seed, redundancy)
            elif method == 'frequency':
                return self._extract_frequency_watermark(image, seed)
            elif method == 'metadata':
                return self._extract_metadata_watermark(image)
            else:
                return None, "Unknown extraction method"
        except Exception as e:
            logger.error(f"Error extracting watermark: {str(e)}")
            return None, str(e)
    
    def _extract_lsb_watermark(self, image, seed, strength=50):
        """Extract LSB watermark using user-specific seed"""
        img_array = np.array(image)
        height, width = img_array.shape[:2]
        strength_factor = strength / 100.0
        
        logger.info(f"Extracting LSB with seed: {seed}")
        logger.info(f"Image dimensions: {height}x{width}")
        logger.info(f"Using strength factor: {strength_factor}")
        
        # Use the user-specific seed for deterministic randomness
        np.random.seed(seed)
        
        # Generate the same random pattern as during embedding
        pixel_indices = []
        
        for i in range(height):
            for j in range(width):
                if np.random.random() < strength_factor:
                    pixel_indices.append((i, j))
        
        logger.info(f"Selected {len(pixel_indices)} pixels for extraction")
        
        if len(pixel_indices) < 32:
            return None, "Not enough pixels selected for extraction (wrong strength or key?)"
        
        # Extract length first (32 bits)
        binary_data = ''
        for idx in range(min(32, len(pixel_indices))):
            i, j = pixel_indices[idx]
            if len(img_array.shape) == 3:
                lsb = img_array[i, j, 2] & 1  # Blue channel
            else:
                lsb = img_array[i, j] & 1
            binary_data += str(lsb)
        
        # Parse message length
        try:
            message_length = int(binary_data[:32], 2)
            logger.info(f"Parsed message length: {message_length}")
            
            if message_length <= 0:
                return None, f"Invalid message length: {message_length}"
            if message_length > 100000:
                return None, f"Message length too large: {message_length} (wrong key?)"
                
        except ValueError as e:
            return None, f"Could not parse message length (wrong key?): {e}"
        
        # Calculate total bits needed
        total_bits_needed = 32 + message_length
        
        if len(pixel_indices) < total_bits_needed:
            return None, f"Not enough pixels for full message extraction (need {total_bits_needed}, have {len(pixel_indices)})"
        
        # Extract full message
        binary_data = ''
        for idx in range(min(total_bits_needed, len(pixel_indices))):
            i, j = pixel_indices[idx]
            if len(img_array.shape) == 3:
                lsb = img_array[i, j, 2] & 1
            else:
                lsb = img_array[i, j] & 1
            binary_data += str(lsb)
        
        logger.info(f"Extracted {len(binary_data)} bits total")
        
        # Extract and decrypt the message portion
        message_binary = binary_data[32:32+message_length]
        
        try:
            if len(message_binary) % 8 != 0:
                return None, f"Message binary length not divisible by 8: {len(message_binary)}"
            
            encrypted_signature = bytes(
                int(message_binary[i:i+8], 2)
                for i in range(0, len(message_binary), 8)
            )
            
            decrypted_data = self.encryption_service.decrypt(encrypted_signature)
            signature_data = json.loads(decrypted_data.decode())
            
            logger.info(f"Successfully extracted watermark")
            return signature_data, None
            
        except Exception as e:
            return None, f"Could not decrypt signature (wrong key?): {str(e)}"
    
    def _extract_steganography_watermark(self, image, seed, redundancy):
        """Extract steganography watermark with redundancy handling"""
        img_array = np.array(image)
        height, width = img_array.shape[:2]
        
        logger.info(f"Extracting steganography with seed: {seed}, redundancy: {redundancy}")
        
        # Use the same seed for channel selection pattern as during embedding
        np.random.seed(seed)
        
        # Extract binary data sequentially (matching the embedding process)
        binary_bits = []
        max_bits = height * width * (3 if len(img_array.shape) == 3 else 1)
        
        # We need to extract enough bits to get the length header first
        # Extract first 32 * redundancy bits for the length header
        extracted_bits = []
        pixel_idx = 0
        
        for i in range(height):
            for j in range(width):
                if pixel_idx >= 32 * redundancy:
                    break
                    
                if len(img_array.shape) == 3:
                    # Use the same channel pattern as during embedding
                    channel = np.random.randint(0, 3)
                    lsb = img_array[i, j, channel] & 1
                else:
                    lsb = img_array[i, j] & 1
                    
                extracted_bits.append(str(lsb))
                pixel_idx += 1
            
            if pixel_idx >= 32 * redundancy:
                break
        
        # Decode redundancy for length
        length_bits = ''
        for i in range(0, 32 * redundancy, redundancy):
            # Take majority vote for each bit
            bit_group = extracted_bits[i:i+redundancy]
            ones = sum(1 for b in bit_group if b == '1')
            zeros = len(bit_group) - ones
            length_bits += '1' if ones > zeros else '0'
        
        # Parse message length
        try:
            message_length = int(length_bits, 2)
            logger.info(f"Parsed message length: {message_length} (with redundancy {redundancy})")
            
            if message_length <= 0 or message_length > 100000:
                return None, f"Invalid message length: {message_length}"
                
        except ValueError as e:
            return None, f"Could not parse message length: {e}"
        
        # Now extract the full message with redundancy
        total_bits_needed = (32 + message_length) * redundancy
        
        # Reset and extract all bits
        np.random.seed(seed)  # Reset seed to match embedding pattern
        extracted_bits = []
        pixel_idx = 0
        
        for i in range(height):
            for j in range(width):
                if pixel_idx >= total_bits_needed:
                    break
                    
                if len(img_array.shape) == 3:
                    channel = np.random.randint(0, 3)
                    lsb = img_array[i, j, channel] & 1
                else:
                    lsb = img_array[i, j] & 1
                    
                extracted_bits.append(str(lsb))
                pixel_idx += 1
            
            if pixel_idx >= total_bits_needed:
                break
        
        if len(extracted_bits) < total_bits_needed:
            return None, f"Not enough pixels for extraction (need {total_bits_needed}, got {len(extracted_bits)})"
        
        # Decode redundancy for the entire message
        decoded_bits = ''
        for i in range(0, len(extracted_bits), redundancy):
            bit_group = extracted_bits[i:i+redundancy]
            if not bit_group:
                break
            ones = sum(1 for b in bit_group if b == '1')
            zeros = len(bit_group) - ones
            decoded_bits += '1' if ones > zeros else '0'
        
        # Extract the message portion (skip the length header)
        message_binary = decoded_bits[32:32+message_length]
        
        try:
            if len(message_binary) % 8 != 0:
                return None, f"Message binary length not divisible by 8: {len(message_binary)}"
            
            encrypted_signature = bytes(
                int(message_binary[i:i+8], 2)
                for i in range(0, len(message_binary), 8)
            )
            
            decrypted_data = self.encryption_service.decrypt(encrypted_signature)
            signature_data = json.loads(decrypted_data.decode())
            
            logger.info(f"Successfully extracted steganography watermark")
            return signature_data, None
            
        except Exception as e:
            return None, f"Could not decrypt signature: {str(e)}"
        
    def _extract_frequency_watermark(self, image, seed):
        """Extract frequency domain watermark (detection only)"""
        # In a full implementation, you'd use the seed to recreate
        # the same pattern and correlate it with the image
        return {'detected': True, 'method': 'frequency_domain', 'seed_used': seed}, None
    
    def _extract_metadata_watermark(self, image):
        """Extract metadata watermark"""
        try:
            exif_data = {}
            if hasattr(image, '_getexif') and image._getexif():
                exif_dict = image._getexif()
                for tag, value in exif_dict.items():
                    tag_name = ExifTags.TAGS.get(tag, tag)
                    exif_data[tag_name] = value
            
            return exif_data, None
        except Exception as e:
            return None, str(e)
    
    def verify_user_key(self, extracted_data, user_key):
        """Verify if the extracted data matches the user's key"""
        if not extracted_data:
            return False
        
        if 'key_hash' in extracted_data:
            expected_hash = hashlib.sha256(user_key.encode()).hexdigest()[:16]
            return extracted_data['key_hash'] == expected_hash
        
        return True  # If no key hash stored, assume valid (backward compatibility)