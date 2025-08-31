from flask import current_app
from werkzeug.datastructures import FileStorage
from utils.file_utils import allowed_file

class RequestValidator:
    """Validate API requests"""
    
    @staticmethod
    def validate_image_upload(request):
        """Validate image upload request"""
        errors = []
        
        # Check if file is present
        if 'image' not in request.files:
            errors.append('No image file provided')
            return None, errors
        
        file = request.files['image']
        
        # Check if file is selected
        if file.filename == '':
            errors.append('No file selected')
            return None, errors
        
        # Check file type
        if not allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
            errors.append('Invalid file type')
            return None, errors
        
        return file, errors
    
    @staticmethod
    def validate_watermark_params(request):
        """Validate watermark parameters"""
        params = {
            'type': request.form.get('type', 'invisible'),
            'strength': 50,
            'text': request.form.get('text', 'Protected Image'),
            'pattern': request.form.get('pattern', 'random')
        }
        
        errors = []
        
        # Validate strength
        try:
            params['strength'] = int(request.form.get('strength', 50))
            if params['strength'] < 0 or params['strength'] > 100:
                errors.append('Strength must be between 0 and 100')
        except ValueError:
            errors.append('Invalid strength value')
        
        # Validate watermark type
        valid_types = ['invisible', 'steganography', 'frequency', 'metadata']
        if params['type'] not in valid_types:
            errors.append(f"Invalid watermark type. Must be one of: {', '.join(valid_types)}")
        
        return params, errors