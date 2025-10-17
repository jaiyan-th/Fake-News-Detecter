#!/usr/bin/env python3
"""
Fix confidence field in existing database records
"""

import os
import sys
from pymongo import MongoClient
import datetime

def fix_confidence_fields():
    """Add confidence field to records that don't have it"""
    try:
        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017/")
        db = client.fake_news_app
        
        print("🔧 Fixing confidence fields in database...")
        
        # Find records without confidence field
        records_without_confidence = list(db.predictions.find({"confidence": {"$exists": False}}))
        
        if not records_without_confidence:
            print("✅ All records already have confidence field")
            return True
        
        print(f"📊 Found {len(records_without_confidence)} records without confidence field")
        
        # Update records to add default confidence
        for record in records_without_confidence:
            # Set default confidence based on prediction
            default_confidence = 0.85 if record.get('prediction') == 'REAL' else 0.80
            
            db.predictions.update_one(
                {"_id": record["_id"]},
                {"$set": {"confidence": default_confidence}}
            )
        
        print(f"✅ Updated {len(records_without_confidence)} records with default confidence values")
        
        # Also ensure all records have required fields
        all_records = list(db.predictions.find({}))
        updated_count = 0
        
        for record in all_records:
            updates = {}
            
            # Add missing fields with defaults
            if 'source' not in record:
                updates['source'] = 'Legacy Data'
            
            if 'category' not in record:
                updates['category'] = 'General'
            
            if 'tags' not in record:
                updates['tags'] = ['general']
            
            if 'model_version' not in record:
                updates['model_version'] = '1.0'
            
            if updates:
                db.predictions.update_one(
                    {"_id": record["_id"]},
                    {"$set": updates}
                )
                updated_count += 1
        
        if updated_count > 0:
            print(f"✅ Updated {updated_count} records with missing fields")
        
        print("🎉 Database fix completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to fix database: {e}")
        return False

def main():
    """Main function"""
    print("🔧 Database Confidence Field Fix")
    print("=" * 40)
    
    if fix_confidence_fields():
        print("\n✅ Fix completed successfully!")
        print("You can now run the server without confidence errors.")
    else:
        print("\n❌ Fix failed!")
        print("Please check the error messages above.")

if __name__ == "__main__":
    main()