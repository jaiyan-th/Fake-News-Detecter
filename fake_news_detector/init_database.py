#!/usr/bin/env python3
"""
Database Initialization Script
Sets up MongoDB collections and indexes for optimal performance
"""

import sys
from pymongo import MongoClient, ASCENDING, DESCENDING
import datetime

def connect_to_database():
    """Connect to MongoDB"""
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client.fake_news_app
        
        # Test connection
        client.server_info()
        print("✅ Connected to MongoDB successfully")
        return db
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return None

def create_collections_and_indexes(db):
    """Create collections and indexes for better performance"""
    print("\n📊 Setting up collections and indexes...")
    
    # Predictions collection
    predictions = db.predictions
    
    # Create indexes for better query performance
    indexes = [
        # Index for timestamp queries (most common)
        [("timestamp", DESCENDING)],
        
        # Index for prediction type filtering
        [("prediction", ASCENDING)],
        
        # Index for username queries
        [("username", ASCENDING)],
        
        # Compound index for filtered queries
        [("prediction", ASCENDING), ("timestamp", DESCENDING)],
        
        # Index for content hash (deduplication)
        [("content_hash", ASCENDING)],
        
        # Text index for search functionality
        [("news", "text"), ("username", "text")]
    ]
    
    for index in indexes:
        try:
            if len(index[0]) == 2 and index[0][1] == "text":
                # Text index
                predictions.create_index(index)
                print(f"   ✅ Created text index: {index}")
            else:
                # Regular index
                predictions.create_index(index)
                print(f"   ✅ Created index: {index}")
        except Exception as e:
            print(f"   ⚠️  Index creation warning: {e}")
    
    # Users collection
    users = db.users
    
    # Create unique index on username
    try:
        users.create_index([("username", ASCENDING)], unique=True)
        print("   ✅ Created unique index on username")
    except Exception as e:
        print(f"   ⚠️  Username index warning: {e}")

def create_sample_data(db):
    """Create sample data for testing"""
    print("\n📝 Creating sample data...")
    
    predictions = db.predictions
    
    # Check if we already have data
    if predictions.count_documents({}) > 0:
        print("   ℹ️  Sample data already exists, skipping creation")
        return
    
    sample_articles = [
        {
            "news": "Scientists at MIT have developed a new artificial intelligence system that can detect fake news with 95% accuracy. The system uses advanced natural language processing techniques to analyze text patterns and cross-reference information with reliable sources.",
            "prediction": "REAL",
            "confidence": 0.92,
            "username": "tech_reporter",
            "timestamp": datetime.datetime.now() - datetime.timedelta(hours=2),
            "source": "Tech News Daily",
            "category": "Technology",
            "tags": ["technology", "science"],
            "language": "en",
            "content_hash": "abc123tech",
            "model_version": "1.0"
        },
        {
            "news": "BREAKING: Aliens have landed in Times Square and are demanding to speak with world leaders. Witnesses report seeing flying saucers and strange beings with green skin. The government is allegedly covering up the incident to prevent panic.",
            "prediction": "FAKE",
            "confidence": 0.96,
            "username": "news_checker",
            "timestamp": datetime.datetime.now() - datetime.timedelta(hours=1),
            "source": "Social Media",
            "category": "General",
            "tags": ["politics"],
            "language": "en",
            "content_hash": "def456fake",
            "model_version": "1.0"
        },
        {
            "news": "Local bakery 'Sweet Dreams' wins national award for best sourdough bread. The family-owned business has been serving the community for over 50 years and uses traditional fermentation methods passed down through generations.",
            "prediction": "REAL",
            "confidence": 0.88,
            "username": "local_reporter",
            "timestamp": datetime.datetime.now() - datetime.timedelta(minutes=30),
            "source": "Local News Network",
            "category": "Business",
            "tags": ["business"],
            "language": "en",
            "content_hash": "ghi789local",
            "model_version": "1.0"
        },
        {
            "news": "New study reveals that drinking 20 cups of coffee daily will make you immortal and give you superpowers. Scientists claim that people who follow this regimen will never age and can fly. The study was conducted on 3 people over 1 week.",
            "prediction": "FAKE",
            "confidence": 0.94,
            "username": "fact_checker",
            "timestamp": datetime.datetime.now() - datetime.timedelta(minutes=15),
            "source": "Dubious Health Blog",
            "category": "Health",
            "tags": ["health"],
            "language": "en",
            "content_hash": "jkl012health",
            "model_version": "1.0"
        },
        {
            "news": "Tesla announces breakthrough in battery technology that could revolutionize electric vehicles. The new lithium-silicon batteries can charge to 80% capacity in just 5 minutes and last for over 1 million miles. Production is expected to begin in 2025.",
            "prediction": "REAL",
            "confidence": 0.89,
            "username": "auto_journalist",
            "timestamp": datetime.datetime.now() - datetime.timedelta(minutes=5),
            "source": "Automotive Weekly",
            "category": "Technology",
            "tags": ["technology", "business"],
            "language": "en",
            "content_hash": "mno345auto",
            "model_version": "1.0"
        }
    ]
    
    try:
        result = predictions.insert_many(sample_articles)
        print(f"   ✅ Created {len(result.inserted_ids)} sample articles")
        
        # Display sample data
        print("\n📋 Sample articles created:")
        for i, article in enumerate(sample_articles, 1):
            prediction_emoji = "✅" if article["prediction"] == "REAL" else "❌"
            print(f"   {i}. {prediction_emoji} {article['prediction']} - {article['title'] if 'title' in article else article['news'][:50]}...")
            
    except Exception as e:
        print(f"   ❌ Failed to create sample data: {e}")

def create_admin_user(db):
    """Create admin user for testing"""
    print("\n👤 Creating admin user...")
    
    users = db.users
    
    # Check if admin user exists
    if users.find_one({"username": "admin"}):
        print("   ℹ️  Admin user already exists")
        return
    
    try:
        from werkzeug.security import generate_password_hash
        
        admin_user = {
            "username": "admin",
            "password": generate_password_hash("admin123"),
            "created_at": datetime.datetime.now(),
            "role": "admin"
        }
        
        users.insert_one(admin_user)
        print("   ✅ Admin user created")
        print("   📝 Username: admin")
        print("   📝 Password: admin123")
        print("   ⚠️  Change the password in production!")
        
    except ImportError:
        print("   ⚠️  Werkzeug not available, skipping admin user creation")
    except Exception as e:
        print(f"   ❌ Failed to create admin user: {e}")

def verify_setup(db):
    """Verify the database setup"""
    print("\n🔍 Verifying database setup...")
    
    # Check collections
    collections = db.list_collection_names()
    print(f"   📊 Collections: {collections}")
    
    # Check predictions count
    predictions_count = db.predictions.count_documents({})
    print(f"   📰 Predictions: {predictions_count}")
    
    # Check users count
    users_count = db.users.count_documents({})
    print(f"   👥 Users: {users_count}")
    
    # Check indexes
    predictions_indexes = list(db.predictions.list_indexes())
    print(f"   🔍 Prediction indexes: {len(predictions_indexes)}")
    
    return predictions_count > 0

def main():
    """Main initialization function"""
    print("🚀 Fake News Detector - Database Initialization")
    print("=" * 55)
    
    # Connect to database
    db = connect_to_database()
    if not db:
        print("\n❌ Cannot proceed without database connection")
        return False
    
    try:
        # Create collections and indexes
        create_collections_and_indexes(db)
        
        # Create sample data
        create_sample_data(db)
        
        # Create admin user
        create_admin_user(db)
        
        # Verify setup
        success = verify_setup(db)
        
        if success:
            print("\n🎉 Database initialization completed successfully!")
            print("\n🚀 Next steps:")
            print("   1. Start the server: python start_server.py")
            print("   2. Open browser: http://localhost:5000")
            print("   3. Test the card grid interface!")
        else:
            print("\n⚠️  Database initialization completed with warnings")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)