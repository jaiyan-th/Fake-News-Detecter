# backend/db/mongo_client.py

from pymongo import MongoClient

def get_mongo_collection():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["fakenews_db"]
    collection = db["predictions"]
    return collection
