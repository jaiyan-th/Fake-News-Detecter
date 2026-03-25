"""
Initialize database with proper tables using Flask-SQLAlchemy models
"""
import os
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from models.user import User
from models.user_analysis import UserAnalysis

print("=" * 60)
print("Initializing Database")
print("=" * 60)

# Create Flask app
app = create_app()

with app.app_context():
    # Create all tables from models (will not recreate existing tables)
    print("\nCreating tables from models...")
    db.create_all()
    print("✓ Created all tables")
    
    # Verify tables were created
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    print("\n" + "=" * 60)
    print("✅ Database initialized successfully!")
    print("=" * 60)
    print(f"\nDatabase location: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"\nTables created ({len(tables)}):")
    for table in tables:
        columns = inspector.get_columns(table)
        print(f"  ✓ {table} ({len(columns)} columns)")
        for col in columns:
            print(f"      - {col['name']}: {col['type']}")
    
    print("\nYou can now start the server:")
    print("  python serve_frontend.py")
    print("=" * 60)
