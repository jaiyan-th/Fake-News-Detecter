#!/usr/bin/env python3
"""
Integrated server serving both frontend and backend
"""

import os
import sys
from flask import send_from_directory

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and create the backend app
from app import create_app

# Create the Flask app with all backend functionality
app = create_app()

# Frontend directory
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), 'frontend')

# Add frontend routes to the same app
@app.route('/')
def serve_index():
    """Serve the main HTML file"""
    from flask import make_response
    response = make_response(send_from_directory(FRONTEND_DIR, 'index.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, images, etc.)"""
    # Skip API routes - they're handled by blueprints
    if filename.startswith('api/') or filename.startswith('analyze'):
        return {'error': 'Not found'}, 404
    from flask import make_response
    response = make_response(send_from_directory(FRONTEND_DIR, filename))
    # Add no-cache headers for CSS and JS files
    if filename.endswith(('.css', '.js')):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    # Ensure correct MIME types
    if filename.endswith('.css'):
        response.headers['Content-Type'] = 'text/css'
    elif filename.endswith('.js'):
        response.headers['Content-Type'] = 'application/javascript'
    return response

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 FAKE NEWS DETECTION SYSTEM - INTEGRATED FRONTEND & BACKEND")
    print("=" * 60)
    print(f"Frontend serving from: {FRONTEND_DIR}")
    print("Backend integrated with full fake news detection pipeline")
    print("")
    print("Features available:")
    print("✅ Real authentication with email notifications")
    print("✅ Google OAuth Sign-in")
    print("✅ Multi-language support")
    print("✅ Pattern detection")
    print("✅ Credibility assessment")
    print("✅ Semantic similarity analysis")
    print("✅ LLM-powered explanations")
    print("✅ Comprehensive error handling")
    print("")
    print("🌐 Open your browser and go to: http://localhost:3000")
    print("📝 Register or login to start analyzing news articles")
    print("")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(host='127.0.0.1', port=3000, debug=True)