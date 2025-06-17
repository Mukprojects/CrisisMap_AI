"""
LLM response generation module for CrisisMap AI.
"""
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import torch
import logging
import json
import os
import traceback
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to system path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config import RESPONSE_MODEL
from database.db_operations import get_crisis_event_ops
from embedding.embedding_generator import get_embedding_generator
from web_scraper import get_web_scraper
from models.summarization import get_summarizer

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
except ImportError:
    logger.error("Failed to import transformers. Make sure it's installed: pip install transformers")
    
class LLMResponseGenerator:
    """
    LLM response generation for crisis data queries using Phi-3-mini-4k-instruct.
    """
    
    def __init__(self, model_name: str = RESPONSE_MODEL):
        """
        Initialize the LLM response generator.
        
        Args:
            model_name: Name of the Hugging Face model to use
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.model_loaded = False
        self.summarizer_loaded = False
        
    def _load_model(self):
        """Load the LLM model and tokenizer."""
        try:
            # Check if CUDA is available
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logger.info(f"Loading LLM response model on {device}...")
            
            # Initialize the model with low precision to save memory
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if device == 'cuda' else torch.float32,
                low_cpu_mem_usage=True,
                device_map="auto" if device == 'cuda' else None,
                trust_remote_code=True
            )
            
            # Set the device for the model
            logger.info(f"Device set to use {device}")
            if device == 'cpu':
                self.model = self.model.to('cpu')
            
            logger.info(f"LLM response model '{self.model_name}' loaded successfully.")
            self.model_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Error loading LLM response model: {e}")
            logger.error(traceback.format_exc())
            logger.error("Using summarizer without LLM model.")
            return False
            
    def _load_summarizer(self):
        """Load the summarizer if not already loaded."""
        try:
            self.summarizer = get_summarizer()
            self.summarizer_loaded = True
            return True
        except Exception as e:
            logger.error(f"Error loading summarizer: {e}")
            logger.error(traceback.format_exc())
            return False
            
    def generate_response(self, user_query: str, context_data: List[Dict[str, Any]], web_data: List[Dict[str, Any]] = None) -> str:
        """
        Generate a response to the user query based on relevant crisis data.
        
        Args:
            user_query: User's query about crisis events
            context_data: List of crisis events to use as context
            web_data: List of web search results to use as additional context
            
        Returns:
            Generated response
        """
        # Make sure we have data - either context_data or web_data
        if not context_data and not web_data:
            # Try to get web data if we don't have it already
            try:
                if not web_data:
                    web_scraper = get_web_scraper()
                    web_data = web_scraper.search_disaster_info(user_query, max_results=5)
                    logger.info(f"Retrieved {len(web_data)} web results for query: {user_query}")
            except Exception as e:
                logger.error(f"Error retrieving web data: {e}")
                logger.error(traceback.format_exc())
                
            # If we still don't have any data, return a simple message
            if not context_data and (not web_data or len(web_data) == 0):
                return f"I couldn't find any information about '{user_query}'. Please try a different query or check your internet connection."
        
        # If we have web data, we'll prioritize that
        if web_data and len(web_data) > 0:
            response = self._generate_web_based_response(user_query, web_data, context_data)
            return self._format_response_text(response)
            
        # If we only have database data, use that
        if context_data and len(context_data) > 0:
            response = self._generate_db_based_response(user_query, context_data)
            return self._format_response_text(response)
            
        # This should never happen given the checks above
        return f"I couldn't find any information about '{user_query}'. Please try a different query."
    
    def _generate_web_based_response(self, user_query: str, web_data: List[Dict[str, Any]], context_data: List[Dict[str, Any]] = None) -> str:
        """Generate a response based primarily on web data."""
        try:
            # First, ensure we have the summarizer loaded
            if not self.summarizer_loaded:
                self._load_summarizer()
                
            # Combine all web data content for a comprehensive response
            all_content = ""
            
            # Keep track of sources for citation
            sources = []
            
            for data in web_data:
                if "content" in data and data["content"]:
                    all_content += data["content"] + " \n\n"
                    
                if "title" in data and "source" in data:
                    sources.append(f"- {data.get('title', 'Unknown')} ({data.get('source', 'Web')})")
            
            # Add database content if available
            if context_data and len(context_data) > 0:
                for event in context_data[:3]:  # Limit to top 3 database results
                    if "text" in event and event["text"]:
                        all_content += event["text"] + " \n\n"
                    elif "summary" in event and event["summary"]:
                        all_content += event["summary"] + " \n\n"
                        
                    if "title" in event:
                        sources.append(f"- {event.get('title', 'Database record')}")
            
            # Try using the LLM if available
            if not self.model_loaded:
                success = self._load_model()
                
            if self.model_loaded:
                try:
                    # Create a simple prompt
                    prompt = f"""
I need information about: {user_query}

Please provide a clear, comprehensive answer based only on the following information:

{all_content}

Summarize the most important points and focus specifically on answering the query. Make your response well-structured, factual, and concise. Use proper capitalization for sentences and ensure the text is professionally formatted.
"""
                    
                    # Use the LLM to generate a response, avoiding the DynamicCache issue
                    inputs = self.tokenizer(prompt, return_tensors="pt")
                    inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
                    
                    # Use a completely different generation approach to avoid the DynamicCache error
                    generation_config = {
                        "max_new_tokens": 500,
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "do_sample": True,
                        "pad_token_id": self.tokenizer.eos_token_id
                    }
                    
                    with torch.no_grad():
                        output_ids = self.model.generate(
                            inputs.input_ids,
                            attention_mask=inputs.attention_mask,
                            **generation_config
                        )
                    
                    response_text = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
                    
                    # Remove the prompt part
                    if response_text.startswith(prompt):
                        response_text = response_text[len(prompt):].strip()
                        
                    # Add sources if we have them
                    if sources:
                        response_text += "\n\n**Sources:**\n" + "\n".join(sources)
                        
                    return response_text
                    
                except Exception as e:
                    logger.error(f"Error generating with LLM: {e}")
                    logger.error(traceback.format_exc())
                    # Fall back to summarizer
            
            # If LLM failed or is not available, use the summarizer directly
            try:
                if len(all_content.split()) > 50:
                    summary = self.summarizer.summarize(all_content, max_length=300, min_length=100)
                    
                    # Add query context to the summary
                    final_response = f"**Information about {user_query}**\n\n{summary}"
                    
                    # Add sources if we have them
                    if sources:
                        final_response += "\n\n**Sources:**\n" + "\n".join(sources)
                        
                    return final_response
                else:
                    # If content is too short, just use it directly
                    return f"**Information about {user_query}**\n\n{all_content.strip()}"
            except Exception as e:
                logger.error(f"Error summarizing content: {e}")
                logger.error(traceback.format_exc())
                
                # In case everything fails, return the raw content truncated
                words = all_content.split()[:300]
                truncated_content = " ".join(words)
                if len(words) < len(all_content.split()):
                    truncated_content += "..."
                    
                return f"**Information about {user_query}**\n\n{truncated_content}"
                
        except Exception as e:
            logger.error(f"Error generating web-based response: {e}")
            logger.error(traceback.format_exc())
            return f"I encountered a technical issue while processing information about '{user_query}'. Please try again."
    
    def _generate_db_based_response(self, user_query: str, context_data: List[Dict[str, Any]]) -> str:
        """Generate a response based on database data."""
        try:
            # Format the context data for the prompt
            formatted_context = self._format_context(context_data)
            
            # If we have a model, try to use it
            if not self.model_loaded:
                success = self._load_model()
                
            if self.model_loaded:
                try:
                    # Create a prompt for the model
                    prompt = f"""
I need information about: {user_query}

Based on the following crisis data, please provide a helpful, accurate, and concise answer:

{formatted_context}

Make your response well-structured, factual, and directly focused on answering the query. Ensure proper capitalization and formatting for a professional presentation.
"""
                    
                    # Generate with the model, avoiding the DynamicCache error
                    inputs = self.tokenizer(prompt, return_tensors="pt")
                    inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
                    
                    # Use a completely different generation approach to avoid the DynamicCache error
                    generation_config = {
                        "max_new_tokens": 500,
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "do_sample": True,
                        "pad_token_id": self.tokenizer.eos_token_id
                    }
                    
                    with torch.no_grad():
                        output_ids = self.model.generate(
                            inputs.input_ids,
                            attention_mask=inputs.attention_mask,
                            **generation_config
                        )
                    
                    response_text = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
                    
                    # Remove the prompt part
                    if response_text.startswith(prompt):
                        response_text = response_text[len(prompt):].strip()
                        
                    return response_text
                    
                except Exception as e:
                    logger.error(f"Error generating with LLM: {e}")
                    logger.error(traceback.format_exc())
                    # Fall back to summarizer
            
            # If we don't have a model or it failed, extract key information from context
            all_text = ""
            for event in context_data:
                if "text" in event and event["text"]:
                    all_text += event["text"] + " \n\n"
                elif "summary" in event and event["summary"]:
                    all_text += event["summary"] + " \n\n"
            
            # Try to summarize if we have enough text
            if all_text and len(all_text.split()) > 30:
                if not self.summarizer_loaded:
                    self._load_summarizer()
                    
                if self.summarizer_loaded:
                    summary = self.summarizer.summarize(all_text, max_length=300, min_length=100)
                    return f"**Information about {user_query}**\n\n{summary}"
            
            # If we can't summarize, create a structured response from the data
            response = f"**Information about {user_query}**\n\n"
            
            for i, event in enumerate(context_data[:3], 1):
                response += f"**Event {i}: {event.get('title', 'Unnamed event')}**\n"
                
                if "date" in event and event["date"]:
                    response += f"Date: {event['date']}\n"
                    
                if "location" in event and event["location"]:
                    response += f"Location: {event['location']}\n"
                    
                if "summary" in event and event["summary"]:
                    response += f"Summary: {event['summary']}\n"
                elif "text" in event and event["text"]:
                    text = event["text"]
                    if len(text.split()) > 100:
                        words = text.split()[:100]
                        text = " ".join(words) + "..."
                    response += f"Information: {text}\n"
                
                response += "\n"
                
            return response
            
        except Exception as e:
            logger.error(f"Error generating database-based response: {e}")
            logger.error(traceback.format_exc())
            
            # Create a very simple response with just the titles
            response = f"I found the following information about '{user_query}':\n\n"
            
            for i, event in enumerate(context_data[:5], 1):
                title = event.get('title', f"Event {i}")
                date = event.get('date', '')
                
                response += f"{i}. {title}"
                if date:
                    response += f" ({date})"
                response += "\n"
                
            return response
    
    def _format_context(self, context_data: List[Dict[str, Any]]) -> str:
        """Format the context data for the prompt."""
        formatted_items = []
        
        for i, event in enumerate(context_data, 1):
            item = f"Event {i}:\n"
            
            # Add title if available
            if "title" in event and event["title"]:
                item += f"Title: {event['title']}\n"
                
            # Add event type if available
            if "event_type" in event and event["event_type"]:
                item += f"Type: {event['event_type']}\n"
            elif "category" in event and event["category"]:
                item += f"Type: {event['category']}\n"
            
            # Add location if available
            location_info = []
            if "country" in event and event["country"]:
                location_info.append(event["country"])
            if "location" in event and event["location"]:
                location_info.append(event["location"])
            if location_info:
                item += f"Location: {', '.join(location_info)}\n"
            
            # Add date if available
            if "date" in event and event["date"]:
                item += f"Date: {event['date']}\n"
            
            # Add summary if available, otherwise use text
            if "summary" in event and event["summary"]:
                item += f"Summary: {event['summary']}\n"
            elif "text" in event and event["text"]:
                item += f"Information: {event['text']}\n"
                
            # Add casualties/impacts if available
            if "casualties" in event and event["casualties"]:
                item += f"Casualties: {event['casualties']}\n"
            if "impacts" in event and event["impacts"]:
                item += f"Impacts: {event['impacts']}\n"
                
            # Add any additional data
            if "data" in event and event["data"] and isinstance(event["data"], dict):
                for key, value in event["data"].items():
                    if key not in ["embedding"] and value:  # Skip embedding vectors
                        item += f"{key}: {value}\n"
            
            formatted_items.append(item)
            
        return "\n".join(formatted_items)
        
    def _format_web_data(self, web_data: List[Dict[str, Any]]) -> str:
        """Format web data for the prompt."""
        formatted_items = []
        
        for i, data in enumerate(web_data, 1):
            item = f"Web Source {i}:\n"
            
            # Add title if available
            if "title" in data and data["title"]:
                item += f"Title: {data['title']}\n"
                
            # Add source if available
            if "source" in data and data["source"]:
                item += f"Source: {data['source']}\n"
                
            # Add content if available
            if "content" in data and data["content"]:
                item += f"Content: {data['content']}\n"
                
            # Add date if available
            if "date" in data and data["date"]:
                item += f"Date: {data['date']}\n"
            elif "date_accessed" in data and data["date_accessed"]:
                item += f"Date Accessed: {data['date_accessed']}\n"
                
            formatted_items.append(item)
            
        return "\n".join(formatted_items)
    
    def _format_response_text(self, text: str) -> str:
        """Format response text for better readability with proper capitalization and formatting."""
        if not text:
            return text
            
        # Split into header and main content if there's a header
        header = ""
        content = text
        
        # Check if there's a header
        if text.startswith("**") and "\n\n" in text:
            parts = text.split("\n\n", 1)
            if len(parts) == 2:
                header = parts[0] + "\n\n"
                content = parts[1]
        
        # Process main content
        processed_content = content
        
        # Handle sources section separately
        sources_section = ""
        if "\n\n**Sources:**\n" in processed_content:
            parts = processed_content.split("\n\n**Sources:**\n", 1)
            processed_content = parts[0]
            sources_section = "\n\n**Sources:**\n" + parts[1] if len(parts) > 1 else ""
        
        # Improve sentence boundary detection with better regex
        # This pattern looks for periods, exclamation marks, or question marks followed by a space or newline
        sentences = re.split(r'([.!?][\s\n]+)', processed_content)
        formatted_parts = []
        
        # Process each sentence and maintain the punctuation
        i = 0
        while i < len(sentences):
            if i < len(sentences) - 1 and re.match(r'[.!?][\s\n]+', sentences[i+1]):
                # Current part is sentence content, next part is the punctuation
                sentence = sentences[i] + sentences[i+1]
                # Only capitalize if not already capitalized or is not part of a proper noun with apostrophe
                if sentence and not sentence.strip().startswith(("'", '"')) and len(sentence.strip()) > 0:
                    # Handle special case for contractions like "israel's" -> "Israel's"
                    if re.match(r'^[a-z]', sentence.strip()):
                        sentence = sentence[0].upper() + sentence[1:]
                formatted_parts.append(sentence)
                i += 2
            else:
                # Only add non-empty parts
                if sentences[i].strip():
                    # Capitalize standalone sentences too
                    if re.match(r'^[a-z]', sentences[i].strip()):
                        sentences[i] = sentences[i][0].upper() + sentences[i][1:]
                    formatted_parts.append(sentences[i])
                i += 1
        
        # Join all parts together
        formatted_content = "".join(formatted_parts)
        
        # Further improve capitalization for sentences without standard punctuation
        # Split by newlines and process each paragraph
        paragraphs = formatted_content.split("\n\n")
        formatted_paragraphs = []
        
        for paragraph in paragraphs:
            if paragraph.strip():
                # Clean up any single newlines within paragraphs
                clean_paragraph = re.sub(r'\s*\n\s*', ' ', paragraph.strip())
                
                # Split into sentences (if any) by looking for periods followed by spaces
                para_sentences = re.split(r'([.!?][\s]+)', clean_paragraph)
                para_formatted = []
                
                i = 0
                while i < len(para_sentences):
                    if i < len(para_sentences) - 1 and re.match(r'[.!?][\s]+', para_sentences[i+1]):
                        # Current part + punctuation
                        sentence = para_sentences[i] + para_sentences[i+1]
                        
                        # Fix capitalization at beginning of each sentence
                        if i == 0 and sentence and len(sentence) > 0:
                            # Ensure first character is uppercase
                            if re.match(r'^[a-z]', sentence):
                                sentence = sentence[0].upper() + sentence[1:]
                                
                        para_formatted.append(sentence)
                        i += 2
                    else:
                        if para_sentences[i].strip():
                            # For the first sentence in paragraph, ensure it starts with uppercase
                            if i == 0 and re.match(r'^[a-z]', para_sentences[i]):
                                para_sentences[i] = para_sentences[i][0].upper() + para_sentences[i][1:]
                            para_formatted.append(para_sentences[i])
                        i += 1
                
                # Ensure the first letter of the paragraph is capitalized
                clean_paragraph = "".join(para_formatted)
                if clean_paragraph and re.match(r'^[a-z]', clean_paragraph):
                    clean_paragraph = clean_paragraph[0].upper() + clean_paragraph[1:]
                
                formatted_paragraphs.append(clean_paragraph)
        
        # Join paragraphs with double newlines
        final_content = "\n\n".join(formatted_paragraphs)
        
        # Fix specific capitalization issues in the text
        # Fix country names, proper nouns, etc.
        for proper_noun in ["israel", "iran", "israeli", "iranian", "monday", "tuesday", "wednesday", 
                            "thursday", "friday", "saturday", "sunday"]:
            pattern = r'(?<![A-Za-z])' + proper_noun + r'(?![A-Za-z])'
            replacement = proper_noun.capitalize()
            final_content = re.sub(pattern, replacement, final_content)
        
        # Special handling for contractions like "israel's" -> "Israel's"
        for proper_noun in ["israel", "iran", "israeli", "iranian"]:
            pattern = r'(?<![A-Za-z])' + proper_noun + r"'s"
            replacement = proper_noun.capitalize() + "'s"
            final_content = re.sub(pattern, replacement, final_content)
        
        # Reassemble the full response
        final_response = header + final_content + sources_section
        
        return final_response
    
    def find_and_respond(self, user_query: str, max_results: int = 5) -> str:
        """
        Find relevant crisis data and generate a response.
        
        Args:
            user_query: User's query about crisis events
            max_results: Maximum number of relevant documents to retrieve
            
        Returns:
            Generated response
        """
        try:
            # Start with web scraping to get real-time data
            web_data = []
            try:
                web_scraper = get_web_scraper()
                web_data = web_scraper.search_disaster_info(user_query, max_results=3)
                logger.info(f"Retrieved {len(web_data)} web results for query: {user_query}")
            except Exception as e:
                logger.error(f"Error retrieving web data: {e}")
                logger.error(traceback.format_exc())
            
            # Get embedding generator
            embedding_generator = get_embedding_generator()
            
            # Generate embedding for query
            query_embedding = embedding_generator.generate_embedding(user_query)
            
            # Get crisis event operations
            crisis_ops = get_crisis_event_ops()
            
            # Perform vector search
            results = crisis_ops.search_by_vector(query_embedding, limit=max_results)
            
            if not results:
                # Try text search as fallback
                results = crisis_ops.search_by_text(user_query, limit=max_results)
            
            # Generate response prioritizing web data
            response = self.generate_response(user_query, results, web_data)
            
            # Format the response for better readability
            return response
            
        except Exception as e:
            logger.error(f"Error in find_and_respond: {e}")
            logger.error(traceback.format_exc())
            
            # Return user-friendly error message
            return f"I encountered an error while searching for information about '{user_query}'. Please try again with a different query."

# Create a singleton instance
llm_response_generator = LLMResponseGenerator()

def get_llm_response_generator():
    """Get the LLM response generator singleton."""
    return llm_response_generator 