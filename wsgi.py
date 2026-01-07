"""
WSGI configuration for PythonAnywhere deployment
"""
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/yourusername/JTKIDZ'  # Update with your PythonAnywhere username
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment to production
os.environ['FLASK_ENV'] = 'production'

# Import the Flask app
from app import app as application
