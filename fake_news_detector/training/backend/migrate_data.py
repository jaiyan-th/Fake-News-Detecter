"""
Data Migration Script for Card Grid UI
Ensures existing prediction data is compatible with new card format
"""

import os
import sys
import datetime
from pymongo import MongoClient
from bson import ObjectId

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def connect_to_database():
    """Connect to MongoDB database"""
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client.fake_news_app
        return db
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        return None

def extract_title_from_text(text, max_length=100):
    """Extract a title from news text"""
    import re
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', text.strip())
    if sentences:
        title = sentences[0].strip()
        # Clean up and truncate
        title = re.sub(r'\s+', ' ', title)
        if len(title) > max_length:
            title = title[:max_length].rsplit(' ', 1)[0] + '...'
        return title
    return "News Article"

def extract_tags_from_text(text, max_tags=3):
    """Extract relevant tags from news text"""
    keywords = ['politics', 'health', 'technology', 'sports', 'business', 'entertainment', 'science']
    text_lower = text.lower()
    found_tags = [tag for tag in keywords if tag in text_lower]
    return found_tags[:max_tags]

def migrate_predictions(db):
    """Migrate existing predictions to include card-compatible fields"""
    predictions_collection = db.predictions
    
    # Find predictions that need migration (missing card fields)
    predictions_to_migrate = predictions_collection.find({
        "$or": [
            {"confidence": {"$exists": False}},
            {"source": {"$exists": False}},
            {"category": {"$exists": False}},
            {"tags": {"$exists": False}}
        ]
    })
    
    migrated_count = 0
    
    for prediction in predictions_to_migrate:
        try:
            # Prepare update fields
            update_fields = {}
            
            # Add confidence if missing (default based on prediction)
            if "confidence" not in prediction:
                # Simulate confidence based on prediction type
                if prediction.get("prediction") == "REAL":
                    update_fields["confidence"] = 0.85
                else:
                    update_fields["confidence"] = 0.78
            
            # Add source if missing
            if "source" not in prediction:
                update_fields["source"] = "User Submission"
            
            # Add category if missing
            if "category" not in prediction:
                update_fields["category"] = "General"
            
            # Add tags if missing
            if "tags" not in prediction:
                update_fields["tags"] = extract_tags_from_text(prediction.get("news", ""))
            
            # Add model version if missing
            if "model_version" not in prediction:
                update_fields["model_version"] = "1.0"
            
            # Update the document
            if update_fields:
                predictions_collection.update_one(
                    {"_id": prediction["_id"]},
                    {"$set": update_fields}
                )
                migrated_count += 1
                
        except Exception as e:
            print(f"Failed to migrate prediction {prediction.get('_id')}: {e}")
    
    return migrated_count

def create_sample_data(db):
    """Create sample data for testing if no data exists"""
    predictions_collection = db.predictions
    
    # Check if we have any data
    if predictions_collection.count_documents({}) > 0:
        print("Existing data found, skipping sample data creation")
        return 0
    
    sample_articles = [
        {
            "news": "Scientists have discovered a new species of butterfly in the Amazon rainforest. The butterfly, named Heliconius amazonia, has unique wing patterns that help it blend with local flowers. Researchers from the University of São Paulo spent three years studying the species before confirming it as new to science.",
            "prediction": "REAL",
            "confidence": 0.92,
            "username": "researcher_jane",
            "timestamp": datetime.datetime.now() - datetime.timedelta(days=2),
            "source": "Science Journal",
            "category": "Science",
            "tags": ["science", "nature"],
            "model_version": "1.0"
        },
        {
            "news": "Breaking: Aliens have landed in Central Park and are demanding to speak with world leaders. Witnesses report seeing flying saucers and strange beings with green skin. The government is allegedly covering up the incident.",
            "prediction": "FAKE",
            "confidence": 0.95,
            "username": "news_checker",
            "timestamp": datetime.datetime.now() - datetime.timedelta(days=1),
            "source": "Social Media",
            "category": "General",
            "tags": ["politics"],
            "model_version": "1.0"
        },
        {
            "news": "Local bakery wins national award for best sourdough bread. The family-owned business has been serving the community for over 50 years and uses traditional fermentation methods passed down through generations.",
            "prediction": "REAL",
            "confidence": 0.88,
            "username": "local_reporter",
            "timestamp": datetime.datetime.now() - datetime.timedelta(hours=12),
            "source": "Local News",
            "category": "Business",
            "tags": ["business"],
            "model_version": "1.0"
        },
        {
            "news": "New study reveals that drinking coffee can make you immortal. Scientists claim that people who drink 10 cups of coffee daily will never age and can live forever. The study was conducted on 5 people over 2 weeks.",
            "prediction": "FAKE",
            "confidence": 0.89,
            "username": "fact_checker",
            "timestamp": datetime.datetime.now() - datetime.timedelta(hours=6),
            "source": "Dubious Website",
            "category": "Health",
            "tags": ["health"],
            "model_version": "1.0"
        },
        {
            "news": "Tech company announces breakthrough in renewable energy storage. The new battery technology can store solar energy for up to 30 days with 95% efficiency. Commercial production is expected to begin next year.",
            "prediction": "REAL",
            "confidence": 0.91,
            "username": "tech_analyst",
            "timestamp": datetime.datetime.now() - datetime.timedelta(hours=3),
            "source": "Tech News",
            "category": "Technology",
            "tags": ["technology"],
            "model_version": "1.0"
        }
    ]
    
    # Insert sample data
    result = predictions_collection.insert_many(sample_articles)
    return len(result.inserted_ids)

def verify_migration(db):
    """Verify that migration was successful"""
    predictions_collection = db.predictions
    
    # Check total count
    total_count = predictions_collection.count_documents({})
    
    # Check for required fields
    missing_confidence = predictions_collection.count_documents({"confidence": {"$exists": False}})
    missing_source = predictions_collection.count_documents({"source": {"$exists": False}})
    missing_tags = predictions_collection.count_documents({"tags": {"$exists": False}})
    
    print(f"\nMigration Verification:")
    print(f"Total predictions: {total_count}")
    print(f"Missing confidence: {missing_confidence}")
    print(f"Missing source: {missing_source}")
    print(f"Missing tags: {missing_tags}")
    
    # Sample a few records to verify structure
    sample_records = list(predictions_collection.find().limit(3))
    print(f"\nSample records structure:")
    for i, record in enumerate(sample_records, 1):
        print(f"Record {i} fields: {list(record.keys())}")
    
    return missing_confidence == 0 and missing_source == 0 and missing_tags == 0

def main():
    """Main migration function"""
    print("Starting data migration for Card Grid UI...")
    
    # Connect to database
    db = connect_to_database()
    if not db:
        print("Failed to connect to database. Exiting.")
        return False
    
    try:
        # Run migration
        print("Migrating existing predictions...")
        migrated_count = migrate_predictions(db)
        print(f"Migrated {migrated_count} predictions")
        
        # Create sample data if needed
        print("Creating sample data if needed...")
        sample_count = create_sample_data(db)
        if sample_count > 0:
            print(f"Created {sample_count} sample records")
        
        # Verify migration
        print("Verifying migration...")
        success = verify_migration(db)
        
        if success:
            print("\n✅ Migration completed successfully!")
            print("The card grid UI is ready to use with existing data.")
        else:
            print("\n❌ Migration verification failed!")
            print("Some records may be missing required fields.")
        
        return success
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)