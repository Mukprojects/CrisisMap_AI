"""
Test script for LLM response functionality.
"""
import sys
import argparse
from pathlib import Path

# Add parent directory to system path for imports
sys.path.append(str(Path(__file__).parent))
from models.llm_response import get_llm_response_generator
from database.db_connection import get_db_connection
from embedding.embedding_generator import get_embedding_generator

def test_llm_response(query):
    """Test the LLM response functionality."""
    print(f"\nTesting LLM response for query: '{query}'")
    
    # Connect to the database
    print("Connecting to MongoDB...")
    db_connection = get_db_connection()
    db_connection.connect()
    print("Connected to MongoDB successfully!")
    
    # Initialize embedding generator
    print("Loading embedding model...")
    embedding_generator = get_embedding_generator()
    print("Embedding model loaded successfully!")
    
    # Get LLM response generator
    print("Loading LLM response model...")
    llm_generator = get_llm_response_generator()
    
    try:
        # Generate response
        print("\nGenerating response...\n")
        response = llm_generator.find_and_respond(query)
        
        # Print response
        print("-" * 80)
        print("QUERY:")
        print(query)
        print("\nRESPONSE:")
        print(response)
        print("-" * 80)
    except Exception as e:
        print(f"Error generating response: {e}")
    finally:
        # Close database connection
        db_connection.close()
        print("MongoDB connection closed.")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test LLM response functionality")
    parser.add_argument('query', type=str, help="Query to test")
    
    args = parser.parse_args()
    
    test_llm_response(args.query)

if __name__ == "__main__":
    main() 