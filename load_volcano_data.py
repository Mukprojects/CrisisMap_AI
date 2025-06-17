"""
Load detailed volcanic eruption data into the CrisisMap database.

This script loads a comprehensive dataset of major volcanic eruptions and 
generates additional synthetic volcanic events to enrich the database.

Usage:
    python load_volcano_data.py [--count COUNT]
    
Options:
    --count COUNT    Number of additional synthetic events to generate (default: 30)
"""
import sys
import os
from pathlib import Path

# Add the current directory to the path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Import the volcanic data generator
from crisismap_ai.data_ingestion.volcano_data_generator import main as generate_volcano_data

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load volcanic eruption data for CrisisMap AI")
    parser.add_argument("--count", type=int, default=30, help="Number of additional synthetic volcanic events to generate")
    
    args = parser.parse_args()
    
    print(f"Loading volcanic eruption data (including {args.count} synthetic events)...")
    generate_volcano_data(args.count)
    print("Volcanic data loading complete! The data is now available in your MongoDB database.") 