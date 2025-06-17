"""
Text summarization module for CrisisMap AI.
"""
import sys
from pathlib import Path
from typing import List, Dict, Any
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Add parent directory to system path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config import SUMMARIZATION_MODEL

class Summarizer:
    """
    Text summarization using Hugging Face Transformers.
    """
    
    def __init__(self, model_name: str = SUMMARIZATION_MODEL):
        """
        Initialize the summarizer with the specified model.
        
        Args:
            model_name: Name of the Hugging Face model to use
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        
    def _load_model(self):
        """Load the summarization model and tokenizer."""
        try:
            # Check if CUDA is available
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            print(f"Loading summarization model on {device}...")
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name).to(device)
            
            print(f"Summarization model '{self.model_name}' loaded successfully.")
        except Exception as e:
            print(f"Error loading summarization model: {e}")
            raise
            
    def summarize(self, text: str, max_length: int = 150, min_length: int = 40) -> str:
        """
        Generate a summary for the input text.
        
        Args:
            text: Input text to summarize
            max_length: Maximum length of the summary
            min_length: Minimum length of the summary
            
        Returns:
            Generated summary
        """
        if not self.model or not self.tokenizer:
            self._load_model()
            
        # Check if text is too short to summarize
        if len(text.split()) < min_length:
            return text
            
        # Prepare input for T5 model
        input_text = "summarize: " + text
        
        # Tokenize input
        inputs = self.tokenizer(input_text, return_tensors="pt", max_length=1024, truncation=True)
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        # Generate summary
        summary_ids = self.model.generate(
            inputs["input_ids"],
            max_length=max_length,
            min_length=min_length,
            num_beams=4,
            early_stopping=True
        )
        
        # Decode summary
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        
        return summary
        
    def summarize_batch(self, texts: List[str], max_length: int = 150, min_length: int = 40) -> List[str]:
        """
        Generate summaries for multiple input texts.
        
        Args:
            texts: List of input texts to summarize
            max_length: Maximum length of each summary
            min_length: Minimum length of each summary
            
        Returns:
            List of generated summaries
        """
        if not self.model or not self.tokenizer:
            self._load_model()
            
        summaries = []
        
        for text in texts:
            # Check if text is too short to summarize
            if len(text.split()) < min_length:
                summaries.append(text)
                continue
                
            # Prepare input for T5 model
            input_text = "summarize: " + text
            
            # Tokenize input
            inputs = self.tokenizer(input_text, return_tensors="pt", max_length=1024, truncation=True)
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            # Generate summary
            summary_ids = self.model.generate(
                inputs["input_ids"],
                max_length=max_length,
                min_length=min_length,
                num_beams=4,
                early_stopping=True
            )
            
            # Decode summary
            summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            summaries.append(summary)
            
        return summaries
        
    def summarize_crisis_data(self, crisis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize the text content of a crisis event.
        
        Args:
            crisis_data: Dictionary containing crisis event data
            
        Returns:
            Crisis data with added summary
        """
        # Check if there's text to summarize
        if 'text' in crisis_data and crisis_data['text']:
            # Generate summary
            summary = self.summarize(crisis_data['text'])
            
            # Add summary to data
            crisis_data['summary'] = summary
            
        return crisis_data
        
    def summarize_crisis_data_batch(self, crisis_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Summarize the text content of multiple crisis events.
        
        Args:
            crisis_data_list: List of dictionaries containing crisis event data
            
        Returns:
            List of crisis data with added summaries
        """
        # Extract text for each crisis event
        texts = []
        valid_indices = []
        
        for i, crisis_data in enumerate(crisis_data_list):
            if 'text' in crisis_data and crisis_data['text']:
                texts.append(crisis_data['text'])
                valid_indices.append(i)
                
        # Generate summaries
        if texts:
            summaries = self.summarize_batch(texts)
            
            # Add summaries to crisis data
            for i, summary_idx in enumerate(valid_indices):
                crisis_data_list[summary_idx]['summary'] = summaries[i]
                
        return crisis_data_list

# Create a singleton instance
summarizer = Summarizer()

def get_summarizer():
    """Get the summarizer singleton."""
    return summarizer 