# CrisisMap AI with Phi-3-mini-4k-instruct

This guide explains how to run the CrisisMap AI application with the Microsoft Phi-3-mini-4k-instruct model for generating responses to crisis-related queries.

## System Requirements

- Python 3.8+
- CUDA-compatible GPU with at least 4GB VRAM (recommended)
- 16GB+ RAM
- MongoDB Atlas account (with vector search capability)

## Step-by-Step Setup

### 1. Install Dependencies

First, install all required packages:

```bash
cd crisismap_ai
pip install -r requirements.txt
```

### 2. Set Up Directories

Create the necessary directories for templates and static files:

```bash
python run.py setup
```

### 3. Verify MongoDB Connection

Make sure your MongoDB connection string in `config.py` is correct. The URI should include proper URL encoding for special characters in the password.

### 4. Load Crisis Data

If you haven't already loaded data, ingest some datasets:

```bash
# Load a specific dataset with a limit to avoid memory issues
python main.py --action ingest --dataset earthquake --limit 100

# You can also load other datasets:
python main.py --action ingest --dataset volcano --limit 100
python main.py --action ingest --dataset floods --limit 100
python main.py --action ingest --dataset tsunami --limit 100
```

### 5. Create Vector Search Index

Create the vector search index in MongoDB:

```bash
python run.py create-index
```

### 6. Start the Server

Launch the FastAPI server:

```bash
python run.py server
```

The server will start on `http://0.0.0.0:8000` by default.

## Using the Web Interface

1. Open your browser and navigate to `http://localhost:8000`

2. Type your question about crisis events in the search box, for example:
   - "How many casualties were there in the California wildfires of 2020?"
   - "What were the impacts of the 2011 Japan tsunami?"
   - "Tell me about recent earthquakes in Turkey"

3. Click "Search" to submit your query

4. The Phi-3-mini-4k-instruct model will process your query, find relevant crisis data, and generate a response

## Troubleshooting

### Model Loading Issues

If you encounter errors loading the Phi-3 model:

1. Check your GPU memory - the model requires approximately 3-4GB VRAM
2. Try running with CPU only by modifying the `device` variable in `llm_response.py`
3. Ensure you have the latest versions of transformers, torch, and accelerate

### No Relevant Results

If the system can't find relevant crisis data:

1. Make sure you've loaded data with the ingest command
2. Verify the MongoDB connection is working
3. Check that the vector search index was created successfully
4. Try a different query related to the datasets you've loaded

### Server Startup Errors

If the server fails to start:

1. Check for port conflicts (default is 8000)
2. Ensure all dependencies are installed correctly
3. Verify the MongoDB connection string is correct
4. Check that the static and templates directories exist

## Advanced Configuration

You can modify the following settings in `config.py`:

- `RESPONSE_MODEL`: The Hugging Face model ID for response generation
- `EMBEDDING_MODEL`: The model used for generating vector embeddings
- `API_HOST` and `API_PORT`: Server host and port settings

## Performance Optimization

For better performance on limited hardware:

1. Load fewer documents (use the `--limit` parameter)
2. Adjust the `max_new_tokens` parameter in `llm_response.py` to control response length
3. Consider using a smaller embedding model if vector generation is slow 