import sys
import logging
from pathlib import Path

# Add the parent directory to the Python path for imports
sys.path.append(str(Path(__file__).parent))

# Import the LLM response generator
from crisismap_ai.models.llm_response import get_llm_response_generator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_text_formatting():
    """Test the text formatting functionality of the LLM response generator."""
    # Sample text with lowercase sentences and spacing issues
    test_text = """**Information about war situation iran and israel**

more than 220 people have been killed in Israeli strikes so far, a health ministry says.israel's military said it had launched strikes on "dozens of military targets" in iran. the international nuclear watchdog has said it has not detected an increase in radiation levels. the conflict between the two countries continues to intensify on Monday. israel says its air force has hit dozens of targets in iran, including a nuclear facility.

**Sources:**
- What we know as Israel-Iran conflict intensifies - BBC
- Home New | Israel War Portal
- Iran Attacked Israel: A Preliminary Risk Assessment Report"""

    # Get the LLM response generator
    response_generator = get_llm_response_generator()
    
    # Format the text
    formatted_text = response_generator._format_response_text(test_text)
    
    print("=== ORIGINAL TEXT ===")
    print(test_text)
    print("\n=== FORMATTED TEXT ===")
    print(formatted_text)
    
    # Print length comparison
    print("\n=== LENGTH COMPARISON ===")
    print(f"Original text length: {len(test_text)}")
    print(f"Formatted text length: {len(formatted_text)}")
    
    # Check for truncation
    original_content = test_text.split("\n\n")[1]  # Get the main content paragraph
    original_words = original_content.split()
    
    formatted_content = formatted_text.split("\n\n")[1]  # Get the main content paragraph
    formatted_words = formatted_content.split()
    
    print(f"\nOriginal content words: {len(original_words)}")
    print(f"Formatted content words: {len(formatted_words)}")
    
    if len(formatted_words) < len(original_words):
        print("\n!!! CONTENT WAS TRUNCATED !!!")
        print(f"Missing words: {' '.join(original_words[len(formatted_words):])}")
    
    # Compare sentences
    print("\n=== DETAILED COMPARISON ===")
    print("Original sentences:")
    orig_sentences = original_content.split('.')
    for i, sentence in enumerate(orig_sentences):
        if sentence.strip():
            print(f"{i+1}. {sentence.strip()}")
    
    print("\nFormatted sentences:")
    fmt_sentences = formatted_content.split('.')
    for i, sentence in enumerate(fmt_sentences):
        if sentence.strip():
            print(f"{i+1}. {sentence.strip()}")

if __name__ == "__main__":
    test_text_formatting() 