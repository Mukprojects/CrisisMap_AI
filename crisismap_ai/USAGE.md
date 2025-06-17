# CrisisMap AI Usage Guide

## Quick Start

We've created a simple wrapper script to make it easier to run the application. Here's how to use it:

```bash
# Set up dependencies
python run.py setup

# Load tweet dataset with 100 records (default)
python run.py load --dataset tweets --limit 100

# Start the API server
python run.py server

# Or do everything at once
python run.py all --dataset tweets --limit 100
```

This will take care of installing dependencies, loading data and starting the server in one command.

## Available Datasets

CrisisMap AI includes several crisis-related datasets:

1. `who` - World Health Organization health statistics by country
2. `emdat` - EM-DAT disaster events database
3. `tweets` - Disaster-related tweets from social media
4. `earthquake` - Global earthquake data from 1995-2023
5. `volcano` - Volcanic eruption events
6. `floods` - Historical flood events
7. `tsunami` - Tsunami events
8. `all` - Load all available datasets

Example:
```bash
python run.py load --dataset earthquake --limit 50
```

## Manual Installation

Follow these steps to set up and run CrisisMap AI.

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Load and Process Data

To load data from datasets:

```bash
python main.py --action load --dataset tweets --limit 100
```

Options:
- `--dataset`: Choose from `who`, `emdat`, `tweets`, `earthquake`, `volcano`, `floods`, `tsunami`, or `all` to load all datasets
- `--limit`: Maximum number of records to load

### 3. Upload Data to MongoDB

To upload processed data to MongoDB:

```bash
python main.py --action upload --dataset tweets --limit 100
```

If MongoDB connection fails, data will be saved to a local JSON file in the `output` directory.

### 4. Run the API Server

Start the REST API server:

```bash
python main.py --action server
```

This will start the API server on `http://0.0.0.0:8000`.

## API Endpoints

Once the server is running, you can access the following endpoints:

### Health Check
```
GET /health
```
Verifies that the API is working properly.

### Search Crisis Events
```
POST /search
```
Search for crisis events using semantic search.

Example request:
```json
{
    "query": "earthquake in California",
    "limit": 10
}
```

### Get All Crisis Events
```
GET /events?limit=100&skip=0
```
Retrieve all crisis events with pagination.

### Get Crisis Event by ID
```
GET /events/{event_id}
```
Retrieve a specific crisis event.

### Create Crisis Event
```
POST /events
```
Create a new crisis event.

Example request:
```json
{
    "title": "Flooding in Miami",
    "summary": "Heavy rainfall causes flooding in Miami neighborhoods",
    "text": "Heavy rainfall over the weekend has led to significant flooding in several Miami neighborhoods...",
    "location": "Miami, Florida",
    "category": "Flood",
    "source": "News Report",
    "date": "2023-08-15"
}
```

### Update Crisis Event
```
PUT /events/{event_id}
```
Update an existing crisis event.

### Delete Crisis Event
```
DELETE /events/{event_id}
```
Delete a crisis event.

### Summarize Text
```
POST /summarize
```
Summarize long text content.

Example request:
```json
{
    "text": "Long text content to summarize..."
}
```

## Working Offline

If no MongoDB connection is available, the system will operate in offline mode:
- Data will be saved to JSON files in the `output` directory
- The API will still be available, but some endpoints may return empty results
- You can still use the basic embedding and summarization features

## Notes

- The API documentation is available at `http://localhost:8000/docs` when the server is running
- Search uses AI-based vector embeddings for semantic search capability
- Summarization uses the T5 model to create concise summaries of long reports

## Configuration

You can configure the application by modifying the `config.py` file or by setting environment variables. Key configuration options include:

- `MONGODB_URI`: MongoDB connection string
- `DB_NAME`: MongoDB database name
- `API_HOST`: Host address for the API server (default: 0.0.0.0)
- `API_PORT`: Port number for the API server (default: 8000)
- `EMBEDDING_MODEL`: Hugging Face model for generating embeddings
- `SUMMARIZATION_MODEL`: Model for text summarization

## Loading Data

You can load data from the included datasets using the main script:

```bash
# Load all datasets
python main.py --action load --dataset all

# Load only WHO dataset
python main.py --action load --dataset who

# Load only EM-DAT dataset
python main.py --action load --dataset emdat

# Load only disaster tweets dataset
python main.py --action load --dataset tweets --limit 500
```

## Uploading Data to MongoDB

After loading data, you can upload it to MongoDB:

```bash
# Load and upload all datasets
python main.py --action upload --dataset all

# Load and upload only WHO dataset
python main.py --action upload --dataset who

# Load and upload with a limit
python main.py --action upload --dataset all --limit 1000
```

## Running the API Server

To start the API server:

```bash
python main.py --action server
```

The API will be available at `http://localhost:8000`. You can access the interactive API documentation at `http://localhost:8000/docs`.

## Testing the API

A test script is provided to verify API functionality:

```bash
# Start the API server in one terminal
python main.py --action server

# Run the tests in another terminal
python test_api.py
```

## API Endpoints

### Search Endpoints

- `POST /search` - Semantic search using vector embeddings
- `POST /search/text` - Text search using MongoDB text search

Example search request:
```json
{
  "query": "Floods in South Asia",
  "limit": 10
}
```

### Event Endpoints

- `GET /events` - Get all crisis events (with pagination)
- `GET /events/{event_id}` - Get a specific crisis event
- `POST /events` - Create a new crisis event
- `PUT /events/{event_id}` - Update an existing crisis event
- `DELETE /events/{event_id}` - Delete a crisis event

### Utility Endpoints

- `POST /summarize` - Summarize text using the T5 model
- `GET /health` - Health check endpoint

## Example Queries

Here are some example queries you can try:

- "Floods in South Asia"
- "Hurricane damage in Florida"
- "Earthquake in Japan"
- "Disease outbreak in Africa"
- "Wildfire California"
- "Conflict in Middle East"

## Using the Python Client

You can also use the API from Python code:

```python
import requests

# API URL
API_URL = "http://localhost:8000"

# Perform semantic search
response = requests.post(
    f"{API_URL}/search",
    json={"query": "Floods in Southeast Asia", "limit": 5}
)

# Process results
results = response.json()
for result in results["results"]:
    print(f"Title: {result['title']}")
    print(f"Summary: {result['summary']}")
    print(f"Location: {result.get('location', 'N/A')}")
    print(f"Score: {result.get('score', 'N/A')}")
    print("---")
``` 