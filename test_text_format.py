import re

def format_response_text(text: str) -> str:
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

def test_text_formatting():
    """Test the text formatting functionality."""
    # Sample text with lowercase sentences and spacing issues
    test_text = """**Information about war situation iran and israel**

more than 220 people have been killed in Israeli strikes so far, a health ministry says.israel's military said it had launched strikes on "dozens of military targets" in iran. the international nuclear watchdog has said it has not detected an increase in radiation levels. the conflict between the two countries continues to intensify on Monday. israel says its air force has hit dozens of targets in iran, including a nuclear facility.

**Sources:**
- What we know as Israel-Iran conflict intensifies - BBC
- Home New | Israel War Portal
- Iran Attacked Israel: A Preliminary Risk Assessment Report"""

    # Format the text
    formatted_text = format_response_text(test_text)
    
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

if __name__ == "__main__":
    test_text_formatting() 