"""
FastAPI application for CrisisMap AI.
"""
import sys
from pathlib import Path
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Query, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse

# Ensure the parent directory is in sys.path
current_dir = Path(__file__).parent.parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Use absolute imports
from crisismap_ai.config import API_HOST, API_PORT, STATIC_DIR, TEMPLATES_DIR
from crisismap_ai.database.db_connection import get_db_connection
from crisismap_ai.database.db_operations import get_crisis_event_ops
from crisismap_ai.embedding.embedding_generator import get_embedding_generator
from crisismap_ai.models.summarization import get_summarizer
from crisismap_ai.models.llm_response import get_llm_response_generator
from crisismap_ai.web_scraper import get_web_scraper
from crisismap_ai.api.models import (
    CrisisEvent, 
    CrisisEventCreate, 
    CrisisEventUpdate,
    SearchQuery,
    SearchResponse,
    HealthResponse,
    ErrorResponse,
    LLMQuery,
    LLMResponse,
    CrisisResponse
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CrisisMap AI API",
    description="API for CrisisMap AI - A global crisis search and monitoring system",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialize templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Initialize database connection
db_connection = get_db_connection()
db_connection.connect()

@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    logger.info("Starting CrisisMap AI API...")
    
    # Ensure database connection
    db_connection.connect()
    
    # Create vector search index if it doesn't exist
    db_connection.create_vector_search_index()
    
    # Initialize embedding generator
    get_embedding_generator()
    
    logger.info("CrisisMap AI API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down CrisisMap AI API...")
    
    # Close database connection
    db_connection.close()
    
    logger.info("CrisisMap AI API shut down successfully")

@app.get("/", response_class=HTMLResponse, tags=["Web Interface"])
async def index(request: Request):
    """Render the main web interface."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        crisis_ops = get_crisis_event_ops()
        db_status = "healthy" if crisis_ops.check_connection() else "unhealthy"
        
        return {
            "status": "ok",
            "database": db_status,
            "api_version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "api_version": "1.0.0"
            }
        )

@app.post("/api/llm-response", response_model=LLMResponse, tags=["LLM"])
async def llm_response(query: LLMQuery):
    """
    Generate an LLM response based on relevant crisis data and web search.
    
    The query is used to find relevant crisis events in the database and online sources,
    then an LLM generates a response based on this data.
    """
    try:
        # Log the query for debugging
        logger.info(f"Processing LLM query: {query.query}")
        
        # Check for California wildfire query to directly use web scraper
        is_california_wildfire = False
        if "california" in query.query.lower() and ("wildfire" in query.query.lower() or "fire" in query.query.lower()):
            is_california_wildfire = True
        
        # Fetch web data first for all queries
        web_data = []
        web_sources = []
        try:
            # Get web scraper
            web_scraper = get_web_scraper()
            
            # Set max_results higher for California wildfire queries
            max_results = 5 if is_california_wildfire else 3
            
            # Search for disaster information
            web_data = web_scraper.search_disaster_info(query.query, max_results=max_results)
            
            # Extract sources for the response
            for data in web_data:
                if "title" in data and "source" in data and "url" in data:
                    web_sources.append({
                        "title": data.get("title", ""),
                        "source": data.get("source", ""),
                        "url": data.get("url", "")
                    })
                    
            logger.info(f"Retrieved {len(web_data)} web sources for query: {query.query}")
        except Exception as e:
            logger.error(f"Error retrieving web data: {e}", exc_info=True)
            logger.warning("Continuing without web data")
        
        # Get database data only if needed (if web data is insufficient or for non-California wildfire queries)
        database_results = []
        if not is_california_wildfire or len(web_data) < 2:
            try:
                # Check database connection
                db_conn = get_db_connection()
                if not db_conn.is_connected():
                    logger.warning("Database not connected. Attempting to connect...")
                    db_conn.connect()
                
                # Get crisis event operations and embedding generator
                crisis_ops = get_crisis_event_ops()
                embedding_generator = get_embedding_generator()
                
                # Generate embedding for query
                query_embedding = embedding_generator.generate_embedding(query.query)
                
                # Perform vector search
                database_results = crisis_ops.search_by_vector(query_embedding, limit=5)
                
                if not database_results:
                    # Try text search as fallback
                    database_results = crisis_ops.search_by_text(query.query, limit=5)
                    
                logger.info(f"Retrieved {len(database_results)} database results for query: {query.query}")
            except Exception as e:
                logger.error(f"Error retrieving database data: {e}", exc_info=True)
                logger.warning("Continuing without database data")
        
        # Generate response with LLM
        llm_generator = get_llm_response_generator()
        response_text = ""
        
        # If we have data from any source, generate a response
        if web_data or database_results:
            response_text = llm_generator.generate_response(query.query, database_results, web_data)
        else:
            response_text = "I couldn't find any information about your query. Please try a different question or check your internet connection."
        
        # Log successful response
        logger.info(f"Generated LLM response for query: {query.query}")
        
        # Return LLM response with sources
        return {
            "query": query.query,
            "response": response_text,
            "sources": web_sources
        }
    except Exception as e:
        logger.error(f"Error generating LLM response: {e}", exc_info=True)
        # Return a user-friendly error message
        error_message = "I'm sorry, I encountered an error while processing your request. Please try again or rephrase your question."
        return {
            "query": query.query,
            "response": error_message,
            "sources": []
        }

@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search(query: SearchQuery):
    """
    Search for crisis events using semantic search.
    
    The query will be converted to an embedding and used to find similar crisis events.
    """
    try:
        # Get embedding generator
        embedding_generator = get_embedding_generator()
        
        # Generate embedding for query
        query_embedding = embedding_generator.generate_embedding(query.query)
        
        # Get crisis event operations
        crisis_ops = get_crisis_event_ops()
        
        # Perform vector search
        results = crisis_ops.search_by_vector(query_embedding, limit=query.limit)
        
        # Return search response
        return {
            "results": results,
            "count": len(results),
            "query": query.query
        }
    except Exception as e:
        logger.error(f"Error performing search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing search: {str(e)}"
        )

@app.post("/search/text", response_model=SearchResponse, tags=["Search"])
async def text_search(query: SearchQuery):
    """
    Search for crisis events using text search.
    
    This endpoint uses MongoDB's text search capabilities.
    """
    try:
        # Get crisis event operations
        crisis_ops = get_crisis_event_ops()
        
        # Perform text search
        results = crisis_ops.search_by_text(query.query, limit=query.limit)
        
        # Return search response
        return {
            "results": results,
            "count": len(results),
            "query": query.query
        }
    except Exception as e:
        logger.error(f"Error performing text search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing text search: {str(e)}"
        )

@app.get("/events", response_model=List[CrisisEvent], tags=["Events"])
async def get_events(
    limit: int = Query(100, description="Maximum number of events to return"),
    skip: int = Query(0, description="Number of events to skip")
):
    """Get all crisis events with pagination."""
    try:
        # Get crisis event operations
        crisis_ops = get_crisis_event_ops()
        
        # Get events
        events = crisis_ops.get_all_crisis_events(limit=limit, skip=skip)
        
        return events
    except Exception as e:
        logger.error(f"Error retrieving events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving events: {str(e)}"
        )

@app.get("/events/{event_id}", response_model=CrisisEvent, tags=["Events"])
async def get_event(event_id: str):
    """Get a specific crisis event by ID."""
    try:
        # Get crisis event operations
        crisis_ops = get_crisis_event_ops()
        
        # Get event
        event = crisis_ops.get_crisis_event(event_id)
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} not found"
            )
            
        return event
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving event {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving event: {str(e)}"
        )

@app.post("/events", response_model=CrisisEvent, status_code=status.HTTP_201_CREATED, tags=["Events"])
async def create_event(event: CrisisEventCreate):
    """Create a new crisis event."""
    try:
        # Get embedding generator
        embedding_generator = get_embedding_generator()
        
        # Get summarizer if text is provided
        if event.text and not event.summary:
            summarizer = get_summarizer()
            summary = summarizer.summarize(event.text)
            event_dict = event.dict()
            event_dict['summary'] = summary
        else:
            event_dict = event.dict()
        
        # Generate embedding
        event_with_embedding = embedding_generator.generate_embedding_for_crisis(event_dict)
        
        # Get crisis event operations
        crisis_ops = get_crisis_event_ops()
        
        # Insert event
        event_id = crisis_ops.insert_crisis_event(event_with_embedding)
        
        # Get the created event
        created_event = crisis_ops.get_crisis_event(event_id)
        
        return created_event
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating event: {str(e)}"
        )

@app.put("/events/{event_id}", response_model=CrisisEvent, tags=["Events"])
async def update_event(event_id: str, event_update: CrisisEventUpdate):
    """Update an existing crisis event."""
    try:
        # Get crisis event operations
        crisis_ops = get_crisis_event_ops()
        
        # Check if event exists
        existing_event = crisis_ops.get_crisis_event(event_id)
        if not existing_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} not found"
            )
        
        # Update event
        update_data = event_update.dict(exclude_unset=True)
        
        # If text changed and there's no summary, generate a new summary
        if 'text' in update_data and update_data['text'] and 'summary' not in update_data:
            summarizer = get_summarizer()
            update_data['summary'] = summarizer.summarize(update_data['text'])
        
        # Update embedding if needed
        update_embedding = False
        for field in ['title', 'summary', 'location', 'category']:
            if field in update_data:
                update_embedding = True
                break
                
        if update_embedding:
            # Merge existing data with updates
            updated_event = {**existing_event, **update_data}
            
            # Generate new embedding
            embedding_generator = get_embedding_generator()
            updated_event = embedding_generator.generate_embedding_for_crisis(updated_event)
            
            # Update data with new embedding
            update_data['embedding'] = updated_event['embedding']
        
        # Update in database
        success = crisis_ops.update_crisis_event(event_id, update_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update event with ID {event_id}"
            )
        
        # Get updated event
        updated_event = crisis_ops.get_crisis_event(event_id)
        
        return updated_event
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating event {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating event: {str(e)}"
        )

@app.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Events"])
async def delete_event(event_id: str):
    """Delete a crisis event."""
    try:
        # Get crisis event operations
        crisis_ops = get_crisis_event_ops()
        
        # Check if event exists
        existing_event = crisis_ops.get_crisis_event(event_id)
        if not existing_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} not found"
            )
        
        # Delete event
        success = crisis_ops.delete_crisis_event(event_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete event with ID {event_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting event {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting event: {str(e)}"
        )

@app.post("/summarize", tags=["Utilities"])
async def summarize_text(text: str):
    """Summarize text using the T5 model."""
    try:
        # Get summarizer
        summarizer = get_summarizer()
        
        # Generate summary
        summary = summarizer.summarize(text)
        
        return {"summary": summary}
    except Exception as e:
        logger.error(f"Error summarizing text: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error summarizing text: {str(e)}"
        )

@app.get("/crisis/query", response_model=CrisisResponse)
async def crisis_query(query: str = Query(..., description="Query for crisis information"), 
                      max_results: int = Query(5, description="Maximum number of results to return")):
    """
    Query the crisis data with natural language and get a response.
    
    Args:
        query: Natural language query about crisis events
        max_results: Maximum number of results to return
        
    Returns:
        Generated response to the query
    """
    try:
        # Log the query
        logger.info(f"Received query: {query}")
        
        # Get the LLM response generator
        llm_response_generator = get_llm_response_generator()
        
        # Get response
        response = llm_response_generator.find_and_respond(query, max_results)
        
        # Extract sources if included in the response
        sources = []
        if "**Sources:**" in response:
            response_parts = response.split("**Sources:**")
            main_response = response_parts[0].strip()
            
            if len(response_parts) > 1:
                # Parse sources
                source_lines = response_parts[1].strip().split("\n")
                for line in source_lines:
                    if line.startswith("-"):
                        source_text = line[1:].strip()
                        
                        # Try to extract title and source if in format "Title (Source)"
                        if "(" in source_text and source_text.endswith(")"):
                            title_part, source_part = source_text.rsplit("(", 1)
                            title = title_part.strip()
                            source = source_part[:-1].strip()  # Remove the closing parenthesis
                            sources.append({"title": title, "source": source})
                        else:
                            sources.append({"title": source_text, "source": "Unknown"})
            
            # Return the response without the sources section
            return CrisisResponse(response=main_response, sources=sources)
        
        # Return the full response if no sources section is found
        return CrisisResponse(response=response)
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=API_HOST, port=API_PORT, reload=True) 