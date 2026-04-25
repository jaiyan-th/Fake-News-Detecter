import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from app import create_app
from models.user import db
from models.database import AnalysisCache

def migrate_data():
    print("Starting data migration from local SQLite to Supabase...")
    
    # Ensure environment is loaded
    load_dotenv()
    
    # We need the Flask app context to use SQLAlchemy
    app = create_app()
    
    with app.app_context():
        # Connect to local SQLite
        db_path = os.path.join(app.config['BASE_DIR'], 'database', 'news.db')
        
        if not os.path.exists(db_path):
            print(f"Local database not found at {db_path}. Nothing to migrate.")
            return
            
        print(f"Connecting to local SQLite: {db_path}")
        sqlite_conn = sqlite3.connect(db_path)
        sqlite_conn.row_factory = sqlite3.Row
        cursor = sqlite_conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM analysis")
            rows = cursor.fetchall()
            print(f"Found {len(rows)} records in local 'analysis' table.")
            
            migrated_count = 0
            skipped_count = 0
            
            for row in rows:
                url = row['url']
                
                # Check if already exists in Postgres
                existing = AnalysisCache.query.filter_by(url=url).first()
                if existing:
                    skipped_count += 1
                    continue
                
                # Parse created_at
                try:
                    created_at = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
                except:
                    # Handle cases where timestamp might include microseconds or be in different format
                    try:
                        created_at = datetime.strptime(row['created_at'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                    except:
                        created_at = datetime.utcnow()
                
                # Create ORM record
                record = AnalysisCache(
                    url=url,
                    summary=row['summary'],
                    verdict=row['verdict'],
                    confidence=row['confidence'],
                    explanation=row['explanation'],
                    matched_articles=row['matched_articles'],
                    key_claims=row['key_claims'],
                    processing_time=row['processing_time'],
                    created_at=created_at
                )
                
                db.session.add(record)
                migrated_count += 1
                
                # Commit in batches of 50 to avoid huge transactions
                if migrated_count % 50 == 0:
                    db.session.commit()
                    print(f"Migrated {migrated_count} records so far...")
                    
            # Final commit
            db.session.commit()
            print(f"Migration complete! Migrated {migrated_count} records. Skipped {skipped_count} (already existed).")
            
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                print("The 'analysis' table does not exist in the local database. Nothing to migrate.")
            else:
                print(f"SQLite error: {e}")
        except Exception as e:
            print(f"Migration failed: {e}")
            db.session.rollback()
        finally:
            sqlite_conn.close()

if __name__ == '__main__':
    migrate_data()
