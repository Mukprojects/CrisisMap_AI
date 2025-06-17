"""
MongoDB connection module for CrisisMap AI.
"""
import sys
from pathlib import Path
import pymongo
from pymongo.errors import ConnectionFailure, OperationFailure
import os
import time
import logging

# Add parent directory to system path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config import MONGODB_URI, DB_NAME, CRISIS_COLLECTION, VECTOR_INDEX_NAME, VECTOR_DIMENSION

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Handles MongoDB database connection and operations."""
    
    def __init__(self):
        """Initialize the database connection."""
        self._client = None
        self._db = None
        self._collection = None
        self._connected = False
        
    def connect(self, max_retries=3):
        """Establish connection to MongoDB with retry mechanism."""
        if self._connected:
            return True
            
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to MongoDB (attempt {attempt+1}/{max_retries})...")
                self._client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
                
                # Ping the server to verify connection
                self._client.admin.command('ping')
                logger.info("Connected to MongoDB successfully!")
                
                self._db = self._client[DB_NAME]
                self._collection = self._db[CRISIS_COLLECTION]
                self._connected = True
                
                return True
            except (ConnectionFailure, OperationFailure) as e:
                logger.error(f"Failed to connect to MongoDB (attempt {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    logger.info("Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    logger.error("All connection attempts failed.")
                    logger.error(f"Please check your MongoDB URI: {MONGODB_URI}")
                    logger.error("Make sure MongoDB Atlas is accessible and your IP is in the allowed list.")
                    logger.error("Continuing in local mode without database functionality.")
                    self._connected = False
                    return False
        
    def is_connected(self):
        """Check if connected to MongoDB."""
        if not self._connected or not self._client:
            return False
            
        try:
            # Check connection with a ping
            self._client.admin.command('ping')
            return True
        except Exception:
            self._connected = False
            return False
        
    def get_collection(self):
        """Get the crisis events collection."""
        if not self._collection:
            self.connect()
        return self._collection
    
    def create_vector_search_index(self):
        """Create vector search index for embeddings."""
        if not self._connected:
            logger.warning("Not connected to MongoDB. Skipping vector search index creation.")
            return False
            
        try:
            # Check if Atlas Search is enabled
            try:
                self._db.command({"listSearchIndexes": CRISIS_COLLECTION})
                logger.info("Atlas Search is enabled on this cluster")
            except OperationFailure as e:
                if "Atlas Search is not enabled" in str(e):
                    logger.error("❌ Atlas Search is not enabled on this cluster.")
                    logger.error("Please enable Atlas Search in your MongoDB Atlas cluster settings.")
                    logger.error("See: https://www.mongodb.com/docs/atlas/atlas-search/enable-disable/")
                    return False
            
            # Drop existing index if it exists
            try:
                self._db.command({
                    "dropSearchIndex": CRISIS_COLLECTION,
                    "name": VECTOR_INDEX_NAME
                })
                logger.info(f"Dropped existing index: {VECTOR_INDEX_NAME}")
            except OperationFailure:
                # Index doesn't exist, which is fine
                pass
            
            # Create vector search index
            self._db.command({
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
            logger.info(f"Vector search index '{VECTOR_INDEX_NAME}' created successfully!")
            return True
        except Exception as e:
            logger.error(f"Error creating vector search index: {e}")
            logger.error("Please make sure you have enabled Atlas Search in your MongoDB Atlas cluster.")
            return False
    
    def check_vector_search_index(self):
        """Check if vector search index exists."""
        if not self._connected:
            logger.warning("Not connected to MongoDB. Cannot check vector search index.")
            return False
            
        try:
            # List search indexes
            result = self._db.command({"listSearchIndexes": CRISIS_COLLECTION})
            
            # Check if our vector index exists
            for index in result.get('searchIndexes', []):
                if index.get('name') == VECTOR_INDEX_NAME:
                    logger.info(f"Vector search index '{VECTOR_INDEX_NAME}' exists.")
                    return True
                    
            logger.warning(f"Vector search index '{VECTOR_INDEX_NAME}' not found.")
            return False
        except Exception as e:
            logger.error(f"Error checking vector search index: {e}")
            return False
    
    def close(self):
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()
            self._connected = False
            logger.info("MongoDB connection closed.")

# Create a singleton instance
db_connection = DatabaseConnection()

def get_db_connection():
    """Get the database connection singleton."""
    return db_connection 