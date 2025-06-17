import sys
import logging
from pathlib import Path
import traceback

# Add the parent directory to the Python path for imports
sys.path.append(str(Path(__file__).parent))

# Import the LLM response generator
from crisismap_ai.models.llm_response import get_llm_response_generator
from crisismap_ai.web_scraper import get_web_scraper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_full_api_response():
    """Test the full API response with the web scraper and response generator."""
    try:
        # Define test query
        test_query = "war situation iran and israel"
        
        print("Starting test...")
        
        # Get the LLM response generator and web scraper
        print("Getting LLM response generator...")
        response_generator = get_llm_response_generator()
        print("Getting web scraper...")
        web_scraper = get_web_scraper()
        
        # Get web data
        print(f"Searching for web data for query: {test_query}")
        web_data = web_scraper.search_disaster_info(test_query, max_results=3)
        print(f"Found {len(web_data)} web results")
        
        # Print web data
        print("\n=== WEB DATA ===")
        for i, data in enumerate(web_data):
            print(f"Result {i+1}:")
            for key, value in data.items():
                if key == "content":
                    print(f"  {key}: {value[:100]}..." if len(value) > 100 else f"  {key}: {value}")
                else:
                    print(f"  {key}: {value}")
            print()
        
        # Generate response with just web data (no DB results needed for this test)
        print("Generating response...")
        response = response_generator.generate_response(test_query, [], web_data)
        
        # Print the response
        print("\n=== FORMATTED API RESPONSE ===")
        print(response)
        
        # Print some statistics
        print("\n=== RESPONSE STATS ===")
        print(f"Response length: {len(response)}")
        print(f"Number of sentences: {response.count('.')}")
        
        # Check if the common formatting issues are fixed
        lower_response = response.lower()
        print("\n=== FORMATTING CHECK ===")
        print(f"Contains lowercase 'israel': {'israel ' in lower_response or ' israel.' in lower_response}")
        print(f"Contains lowercase 'iran': {'iran ' in lower_response or ' iran.' in lower_response}")
        print(f"Contains lowercase starting sentences: {any(s.strip() and s.strip()[0].islower() for s in response.split('.') if s.strip())}")
        
    except Exception as e:
        print(f"Error: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    test_full_api_response() 