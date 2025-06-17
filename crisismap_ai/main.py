"""
Main entry point for CrisisMap AI.

This script can be used to:
1. Load and process datasets
2. Upload data to MongoDB
3. Create vector search index
4. Run the API server
5. Test the system with a query
"""
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
import uvicorn
from tqdm import tqdm
import json
import os
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
from config import API_HOST, API_PORT, VECTOR_INDEX_NAME
from data_ingestion.load_datasets import (
    load_all_datasets, load_who_dataset, load_emdat_dataset, 
    load_disaster_tweets_dataset, load_earthquake_dataset,
    load_volcano_dataset, load_floods_dataset, load_tsunami_dataset
)
from data_ingestion.data_processor import process_crisis_data, clean_crisis_data
from database.db_connection import get_db_connection
from database.db_operations import get_crisis_event_ops
from embedding.embedding_generator import get_embedding_generator
from models.llm_response import get_llm_response_generator
from models.summarization import get_summarizer
import mongo_setup

# MongoDB Atlas Free Tier has 512MB storage limit
MONGODB_ATLAS_FREE_TIER_WARNING = """
⚠️  WARNING: MongoDB Atlas Free Tier has a 512MB storage limit ⚠️
Loading large amounts of data may exceed this limit.
For large datasets, consider:
1. Using smaller limits (e.g. --limit 10)
2. Loading only specific datasets instead of 'all'
3. Using the local storage option instead of MongoDB
"""

def load_and_process_data(dataset: str = 'all', limit: int = None) -> List[Dict[str, Any]]:
    """
    Load and process datasets.
    
    Args:
        dataset: Which dataset to load ('all', 'who', 'emdat', 'tweets', 'earthquake', 'volcano', 'floods', 'tsunami')
        limit: Maximum number of records to load
        
    Returns:
        Processed data
    """
    logger.info(f"Loading dataset: {dataset}")
    
    # Load dataset
    if dataset == 'all':
        data = load_all_datasets()
    elif dataset == 'who':
        data = load_who_dataset()
    elif dataset == 'emdat':
        data = load_emdat_dataset()
    elif dataset == 'tweets':
        data = load_disaster_tweets_dataset(limit=limit)
    elif dataset == 'earthquake':
        data = load_earthquake_dataset(limit=limit)
    elif dataset == 'volcano':
        data = load_volcano_dataset(limit=limit)
    elif dataset == 'floods':
        data = load_floods_dataset(limit=limit)
    elif dataset == 'tsunami':
        data = load_tsunami_dataset(limit=limit)
    else:
        logger.error(f"Unknown dataset: {dataset}")
        return []
    
    # Apply limit if provided
    if limit and limit > 0 and dataset != 'all':
        data = data[:limit]
        
    # Clean data
    data = clean_crisis_data(data)
    
    # Process data
    data = process_crisis_data(data)
    
    return data

def save_to_local_file(data: List[Dict[str, Any]], filename: str = "crisis_data.json") -> bool:
    """
    Save data to a local JSON file as a fallback when MongoDB is not available.
    
    Args:
        data: List of crisis event dictionaries
        filename: Name of the file to save to
        
    Returns:
        Success status
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        
        # Save to file
        output_path = output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Saved {len(data)} events to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving data to file: {e}")
        return False

def upload_to_mongodb(data: List[Dict[str, Any]]) -> bool:
    """
    Upload data to MongoDB.
    
    Args:
        data: List of crisis event dictionaries
        
    Returns:
        Success status
    """
    # Show warning about MongoDB Atlas free tier limits
    if len(data) > 50:  # If we're uploading a lot of data
        print(MONGODB_ATLAS_FREE_TIER_WARNING)
        confirm = input("Continue with upload? (y/n): ")
        if confirm.lower() != 'y':
            logger.info("Upload cancelled by user")
            return False
    
    logger.info(f"Uploading {len(data)} events to MongoDB...")
    
    # Get database connection
    db_conn = get_db_connection()
    connected = db_conn.connect()
    
    if not connected:
        logger.warning("Could not connect to MongoDB. Saving to local file instead.")
        return save_to_local_file(data)
    
    # Create vector search index
    db_conn.create_vector_search_index()
    
    # Get crisis event operations
    crisis_ops = get_crisis_event_ops()
    
    # Insert data in batches
    batch_size = 50  # Smaller batch size to avoid overloading the server
    successful_count = 0
    
    for i in tqdm(range(0, len(data), batch_size), desc="Uploading batches"):
        batch = data[i:i+batch_size]
        try:
            inserted_ids = crisis_ops.insert_many_crisis_events(batch)
            successful_count += len(inserted_ids)
            # Small delay to avoid overwhelming the server
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Error uploading batch: {e}")
            logger.error(f"Continuing with next batch...")
    
    if successful_count > 0:
        logger.info(f"Successfully uploaded {successful_count} events to MongoDB")
        return True
    else:
        logger.error("Failed to upload any events to MongoDB")
        return False

def create_vector_index():
    """Create or recreate the vector search index."""
    logger.info("Creating vector search index...")
    
    # Get database connection
    db_conn = get_db_connection()
    connected = db_conn.connect()
    
    if not connected:
        logger.error("Could not connect to MongoDB. Cannot create vector search index.")
        return False
    
    # Create vector search index
    success = db_conn.create_vector_search_index()
    
    if success:
        logger.info(f"Vector search index '{VECTOR_INDEX_NAME}' created successfully!")
    else:
        logger.error(f"Failed to create vector search index '{VECTOR_INDEX_NAME}'")
        logger.error("Please make sure you have enabled Atlas Search in your MongoDB Atlas cluster.")
        logger.error("See: https://www.mongodb.com/docs/atlas/atlas-search/enable-disable/")
    
    return success

def run_api_server():
    """Run the FastAPI server."""
    # Setup directories
    static_dir = Path(__file__).parent / "static"
    templates_dir = Path(__file__).parent / "templates"
    static_dir.mkdir(exist_ok=True)
    templates_dir.mkdir(exist_ok=True)
    (static_dir / "css").mkdir(exist_ok=True)
    (static_dir / "js").mkdir(exist_ok=True)
    
    # Ensure vector search index exists
    db_conn = get_db_connection()
    if db_conn.connect():
        if not db_conn.check_vector_search_index():
            logger.warning("Vector search index not found, creating it now...")
            db_conn.create_vector_search_index()
    
    # Initialize embedding generator
    get_embedding_generator()
    
    # Start the server
    logger.info(f"Starting API server on {API_HOST}:{API_PORT}")
    logger.info(f"You can access the web interface at http://{API_HOST}:{API_PORT}/")
    logger.info("Press Ctrl+C to stop the server")
    
    try:
        uvicorn.run("api.app:app", host=API_HOST, port=API_PORT, reload=True)
    except Exception as e:
        logger.error(f"Error starting API server: {e}")
        return False
    
    return True

def setup_mongodb():
    """Set up MongoDB for vector search."""
    logger.info("Setting up MongoDB for vector search...")
    success = mongo_setup.main()
    return success

def test_query(query_text: str):
    """Test the system with a query."""
    logger.info(f"Testing query: '{query_text}'")
    
    # Print current working directory
    print(f"Current working directory: {os.getcwd()}")
    
    # Get database connection
    db_conn = get_db_connection()
    connected = db_conn.connect()
    
    if connected:
        # Check if there's data in the database
        crisis_ops = get_crisis_event_ops()
        events = crisis_ops.get_all_crisis_events(limit=5)
        
        # If no data, load a small sample
        if not events:
            logger.info("No data found in database. Loading a small sample dataset...")
            # Load and process earthquake data (limited to 5 records)
            data = load_and_process_data('earthquake', limit=5)
            if data:
                # Upload to MongoDB
                upload_to_mongodb(data)
    
    # Get LLM response generator
    llm_gen = get_llm_response_generator()
    
    # Generate response
    logger.info("Generating response...")
    response = llm_gen.find_and_respond(query_text)
    
    # Print response
    print("\n" + "-" * 80)
    print(f"Query: {query_text}")
    print("-" * 80)
    print(response)
    print("-" * 80)
    
    return True

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="CrisisMap AI")
    
    # Add arguments
    parser.add_argument('--action', type=str, required=True, 
                        choices=['load', 'upload', 'server', 'create-index', 'setup', 'ingest', 'test', 'search'],
                        help='Action to perform')
    parser.add_argument('--dataset', type=str, default='all', 
                        choices=['all', 'who', 'emdat', 'tweets', 'earthquake', 'volcano', 'floods', 'tsunami'],
                        help='Dataset to load (all, who, emdat, tweets, earthquake, volcano, floods, tsunami)')
    parser.add_argument('--limit', type=int, default=None,
                        help='Maximum number of records to load')
    parser.add_argument('--query', type=str, default=None,
                        help='Query to test (for test action)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show warning for large data loads with MongoDB Atlas free tier
    if args.action in ['load', 'upload', 'ingest'] and (args.dataset == 'all' or args.limit is None or args.limit > 50):
        print(MONGODB_ATLAS_FREE_TIER_WARNING)
    
    # Perform action
    if args.action in ['load', 'upload', 'ingest']:
        # Load and process data
        data = load_and_process_data(args.dataset, args.limit)
        logger.info(f"Loaded and processed {len(data)} events")
        
        if args.action == 'load':
            # Save to local file
            save_to_local_file(data)
        else:  # upload or ingest
            # Upload to MongoDB
            upload_to_mongodb(data)
        
    elif args.action == 'server':
        # Run API server
        run_api_server()
        
    elif args.action == 'create-index':
        # Create vector search index
        create_vector_index()
        
    elif args.action == 'setup':
        # Set up MongoDB
        setup_mongodb()
        
    elif args.action == 'test' or args.action == 'search':
        # Test with a query
        if args.query:
            test_query(args.query)
        else:
            query = input("Enter your query: ")
            test_query(query)
        
    else:
        logger.error(f"Unknown action: {args.action}")
        
if __name__ == "__main__":
    main() 