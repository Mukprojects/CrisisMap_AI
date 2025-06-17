"""
API models for CrisisMap AI.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class CrisisEvent(BaseModel):
    """Model for a crisis event."""
    id: Optional[str] = Field(None, description="Database ID of the crisis event")
    title: str = Field(..., description="Title of the crisis event")
    summary: str = Field(..., description="Summary of the crisis event")
    location: Optional[str] = Field(None, description="Location of the crisis event")
    date: Optional[str] = Field(None, description="Date of the crisis event (YYYY-MM-DD)")
    category: Optional[str] = Field(None, description="Category of crisis (e.g., Natural Disaster, Conflict)")
    source: Optional[str] = Field(None, description="Source of the crisis information")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data about the crisis")
    score: Optional[float] = Field(None, description="Search score")
    
class CrisisEventCreate(BaseModel):
    """Model for creating a new crisis event."""
    title: str = Field(..., description="Title of the crisis event")
    summary: Optional[str] = Field(None, description="Summary of the crisis event")
    text: Optional[str] = Field(None, description="Full text of the crisis report")
    location: Optional[str] = Field(None, description="Location of the crisis event")
    date: Optional[str] = Field(None, description="Date of the crisis event (YYYY-MM-DD)")
    category: Optional[str] = Field(None, description="Category of crisis (e.g., Natural Disaster, Conflict)")
    source: Optional[str] = Field(None, description="Source of the crisis information")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data about the crisis")
    
class CrisisEventUpdate(BaseModel):
    """Model for updating a crisis event."""
    title: Optional[str] = Field(None, description="Title of the crisis event")
    summary: Optional[str] = Field(None, description="Summary of the crisis event")
    text: Optional[str] = Field(None, description="Full text of the crisis report")
    location: Optional[str] = Field(None, description="Location of the crisis event")
    date: Optional[str] = Field(None, description="Date of the crisis event (YYYY-MM-DD)")
    category: Optional[str] = Field(None, description="Category of crisis (e.g., Natural Disaster, Conflict)")
    source: Optional[str] = Field(None, description="Source of the crisis information")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data about the crisis")

class SearchQuery(BaseModel):
    """Model for a search query."""
    query: str = Field(..., description="Search query text")
    limit: Optional[int] = Field(10, description="Maximum number of results to return")
    
class SearchResponse(BaseModel):
    """Model for a search response."""
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    count: int = Field(..., description="Number of results returned")
    query: str = Field(..., description="Original search query")
    
class HealthResponse(BaseModel):
    """Model for the health check response."""
    status: str = Field(..., description="API status")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Current timestamp")
    
class ErrorResponse(BaseModel):
    """Model for an error response."""
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")

class LLMQuery(BaseModel):
    """LLM query model."""
    query: str = Field(..., description="The query to send to the LLM")
    max_results: int = Field(5, description="Maximum number of results to return")
    
class LLMResponseSource(BaseModel):
    """Source information for LLM responses."""
    title: Optional[str] = Field(None, description="Source title")
    source: Optional[str] = Field(None, description="Source name (e.g., Wikipedia, ReliefWeb)")
    url: Optional[str] = Field(None, description="Source URL")
    date: Optional[str] = Field(None, description="Publication date or date accessed")
    event_id: Optional[str] = Field(None, description="ID of the source event in the database (if applicable)")
    
class LLMResponse(BaseModel):
    """LLM response model."""
    response: str = Field(..., description="The response from the LLM")
    source_data: Optional[List[Dict[str, Any]]] = Field(None, description="Source data used to generate the response")

class CrisisResponse(BaseModel):
    """Crisis query response model."""
    response: str = Field(..., description="The formatted response to the crisis query")
    sources: Optional[List[Dict[str, Any]]] = Field(None, description="Source information used in the response") 