import hashlib
import secrets
from cryptography.fernet import Fernet
from utils.logger import get_logger

logger = get_logger(__name__)

class EncryptionService:
    def __init__(self, key=None):
        """Initialize encryption service"""
        if key:
            self.encryption_key = key.encode() if isinstance(key, str) else key
        else:
            self.encryption_key = Fernet.generate_key()
        
        self.cipher = Fernet(self.encryption_key)
    
    def encrypt(self, data):
        """Encrypt data"""
        try:
            if isinstance(data, str):
                data = data.encode()
            return self.cipher.encrypt(data)
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
    
    def decrypt(self, encrypted_data):
        """Decrypt data"""
        try:
            return self.cipher.decrypt(encrypted_data)
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise
    
    @staticmethod
    def generate_hash(data, length=16):
        """Generate SHA-256 hash of the data"""
        if isinstance(data, str):
            data = data.encode()
        return hashlib.sha256(data).hexdigest()[:length]
    
    @staticmethod
    def generate_token(length=16):
        """Generate secure random token"""
        return secrets.token_hex(length)