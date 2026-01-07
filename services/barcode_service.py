import barcode
from barcode.writer import ImageWriter
import os
from config import Config

def generate_barcode(barcode_value, kid_name):
    """
    Generate Code128 barcode image
    
    Args:
        barcode_value: The barcode value (e.g., JT000123)
        kid_name: The child's name for filename
    
    Returns:
        Filename of generated barcode image
    """
    # Ensure upload folder exists
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    # Generate Code128 barcode
    code128 = barcode.get_barcode_class('code128')
    
    # Create barcode with image writer
    barcode_instance = code128(barcode_value, writer=ImageWriter())
    
    # Safe filename
    safe_name = ''.join(c if c.isalnum() else '_' for c in kid_name)
    filename = f'{barcode_value}_{safe_name}'
    
    # Full path without extension (barcode library adds .png)
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    
    # Save barcode image
    options = {
        'module_width': 0.3,
        'module_height': 10,
        'font_size': 10,
        'text_distance': 5,
        'quiet_zone': 3
    }
    
    barcode_instance.save(filepath, options=options)
    
    return f'{filename}.png'

def get_barcode_path(barcode_value):
    """Get the path to a barcode image"""
    files = os.listdir(Config.UPLOAD_FOLDER)
    for file in files:
        if file.startswith(barcode_value):
            return os.path.join('img', 'barcodes', file)
    return None
