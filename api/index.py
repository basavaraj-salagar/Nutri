import sys
import os

# Ensure the project root directory is on the python search path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Import the Flask application
from app import app

# Export handler for Vercel Python WSGI
handler = app
