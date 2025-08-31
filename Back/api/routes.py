from flask import Blueprint, request, jsonify, session
from core.watermark_processor import WatermarkProcessor
from services.analysis_service import ImageAnalysisService
from api.validators import RequestValidator
from utils.file_utils import image_to_base64, load_and_validate_image
from utils.logger import get_logger
from datetime import datetime
import secrets
import hashlib

api_bp = Blueprint('api', __name__)
logger = get_logger(__name__)

# Initialize services
watermark_processor = WatermarkProcessor()
analysis_service = ImageAnalysisService()
validator = RequestValidator()

# Store user keys temporarily (in production, use a database)
# This is just for demonstration - use proper storage in production
user_keys_store = {}

@api_bp.route('/keys/generate', methods=['POST'])
def generate_user_key():
    """Generate a new user-specific secret key"""
    try:
        # Generate a cryptographically secure key
        user_key = secrets.token_hex(32)  # 64-character hex string
        key_id = secrets.token_urlsafe(16)  # Short ID for reference
        
        # Store key with metadata (in production, store in database)
        user_keys_store[key_id] = {
            'key': user_key,
            'created_at': datetime.now().isoformat(),
            'usage_count': 0
        }
        
        logger.info(f"Generated new user key with ID: {key_id}")
        
        return jsonify({
            'success': True,
            'keyId': key_id,
            'secretKey': user_key,
            'message': 'Save this key securely! You will need it to verify your watermarks.',
            'warning': 'This key cannot be recovered if lost. Consider backing it up safely.'
        })
    
    except Exception as e:
        logger.error(f"Error generating user key: {str(e)}")
        return jsonify({'error': 'Failed to generate key'}), 500

@api_bp.route('/images/watermark', methods=['POST'])
def apply_watermark():
    """Apply watermark to uploaded image with user key"""
    try:
        # Validate image upload
        file, errors = validator.validate_image_upload(request)
        if errors:
            return jsonify({'error': ', '.join(errors)}), 400
        
        # Validate watermark parameters
        params, param_errors = validator.validate_watermark_params(request)
        if param_errors:
            return jsonify({'error': ', '.join(param_errors)}), 400
        
        # Get user key from request
        user_key = request.form.get('userKey')
        if not user_key:
            # Generate a temporary key if none provided (for backward compatibility)
            user_key = secrets.token_hex(32)
            logger.warning("No user key provided, generated temporary key")
            temporary_key = True
        else:
            temporary_key = False
        
        # Load and validate image
        image, error = load_and_validate_image(file.stream)
        if error:
            return jsonify({'error': error}), 400
        
        # Apply watermark with user key
        watermarked_image, signature_hash = watermark_processor.apply_watermark(
            image,
            params['text'],
            user_key,  # Pass the user key
            params['type'],
            params['strength']
        )
        
        # Convert to base64
        base64_image = image_to_base64(watermarked_image)
        
        # Create a key hint (first 8 chars of key hash) for verification
        key_hint = hashlib.sha256(user_key.encode()).hexdigest()[:8]
        
        logger.info(f"Applied {params['type']} watermark with user key (hint: {key_hint})")
        
        response_data = {
            'success': True,
            'base64Image': base64_image,
            'verificationHash': signature_hash,
            'watermarkType': params['type'],
            'strength': params['strength'],
            'keyHint': key_hint,
            'message': f"Successfully applied {params['type']} watermark"
        }
        
        if temporary_key:
            response_data['temporaryKey'] = user_key
            response_data['warning'] = 'A temporary key was generated. Save it to verify your watermark later!'
        
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error in apply_watermark: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@api_bp.route('/images/verify', methods=['POST'])
def verify_watermark():
    """Verify watermark in uploaded image using user key"""
    try:
        # Validate image upload
        file, errors = validator.validate_image_upload(request)
        if errors:
            return jsonify({'error': ', '.join(errors)}), 400
        
        # Get user key from request
        user_key = request.form.get('userKey')
        if not user_key:
            return jsonify({
                'error': 'User key is required for verification',
                'hasWatermark': False,
                'message': 'Please provide your secret key to verify the watermark'
            }), 400
        
        # Get extraction parameters
        method = request.form.get('method', 'invisible')
        strength = int(request.form.get('strength', 50))
        
        # Load image
        image, error = load_and_validate_image(file.stream)
        if error:
            return jsonify({'error': error}), 400
        
        # Try to extract with the provided key
        signature_data, error = watermark_processor.extract_watermark(
            image, 
            user_key,
            method,
            strength
        )
        
        if signature_data and not error:
            # Verify the key matches
            is_valid_key = watermark_processor.verify_user_key(signature_data, user_key)
            
            if is_valid_key:
                logger.info(f"Successfully verified watermark with user key")
                return jsonify({
                    'hasWatermark': True,
                    'isValidKey': True,
                    'extractedMessage': signature_data.get('text', 'N/A'),
                    'timestamp': signature_data.get('timestamp', 'Unknown'),
                    'method': signature_data.get('method', method),
                    'details': signature_data,
                    'message': 'Watermark successfully verified with your key!'
                })
            else:
                logger.warning(f"Watermark found but key doesn't match")
                return jsonify({
                    'hasWatermark': True,
                    'isValidKey': False,
                    'message': 'A watermark was detected but your key does not match',
                    'hint': 'This image may be protected by someone else'
                })
        else:
            # Try other methods if the first one fails
            extraction_methods = ['invisible', 'steganography', 'frequency', 'metadata']
            extraction_methods.remove(method)  # Remove already tried method
            
            for alt_method in extraction_methods:
                alt_data, alt_error = watermark_processor.extract_watermark(
                    image, 
                    user_key,
                    alt_method,
                    strength
                )
                if alt_data and not alt_error:
                    is_valid_key = watermark_processor.verify_user_key(alt_data, user_key)
                    if is_valid_key:
                        return jsonify({
                            'hasWatermark': True,
                            'isValidKey': True,
                            'extractedMessage': alt_data.get('text', 'N/A'),
                            'timestamp': alt_data.get('timestamp', 'Unknown'),
                            'method': alt_data.get('method', alt_method),
                            'details': alt_data,
                            'message': f'Watermark found using {alt_method} method!'
                        })
            
            # No watermark found with this key
            logger.info(f"No watermark found with provided key")
            return jsonify({
                'hasWatermark': False,
                'message': 'No watermark found with your key',
                'possibleReasons': [
                    'The image may not have a watermark',
                    'The watermark may have been created with a different key',
                    'The image may have been modified after watermarking'
                ],
                'error': error if error else None
            })
    
    except Exception as e:
        logger.error(f"Error in verify_watermark: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@api_bp.route('/images/analyze', methods=['POST'])
def analyze_image():
    """Analyze image properties and potential tampering"""
    try:
        # Validate image upload
        file, errors = validator.validate_image_upload(request)
        if errors:
            return jsonify({'error': ', '.join(errors)}), 400
        
        # Get file size
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        
        # Load image
        image, error = load_and_validate_image(file.stream)
        if error:
            return jsonify({'error': error}), 400
        
        # Analyze image
        analysis, error = analysis_service.analyze_image(image, file_size)
        if error:
            return jsonify({'error': error}), 400
        
        # Check for tampering
        tampering_results = analysis_service.detect_tampering(image)
        analysis['tampering_analysis'] = tampering_results
        
        # Check if any watermark exists (without key verification)
        watermark_detected = False
        for method in ['invisible', 'steganography', 'frequency', 'metadata']:
            # Use a dummy key just to check for watermark presence
            dummy_key = 'dummy_detection_key'
            data, _ = watermark_processor.extract_watermark(image, dummy_key, method)
            if data:
                watermark_detected = True
                break
        
        analysis['watermark_detected'] = watermark_detected
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
    
    except Exception as e:
        logger.error(f"Error in analyze_image: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })