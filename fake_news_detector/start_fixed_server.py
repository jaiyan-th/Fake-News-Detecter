#!/usr/bin/env python3
"""
Start the fixed Flask server with proper authentication
"""

import os
import sys
import subprocess
from pathlib import Path

def check_mongodb():
    """Check if MongoDB is running"""
    try:
        import pymongo
        client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        client.server_info()
        print("✅ MongoDB is running")
        return True
    except Exception:
        print("❌ MongoDB is not running")
        print("💡 Start MongoDB:")
        print("   Windows: net start MongoDB")
        print("   macOS: brew services start mongodb-community") 
        print("   Linux: sudo systemctl start mongod")
        return False

def start_server():
    """Start the fixed Flask server"""
    print("🚀 Starting fixed Flask server...")
    
    try:
        os.chdir("training/backend")
        
        print("\n" + "="*50)
        print("🎉 Fake News Detector - Fixed Version")
        print("="*50)
        print("📱 Open your browser: http://localhost:5000")
        print("🔧 Using enhanced ML model with proper authentication")
        print("⚡ Press Ctrl+C to stop")
        print("="*50 + "\n")
        
        # Start the fixed app.py
        subprocess.run([sys.executable, "app.py"])
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        print("\n💡 If you get import errors, try:")
        print("   python quick_start.py")
    finally:
        os.chdir("../..")

def main():
    """Main function"""
    print("⚡ Starting Fixed Fake News Detector")
    print("=" * 40)
    print("🔧 This version has fixed authentication")
    print()
    
    # Check MongoDB
    if not check_mongodb():
        print("\n❌ Cannot continue without MongoDB")
        print("Please start MongoDB and run this script again")
        return False
    
    # Start server
    start_server()
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Startup cancelled")
    except Exception as e:
        print(f"❌ Startup failed: {e}")