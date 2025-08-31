from flask import Flask
from flask_cors import CORS
import os
from config import config_dict
from api.routes import api_bp
from utils.logger import setup_logging
from utils.file_utils import create_directories

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_dict[config_name])
    
    # Setup CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Setup logging
    setup_logging(app.config['LOG_LEVEL'], app.config.get('LOG_FILE'))
    
    # Create required directories
    create_directories([
        app.config['UPLOAD_FOLDER'],
        app.config['PROTECTED_FOLDER']
    ])
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def register_error_handlers(app):
    @app.errorhandler(413)
    def too_large(e):
        return {'error': 'File too large. Maximum size is 10MB.'}, 413

    @app.errorhandler(404)
    def not_found(e):
        return {'error': 'Endpoint not found'}, 404

    @app.errorhandler(500)
    def internal_error(e):
        return {'error': 'Internal server error'}, 500

if __name__ == '__main__':
    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    app.run(
        debug=app.config['DEBUG'],
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000))
    )