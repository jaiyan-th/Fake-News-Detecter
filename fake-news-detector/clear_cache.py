"""
Clear analysis cache from database
"""
import sqlite3
import os

# Get database path
db_path = os.path.join(os.path.dirname(__file__), 'database', 'news.db')

if not os.path.exists(db_path):
    print(f"❌ Database not found at: {db_path}")
    exit(1)

print(f"Clearing cache from: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Count entries before deletion
    cursor.execute("SELECT COUNT(*) FROM analysis")
    count_before = cursor.fetchone()[0]
    
    print(f"Found {count_before} cached entries")
    
    # Delete all cached analyses
    cursor.execute("DELETE FROM analysis")
    conn.commit()
    
    # Count entries after deletion
    cursor.execute("SELECT COUNT(*) FROM analysis")
    count_after = cursor.fetchone()[0]
    
    print(f"✅ Cache cleared! Deleted {count_before - count_after} entries")
    print(f"Remaining entries: {count_after}")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error clearing cache: {e}")
    exit(1)
