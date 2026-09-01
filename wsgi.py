"""
WSGI / ASGI entry point for production servers (Render, Gunicorn, Uvicorn, etc.)
"""
import os
import sys

# Ensure root workspace directory is in sys.path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.main import app as asgi_app

try:
    from a2wsgi import ASGIMiddleware
    application = ASGIMiddleware(asgi_app)
    app = application
except Exception:
    application = asgi_app
    app = asgi_app

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run("backend.main:app", host='0.0.0.0', port=port)
