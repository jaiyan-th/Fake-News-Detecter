"""Start the API server with proper path setup"""
import os
import sys

# Change to backend directory
backend_dir = os.path.join(os.path.dirname(__file__), 'fake_news_detector', 'training', 'backend')
os.chdir(backend_dir)

# Run the API
exec(open('api_enhanced.py').read())
