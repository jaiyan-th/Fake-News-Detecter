#!/usr/bin/env python3
"""
Add sample data to test the dashboard
"""

from pymongo import MongoClient
import datetime

def add_sample_data():
    """Add sample prediction data"""
    try:
        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017/")
        db = client.fake_news_app
        
        print("🔧 Adding sample data for dashboard testing...")
        
        # Sample predictions
        sample_predictions = [
            {
                "username": "test_user",
                "news": "Scientists at MIT have developed a breakthrough AI system that can detect deepfake videos with 99% accuracy.",
                "prediction": "REAL",
                "confidence": 0.92,
                "timestamp": datetime.datetime.now() - datetime.timedelta(hours=1),
                "source": "Tech News",
                "category": "Technology",
                "tags": ["technology", "science"],
                "model_version": "1.0"
            },
            {
                "username": "test_user",
                "news": "BREAKING: Aliens land in Times Square demanding to speak with world leaders.",
                "prediction": "FAKE",
                "confidence": 0.96,
                "timestamp": datetime.datetime.now() - datetime.timedelta(minutes=30),
                "source": "Social Media",
                "category": "General",
                "tags": ["conspiracy"],
                "model_version": "1.0"
            },
            {
                "username": "test_user",
                "news": "Local bakery wins national award for best sourdough bread after 50 years of traditional methods.",
                "prediction": "REAL",
                "confidence": 0.88,
                "timestamp": datetime.datetime.now() - datetime.timedelta(minutes=15),
                "source": "Local News",
                "category": "Business",
                "tags": ["business", "local"],
                "model_version": "1.0"
            },
            {
                "username": "demo_user",
                "news": "Government officials confirm secret alien technology has been used in smartphones for decades.",
                "prediction": "FAKE",
                "confidence": 0.94,
                "timestamp": datetime.datetime.now() - datetime.timedelta(hours=2),
                "source": "Conspiracy Site",
                "category": "General",
                "tags": ["conspiracy", "technology"],
                "model_version": "1.0"
            },
            {
                "username": "demo_user",
                "news": "New study shows regular exercise can reduce risk of heart disease by up to 35%.",
                "prediction": "REAL",
                "confidence": 0.89,
                "timestamp": datetime.datetime.now() - datetime.timedelta(hours=3),
                "source": "Medical Journal",
                "category": "Health",
                "tags": ["health", "science"],
                "model_version": "1.0"
            }
        ]
        
        # Insert sample data
        result = db.predictions.insert_many(sample_predictions)
        print(f"✅ Added {len(result.inserted_ids)} sample predictions")
        
        # Check total count
        total_count = db.predictions.count_documents({})
        print(f"📊 Total predictions in database: {total_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to add sample data: {e}")
        return False

if __name__ == "__main__":
    add_sample_data()