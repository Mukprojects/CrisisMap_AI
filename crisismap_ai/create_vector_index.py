"""
Create vector search index for MongoDB Atlas.

This script creates the vector search index required for the CrisisMap AI
application to work properly with MongoDB Atlas.
"""
import sys
import pymongo
from pathlib import Path
import json
import time
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

# Import configuration
from config import MONGODB_URI, DB_NAME, CRISIS_COLLECTION, VECTOR_INDEX_NAME, VECTOR_DIMENSION

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_vector_index():
    """Create vector search index for MongoDB Atlas."""
    logger.info("Creating vector search index...")
    
    # Connect to MongoDB
    try:
        client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        logger.info("Connected to MongoDB successfully!")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return False
    
    # Get database and collection
    db = client[DB_NAME]
    
    # Check if Atlas Search is available
    try:
        # Try listing search indexes
        db.command({"listSearchIndexes": CRISIS_COLLECTION})
        logger.info("Atlas Search is available on this cluster.")
    except pymongo.errors.OperationFailure as e:
        if "Atlas Search is not enabled" in str(e):
            logger.error("Atlas Search is not enabled on this cluster.")
            logger.error("Please enable Atlas Search in your MongoDB Atlas cluster settings.")
            logger.error("Go to: https://cloud.mongodb.com")
            logger.error("Select your cluster > Search tab > Create Search Index")
            return False
        else:
            logger.error(f"Error checking search indexes: {e}")
    
    # Check if index already exists
    try:
        indexes = db.command({"listSearchIndexes": CRISIS_COLLECTION})
        for index in indexes.get('searchIndexes', []):
            if index.get('name') == VECTOR_INDEX_NAME:
                logger.info(f"Vector search index '{VECTOR_INDEX_NAME}' already exists.")
                return True
    except Exception as e:
        logger.error(f"Error checking existing indexes: {e}")
    
    # Create the vector search index
    try:
        # Define the index
        index_definition = {
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
        
        # Create the index
        db.command({
            "createSearchIndex": CRISIS_COLLECTION,
            "name": VECTOR_INDEX_NAME,
            "definition": index_definition
        })
        
        logger.info(f"Vector search index '{VECTOR_INDEX_NAME}' created successfully!")
        
        # Wait for the index to be built
        logger.info("Waiting for index to be built (this may take a few minutes)...")
        for _ in range(10):
            try:
                status = db.command({"listSearchIndexes": CRISIS_COLLECTION})
                for index in status.get('searchIndexes', []):
                    if index.get('name') == VECTOR_INDEX_NAME:
                        state = index.get('status', 'PENDING')
                        logger.info(f"Index status: {state}")
                        if state == "READY":
                            logger.info("Index is ready!")
                            return True
            except Exception as e:
                logger.error(f"Error checking index status: {e}")
            
            time.sleep(10)  # Wait 10 seconds before checking again
        
        logger.warning("Index creation is taking longer than expected.")
        logger.warning("You can continue with the application, but vector search may not work immediately.")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create vector search index: {e}")
        return False

def main():
    """Main entry point."""
    success = create_vector_index()
    if success:
        logger.info("Vector search index setup completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Load data: python run.py load")
        logger.info("2. Start the server: python run.py server")
    else:
        logger.error("Failed to set up vector search index.")
        logger.error("\nTroubleshooting steps:")
        logger.error("1. Check if MongoDB Atlas is accessible")
        logger.error("2. Make sure Atlas Search is enabled for your cluster")
        logger.error("3. Verify that your cluster is M0 (free) or higher")
        logger.error("4. Follow the guide at: https://www.mongodb.com/docs/atlas/atlas-search/enable-disable/")
    
    return success

if __name__ == "__main__":
    sys.exit(0 if main() else 1) 