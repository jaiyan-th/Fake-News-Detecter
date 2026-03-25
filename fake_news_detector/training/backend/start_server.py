#!/usr/bin/env python3
"""
Simple server startup script
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    print("🚀 Starting Fake News Detection Server...")
    print("📍 Server will be available at: http://localhost:5000")
    print("=" * 50)
    
    # Import and run the main application
    from api_enhanced import app
    
    print("✅ All modules loaded successfully!")
    print("🌐 Starting Flask server...")
    print("=" * 50)
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("💡 Make sure all dependencies are installed:")
    print("   pip install flask flask-cors requests beautifulsoup4 scikit-learn pandas nltk")
    
except Exception as e:
    print(f"❌ Error starting server: {e}")
    print("💡 Check the error message above for details")