#!/usr/bin/env python3
"""
SQLite Database Initialization Script
Sets up SQLite database with sample data for the Fake News Detector
"""

import sys
import os
from werkzeug.security import generate_password_hash

# Add the backend directory to the path so we can import our database module
sys.path.append(os.path.join(os.path.dirname(__file__), 'training', 'backend'))

from database import get_db

def create_admin_user(db):
    """Create admin user for testing"""
    print("👤 Creating admin user...")
    
    # Check if admin user exists
    if db.get_user("admin"):
        print("   ℹ️  Admin user already exists")
        return
    
    try:
        admin_password = generate_password_hash("admin123")
        
        if db.create_user("admin", "admin@example.com", admin_password, "admin"):
            print("   ✅ Admin user created")
            print("   📝 Username: admin")
            print("   📝 Password: admin123")
            print("   ⚠️  Change the password in production!")
        else:
            print("   ❌ Failed to create admin user")
        
    except Exception as e:
        print(f"   ❌ Failed to create admin user: {e}")

def create_demo_user(db):
    """Create demo user for testing"""
    print("👤 Creating demo user...")
    
    # Check if demo user exists
    if db.get_user("demo"):
        print("   ℹ️  Demo user already exists")
        return
    
    try:
        demo_password = generate_password_hash("demo123")
        
        if db.create_user("demo", "demo@example.com", demo_password, "user"):
            print("   ✅ Demo user created")
            print("   📝 Username: demo")
            print("   📝 Password: demo123")
        else:
            print("   ❌ Failed to create demo user")
        
    except Exception as e:
        print(f"   ❌ Failed to create demo user: {e}")

def verify_setup(db):
    """Verify the database setup"""
    print("\n🔍 Verifying database setup...")
    
    try:
        # Check database statistics
        stats = db.get_statistics()
        
        print(f"   📰 Total predictions: {stats['total_predictions']}")
        print(f"   👥 Prediction breakdown: {stats['by_prediction']}")
        print(f"   📊 Recent activity: {stats['recent_activity']}")
        
        # Check if we have users
        admin_user = db.get_user("admin")
        demo_user = db.get_user("demo")
        
        print(f"   👤 Admin user exists: {'✅' if admin_user else '❌'}")
        print(f"   👤 Demo user exists: {'✅' if demo_user else '❌'}")
        
        return stats['total_predictions'] >= 0  # At least database is working
        
    except Exception as e:
        print(f"   ❌ Verification failed: {e}")
        return False

def main():
    """Main initialization function"""
    print("🚀 Fake News Detector - SQLite Database Initialization")
    print("=" * 60)
    
    try:
        # Get database instance (this will create the database and tables)
        db = get_db()
        print("✅ SQLite database initialized successfully")
        print(f"📁 Database location: {db.db_path}")
        
        # Create admin user
        create_admin_user(db)
        
        # Create demo user
        create_demo_user(db)
        
        # Create sample data
        print("\n📝 Creating sample data...")
        try:
            db.create_sample_data()
            print("   ✅ Sample data created")
        except Exception as e:
            print(f"   ⚠️  Sample data creation failed: {e}")
        
        # Verify setup
        success = verify_setup(db)
        
        if success:
            print("\n🎉 SQLite database initialization completed successfully!")
            print("\n🚀 Next steps:")
            print("   1. Start the server: python training/backend/app.py")
            print("   2. Open browser: http://localhost:5000")
            print("   3. Login with admin/admin123 or demo/demo123")
            print("   4. Test the application!")
        else:
            print("\n⚠️  Database initialization completed with warnings")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)