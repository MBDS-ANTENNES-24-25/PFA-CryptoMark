import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logging(level='INFO', log_file=None):
    """Configure application logging"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10485760, backupCount=10
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(console_format)
        root_logger.addHandler(file_handler)
    
    return root_logger

def get_logger(name):
    """Get a logger instance"""
    return logging.getLogger(name)