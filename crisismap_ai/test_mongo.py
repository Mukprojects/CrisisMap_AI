"""
Test script to verify MongoDB connection.
"""
import pymongo
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

def test_connection():
    """Test connection to MongoDB using the correct URI format."""
    print("Testing MongoDB connection...")
    
    # Get URI from environment variable or use a placeholder for testing
    uri = os.getenv('MONGODB_URI', 'mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority')
    
    # Print sanitized URI (hide password)
    sanitized_uri = uri.split('@')[0].split('://')[0] + '://' + uri.split('://')[1].split(':')[0] + ':******@' + uri.split('@')[1]
    print(f"Connecting with URI: {sanitized_uri}")
    
    try:
        # Set a short timeout for faster feedback
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
        
        # Force a command to check the connection
        client.admin.command('ping')
        
        print("✅ Connection successful!")
        
        # Try to list databases
        db_names = client.list_database_names()
        print("Available databases:", db_names)
        
        # Try to create the database and collection if they don't exist
        db = client.get_database("crisismap")
        collection = db.get_collection("crisis_events")
        
        # Count documents in the collection
        doc_count = collection.count_documents({})
        print(f"Collection 'crisis_events' contains {doc_count} documents")
        
        # Insert a test document if collection is empty
        if doc_count == 0:
            print("Inserting a test document...")
            test_doc = {
                "title": "Test Event",
                "summary": "This is a test crisis event",
                "category": "Test",
                "source": "MongoDB Connection Test"
            }
            result = collection.insert_one(test_doc)
            print(f"Test document inserted with ID: {result.inserted_id}")
        
        print("MongoDB connection and database access verified successfully!")
        return True
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check that the MongoDB username and password are correct")
        print("2. Ensure the cluster name and hostname are correct")
        print("3. Verify that your IP address is whitelisted in MongoDB Atlas Network Access")
        print("4. Check your network connection and any firewalls")
        return False

if __name__ == "__main__":
    success = test_connection()
    if success:
        print("\nMongoDB connection test passed!")
        sys.exit(0)  # Success
    else:
        print("\nMongoDB connection test failed.")
        sys.exit(1)  # Failure 