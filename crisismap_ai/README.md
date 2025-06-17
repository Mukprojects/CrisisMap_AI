# CrisisMap AI

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

CrisisMap AI is an advanced crisis monitoring and detection platform that leverages AI, vector search, and real-time data ingestion to provide actionable insights on global crises and natural disasters.

## Overview

CrisisMap AI addresses the growing need for real-time crisis monitoring by using cutting-edge AI technologies to process, analyze, and deliver critical information about natural disasters, disease outbreaks, conflicts, and humanitarian crises worldwide.

### Key Capabilities

- **Real-time Crisis Detection:** Identify emerging crises as they develop
- **Semantic Search:** Find relevant information using natural language queries
- **Multi-source Data Integration:** Combine data from official sources, news feeds, and social media
- **Interactive Visualizations:** Explore crisis data through intuitive interfaces
- **Automated Summarization:** Generate concise summaries of complex crisis situations
- **Scalable Architecture:** Handle millions of crisis reports with MongoDB Atlas

## Technology Stack

### Data Infrastructure

- **MongoDB Atlas:** Cloud-based document database with vector search capabilities
  - Vector embeddings for semantic search
  - Geospatial indexing for location-based queries
  - Atlas Search for advanced text search functionality
  - Scalable storage for crisis reports and embeddings

### AI & ML Components

- **LLM Integration:** Microsoft's Phi-3-mini-4k-instruct model for natural language understanding and response generation
- **Embedding Models:** Sentence-transformers/all-MiniLM-L6-v2 for generating vector representations
- **Summarization:** Google's T5-small model for creating concise summaries of crisis reports
- **Data Enrichment:** Named entity recognition and relationship extraction

### Backend & API

- **FastAPI:** High-performance web framework for the REST API
- **Uvicorn:** ASGI server for hosting the application
- **PyMongo:** MongoDB driver for Python
- **Python Ecosystem:** NumPy, tqdm, and other data processing libraries

### Data Acquisition

- **Web Scraping:** Automated collection of crisis data from authoritative sources using BeautifulSoup4
- **Dataset Integration:** Processing and normalization of multiple disaster datasets
- **Synthetic Data Generation:** Creation of supplemental crisis data for testing and development

## Architecture

CrisisMap AI follows a modular, scalable architecture:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Data Ingestion │────▶│  Data Processing│────▶│  MongoDB Atlas  │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
       ▲                                                 │
       │                                                 ▼
┌──────┴────────┐                              ┌─────────────────┐
│ Web Scraping  │                              │  Vector Search  │
└───────────────┘                              └────────┬────────┘
                                                        │
┌─────────────────┐     ┌─────────────────┐     ┌──────┴────────┐
│   Web UI        │◀────│   FastAPI       │◀────│  LLM Response │
└─────────────────┘     └─────────────────┘     └───────────────┘
```

## Installation

1. Clone the repository
2. Create a `.env` file in the `crisismap_ai` directory (see detailed instructions in `ENV_SETUP.md`)
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   cd crisismap_ai
   python run.py server
   ```

## Environment Setup

This project uses environment variables to protect sensitive information:

1. Copy the template from `ENV_SETUP.md` or use this minimal setup:
   ```
   # MongoDB Configuration
   MONGODB_URI=mongodb+srv://your_username:your_password@your_cluster.mongodb.net/?retryWrites=true&w=majority
   ```
2. Replace the placeholders with your actual MongoDB credentials
3. See `ENV_SETUP.md` for complete configuration options and troubleshooting

## Data Processing Pipeline

CrisisMap AI processes data through several stages:

1. **Collection:** Data is gathered from multiple sources including:
   - Official datasets (WHO, UN, EM-DAT, USGS)
   - Web scraping of authoritative sites
   - Real-time feeds and APIs

2. **Processing:** Raw data undergoes:
   - Normalization and standardization
   - Enrichment with location data
   - Classification and categorization

3. **Embedding:** Text is converted to vector embeddings:
   - Using Sentence Transformers models
   - Optimized for semantic search capabilities
   - Stored alongside document data in MongoDB

4. **Indexing:** Vector search indexes are created:
   - Using MongoDB Atlas Vector Search
   - Supporting k-nearest neighbors (kNN) searches
   - Enabling fast retrieval of relevant crisis information

## Web Scraping

The platform includes sophisticated web scraping capabilities:

- **Multi-source Extraction:** Gathers data from Wikipedia, ReliefWeb, and other authoritative sources
- **Structured Parsing:** Extracts key information from unstructured web content
- **Attribution:** Maintains source information for proper citation
- **Rate Limiting:** Implements responsible scraping practices

For more details, see [WEB_SCRAPING_GUIDE.md](WEB_SCRAPING_GUIDE.md).

## LLM Integration

CrisisMap AI leverages Microsoft's Phi-3-mini-4k-instruct model:

- **Query Processing:** Interprets natural language questions
- **Response Generation:** Creates coherent, informative answers
- **Context Integration:** Combines database results with scraped information
- **Fallback Mechanisms:** Gracefully handles cases where model access is limited

For more details, see [README_PHI3.md](README_PHI3.md).

## Dataset Generation & Management

The platform includes tools for dataset generation and management:

```bash
# Generate synthetic crisis data
python generate_dataset.py --count 5000

# Load specific datasets
python main.py --action ingest --dataset earthquake --limit 1000
python main.py --action ingest --dataset floods --limit 1000
```

## API Documentation

Once the server is running, access the API documentation at:
```
http://localhost:8000/docs
```

Key endpoints include:
- `POST /api/search` - Search for crisis events
- `POST /api/llm-response` - Get AI-generated responses to queries
- `GET /api/crisis/{id}` - Get details about a specific crisis

## Sample Queries

Users can enter natural language queries like:
- "Floods in South Asia from the past 5 years"
- "Compare recent Ebola outbreaks in Africa"
- "What was the economic impact of the 2011 Japan tsunami?"
- "Predict potential hurricanes in the Caribbean this season"
- "Show earthquake trends in California since 1990"

## Project Structure

```
/crisismap_ai
  /api                  # FastAPI implementation
  /data_ingestion       # Data processing pipeline
  /database             # MongoDB connection and operations
  /embedding            # Vector embedding generation
  /models               # LLM and summarization models
  /static               # CSS, JS, and other static files
  /templates            # HTML templates for web interface
  .env                  # Environment variables (not tracked in git)
  config.py             # Configuration settings
  requirements.txt      # Python dependencies
  run.py                # Main entry point
  web_scraper.py        # Web scraping functionality
```

## Future Roadmap

- Real-time social media monitoring
- Multi-language support
- Mobile applications for field reporting
- Advanced crisis prediction using machine learning
- Interactive global crisis mapping

## License

This project is open source and available under the MIT License.

## Contributors

Created for Google Cloud: AI in Action Hackathon 2025.
