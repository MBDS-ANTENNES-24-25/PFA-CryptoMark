
from flask import Blueprint, request, jsonify, session
from core.watermark_processor import WatermarkProcessor
from services.analysis_service import ImageAnalysisService
from api.validators import RequestValidator
from utils.file_utils import image_to_base64, load_and_validate_image
from utils.logger import get_logger
from datetime import datetime
import secrets
import hashlib
import os
import json
from typing import Dict, List, Optional
import uuid

# Import LangChain and Gemini dependencies
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.chains import ConversationChain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.prompts import PromptTemplate

# Existing code remains the same...
api_bp = Blueprint('api', __name__)
logger = get_logger(__name__)

# Initialize services
watermark_processor = WatermarkProcessor()
analysis_service = ImageAnalysisService()
validator = RequestValidator()

# Store user keys temporarily (in production, use a database)
user_keys_store = {}

# Agent conversation storage (in production, use a database)
conversation_histories = {}

# System prompt for the steganography expert agent
STEGANOGRAPHY_EXPERT_PROMPT = """You are an advanced AI expert specializing in steganography, digital watermarking, and cryptographic image protection techniques. You have deep knowledge in:

## Your Expertise Areas:

1. **Digital Watermarking Technologies:**
   - Invisible watermarking using LSB (Least Significant Bit) manipulation
   - Frequency domain watermarking (DCT, DWT, DFT transforms)
   - Spatial domain watermarking techniques
   - Robust vs. fragile watermarking methods
   - Reversible watermarking for medical and legal applications

2. **Steganography Methods:**
   - Classical steganography (LSB, MSB techniques)
   - Advanced steganographic algorithms (F5, OutGuess, StegHide)
   - Spread spectrum steganography
   - Transform domain steganography
   - Adaptive steganography techniques
   - Steganalysis and detection methods

3. **Cryptographic Protection:**
   - Hash-based message authentication codes (HMAC)
   - Digital signatures and verification
   - Key management and secure key generation
   - Encryption algorithms for payload protection
   - Blockchain-based watermarking verification

4. **Our Platform's Specific Services:**
   - Our system uses user-specific secret keys for watermark authentication
   - We support multiple watermarking methods: invisible, steganography, frequency domain, and metadata embedding
   - Watermark strength can be adjusted (0-100 scale) for balance between robustness and invisibility
   - We provide tampering detection and image authenticity analysis
   - Each watermark includes timestamp and cryptographic verification

## Your Communication Style:

- Be precise and technically accurate while remaining accessible
- Provide practical examples when explaining complex concepts
- Offer security best practices and recommendations
- Warn about potential vulnerabilities or limitations
- Suggest optimal settings based on use case (e.g., high strength for security, low for quality preservation)

## Important Guidelines:

- Always emphasize the importance of secure key storage
- Explain trade-offs between watermark robustness and image quality
- Discuss legal and ethical considerations of watermarking
- Provide guidance on detecting and preventing watermark removal attacks
- Recommend appropriate watermarking methods based on specific use cases
- Refuse answering to any question that is out of our context

## Available Services Information:

1. **Key Generation**: Generates cryptographically secure 256-bit keys
2. **Watermark Application**: Supports text watermarks with adjustable strength
3. **Watermark Verification**: Requires original key for authentication
4. **Image Analysis**: Detects tampering and analyzes image properties
5. **Multi-method Support**: invisible, steganography, frequency, metadata

Remember: You are helping users protect their digital assets and verify image authenticity. Always prioritize security and provide actionable advice.

Current context: You are assisting a user with our  steganography platform."""

class SteganographyAgent:
    """Specialized agent for steganography and watermarking expertise"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the agent with Gemini model"""
        # Get API key from environment if not provided
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY environment variable.")
        
        self.llm = ChatGoogleGenerativeAI(
            model="models/gemini-2.0-flash", 
            google_api_key=self.api_key,
            temperature=0.7,
            max_tokens=2048,
            top_p=0.95
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", STEGANOGRAPHY_EXPERT_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
        
        # Store active conversations
        self.conversations = {}
    
    def get_or_create_memory(self, session_id: str) -> ConversationBufferWindowMemory:
        """Get existing memory or create new one for session"""
        if session_id not in self.conversations:
            self.conversations[session_id] = ConversationBufferWindowMemory(
                return_messages=True,
                k=20,  # Keep last 20 exchanges
                memory_key="history"
            )
        return self.conversations[session_id]
    
    def process_message(self, session_id: str, message: str, context: Optional[Dict] = None) -> Dict:
        """Process user message and return agent response"""
        try:
            # Get or create memory for this session
            memory = self.get_or_create_memory(session_id)
            
            # Create conversation chain
            conversation = ConversationChain(
                llm=self.llm,
                memory=memory,
                prompt=self.prompt,
                verbose=False
            )
            
            if context:
                enriched_message = f"{message}\n\nContext: {json.dumps(context, indent=2)}"
            else:
                enriched_message = message
            
            response = conversation.predict(input=enriched_message)
            
            self._save_to_history(session_id, message, response, context)
            
            return {
                "success": True,
                "response": response,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Agent processing error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Retrieve conversation history for a session"""
        if session_id in conversation_histories:
            return conversation_histories[session_id]
        return []
    
    def clear_session(self, session_id: str) -> bool:
        """Clear conversation memory for a session"""
        try:
            if session_id in self.conversations:
                del self.conversations[session_id]
            if session_id in conversation_histories:
                del conversation_histories[session_id]
            return True
        except Exception as e:
            logger.error(f"Error clearing session {session_id}: {str(e)}")
            return False
    
    def _save_to_history(self, session_id: str, user_message: str, agent_response: str, context: Optional[Dict] = None):
        """Save conversation to history storage"""
        if session_id not in conversation_histories:
            conversation_histories[session_id] = []
        
        conversation_histories[session_id].append({
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "agent_response": agent_response,
            "context": context
        })
        
        if len(conversation_histories[session_id]) > 100:
            conversation_histories[session_id] = conversation_histories[session_id][-100:]

try:
    steganography_agent = SteganographyAgent(api_key="AIzaSyBhSRnyRF4s5OVaxNzLAoMjZJJY23eY330")
    logger.info("Steganography agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize steganography agent: {str(e)}")
    steganography_agent = None

@api_bp.route('/agent/chat', methods=['POST'])
def agent_chat():
    """Chat with the steganography expert agent"""
    try:
        if not steganography_agent:
            return jsonify({
                'error': 'Agent service is not available. Please check configuration.',
                'success': False
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        message = data.get('message')
        session_id = data.get('sessionId', str(uuid.uuid4()))
        context = data.get('context', {})
        
        if not message or not message.strip():
            return jsonify({'error': 'Message is required'}), 400
        
        context['available_services'] = {
            'key_generation': '/keys/generate',
            'apply_watermark': '/images/watermark',
            'verify_watermark': '/images/verify',
            'analyze_image': '/images/analyze',
            'supported_methods': ['invisible', 'steganography', 'frequency', 'metadata'],
            'strength_range': '0-100'
        }
        
        result = steganography_agent.process_message(session_id, message, context)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in agent_chat: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'success': False
        }), 500

@api_bp.route('/agent/history/<session_id>', methods=['GET'])
def get_agent_history(session_id):
    """Get conversation history for a session"""
    try:
        if not steganography_agent:
            return jsonify({
                'error': 'Agent service is not available',
                'success': False
            }), 503
        
        history = steganography_agent.get_conversation_history(session_id)
        
        return jsonify({
            'success': True,
            'sessionId': session_id,
            'history': history,
            'messageCount': len(history)
        })
        
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        return jsonify({
            'error': f'Failed to retrieve history: {str(e)}',
            'success': False
        }), 500

@api_bp.route('/agent/session', methods=['POST'])
def create_agent_session():
    """Create a new agent session"""
    try:
        session_id = str(uuid.uuid4())
        
        if steganography_agent:
            steganography_agent.get_or_create_memory(session_id)
        
        return jsonify({
            'success': True,
            'sessionId': session_id,
            'createdAt': datetime.now().isoformat(),
            'message': 'New session created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        return jsonify({
            'error': f'Failed to create session: {str(e)}',
            'success': False
        }), 500

@api_bp.route('/agent/session/<session_id>', methods=['DELETE'])
def clear_agent_session(session_id):
    """Clear conversation history for a session"""
    try:
        if not steganography_agent:
            return jsonify({
                'error': 'Agent service is not available',
                'success': False
            }), 503
        
        success = steganography_agent.clear_session(session_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Session {session_id} cleared successfully'
            })
        else:
            return jsonify({
                'error': 'Failed to clear session',
                'success': False
            }), 500
            
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        return jsonify({
            'error': f'Failed to clear session: {str(e)}',
            'success': False
        }), 500

@api_bp.route('/agent/status', methods=['GET'])
def agent_status():
    """Check agent service status"""
    try:
        is_available = steganography_agent is not None
        
        status_data = {
            'success': True,
            'available': is_available,
            'timestamp': datetime.now().isoformat(),
            'capabilities': {
                'chat': is_available,
                'history': is_available,
                'sessions': is_available,
                'model': 'gemini-1.5-flash' if is_available else None
            }
        }
        
        if is_available:
            status_data['activeSessions'] = len(steganography_agent.conversations)
        
        return jsonify(status_data)
        
    except Exception as e:
        logger.error(f"Error checking status: {str(e)}")
        return jsonify({
            'success': False,
            'available': False,
            'error': str(e)
        }), 500

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