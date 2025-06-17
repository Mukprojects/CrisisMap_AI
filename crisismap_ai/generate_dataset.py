"""
Entry point script for generating and loading a comprehensive disaster dataset.

Usage:
    python generate_dataset.py [--count COUNT]
    
Options:
    --count COUNT    Number of synthetic records to generate (default: 5000)
"""
import sys
import argparse
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to system path for imports
sys.path.append(str(Path(__file__).parent))

def main():
    """Parse arguments and run the dataset generator."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate and load a comprehensive disaster dataset")
    parser.add_argument("--count", type=int, default=5000, 
                        help="Number of synthetic records to generate (default: 5000)")
    args = parser.parse_args()
    
    logger.info(f"Starting dataset generation with {args.count} synthetic records...")
    
    try:
        # Import the generator module
        from data_ingestion.generate_disaster_dataset import main as generator_main
        
        # Run the generator
        success = generator_main(synthetic_count=args.count)
        
        if success:
            logger.info("Dataset generation and loading completed successfully!")
            return 0
        else:
            logger.error("Dataset generation and loading failed.")
            return 1
            
    except Exception as e:
        logger.error(f"Error running dataset generator: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 