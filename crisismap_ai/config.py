"""
Configuration module for CrisisMap AI project.
"""
import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# MongoDB Configuration
# Use environment variable or placeholder - DO NOT include credentials in code
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority')
DB_NAME = os.getenv('DB_NAME', 'crisismap')
CRISIS_COLLECTION = os.getenv('CRISIS_COLLECTION', 'crisis_events')
VECTOR_INDEX_NAME = os.getenv('VECTOR_INDEX_NAME', 'vector_index')

# API Settings
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 8000))

# Hugging Face Model Settings
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
SUMMARIZATION_MODEL = os.getenv('SUMMARIZATION_MODEL', 'google-t5/t5-small')
RESPONSE_MODEL = os.getenv('RESPONSE_MODEL', 'microsoft/Phi-3-mini-4k-instruct')

# Dataset Paths
DATASET_DIR = Path(__file__).parent.parent / 'Dataset'

# Original datasets
WHO_DATASET = DATASET_DIR / 'Who dataset' / 'WHO.csv'
EMDAT_DATASET = DATASET_DIR / 'EM-DAT dataset' / 'events-US-1980-2024.csv'
DISASTER_TWEETS = DATASET_DIR / 'Disaster Tweets' / 'tweets.csv'

# New datasets
EARTHQUAKE_DATASET = DATASET_DIR / 'Earthquake' / 'earthquake_1995-2023.csv'
EARTHQUAKE_DATA = DATASET_DIR / 'Earthquake' / 'earthquake_data.csv'
VOLCANO_DATASET = DATASET_DIR / 'Other Datasets' / 'volcano-events.csv'
FLOODS_DATASET = DATASET_DIR / 'Other Datasets' / 'floods.csv'
TSUNAMI_DATASET = DATASET_DIR / 'Other Datasets' / 'tsunami_dataset.csv'
FIRE_DATASET = DATASET_DIR / 'Other Datasets' / 'fire_nrt_M-C61_625841.csv'

# Vector Dimension
VECTOR_DIMENSION = 384  # for all-MiniLM-L6-v2

# Web interface settings
STATIC_DIR = Path(__file__).parent / 'static'
TEMPLATES_DIR = Path(__file__).parent / 'templates' 