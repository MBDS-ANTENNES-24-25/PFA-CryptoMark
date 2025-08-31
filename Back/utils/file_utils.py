import os
import io
import base64
from PIL import Image
from werkzeug.utils import secure_filename

def create_directories(directories):
    """Create directories if they don't exist"""
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def image_to_base64(image):
    """Convert PIL Image to base64 string"""
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str

def load_and_validate_image(file_stream):
    """Load and validate image from file stream"""
    try:
        image = Image.open(file_stream)
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        return image, None
    except Exception as e:
        return None, f'Could not process image: {str(e)}'

def save_image(image, filepath, format='PNG'):
    """Save image to file"""
    try:
        image.save(filepath, format=format)
        return True
    except Exception as e:
        return False