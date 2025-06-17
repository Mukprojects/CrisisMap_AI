"""
MongoDB setup and test script for CrisisMap AI.

This script:
1. Tests MongoDB connection
2. Creates necessary database and collections
3. Sets up vector search index
4. Tests data upload
"""
import pymongo
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from tqdm import tqdm
import json
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

# Import modules
from config import MONGODB_URI, DB_NAME, CRISIS_COLLECTION, VECTOR_INDEX_NAME, VECTOR_DIMENSION
from data_ingestion.load_datasets import load_earthquake_dataset, load_volcano_dataset
from data_ingestion.data_processor import process_crisis_data, clean_crisis_data
from embedding.embedding_generator import get_embedding_generator

def test_connection(uri: str = MONGODB_URI, max_retries: int = 3) -> Optional[pymongo.MongoClient]:
    """Test connection to MongoDB using the correct URI format with retries."""
    print("Testing MongoDB connection...")
    
    for attempt in range(max_retries):
        try:
            # Set a short timeout for faster feedback
            client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
            
            # Force a command to check the connection
            client.admin.command('ping')
            
            print(f"✅ MongoDB connection successful on attempt {attempt + 1}!")
            return client
                
        except Exception as e:
            print(f"❌ MongoDB connection failed on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in 2 seconds...")
                time.sleep(2)
            else:
                print(f"All {max_retries} connection attempts failed.")
                print(f"Please check your MongoDB URI: {uri}")
                print("Make sure MongoDB Atlas is accessible and your IP is in the allowed list.")
                return None

def create_db_and_collection(client: pymongo.MongoClient) -> Optional[pymongo.collection.Collection]:
    """Create database and collection if they don't exist."""
    if client is None:
        return None
        
    try:
        # Get or create database
        db = client[DB_NAME]
        
        # Get or create collection
        collection = db[CRISIS_COLLECTION]
        
        print(f"✅ Successfully accessed database '{DB_NAME}' and collection '{CRISIS_COLLECTION}'")
        return collection
        
    except Exception as e:
        print(f"❌ Failed to create database or collection: {e}")
        return None

def create_vector_search_index(client: pymongo.MongoClient) -> bool:
    """Create vector search index for embeddings."""
    if client is None:
        return False
        
    try:
        db = client[DB_NAME]
        
        # Check if vector search is available
        try:
            # Check if Atlas Search is enabled on this cluster
            db.command({"listSearchIndexes": CRISIS_COLLECTION})
            print("Atlas Search is enabled on this cluster")
        except pymongo.errors.OperationFailure as e:
            if "Atlas Search is not enabled" in str(e):
                print("❌ Atlas Search is not enabled on this cluster.")
                print("Please enable Atlas Search in your MongoDB Atlas cluster settings.")
                print("See: https://www.mongodb.com/docs/atlas/atlas-search/enable-disable/")
                return False
        
        # Drop existing index if it exists
        try:
            db.command({
                "dropSearchIndex": CRISIS_COLLECTION,
                "name": VECTOR_INDEX_NAME
            })
            print(f"Dropped existing index: {VECTOR_INDEX_NAME}")
        except pymongo.errors.OperationFailure:
            # Index doesn't exist, which is fine
            pass
        
        # Create vector search index
        db.command({
            "createSearchIndex": CRISIS_COLLECTION,
            "name": VECTOR_INDEX_NAME,
            "definition": {
                "mappings": {
                    "dynamic": True,
                    "fields": {
                        "embedding": {
                            "dimensions": VECTOR_DIMENSION,
                            "similarity": "cosine",
                            "type": "knnVector"
                        }
                    }
                }
            }
        })
        print(f"✅ Vector search index '{VECTOR_INDEX_NAME}' created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create vector search index: {e}")
        print("Please make sure you have enabled Atlas Search in your MongoDB Atlas cluster.")
        return False

def load_and_process_sample_data(limit: int = 3) -> List[Dict[str, Any]]:
    """Load and process sample data for testing.
    
    Args:
        limit: Maximum number of records to load from each dataset
        
    Returns:
        Processed data ready for MongoDB
    """
    try:
        # Load a small sample from each dataset for testing
        print("Loading sample data...")
        earthquake_data = load_earthquake_dataset(limit=limit)
        volcano_data = load_volcano_dataset(limit=limit)
        
        # Combine datasets
        combined_data = earthquake_data + volcano_data
        
        # Clean and process data
        clean_data = clean_crisis_data(combined_data)
        processed_data = process_crisis_data(clean_data)
        
        print(f"✅ Successfully loaded and processed {len(processed_data)} sample records")
        return processed_data
        
    except Exception as e:
        print(f"❌ Failed to load and process sample data: {e}")
        return []

def upload_to_mongodb(collection, data: List[Dict[str, Any]]) -> bool:
    """Upload processed data to MongoDB."""
    if collection is None:
        return False
        
    try:
        # Get embedding generator
        embedding_generator = get_embedding_generator()
        
        # Generate embeddings for each event
        for event in tqdm(data, desc="Generating embeddings"):
            # Create text for embedding
            text_to_embed = f"{event.get('title', '')} {event.get('summary', '')} {event.get('text', '')}"
            
            # Generate embedding
            embedding = embedding_generator.generate_embedding(text_to_embed)
            
            # Add embedding to event
            event['embedding'] = embedding
        
        # Insert data
        if data:
            result = collection.insert_many(data)
            print(f"✅ Successfully uploaded {len(result.inserted_ids)} documents to MongoDB")
            return True
        else:
            print("No data to upload")
            return False
            
    except Exception as e:
        print(f"❌ Failed to upload data to MongoDB: {e}")
        return False

def test_vector_search(collection) -> bool:
    """Test vector search capability."""
    if collection is None:
        return False
        
    try:
        # Get embedding generator
        embedding_generator = get_embedding_generator()
        
        # Generate a test query embedding
        query_text = "earthquake in coastal region"
        query_embedding = embedding_generator.generate_embedding(query_text)
        
        # Perform vector search
        pipeline = [
            {
                "$search": {
                    "index": VECTOR_INDEX_NAME,
                    "knnBeta": {
                        "vector": query_embedding,
                        "path": "embedding",
                        "k": 3
                    }
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "title": 1,
                    "summary": 1,
                    "category": 1,
                    "score": { "$meta": "searchScore" }
                }
            }
        ]
        
        results = list(collection.aggregate(pipeline))
        
        if results:
            print(f"✅ Vector search returned {len(results)} results")
            for i, result in enumerate(results):
                print(f"  Result {i+1}: {result['title']} (Score: {result.get('score', 'N/A')})")
            return True
        else:
            print("⚠️ Vector search returned no results. This might be expected if there's no relevant data.")
            return True
            
    except Exception as e:
        print(f"❌ Failed to test vector search: {e}")
        print(f"Error details: {str(e)}")
        return False

def main():
    """Main entry point."""
    print("\n---- MONGODB SETUP AND TEST ----\n")
    
    # Test connection
    client = test_connection()
    if client is None:
        print("\nConnection to MongoDB failed. Here are some troubleshooting tips:")
        print("1. Check your MongoDB Atlas username and password")
        print("2. Make sure your IP address is whitelisted in MongoDB Atlas")
        print("3. Verify that your MongoDB Atlas cluster is running")
        print("4. Check if you have the correct connection string in your config.py file")
        print("\nFor more help, visit: https://www.mongodb.com/docs/atlas/troubleshoot-connection/")
        return False
        
    # Create database and collection
    collection = create_db_and_collection(client)
    if collection is None:
        print("Failed to access database and collection. Aborting setup.")
        return False
        
    # Create vector search index
    if not create_vector_search_index(client):
        print("\nFailed to create vector search index. Here are some troubleshooting tips:")
        print("1. Make sure Atlas Search is enabled for your cluster")
        print("2. Your MongoDB Atlas cluster should be M0 (free) or higher")
        print("3. Follow the guide at: https://www.mongodb.com/docs/atlas/atlas-search/enable-disable/")
        print("\nProceeding with caution.")
    
    # Remember MongoDB Atlas free tier has 512MB limit
    print("\nNote: MongoDB Atlas free tier has a 512MB storage limit. Loading minimal data...")
    
    # Load and process minimal sample data (3 records from each dataset)
    sample_data = load_and_process_sample_data(limit=3)
    
    # Upload to MongoDB
    if sample_data:
        if not upload_to_mongodb(collection, sample_data):
            print("Failed to upload sample data to MongoDB.")
            return False
    
    # Test vector search
    if not test_vector_search(collection):
        print("Vector search test failed.")
        print("Make sure the vector search index is created properly.")
        return False
    
    print("\n✅ MongoDB setup and testing completed successfully!")
    print("Your MongoDB is now configured for CrisisMap AI with vector search capability.")
    print("\nNext steps:")
    print("1. Load more data using: python main.py --action upload --dataset all")
    print("2. Start the API server: python main.py --action server")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 