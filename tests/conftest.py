"""
Pytest configuration and fixtures for CrisisMap AI tests.
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient
from pymongo.collection import Collection

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from crisismap_ai.api.app import app
from crisismap_ai.config import MONGODB_URI, DB_NAME, CRISIS_COLLECTION
from crisismap_ai.database.db_connection import DatabaseConnection


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_db_connection():
    """Create a mock database connection."""
    mock_conn = Mock(spec=DatabaseConnection)
    mock_conn.client = Mock(spec=MongoClient)
    mock_conn.db = Mock()
    mock_conn.collection = Mock(spec=Collection)
    mock_conn.is_connected.return_value = True
    return mock_conn


@pytest.fixture
def sample_crisis_data():
    """Sample crisis data for testing."""
    return [
        {
            "_id": "test_1",
            "title": "2011 Japan Tsunami",
            "description": "Massive tsunami following 9.0 earthquake off Japan's coast",
            "date": "2011-03-11",
            "location": "Japan",
            "type": "tsunami",
            "magnitude": 9.0,
            "casualties": 15894,
            "embedding": [0.1, 0.2, 0.3] * 128  # Mock embedding vector
        },
        {
            "_id": "test_2",
            "title": "Haiti Earthquake 2010",
            "description": "Catastrophic earthquake in Haiti",
            "date": "2010-01-12",
            "location": "Haiti",
            "type": "earthquake",
            "magnitude": 7.0,
            "casualties": 316000,
            "embedding": [0.2, 0.3, 0.4] * 128
        },
        {
            "_id": "test_3",
            "title": "Australian Bushfires 2019-2020",
            "description": "Severe bushfire season in Australia",
            "date": "2019-09-01",
            "location": "Australia",
            "type": "wildfire",
            "area_affected": "18.6 million hectares",
            "casualties": 34,
            "embedding": [0.3, 0.4, 0.5] * 128
        }
    ]


@pytest.fixture
def sample_search_query():
    """Sample search query for testing."""
    return {
        "query": "tsunami in Japan",
        "limit": 10,
        "threshold": 0.7
    }


@pytest.fixture
def sample_llm_query():
    """Sample LLM query for testing."""
    return {
        "query": "What were the impacts of the 2011 Japan tsunami?",
        "context": [
            {
                "title": "2011 Japan Tsunami",
                "description": "Massive tsunami following 9.0 earthquake",
                "casualties": 15894
            }
        ]
    }


@pytest.fixture
def mock_embedding_generator():
    """Mock embedding generator."""
    mock_gen = Mock()
    mock_gen.generate_embedding.return_value = [0.1, 0.2, 0.3] * 128
    mock_gen.generate_embeddings.return_value = [[0.1, 0.2, 0.3] * 128] * 3
    return mock_gen


@pytest.fixture
def mock_llm_response_generator():
    """Mock LLM response generator."""
    mock_gen = Mock()
    mock_gen.generate_response.return_value = {
        "response": "The 2011 Japan tsunami was a devastating natural disaster...",
        "confidence": 0.95
    }
    return mock_gen


@pytest.fixture
def mock_web_scraper():
    """Mock web scraper."""
    mock_scraper = Mock()
    mock_scraper.scrape_crisis_data.return_value = [
        {
            "title": "Recent Crisis Event",
            "description": "Description from web scraping",
            "source": "https://example.com/news",
            "date": "2024-01-01"
        }
    ]
    return mock_scraper


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    test_env = {
        "MONGODB_URI": "mongodb://localhost:27017/test_crisismap",
        "DB_NAME": "test_crisismap",
        "CRISIS_COLLECTION": "test_crisis_events",
        "VECTOR_INDEX_NAME": "test_vector_index",
        "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
        "SUMMARIZATION_MODEL": "google-t5/t5-small",
        "RESPONSE_MODEL": "microsoft/Phi-3-mini-4k-instruct",
        "API_HOST": "localhost",
        "API_PORT": "8000"
    }
    
    with patch.dict(os.environ, test_env):
        yield


@pytest.fixture
def test_data_file(tmp_path):
    """Create a temporary test data file."""
    data_file = tmp_path / "test_data.json"
    test_data = {
        "crisis_events": [
            {
                "title": "Test Earthquake",
                "date": "2024-01-01",
                "location": "Test Location",
                "magnitude": 7.5
            }
        ]
    }
    
    import json
    with open(data_file, "w") as f:
        json.dump(test_data, f)
    
    return data_file


@pytest.fixture
async def async_client() -> AsyncGenerator[TestClient, None]:
    """Create an async test client."""
    async with TestClient(app) as client:
        yield client


@pytest.fixture
def disable_external_calls():
    """Disable external HTTP calls during tests."""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post, \
         patch('httpx.get') as mock_httpx_get, \
         patch('httpx.post') as mock_httpx_post:
        
        # Configure mock responses
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {}
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {}
        mock_httpx_get.return_value.status_code = 200
        mock_httpx_get.return_value.json.return_value = {}
        mock_httpx_post.return_value.status_code = 200
        mock_httpx_post.return_value.json.return_value = {}
        
        yield {
            'get': mock_get,
            'post': mock_post,
            'httpx_get': mock_httpx_get,
            'httpx_post': mock_httpx_post
        }


# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add unit marker to tests in unit/ directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to tests in integration/ directory
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to tests that might be slow
        if any(keyword in item.name.lower() for keyword in ['llm', 'embedding', 'scraping']):
            item.add_marker(pytest.mark.slow)