"""
Database operations for CrisisMap AI.
"""
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from bson.objectid import ObjectId
import logging
import json
from datetime import datetime

# Add parent directory to system path for imports
sys.path.append(str(Path(__file__).parent.parent))
from database.db_connection import get_db_connection
from embedding.embedding_generator import get_embedding_generator
from config import VECTOR_DIMENSION, VECTOR_INDEX_NAME

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CrisisEventOperations:
    """Class for performing operations on crisis events."""
    
    def __init__(self):
        """Initialize with database connection."""
        self.db_conn = get_db_connection()
        # Try to connect but don't fail if connection fails
        try:
            self.collection = self.db_conn.get_collection()
        except Exception as e:
            logger.warning(f"Could not connect to database: {e}")
            self.collection = None
        
        # Initialize embedding generator
        self.embedding_generator = get_embedding_generator()
        
    def is_db_available(self):
        """Check if database is available."""
        return self.db_conn.is_connected() and self.collection is not None
        
    def insert_crisis_event(self, crisis_event: Dict[str, Any]) -> Optional[str]:
        """
        Insert a crisis event into the database.
        
        Args:
            crisis_event: Dictionary containing crisis event data
            
        Returns:
            Inserted document ID or None if operation failed
        """
        if not self.is_db_available():
            logger.warning("Database not available. Cannot insert crisis event.")
            return None
            
        try:
            # Generate embedding for the crisis event
            text_to_embed = f"{crisis_event.get('title', '')} {crisis_event.get('summary', '')} {crisis_event.get('text', '')}"
            embedding = self.embedding_generator.generate_embedding(text_to_embed)
            
            # Add embedding to crisis event
            crisis_event['embedding'] = embedding
            
            # Insert into database
            result = self.collection.insert_one(crisis_event)
            
            logger.info(f"Inserted crisis event with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error inserting crisis event: {e}")
            return None
    
    def insert_many_crisis_events(self, events: List[Dict[str, Any]]) -> List[str]:
        """
        Insert multiple crisis events into the database.
        
        Args:
            events: List of dictionaries containing crisis event data
            
        Returns:
            List of inserted document IDs
        """
        if not self.is_db_available():
            logger.warning("Database not available. Cannot insert crisis events.")
            return []
            
        try:
            # Generate embeddings for each event
            for event in events:
                text_to_embed = f"{event.get('title', '')} {event.get('summary', '')} {event.get('text', '')}"
                embedding = self.embedding_generator.generate_embedding(text_to_embed)
                event['embedding'] = embedding
            
            # Insert into database
            result = self.collection.insert_many(events)
            
            # Convert ObjectIds to strings
            inserted_ids = [str(id) for id in result.inserted_ids]
            
            logger.info(f"Inserted {len(inserted_ids)} crisis events")
            return inserted_ids
            
        except Exception as e:
            logger.error(f"Error inserting crisis events: {e}")
            return []
    
    def update_crisis_event(self, event_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update a crisis event in the database.
        
        Args:
            event_id: ID of the crisis event to update
            update_data: Dictionary containing updated data
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_db_available():
            logger.warning("Database not available. Cannot update crisis event.")
            return False
            
        try:
            # Validate embedding if present
            if 'embedding' in update_data and len(update_data['embedding']) != VECTOR_DIMENSION:
                raise ValueError(f"Embedding must have exactly {VECTOR_DIMENSION} dimensions")
                
            # If content changed, regenerate embedding
            if any(field in update_data for field in ['title', 'summary', 'text']):
                # Get the full event first
                event = self.get_crisis_event(event_id)
                if not event:
                    return False
                    
                # Merge with updates
                event.update(update_data)
                
                # Generate new embedding
                text_to_embed = f"{event.get('title', '')} {event.get('summary', '')} {event.get('text', '')}"
                embedding = self.embedding_generator.generate_embedding(text_to_embed)
                update_data['embedding'] = embedding
                
            # Update document
            result = self.collection.update_one(
                {'_id': ObjectId(event_id)},
                {'$set': update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating crisis event: {e}")
            return False
    
    def delete_crisis_event(self, event_id: str) -> bool:
        """
        Delete a crisis event from the database.
        
        Args:
            event_id: ID of the crisis event to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_db_available():
            logger.warning("Database not available. Cannot delete crisis event.")
            return False
            
        try:
            result = self.collection.delete_one({'_id': ObjectId(event_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting crisis event: {e}")
            return False
    
    def get_crisis_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a crisis event by ID.
        
        Args:
            event_id: ID of the crisis event to retrieve
            
        Returns:
            Event data or None if not found
        """
        if not self.is_db_available():
            logger.warning("Database not available. Cannot get crisis event.")
            return None
            
        try:
            event = self.collection.find_one({'_id': ObjectId(event_id)})
            if event:
                # Convert ObjectId to string
                event['_id'] = str(event['_id'])
                return event
            return None
        except Exception as e:
            logger.error(f"Error retrieving crisis event: {e}")
            return None
    
    def get_all_crisis_events(self, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Get all crisis events with pagination.
        
        Args:
            limit: Maximum number of events to return
            skip: Number of events to skip
            
        Returns:
            List of crisis events
        """
        if not self.is_db_available():
            logger.warning("Database not available. Cannot get crisis events.")
            return []
            
        try:
            events = list(self.collection.find().skip(skip).limit(limit))
            
            # Convert ObjectIds to strings
            for event in events:
                event['_id'] = str(event['_id'])
                
            return events
        except Exception as e:
            logger.error(f"Error retrieving crisis events: {e}")
            return []
            
    def search_by_vector(self, query_vector: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform vector search for similar crisis events.
        
        Args:
            query_vector: Embedding vector to search for
            limit: Maximum number of results to return
            
        Returns:
            List of matching crisis events
        """
        if not self.is_db_available():
            logger.warning("Database not available. Cannot perform vector search.")
            return []
            
        try:
            # Validate query vector
            if len(query_vector) != VECTOR_DIMENSION:
                logger.warning(f"Query vector has {len(query_vector)} dimensions, expected {VECTOR_DIMENSION}. Resizing...")
                # Resize the vector instead of failing
                if len(query_vector) > VECTOR_DIMENSION:
                    query_vector = query_vector[:VECTOR_DIMENSION]
                else:
                    # Pad with zeros
                    query_vector = query_vector + [0.0] * (VECTOR_DIMENSION - len(query_vector))
                
            try:
                # Perform vector search
                pipeline = [
                    {
                        "$search": {
                            "index": VECTOR_INDEX_NAME,
                            "knnBeta": {
                                "vector": query_vector,
                                "path": "embedding",
                                "k": limit
                            }
                        }
                    },
                    {
                        "$project": {
                            "_id": 1,
                            "title": 1,
                            "summary": 1,
                            "text": 1,
                            "location": 1,
                            "category": 1,
                            "source": 1,
                            "date": 1,
                            "data": 1,
                            "score": { "$meta": "searchScore" }
                        }
                    }
                ]
                
                results = list(self.collection.aggregate(pipeline))
                
                if not results:
                    logger.warning("Vector search returned no results. Falling back to regular find.")
                    results = list(self.collection.find().limit(limit))
                    
            except Exception as e:
                logger.error(f"Vector search failed: {e}. Falling back to regular find.")
                # Fallback to regular find if vector search fails
                results = list(self.collection.find().limit(limit))
            
            # Convert ObjectIds to strings
            for result in results:
                result['_id'] = str(result['_id'])
                
            return results
        except Exception as e:
            logger.error(f"Error performing vector search: {e}")
            return []
            
    def search_by_text(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform text search for crisis events.
        
        Args:
            query: Text query to search for
            limit: Maximum number of results to return
            
        Returns:
            List of matching crisis events
        """
        if not self.is_db_available():
            logger.warning("Database not available. Cannot perform text search.")
            return []
            
        try:
            # Use embedding generator to perform semantic search
            results = self.search_by_vector(
                self.embedding_generator.generate_embedding(query),
                limit=limit
            )
            
            return results
        except Exception as e:
            logger.error(f"Error performing text search: {e}")
            return []

# Create a singleton instance
crisis_event_ops = CrisisEventOperations()

def get_crisis_event_ops():
    """Get the crisis event operations singleton."""
    return crisis_event_ops 