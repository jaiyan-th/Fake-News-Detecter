#!/usr/bin/env python3
"""
Dependency Installation Script
Installs packages one by one to handle compatibility issues
"""

import subprocess
import sys

def install_package(package):
    """Install a single package"""
    try:
        print(f"📦 Installing {package}...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package, "--user"
        ], capture_output=True, text=True, check=True)
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    """Install all required packages"""
    print("🚀 Installing Python dependencies for Fake News Detector")
    print("=" * 60)
    
    # Core packages (install first)
    core_packages = [
        "Flask",
        "Werkzeug",
        "pymongo",
        "Flask-PyMongo", 
        "Flask-CORS",
        "requests",
        "python-dotenv"
    ]
    
    # ML packages (may need special handling)
    ml_packages = [
        "numpy",
        "pandas", 
        "scikit-learn",
        "nltk"
    ]
    
    # Optional packages
    optional_packages = [
        "psutil"
    ]
    
    failed_packages = []
    
    # Install core packages
    print("\n🔧 Installing core packages...")
    for package in core_packages:
        if not install_package(package):
            failed_packages.append(package)
    
    # Install ML packages
    print("\n🤖 Installing ML packages...")
    for package in ml_packages:
        if not install_package(package):
            failed_packages.append(package)
    
    # Install optional packages
    print("\n📊 Installing optional packages...")
    for package in optional_packages:
        if not install_package(package):
            print(f"⚠️  Optional package {package} failed, continuing...")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 INSTALLATION SUMMARY")
    print("=" * 60)
    
    if not failed_packages:
        print("🎉 All packages installed successfully!")
        print("\n🚀 Next steps:")
        print("   1. Run: python test_connection.py")
        print("   2. Run: python start_server.py")
        return True
    else:
        print("⚠️  Some packages failed to install:")
        for package in failed_packages:
            print(f"   ❌ {package}")
        
        print("\n💡 Try these alternatives:")
        print("   1. Update pip: python -m pip install --upgrade pip")
        print("   2. Install without versions: pip install Flask pymongo scikit-learn pandas numpy nltk")
        print("   3. Use conda instead: conda install scikit-learn pandas numpy")
        
        return len(failed_packages) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)