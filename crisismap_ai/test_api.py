"""
Test script for CrisisMap AI API.
"""
import requests
import json
import time
from typing import Dict, Any

# API URL
API_URL = "http://localhost:8000"

def test_health():
    """Test health check endpoint."""
    print("\n🔍 Testing health check endpoint...")
    response = requests.get(f"{API_URL}/health")
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    print("✅ Health check test passed!")

def test_search(query: str):
    """Test semantic search endpoint."""
    print(f"\n🔍 Testing semantic search with query: '{query}'...")
    response = requests.post(
        f"{API_URL}/search",
        json={"query": query, "limit": 5}
    )
    print(f"Status code: {response.status_code}")
    data = response.json()
    print(f"Found {data['count']} results")
    
    if data['count'] > 0:
        print("\nTop result:")
        result = data['results'][0]
        print(f"Title: {result['title']}")
        print(f"Summary: {result['summary']}")
        print(f"Location: {result.get('location', 'N/A')}")
        print(f"Score: {result.get('score', 'N/A')}")
    
    assert response.status_code == 200
    print("✅ Semantic search test passed!")

def test_text_search(query: str):
    """Test text search endpoint."""
    print(f"\n🔍 Testing text search with query: '{query}'...")
    response = requests.post(
        f"{API_URL}/search/text",
        json={"query": query, "limit": 5}
    )
    print(f"Status code: {response.status_code}")
    data = response.json()
    print(f"Found {data['count']} results")
    
    if data['count'] > 0:
        print("\nTop result:")
        result = data['results'][0]
        print(f"Title: {result['title']}")
        print(f"Summary: {result['summary']}")
        print(f"Location: {result.get('location', 'N/A')}")
        print(f"Score: {result.get('score', 'N/A')}")
    
    assert response.status_code == 200
    print("✅ Text search test passed!")

def test_create_event():
    """Test creating a new event."""
    print("\n🔍 Testing event creation...")
    test_event = {
        "title": "Test Crisis Event",
        "summary": "This is a test crisis event for API testing purposes.",
        "text": "This is a longer text describing the test crisis event. It provides more details about what happened, where it happened, and the impact it had.",
        "location": "Test Location",
        "category": "Test Category",
        "source": "Test Source",
        "date": "2023-01-01"
    }
    
    response = requests.post(
        f"{API_URL}/events",
        json=test_event
    )
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 201:
        event = response.json()
        print(f"Created event with ID: {event['id']}")
        return event['id']
    else:
        print(f"Error: {response.text}")
        return None

def test_get_event(event_id: str):
    """Test retrieving an event."""
    print(f"\n🔍 Testing event retrieval for ID: {event_id}...")
    response = requests.get(f"{API_URL}/events/{event_id}")
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        event = response.json()
        print(f"Retrieved event: {event['title']}")
        assert event['id'] == event_id
        print("✅ Event retrieval test passed!")
        return event
    else:
        print(f"Error: {response.text}")
        return None

def test_update_event(event_id: str):
    """Test updating an event."""
    print(f"\n🔍 Testing event update for ID: {event_id}...")
    update_data = {
        "title": "Updated Test Crisis Event",
        "summary": "This event has been updated through the API."
    }
    
    response = requests.put(
        f"{API_URL}/events/{event_id}",
        json=update_data
    )
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        event = response.json()
        print(f"Updated event: {event['title']}")
        assert event['title'] == update_data['title']
        print("✅ Event update test passed!")
        return event
    else:
        print(f"Error: {response.text}")
        return None

def test_delete_event(event_id: str):
    """Test deleting an event."""
    print(f"\n🔍 Testing event deletion for ID: {event_id}...")
    response = requests.delete(f"{API_URL}/events/{event_id}")
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 204:
        print("Event deleted successfully")
        
        # Verify it's gone
        get_response = requests.get(f"{API_URL}/events/{event_id}")
        assert get_response.status_code == 404
        print("✅ Event deletion test passed!")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_summarize():
    """Test text summarization."""
    print("\n🔍 Testing text summarization...")
    test_text = """
    A major flooding has occurred in Southeast Asia affecting millions of people.
    The flooding has caused significant damage to infrastructure, crops, and homes.
    Rescue teams are working around the clock to evacuate people from affected areas.
    International aid organizations have pledged support for the affected countries.
    The flooding is expected to continue for several more days as rain continues to fall.
    This is the worst flooding the region has seen in decades according to local officials.
    """
    
    response = requests.post(
        f"{API_URL}/summarize",
        params={"text": test_text}
    )
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Summary: {data['summary']}")
        assert data['summary']
        print("✅ Text summarization test passed!")
    else:
        print(f"Error: {response.text}")

def run_all_tests():
    """Run all API tests."""
    print("🚀 Starting CrisisMap AI API Tests")
    
    # Basic tests
    test_health()
    
    # Search tests
    test_search("Flooding in Southeast Asia")
    test_text_search("hurricane")
    
    # CRUD tests
    event_id = test_create_event()
    if event_id:
        test_get_event(event_id)
        test_update_event(event_id)
        test_delete_event(event_id)
    
    # Utility tests
    test_summarize()
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    run_all_tests() 