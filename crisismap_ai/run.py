"""
Main entry point for CrisisMap AI.
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a shell command."""
    print(f"\n{description}...")
    try:
        # Use PowerShell-compatible command separator
        if "&&" in command:
            command = command.replace("&&", ";")
            
        process = subprocess.run(command, check=True, shell=True)
        return process.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        return e.returncode
        
def setup_directories():
    """Create necessary directories if they don't exist."""
    base_dir = Path(__file__).parent
    
    # Create directories
    directories = [
        base_dir / 'templates',
        base_dir / 'static',
        base_dir / 'static/css',
        base_dir / 'static/js',
        base_dir / 'output'
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True)
        print(f"Ensured directory exists: {directory}")

def setup_mongodb():
    """Set up MongoDB connection and vector search index."""
    print("\nSetting up MongoDB and vector search index...")
    
    # First try our specialized vector index creation script
    try:
        import create_vector_index
        success = create_vector_index.main()
        if success:
            return 0
    except ImportError:
        print("create_vector_index.py not found, falling back to mongo_setup.py")
    except Exception as e:
        print(f"Error running create_vector_index.py: {e}")
        print("Falling back to mongo_setup.py")
    
    # Fall back to the original setup script
    return run_command("python mongo_setup.py", "Setting up MongoDB and vector search")

def ingest_data():
    """Run the data ingestion process."""
    return run_command("python main.py --action ingest", "Ingesting data")

def load_one_dataset(dataset_name, limit=None):
    """Load a specific dataset."""
    limit_arg = f"--limit {limit}" if limit else ""
    return run_command(f"python main.py --action ingest --dataset {dataset_name} {limit_arg}", f"Loading {dataset_name} dataset")

def create_vector_index():
    """Create the MongoDB vector search index."""
    try:
        import create_vector_index
        success = create_vector_index.main()
        return 0 if success else 1
    except ImportError:
        return run_command("python main.py --action create-index", "Creating vector search index")

def search():
    """Run a search query."""
    query = input("Enter your search query: ")
    return run_command(f"python main.py --action search --query \"{query}\"", "Searching")

def start_server():
    """Start the API server."""
    # First ensure the setup is complete
    setup_directories()
    setup_mongodb()
    
    print("\nStarting CrisisMap AI server...")
    print("You can access the web interface at http://localhost:8000/")
    print("Press Ctrl+C to stop the server")
    
    return run_command("python main.py --action server", "Starting API server")

def print_usage():
    """Print usage instructions."""
    print("""
CrisisMap AI Usage:
------------------
1. setup:        Set up MongoDB and create vector search index
2. ingest:       Ingest all datasets
3. load:         Load a specific dataset (will prompt for dataset name)
4. create-index: Create the MongoDB vector search index
5. search:       Run a search query (will prompt for query)
6. server:       Start the API server
7. test:         Run a basic test with a sample query
0. exit:         Exit the application
    """)

def test():
    """Run a basic test with a sample query."""
    print("\nRunning a basic test...")
    
    # Directly use the main.py script with test action
    return run_command("python main.py --action test --query \"Tell me about recent earthquakes\"", "Testing system")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="CrisisMap AI")
    parser.add_argument('action', nargs='?', help="Action to perform")
    
    args = parser.parse_args()
    
    if args.action:
        if args.action == "ingest":
            return ingest_data()
        elif args.action == "create-index":
            return create_vector_index()
        elif args.action == "search":
            return search()
        elif args.action == "server":
            return start_server()
        elif args.action == "setup":
            setup_directories()
            return setup_mongodb()
        elif args.action == "test":
            return test()
        else:
            print(f"Unknown action: {args.action}")
            print_usage()
            return 1
    
    while True:
        print_usage()
        choice = input("\nSelect an option (0-7): ")
        
        if choice == "0":
            print("Exiting...")
            break
        elif choice == "1":
            setup_directories()
            setup_mongodb()
        elif choice == "2":
            ingest_data()
        elif choice == "3":
            dataset = input("Enter dataset name (who, emdat, tweets, earthquake, volcano, floods, tsunami): ")
            limit = input("Enter record limit (or press Enter for all): ")
            limit = int(limit) if limit.strip() else None
            load_one_dataset(dataset, limit)
        elif choice == "4":
            create_vector_index()
        elif choice == "5":
            search()
        elif choice == "6":
            start_server()
        elif choice == "7":
            test()
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    sys.exit(main()) 