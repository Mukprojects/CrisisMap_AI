"""
Unit tests for CrisisMap AI API endpoints.
"""
import json
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from crisismap_ai.api.app import app


class TestHealthEndpoint:
    """Test the health check endpoint."""
    
    def test_health_endpoint_success(self, client: TestClient):
        """Test successful health check."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_health_endpoint_database_error(self, client: TestClient):
        """Test health check with database error."""
        with patch('crisismap_ai.database.db_connection.get_db_connection') as mock_get_db:
            mock_db = Mock()
            mock_db.is_connected.return_value = False
            mock_get_db.return_value = mock_db
            
            response = client.get("/health")
            assert response.status_code == 503
            
            data = response.json()
            assert data["status"] == "unhealthy"


class TestRootEndpoint:
    """Test the root endpoint that serves the web interface."""
    
    def test_root_endpoint(self, client: TestClient):
        """Test that root endpoint returns HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "CrisisMap AI" in response.text


class TestSearchEndpoint:
    """Test the search API endpoint."""
    
    def test_search_success(self, client: TestClient, sample_crisis_data):
        """Test successful search."""
        with patch('crisismap_ai.database.db_operations.get_crisis_event_ops') as mock_ops, \
             patch('crisismap_ai.embedding.embedding_generator.get_embedding_generator') as mock_embed:
            
            # Mock the operations
            mock_crisis_ops = Mock()
            mock_crisis_ops.search_similar_events.return_value = sample_crisis_data[:2]
            mock_ops.return_value = mock_crisis_ops
            
            # Mock embedding generator
            mock_embedding_gen = Mock()
            mock_embedding_gen.generate_embedding.return_value = [0.1, 0.2, 0.3] * 128
            mock_embed.return_value = mock_embedding_gen
            
            # Test the endpoint
            response = client.post("/api/search", json={
                "query": "tsunami in Japan",
                "limit": 10,
                "threshold": 0.7
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert len(data["results"]) == 2
            assert data["results"][0]["title"] == "2011 Japan Tsunami"
    
    def test_search_validation_error(self, client: TestClient):
        """Test search with invalid input."""
        response = client.post("/api/search", json={
            "query": "",  # Empty query should fail
            "limit": 10
        })
        
        assert response.status_code == 422
    
    def test_search_database_error(self, client: TestClient):
        """Test search with database error."""
        with patch('crisismap_ai.database.db_operations.get_crisis_event_ops') as mock_ops:
            mock_crisis_ops = Mock()
            mock_crisis_ops.search_similar_events.side_effect = Exception("Database error")
            mock_ops.return_value = mock_crisis_ops
            
            response = client.post("/api/search", json={
                "query": "test query",
                "limit": 10
            })
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data


class TestLLMResponseEndpoint:
    """Test the LLM response API endpoint."""
    
    def test_llm_response_success(self, client: TestClient, sample_llm_query):
        """Test successful LLM response."""
        with patch('crisismap_ai.models.llm_response.get_llm_response_generator') as mock_llm:
            mock_llm_gen = Mock()
            mock_llm_gen.generate_response.return_value = {
                "response": "The 2011 Japan tsunami was devastating...",
                "confidence": 0.95,
                "sources": []
            }
            mock_llm.return_value = mock_llm_gen
            
            response = client.post("/api/llm-response", json=sample_llm_query)
            
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert "confidence" in data
            assert data["response"].startswith("The 2011 Japan tsunami")
    
    def test_llm_response_validation_error(self, client: TestClient):
        """Test LLM response with invalid input."""
        response = client.post("/api/llm-response", json={
            "query": "",  # Empty query
            "context": []
        })
        
        assert response.status_code == 422
    
    def test_llm_response_model_error(self, client: TestClient, sample_llm_query):
        """Test LLM response with model error."""
        with patch('crisismap_ai.models.llm_response.get_llm_response_generator') as mock_llm:
            mock_llm_gen = Mock()
            mock_llm_gen.generate_response.side_effect = Exception("Model error")
            mock_llm.return_value = mock_llm_gen
            
            response = client.post("/api/llm-response", json=sample_llm_query)
            
            assert response.status_code == 500


class TestCrisisEventEndpoints:
    """Test crisis event CRUD endpoints."""
    
    def test_get_crisis_event_success(self, client: TestClient, sample_crisis_data):
        """Test getting a specific crisis event."""
        with patch('crisismap_ai.database.db_operations.get_crisis_event_ops') as mock_ops:
            mock_crisis_ops = Mock()
            mock_crisis_ops.get_event_by_id.return_value = sample_crisis_data[0]
            mock_ops.return_value = mock_crisis_ops
            
            response = client.get("/api/crisis/test_1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "2011 Japan Tsunami"
    
    def test_get_crisis_event_not_found(self, client: TestClient):
        """Test getting a non-existent crisis event."""
        with patch('crisismap_ai.database.db_operations.get_crisis_event_ops') as mock_ops:
            mock_crisis_ops = Mock()
            mock_crisis_ops.get_event_by_id.return_value = None
            mock_ops.return_value = mock_crisis_ops
            
            response = client.get("/api/crisis/nonexistent")
            
            assert response.status_code == 404
    
    def test_create_crisis_event_success(self, client: TestClient):
        """Test creating a new crisis event."""
        new_event = {
            "title": "New Crisis Event",
            "description": "A new crisis for testing",
            "date": "2024-01-01",
            "location": "Test Location",
            "type": "earthquake",
            "magnitude": 6.5
        }
        
        with patch('crisismap_ai.database.db_operations.get_crisis_event_ops') as mock_ops:
            mock_crisis_ops = Mock()
            mock_crisis_ops.create_event.return_value = {**new_event, "_id": "new_id"}
            mock_ops.return_value = mock_crisis_ops
            
            response = client.post("/api/crisis", json=new_event)
            
            assert response.status_code == 201
            data = response.json()
            assert data["title"] == "New Crisis Event"
            assert "_id" in data
    
    def test_update_crisis_event_success(self, client: TestClient):
        """Test updating a crisis event."""
        update_data = {
            "title": "Updated Crisis Event",
            "casualties": 1000
        }
        
        with patch('crisismap_ai.database.db_operations.get_crisis_event_ops') as mock_ops:
            mock_crisis_ops = Mock()
            mock_crisis_ops.update_event.return_value = {
                "_id": "test_1",
                "title": "Updated Crisis Event",
                "casualties": 1000
            }
            mock_ops.return_value = mock_crisis_ops
            
            response = client.put("/api/crisis/test_1", json=update_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Updated Crisis Event"
    
    def test_delete_crisis_event_success(self, client: TestClient):
        """Test deleting a crisis event."""
        with patch('crisismap_ai.database.db_operations.get_crisis_event_ops') as mock_ops:
            mock_crisis_ops = Mock()
            mock_crisis_ops.delete_event.return_value = True
            mock_ops.return_value = mock_crisis_ops
            
            response = client.delete("/api/crisis/test_1")
            
            assert response.status_code == 204


class TestErrorHandling:
    """Test error handling across the API."""
    
    def test_404_error(self, client: TestClient):
        """Test 404 error handling."""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client: TestClient):
        """Test method not allowed error."""
        response = client.patch("/api/search")  # PATCH not allowed on search
        assert response.status_code == 405
    
    def test_large_payload(self, client: TestClient):
        """Test handling of large payloads."""
        large_query = "x" * 10000  # Very large query
        
        response = client.post("/api/search", json={
            "query": large_query,
            "limit": 10
        })
        
        # Should either handle gracefully or return appropriate error
        assert response.status_code in [200, 413, 422]


class TestCORS:
    """Test CORS configuration."""
    
    def test_cors_headers(self, client: TestClient):
        """Test that CORS headers are present."""
        response = client.options("/api/search")
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers


class TestRateLimiting:
    """Test rate limiting (if implemented)."""
    
    @pytest.mark.skip(reason="Rate limiting not yet implemented")
    def test_rate_limiting(self, client: TestClient):
        """Test rate limiting functionality."""
        # This test would check if rate limiting is working
        # when it's implemented
        pass