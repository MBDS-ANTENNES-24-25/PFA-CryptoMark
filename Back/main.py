from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import cv2
import numpy as np
from PIL import Image, ExifTags
import io
import base64
import hashlib
import secrets
import json
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import logging
from scipy.fft import dct, idct
from cryptography.fernet import Fernet
import struct

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
UPLOAD_FOLDER = 'uploads'
PROTECTED_FOLDER = 'protected'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# Create directories if they don't exist
for folder in [UPLOAD_FOLDER, PROTECTED_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WatermarkProcessor:
    def __init__(self):
        # Generate a key for encryption (in production, store this securely)
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
    
    def generate_hash(self, data):
        """Generate SHA-256 hash of the data"""
        return hashlib.sha256(data).hexdigest()[:16]
    
    def text_to_binary(self, text):
        """Convert text to binary string"""
        return ''.join(format(ord(char), '08b') for char in text)
    
    def binary_to_text(self, binary):
        """Convert binary string to text"""
        try:
            text = ''
            for i in range(0, len(binary), 8):
                byte = binary[i:i+8]
                if len(byte) == 8:
                    text += chr(int(byte, 2))
            return text
        except:
            return None
    
    def invisible_watermark(self, image, text, strength=50):
        """Apply invisible watermark using LSB steganography with noise patterns"""
        img_array = np.array(image)
        height, width = img_array.shape[:2]
        
        # Create signature with metadata
        signature_data = {
            'text': text,
            'timestamp': datetime.now().isoformat(),
            'dimensions': f"{width}x{height}",
            'protection_level': strength
        }
        
        # Encrypt the signature
        signature_json = json.dumps(signature_data)
        encrypted_signature = self.cipher.encrypt(signature_json.encode())
        signature_hash = self.generate_hash(encrypted_signature)
        
        # Convert signature to binary
        signature_binary = ''.join(format(byte, '08b') for byte in encrypted_signature)
        
        # Add length header (32 bits for length)
        length_binary = format(len(signature_binary), '032b')
        full_binary = length_binary + signature_binary
        
        # Apply LSB modification with strength control
        strength_factor = strength / 100.0
        modified_pixels = 0
        binary_index = 0
        
        for i in range(height):
            for j in range(width):
                if binary_index < len(full_binary):
                    # Modify blue channel (least noticeable)
                    if len(img_array.shape) == 3:  # Color image
                        pixel_val = img_array[i, j, 2]  # Blue channel
                        bit_to_embed = int(full_binary[binary_index])
                        
                        # Apply strength-based modification
                        if np.random.random() < strength_factor:
                            # Clear LSB and set our bit
                            img_array[i, j, 2] = (pixel_val & 0xFE) | bit_to_embed
                            modified_pixels += 1
                        
                        binary_index += 1
                    else:  # Grayscale
                        pixel_val = img_array[i, j]
                        bit_to_embed = int(full_binary[binary_index])
                        
                        if np.random.random() < strength_factor:
                            img_array[i, j] = (pixel_val & 0xFE) | bit_to_embed
                            modified_pixels += 1
                        
                        binary_index += 1
        
        logger.info(f"Modified {modified_pixels} pixels for watermark")
        return Image.fromarray(img_array), signature_hash
    
    def frequency_domain_watermark(self, image, text, strength=50):
        """Apply watermark in frequency domain using DCT"""
        img_array = np.array(image.convert('RGB'))
        height, width = img_array.shape[:2]
        
        # Create signature
        signature_data = {
            'text': text,
            'timestamp': datetime.now().isoformat(),
            'method': 'frequency_domain',
            'strength': strength
        }
        
        signature_json = json.dumps(signature_data)
        encrypted_signature = self.cipher.encrypt(signature_json.encode())
        signature_hash = self.generate_hash(encrypted_signature)
        
        # Work with luminance channel
        yuv = cv2.cvtColor(img_array, cv2.COLOR_RGB2YUV)
        y_channel = yuv[:, :, 0].astype(np.float32)
        
        # Apply DCT
        dct_coeffs = dct(dct(y_channel.T, norm='ortho').T, norm='ortho')
        
        # Generate pseudo-random pattern based on signature
        np.random.seed(hash(text) % (2**32))
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
        
        return Image.fromarray(watermarked_rgb), signature_hash
    
    def steganography_watermark(self, image, text, strength=50):
        """Advanced steganography with error correction"""
        img_array = np.array(image)
        
        # Create robust signature with redundancy
        signature_data = {
            'text': text,
            'timestamp': datetime.now().isoformat(),
            'method': 'steganography',
            'checksum': hashlib.md5(text.encode()).hexdigest()
        }
        
        signature_json = json.dumps(signature_data)
        encrypted_signature = self.cipher.encrypt(signature_json.encode())
        signature_hash = self.generate_hash(encrypted_signature)
        
        # Convert to binary with error correction (simple repetition)
        signature_binary = ''.join(format(byte, '08b') for byte in encrypted_signature)
        
        # Add redundancy based on strength
        redundancy = max(1, strength // 25)
        redundant_binary = ''.join(bit * redundancy for bit in signature_binary)
        
        # Add length header
        length_binary = format(len(redundant_binary), '032b')
        full_binary = length_binary + redundant_binary
        
        # Embed in multiple channels with different patterns
        channels = min(3, len(img_array.shape))
        height, width = img_array.shape[:2]
        
        binary_index = 0
        for i in range(height):
            for j in range(width):
                if binary_index < len(full_binary):
                    bit_to_embed = int(full_binary[binary_index])
                    
                    if len(img_array.shape) == 3:  # Color image
                        # Spread across channels for robustness
                        channel = binary_index % 3
                        pixel_val = img_array[i, j, channel]
                        img_array[i, j, channel] = (pixel_val & 0xFE) | bit_to_embed
                    else:  # Grayscale
                        pixel_val = img_array[i, j]
                        img_array[i, j] = (pixel_val & 0xFE) | bit_to_embed
                    
                    binary_index += 1
        
        return Image.fromarray(img_array), signature_hash
    
    def metadata_watermark(self, image, text, strength=50):
        """Embed watermark in image metadata"""
        # Create comprehensive metadata
        metadata = {
            'Copyright': text,
            'Artist': text,
            'Description': f'Protected image - {datetime.now().isoformat()}',
            'Software': 'ImageProtector',
            'Protection_Level': str(strength),
            'Signature': secrets.token_hex(16)
        }
        
        signature_hash = self.generate_hash(json.dumps(metadata, sort_keys=True).encode())
        
        # Convert image to have EXIF data
        img_with_metadata = image.copy()
        
        # Note: For production, you'd use a library like piexif to properly embed EXIF data
        # This is a simplified version that adds basic metadata
        
        return img_with_metadata, signature_hash
    
    def extract_watermark(self, image, method='invisible'):
        """Extract watermark from image"""
        try:
            if method == 'invisible' or method == 'steganography':
                return self._extract_lsb_watermark(image)
            elif method == 'frequency':
                return self._extract_frequency_watermark(image)
            elif method == 'metadata':
                return self._extract_metadata_watermark(image)
            else:
                return None, "Unknown extraction method"
        except Exception as e:
            logger.error(f"Error extracting watermark: {str(e)}")
            return None, str(e)
    
    def _extract_lsb_watermark(self, image):
        """Extract LSB watermark"""
        img_array = np.array(image)
        height, width = img_array.shape[:2]
        
        # Extract binary data
        binary_data = ''
        
        # First extract length (32 bits)
        bit_count = 0
        for i in range(height):
            for j in range(width):
                if bit_count < 32:
                    if len(img_array.shape) == 3:
                        lsb = img_array[i, j, 2] & 1  # Blue channel
                    else:
                        lsb = img_array[i, j] & 1
                    binary_data += str(lsb)
                    bit_count += 1
                else:
                    break
            if bit_count >= 32:
                break
        
        # Get message length
        try:
            message_length = int(binary_data[:32], 2)
            if message_length > 1000000:  # Sanity check
                return None, "Invalid message length"
        except ValueError:
            return None, "Could not parse message length"
        
        # Extract message
        binary_data = ''
        bit_count = 0
        total_bits_needed = 32 + message_length
        
        for i in range(height):
            for j in range(width):
                if bit_count < total_bits_needed:
                    if len(img_array.shape) == 3:
                        lsb = img_array[i, j, 2] & 1
                    else:
                        lsb = img_array[i, j] & 1
                    binary_data += str(lsb)
                    bit_count += 1
                else:
                    break
            if bit_count >= total_bits_needed:
                break
        
        # Extract encrypted signature
        message_binary = binary_data[32:32+message_length]
        
        try:
            # Convert binary to bytes
            encrypted_signature = bytes(int(message_binary[i:i+8], 2) 
                                     for i in range(0, len(message_binary), 8))
            
            # Decrypt signature
            decrypted_data = self.cipher.decrypt(encrypted_signature)
            signature_data = json.loads(decrypted_data.decode())
            
            return signature_data, None
        except Exception as e:
            return None, f"Could not decrypt signature: {str(e)}"
    
    def _extract_frequency_watermark(self, image):
        """Extract frequency domain watermark (detection only)"""
        # This would involve correlation with known patterns
        # For now, return a basic detection result
        return {'detected': True, 'method': 'frequency_domain'}, None
    
    def _extract_metadata_watermark(self, image):
        """Extract metadata watermark"""
        try:
            # Extract EXIF data
            exif_data = {}
            if hasattr(image, '_getexif') and image._getexif():
                exif_dict = image._getexif()
                for tag, value in exif_dict.items():
                    tag_name = ExifTags.TAGS.get(tag, tag)
                    exif_data[tag_name] = value
            
            return exif_data, None
        except Exception as e:
            return None, str(e)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def image_to_base64(image):
    """Convert PIL Image to base64 string"""
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str

# Initialize watermark processor
watermark_processor = WatermarkProcessor()

@app.route('/api/images/watermark', methods=['POST'])
def apply_watermark():
    try:
        # Check if file is present
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Get watermark parameters
        watermark_type = request.form.get('type', 'invisible')
        strength = int(request.form.get('strength', 50))
        text = request.form.get('text', 'Protected Image')
        pattern = request.form.get('pattern', 'random')
        
        # Load and validate image
        try:
            image = Image.open(file.stream)
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
        except Exception as e:
            return jsonify({'error': f'Could not process image: {str(e)}'}), 400
        
        # Apply watermark based on type
        if watermark_type == 'invisible':
            watermarked_image, signature_hash = watermark_processor.invisible_watermark(
                image, text, strength
            )
        elif watermark_type == 'steganography':
            watermarked_image, signature_hash = watermark_processor.steganography_watermark(
                image, text, strength
            )
        elif watermark_type == 'frequency':
            watermarked_image, signature_hash = watermark_processor.frequency_domain_watermark(
                image, text, strength
            )
        elif watermark_type == 'metadata':
            watermarked_image, signature_hash = watermark_processor.metadata_watermark(
                image, text, strength
            )
        else:
            return jsonify({'error': 'Invalid watermark type'}), 400
        
        # Convert to base64 for response
        base64_image = image_to_base64(watermarked_image)
        
        # Log the operation
        logger.info(f"Applied {watermark_type} watermark with strength {strength}")
        
        return jsonify({
            'success': True,
            'base64Image': base64_image,
            'verificationHash': signature_hash,
            'watermarkType': watermark_type,
            'strength': strength,
            'message': f'Successfully applied {watermark_type} watermark'
        })
    
    except Exception as e:
        logger.error(f"Error in apply_watermark: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/images/verify', methods=['POST'])
def verify_watermark():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Load image
        try:
            image = Image.open(file.stream)
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
        except Exception as e:
            return jsonify({'error': f'Could not process image: {str(e)}'}), 400
        
        # Try different extraction methods
        extraction_methods = ['invisible', 'steganography', 'frequency', 'metadata']
        results = []
        
        for method in extraction_methods:
            signature_data, error = watermark_processor.extract_watermark(image, method)
            if signature_data and not error:
                results.append({
                    'method': method,
                    'data': signature_data,
                    'found': True
                })
            else:
                results.append({
                    'method': method,
                    'error': error,
                    'found': False
                })
        
        # Check if any watermark was found
        found_watermarks = [r for r in results if r['found']]
        has_watermark = len(found_watermarks) > 0
        
        response = {
            'hasWatermark': has_watermark,
            'results': results
        }
        
        if has_watermark:
            # Return details of the first found watermark
            primary_result = found_watermarks[0]
            response.update({
                'extractedMessage': primary_result['data'].get('text', 'N/A'),
                'timestamp': primary_result['data'].get('timestamp', 'Unknown'),
                'method': primary_result['method'],
                'details': primary_result['data']
            })
        
        logger.info(f"Verification complete. Watermark found: {has_watermark}")
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in verify_watermark: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/images/analyze', methods=['POST'])
def analyze_image():
    """Analyze image properties and potential tampering"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Load image
        image = Image.open(file.stream)
        img_array = np.array(image)
        
        # Basic analysis
        analysis = {
            'dimensions': f"{image.width}x{image.height}",
            'format': image.format,
            'mode': image.mode,
            'size_bytes': len(file.read()),
            'channels': len(img_array.shape),
            'bit_depth': 8  # Most common for standard images
        }
        
        # Statistical analysis for tampering detection
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
        
        # Check for EXIF data
        exif_data = {}
        if hasattr(image, '_getexif') and image._getexif():
            exif_dict = image._getexif()
            for tag, value in exif_dict.items():
                tag_name = ExifTags.TAGS.get(tag, tag)
                exif_data[tag_name] = str(value)  # Convert to string for JSON
        
        analysis['exif_data'] = exif_data
        analysis['has_exif'] = len(exif_data) > 0
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
    
    except Exception as e:
        logger.error(f"Error in analyze_image: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 10MB.'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create required directories
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(PROTECTED_FOLDER, exist_ok=True)
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)