#!/usr/bin/env python3
"""
Quick Start Script - Works around dependency issues
Gets the system running with minimal dependencies
"""

import subprocess
import sys
import os
from pathlib import Path

def install_minimal_deps():
    """Install only the essential packages"""
    print("📦 Installing minimal dependencies...")
    
    essential_packages = [
        "Flask",
        "pymongo", 
        "Flask-PyMongo",
        "Flask-CORS",
        "Werkzeug",
        "requests"
    ]
    
    for package in essential_packages:
        try:
            print(f"   Installing {package}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", package, "--user"
            ], check=True, capture_output=True)
            print(f"   ✅ {package} installed")
        except subprocess.CalledProcessError:
            print(f"   ⚠️  {package} installation failed, but continuing...")
    
    print("✅ Essential packages installed")

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

def create_sample_data():
    """Create sample data in MongoDB"""
    try:
        import pymongo
        from datetime import datetime, timedelta
        
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client.fake_news_app
        
        # Check if data already exists
        if db.predictions.count_documents({}) > 0:
            print("✅ Sample data already exists")
            return True
        
        sample_data = [
            {
                "news": "Scientists at MIT develop new AI system for detecting misinformation with 95% accuracy using advanced natural language processing.",
                "prediction": "REAL",
                "confidence": 0.92,
                "username": "tech_reporter",
                "timestamp": datetime.now() - timedelta(hours=2),
                "source": "Tech News",
                "category": "Technology",
                "tags": ["technology", "science"]
            },
            {
                "news": "BREAKING: Aliens land in Times Square demanding to speak with world leaders. Government allegedly covering up the incident.",
                "prediction": "FAKE", 
                "confidence": 0.96,
                "username": "news_checker",
                "timestamp": datetime.now() - timedelta(hours=1),
                "source": "Social Media",
                "category": "General", 
                "tags": ["conspiracy"]
            },
            {
                "news": "Local bakery wins national award for best sourdough bread after 50 years of traditional fermentation methods.",
                "prediction": "REAL",
                "confidence": 0.88,
                "username": "local_reporter", 
                "timestamp": datetime.now() - timedelta(minutes=30),
                "source": "Local News",
                "category": "Business",
                "tags": ["business", "local"]
            }
        ]
        
        db.predictions.insert_many(sample_data)
        print("✅ Sample data created")
        return True
        
    except Exception as e:
        print(f"⚠️  Failed to create sample data: {e}")
        return False

def start_minimal_server():
    """Start the minimal server"""
    print("🚀 Starting minimal server...")
    
    try:
        os.chdir("training/backend")
        
        print("\n" + "="*50)
        print("🎉 Fake News Detector - Quick Start")
        print("="*50)
        print("📱 Open your browser: http://localhost:5000")
        print("🔧 Using rule-based prediction (no ML model needed)")
        print("⚡ Press Ctrl+C to stop")
        print("="*50 + "\n")
        
        subprocess.run([sys.executable, "app_minimal.py"])
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
    finally:
        os.chdir("../..")

def main():
    """Main quick start function"""
    print("⚡ Quick Start - Fake News Detector")
    print("=" * 40)
    print("🎯 Getting you up and running quickly!")
    print()
    
    # Install minimal dependencies
    install_minimal_deps()
    
    # Check MongoDB
    if not check_mongodb():
        print("\n❌ Cannot continue without MongoDB")
        print("Please start MongoDB and run this script again")
        return False
    
    # Create sample data
    create_sample_data()
    
    # Start server
    start_minimal_server()
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Quick start cancelled")
    except Exception as e:
        print(f"❌ Quick start failed: {e}")
        print("\n💡 Try the full setup:")
        print("   1. Fix Python dependencies")
        print("   2. Run: python start_server.py")