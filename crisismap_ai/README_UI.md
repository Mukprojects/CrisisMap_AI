# CrisisMap AI Web Interface Guide

This document explains how to run and use the new CrisisMap AI web interface with LLM-powered responses.

## Overview

The web interface allows users to ask natural language questions about crisis events, and the system will:
1. Convert the query into an embedding
2. Search the MongoDB database for relevant crisis events
3. Use a language model to generate a comprehensive response based on the found data
4. Return the results in a user-friendly web interface

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up the directory structure (creates templates and static folders):
   ```bash
   python run.py setup
   ```

3. Make sure your MongoDB connection is configured correctly in `config.py`

4. If you haven't already loaded data, ingest some datasets:
   ```bash
   python run.py ingest  # Load all datasets
   # OR
   python main.py --action ingest --dataset earthquake  # Load specific dataset
   ```

5. Create the vector search index if it doesn't exist:
   ```bash
   python run.py create-index
   ```

## Starting the Web Server

Run the following command to start the web server:

```bash
python run.py server
```

This will start the FastAPI server with the web interface. By default, it will run on `http://0.0.0.0:8000`.

## Using the Web Interface

1. Open a web browser and navigate to `http://localhost:8000`

2. Enter your query in the search box. Example questions:
   - "What were the major impacts of the 2011 Japan tsunami?"
   - "Tell me about recent earthquakes in Turkey"
   - "How many casualties were there in the California wildfires of 2020?"
   - "What are the health impacts of flooding in Bangladesh?"

3. Click "Search" to send your query

4. View the AI-generated response based on the crisis data

## Technical Details

The web interface is built with:
- FastAPI for the backend API
- Jinja2 for HTML templates
- Vanilla JavaScript for frontend functionality

The LLM response generation uses:
- Sentence Transformers for embeddings
- Hugging Face Transformers for text generation
- MongoDB Vector Search for similarity search

## Troubleshooting

If you encounter any issues:

1. Check the MongoDB connection string in `config.py`
2. Ensure all dependencies are installed correctly
3. Verify that the datasets have been loaded
4. Check that the vector search index has been created
5. Look at the server logs for any error messages

If you see "command not found" errors for the vector index creation, make sure your MongoDB Atlas cluster supports vector search (requires M10 or higher tier). 