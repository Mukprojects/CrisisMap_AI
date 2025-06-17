"""
Data processing module for CrisisMap AI.
"""
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from tqdm import tqdm

# Add parent directory to system path for imports
sys.path.append(str(Path(__file__).parent.parent))
from embedding.embedding_generator import get_embedding_generator
from models.summarization import get_summarizer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_crisis_data(crisis_data: List[Dict[str, Any]], 
                       generate_embeddings: bool = True,
                       generate_summaries: bool = True,
                       batch_size: int = 32) -> List[Dict[str, Any]]:
    """
    Process crisis data by generating embeddings and summaries.
    
    Args:
        crisis_data: List of crisis event dictionaries
        generate_embeddings: Whether to generate embeddings
        generate_summaries: Whether to generate summaries
        batch_size: Batch size for processing
        
    Returns:
        Processed crisis data
    """
    logger.info(f"Processing {len(crisis_data)} crisis events...")
    
    # Process in batches
    processed_data = []
    total_batches = (len(crisis_data) + batch_size - 1) // batch_size
    
    for i in range(0, len(crisis_data), batch_size):
        batch = crisis_data[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)")
        
        # Generate summaries if needed
        if generate_summaries:
            # Check which items need summarization
            items_to_summarize = []
            for item in batch:
                if 'text' in item and item['text'] and ('summary' not in item or not item['summary']):
                    items_to_summarize.append(item)
            
            if items_to_summarize:
                logger.info(f"Generating summaries for {len(items_to_summarize)} items in batch {batch_num}")
                summarizer = get_summarizer()
                summarizer.summarize_crisis_data_batch(items_to_summarize)
                
        # Generate embeddings if needed
        if generate_embeddings:
            logger.info(f"Generating embeddings for batch {batch_num}")
            embedding_generator = get_embedding_generator()
            batch = embedding_generator.generate_embeddings_for_crises(batch)
        
        # Add processed batch to results
        processed_data.extend(batch)
        
    logger.info(f"Processed {len(processed_data)} crisis events")
    return processed_data

def clean_crisis_data(crisis_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Clean and validate crisis data.
    
    Args:
        crisis_data: List of crisis event dictionaries
        
    Returns:
        Cleaned crisis data
    """
    logger.info(f"Cleaning {len(crisis_data)} crisis events...")
    
    cleaned_data = []
    
    for event in crisis_data:
        # Ensure required fields are present
        if 'title' not in event or not event['title']:
            logger.warning("Skipping event without title")
            continue
            
        # Ensure summary exists
        if 'summary' not in event or not event['summary']:
            if 'text' in event and event['text']:
                # Use text as summary if available
                event['summary'] = event['text']
            else:
                logger.warning(f"Skipping event without summary: {event['title']}")
                continue
                
        # Ensure date is in correct format
        if 'date' not in event or not event['date']:
            logger.warning(f"Event missing date, using current date: {event['title']}")
            from datetime import datetime
            event['date'] = datetime.now().strftime('%Y-%m-%d')
            
        # Add to cleaned data
        cleaned_data.append(event)
        
    logger.info(f"Cleaned data contains {len(cleaned_data)} valid crisis events")
    return cleaned_data 