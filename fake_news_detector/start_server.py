#!/usr/bin/env python3
"""
Startup script for the Fake News Detector Card Grid UI
Handles initialization, migration, and server startup
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

def check_mongodb():
    """Check if MongoDB is running"""
    try:
        import pymongo
        client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        client.server_info()
        print("✅ MongoDB is running")
        return True
    except Exception as e:
        print("❌ MongoDB is not running or not accessible")
        print("Please start MongoDB service:")
        print("  - Windows: net start MongoDB")
        print("  - macOS: brew services start mongodb-community")
        print("  - Linux: sudo systemctl start mongod")
        return False

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

def run_migration():
    """Run data migration script"""
    print("🔄 Running data migration...")
    try:
        # Change to backend directory
        os.chdir("training/backend")
        
        # Run migration script
        result = subprocess.run([sys.executable, "migrate_data.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Data migration completed")
            print(result.stdout)
            return True
        else:
            print("❌ Data migration failed")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False
    finally:
        # Return to original directory
        os.chdir("../..")

def start_server():
    """Start the Flask development server"""
    print("🚀 Starting Flask server...")
    try:
        os.chdir("training/backend")
        
        # Set environment variables
        env = os.environ.copy()
        env['FLASK_APP'] = 'app.py'
        env['FLASK_ENV'] = 'development'
        env['FLASK_DEBUG'] = '1'
        
        print("\n" + "="*50)
        print("🎉 Fake News Detector Card Grid UI")
        print("="*50)
        print("📱 Open your browser and go to: http://localhost:5000")
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

def initialize_database():
    """Initialize database with sample data"""
    print("🗄️  Initializing database...")
    try:
        result = subprocess.run([sys.executable, "init_database.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database initialized successfully")
            return True
        else:
            print("⚠️  Database initialization had warnings")
            print(result.stdout)
            return True  # Continue anyway
    except Exception as e:
        print(f"⚠️  Database initialization failed: {e}")
        return True  # Continue anyway

def run_connection_test():
    """Run connection test"""
    print("🔍 Running connection test...")
    try:
        result = subprocess.run([sys.executable, "test_connection.py"], 
                              capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
            
        return result.returncode == 0
    except Exception as e:
        print(f"⚠️  Connection test failed: {e}")
        return False

def main():
    """Main startup function"""
    print("🚀 Starting Fake News Detector Card Grid UI...")
    print("="*50)
    
    # Check system requirements
    if not check_python_version():
        return False
    
    if not check_mongodb():
        return False
    
    # Install dependencies
    if not install_dependencies():
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
    
    # Run migration
    if not run_migration():
        print("⚠️  Migration failed, but continuing...")
    
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