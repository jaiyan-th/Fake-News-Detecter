#!/usr/bin/env python3
"""
Startup script for the SQLite-based Fake News Detector
Handles initialization and server startup without MongoDB dependency
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def install_ml_dependencies():
    """Install ML dependencies"""
    print("🤖 Installing ML dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "scikit-learn", "pandas", "numpy", "nltk"])
        print("✅ ML dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install ML dependencies: {e}")
        return False

def check_model_files():
    """Check if model files exist"""
    model_dir = Path("training/backend/model")
    model_file = model_dir / "model.pkl"
    vectorizer_file = model_dir / "vectorizer.pkl"
    
    if model_file.exists() and vectorizer_file.exists():
        print("✅ Model files found")
        return True
    else:
        print("❌ Model files not found")
        print("Please train the model first:")
        print("  cd training && python train_model.py")
        return False

def initialize_database():
    """Initialize SQLite database with sample data"""
    print("🗄️  Initializing SQLite database...")
    try:
        result = subprocess.run([sys.executable, "init_database_sqlite.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database initialized successfully")
            print(result.stdout)
            return True
        else:
            print("⚠️  Database initialization had warnings")
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return True  # Continue anyway
    except Exception as e:
        print(f"⚠️  Database initialization failed: {e}")
        return True  # Continue anyway

def start_server():
    """Start the Flask development server"""
    print("🚀 Starting Flask server with SQLite...")
    try:
        os.chdir("training/backend")
        
        # Set environment variables
        env = os.environ.copy()
        env['FLASK_APP'] = 'app.py'
        env['FLASK_ENV'] = 'development'
        env['FLASK_DEBUG'] = '1'
        
        print("\n" + "="*50)
        print("🎉 Fake News Detector - SQLite Version")
        print("="*50)
        print("📱 Open your browser and go to: http://localhost:5000")
        print("🗄️  Using SQLite database (no MongoDB required)")
        print("👤 Login: admin/admin123 or demo/demo123")
        print("🔧 Press Ctrl+C to stop the server")
        print("="*50 + "\n")
        
        # Start Flask server
        subprocess.run([sys.executable, "app.py"], env=env)
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
    finally:
        os.chdir("../..")

def run_connection_test():
    """Run connection test"""
    print("🔍 Running connection test...")
    try:
        # Simple test to check if we can import our modules
        sys.path.append(os.path.join("training", "backend"))
        from database import get_db
        
        db = get_db()
        stats = db.get_statistics()
        
        print(f"   ✅ Database connection successful")
        print(f"   📊 Total predictions: {stats['total_predictions']}")
        
        return True
    except Exception as e:
        print(f"   ⚠️  Connection test failed: {e}")
        return False

def main():
    """Main startup function"""
    print("🚀 Starting Fake News Detector - SQLite Version")
    print("="*55)
    
    # Check system requirements
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Install ML dependencies
    if not install_ml_dependencies():
        return False
    
    # Check model files
    if not check_model_files():
        print("\n💡 To train the model:")
        print("1. cd training")
        print("2. python train_model.py")
        print("3. Run this script again")
        return False
    
    # Initialize database
    if not initialize_database():
        print("⚠️  Database initialization failed, but continuing...")
    
    # Run connection test
    print("\n" + "="*50)
    if not run_connection_test():
        print("⚠️  Some connection tests failed, but starting server anyway...")
    
    # Start server
    start_server()
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Startup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        sys.exit(1)