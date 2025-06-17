"""
Embedding generator for CrisisMap AI.
"""
import sys
from pathlib import Path
from typing import List, Union, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import torch

# Add parent directory to system path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config import EMBEDDING_MODEL

class EmbeddingGenerator:
    """Generates embeddings for crisis data using sentence-transformers."""
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """
        Initialize the embedding generator with the specified model.
        
        Args:
            model_name: Name of the sentence-transformer model to use
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
        
    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            # Check if CUDA is available
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            print(f"Loading embedding model on {device}...")
            
            self.model = SentenceTransformer(self.model_name, device=device)
            print(f"Embedding model '{self.model_name}' loaded successfully.")
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to generate embedding for
            
        Returns:
            List of floats representing the embedding vector
        """
        if not self.model:
            self._load_model()
            
        # Generate embedding
        embedding = self.model.encode(text)
        
        # Convert to list of floats
        return embedding.tolist()
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        if not self.model:
            self._load_model()
            
        # Generate embeddings
        embeddings = self.model.encode(texts)
        
        # Convert to list of lists
        return embeddings.tolist()
    
    def generate_embedding_for_crisis(self, crisis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate embedding for a crisis event and add it to the data.
        
        Args:
            crisis_data: Dictionary containing crisis event data
            
        Returns:
            Crisis data with added embedding
        """
        # Combine relevant fields for embedding
        text_parts = []
        
        if 'title' in crisis_data and crisis_data['title']:
            text_parts.append(crisis_data['title'])
            
        if 'summary' in crisis_data and crisis_data['summary']:
            text_parts.append(crisis_data['summary'])
            
        if 'location' in crisis_data and crisis_data['location']:
            text_parts.append(f"Location: {crisis_data['location']}")
            
        if 'category' in crisis_data and crisis_data['category']:
            text_parts.append(f"Category: {crisis_data['category']}")
        
        # Join parts with spaces
        combined_text = " ".join(text_parts)
        
        # Generate embedding
        crisis_data['embedding'] = self.generate_embedding(combined_text)
        
        return crisis_data
    
    def generate_embeddings_for_crises(self, crisis_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for multiple crisis events.
        
        Args:
            crisis_data_list: List of dictionaries containing crisis event data
            
        Returns:
            List of crisis data with added embeddings
        """
        # Extract text for each crisis event
        texts = []
        for crisis_data in crisis_data_list:
            text_parts = []
            
            if 'title' in crisis_data and crisis_data['title']:
                text_parts.append(crisis_data['title'])
                
            if 'summary' in crisis_data and crisis_data['summary']:
                text_parts.append(crisis_data['summary'])
                
            if 'location' in crisis_data and crisis_data['location']:
                text_parts.append(f"Location: {crisis_data['location']}")
                
            if 'category' in crisis_data and crisis_data['category']:
                text_parts.append(f"Category: {crisis_data['category']}")
            
            # Join parts with spaces
            combined_text = " ".join(text_parts)
            texts.append(combined_text)
        
        # Generate embeddings for all texts at once
        embeddings = self.generate_embeddings(texts)
        
        # Add embeddings to crisis data
        for i, crisis_data in enumerate(crisis_data_list):
            crisis_data['embedding'] = embeddings[i]
        
        return crisis_data_list

# Create a singleton instance
embedding_generator = EmbeddingGenerator()

def get_embedding_generator():
    """Get the embedding generator singleton."""
    return embedding_generator 

def generate_embedding(text: str, generator: Optional[EmbeddingGenerator] = None) -> Optional[List[float]]:
    """
    Generate an embedding for the given text.
    
    Args:
        text: The text to generate an embedding for
        generator: Optional embedding generator instance
        
    Returns:
        List of floats representing the embedding vector, or None if an error occurs
    """
    try:
        if generator is None:
            generator = get_embedding_generator()
        
        return generator.generate_embedding(text)
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None 