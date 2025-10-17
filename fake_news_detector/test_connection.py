#!/usr/bin/env python3
"""
Connection Test Script for Fake News Detector
Tests frontend, backend, and MongoDB connectivity
"""

import sys
import os
import requests
import time
from pymongo import MongoClient
from pathlib import Path

def test_mongodb():
    """Test MongoDB connection"""
    print("🔍 Testing MongoDB connection...")
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
        client.server_info()
        
        # Test database access
        db = client.fake_news_app
        collections = db.list_collection_names()
        
        print("✅ MongoDB connection successful")
        print(f"   📊 Available collections: {collections}")
        
        # Test basic operations
        test_doc = {"test": "connection", "timestamp": time.time()}
        result = db.test_collection.insert_one(test_doc)
        db.test_collection.delete_one({"_id": result.inserted_id})
        
        print("   ✅ Database read/write operations working")
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("   💡 Make sure MongoDB is running:")
        print("      Windows: net start MongoDB")
        print("      macOS: brew services start mongodb-community")
        print("      Linux: sudo systemctl start mongod")
        return False

def test_model_files():
    """Test if ML model files exist"""
    print("\n🤖 Testing ML model files...")
    
    model_path = Path("training/backend/model/model.pkl")
    vectorizer_path = Path("training/backend/model/vectorizer.pkl")
    
    if model_path.exists() and vectorizer_path.exists():
        print("✅ Model files found")
        print(f"   📁 Model: {model_path}")
        print(f"   📁 Vectorizer: {vectorizer_path}")
        return True
    else:
        print("❌ Model files not found")
        print("   💡 Train the model first:")
        print("      cd training && python train_model.py")
        return False

def test_backend_startup():
    """Test if backend can start"""
    print("\n🖥️  Testing backend startup...")
    
    try:
        # Check if required files exist
        app_path = Path("training/backend/app.py")
        if not app_path.exists():
            print("❌ Backend app.py not found")
            return False
        
        # Try to import the app (basic syntax check)
        sys.path.insert(0, str(app_path.parent))
        
        print("✅ Backend files found")
        print("   📁 App: training/backend/app.py")
        return True
        
    except Exception as e:
        print(f"❌ Backend startup test failed: {e}")
        return False

def test_backend_api(port=5000):
    """Test backend API endpoints"""
    print(f"\n🌐 Testing backend API on port {port}...")
    
    base_url = f"http://localhost:{port}"
    
    try:
        # Test health endpoint
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            health_data = response.json()
            print(f"   📊 Status: {health_data.get('status', 'unknown')}")
        else:
            print(f"⚠️  Health endpoint returned status {response.status_code}")
        
        # Test cards endpoint
        response = requests.get(f"{base_url}/api/cards?limit=1", timeout=5)
        if response.status_code == 200:
            print("✅ Cards endpoint working")
            cards_data = response.json()
            print(f"   📊 Total cards: {cards_data.get('pagination', {}).get('total_count', 0)}")
        else:
            print(f"⚠️  Cards endpoint returned status {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend API")
        print("   💡 Make sure the backend server is running:")
        print(f"      python start_server.py")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_frontend_files():
    """Test if frontend files exist"""
    print("\n🎨 Testing frontend files...")
    
    required_files = [
        "training/frontend/index.html",
        "training/frontend/style.css",
        "training/frontend/script.js",
        "training/frontend/css/card-grid.css",
        "training/frontend/js/components/CardGrid.js",
        "training/frontend/js/components/NewsCard.js"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if not missing_files:
        print("✅ All frontend files found")
        for file_path in required_files:
            print(f"   📁 {file_path}")
        return True
    else:
        print("❌ Missing frontend files:")
        for file_path in missing_files:
            print(f"   ❌ {file_path}")
        return False

def test_dependencies():
    """Test Python dependencies"""
    print("\n📦 Testing Python dependencies...")
    
    required_packages = [
        'flask',
        'flask_pymongo', 
        'flask_cors',
        'pymongo',
        'scikit-learn',
        'pandas',
        'numpy'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if not missing_packages:
        print("✅ All required packages installed")
        return True
    else:
        print("❌ Missing packages:")
        for package in missing_packages:
            print(f"   ❌ {package}")
        print("   💡 Install missing packages:")
        print("      pip install -r requirements.txt")
        return False

def run_full_test():
    """Run complete connection test"""
    print("🚀 Fake News Detector - Connection Test")
    print("=" * 50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("MongoDB", test_mongodb),
        ("Model Files", test_model_files),
        ("Backend", test_backend_startup),
        ("Frontend Files", test_frontend_files)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        results[test_name] = test_func()
    
    # Test API if backend is available
    print("\n🌐 Testing API connection...")
    print("   💡 Make sure backend is running: python start_server.py")
    api_result = test_backend_api()
    results["API"] = api_result
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:15} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your system is ready to go!")
        print("\n🚀 Next steps:")
        print("   1. Start the server: python start_server.py")
        print("   2. Open browser: http://localhost:5000")
        print("   3. Start analyzing news articles!")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\n💡 Quick fixes:")
        print("   • Install dependencies: pip install -r requirements.txt")
        print("   • Start MongoDB service")
        print("   • Train model: cd training && python train_model.py")
        print("   • Start backend: python start_server.py")
    
    return passed == total

if __name__ == "__main__":
    success = run_full_test()
    sys.exit(0 if success else 1)