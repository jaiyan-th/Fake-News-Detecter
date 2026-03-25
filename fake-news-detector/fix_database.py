"""
Script to recreate the database
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db

def fix_database():
    """Recreate database tables"""
    print("=" * 60)
    print("Fixing Database")
    print("=" * 60)
    
    try:
        # Create Flask app
        print("Creating Flask app...")
        app = create_app()
        
        # Push app context
        print("Pushing app context...")
        with app.app_context():
            # Drop all tables (if they exist)
            print("Dropping existing tables...")
            db.drop_all()
            
            # Create all tables
            print("Creating new tables...")
            db.create_all()
            
            print("\n" + "=" * 60)
            print("✅ Database created successfully!")
            print("=" * 60)
            print("\nDatabase location: database/news.db")
            print("\nYou can now start the server with:")
            print("  python serve_frontend.py")
            print("=" * 60)
            
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ Error creating database:")
        print(str(e))
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    fix_database()
