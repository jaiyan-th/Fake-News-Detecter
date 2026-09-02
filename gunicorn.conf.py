import os

# Gunicorn configuration for production deployment (Render, Heroku, etc.)
port = os.environ.get("PORT", "8000")
bind = f"0.0.0.0:{port}"

# Crucial: Use Uvicorn's ASGI worker class so Gunicorn runs FastAPI natively as ASGI
worker_class = "uvicorn.workers.UvicornWorker"
workers = 1
timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"
