"""
WSGI entry point for production servers (Render, Gunicorn, etc.)
"""
import os
import sys

# Ensure fake-news-detector directory is in Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fake-news-detector'))

from serve_frontend import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
