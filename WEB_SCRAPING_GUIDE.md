CrisisMap AI: Web Scraping & Enhanced Responses
This guide explains the web scraping and enhanced response features added to CrisisMap AI to provide more accurate, up-to-date information about natural disasters.

Overview
The web scraping functionality enhances CrisisMap AI's capabilities by:

Supplementing the MongoDB database with real-time information from the web
Providing more comprehensive and accurate responses for complex queries
Creating better-formatted, summarized responses with proper citations
How It Works
Web Scraping Module
The web_scraper.py module:

Uses Beautiful Soup 4 to extract disaster information from multiple sources
Prioritizes authoritative sources like Wikipedia and ReliefWeb
Formats and cleans extracted content for LLM processing
Provides proper attribution with source information
Enhanced LLM Response Generator
The improved llm_response.py module:

Fixes Phi-3 model compatibility issues by using direct token generation
Integrates web scraping data with database results
Produces more concise, readable responses through summarization
Provides better fallback responses when the LLM model is unavailable
API Integration
The updated API endpoint:

Handles web scraping in parallel with database searches
Returns sources in the response for proper attribution
Provides more robust error handling
Usage
Basic Query
POST /api/llm-response

{
  "query": "What was the impact of the 2011 Tōhoku earthquake and tsunami?"
}
Response Format
{
  "query": "What was the impact of the 2011 Tōhoku earthquake and tsunami?",
  "response": "The 2011 Tōhoku earthquake and tsunami occurred on March 11, 2011, with a magnitude of 9.0-9.1. It caused widespread devastation across northeastern Japan, resulting in over 19,000 deaths, mainly from the tsunami which reached heights of up to 40 meters in some areas. The disaster triggered a Level 7 nuclear meltdown at the Fukushima Daiichi Nuclear Power Plant, leading to the evacuation of hundreds of thousands of residents. Economic damages exceeded $360 billion, making it the costliest natural disaster in world history. Infrastructure damage was extensive, with over a million buildings damaged or destroyed, and significant disruptions to water, electricity, and transportation systems.",
  "sources": [
    {
      "title": "2011 Tōhoku earthquake and tsunami",
      "source": "Wikipedia",
      "url": "https://en.wikipedia.org/wiki/2011_T%C5%8Dhoku_earthquake_and_tsunami"
    },
    {
      "title": "Japan Earthquake and Tsunami of 2011",
      "source": "Web Search Result",
      "url": "https://www.britannica.com/event/Japan-earthquake-and-tsunami-of-2011"
    }
  ]
}
Error Handling
The system will gracefully fall back to:

Database-only searches if web scraping fails
Text-based search if vector search is unavailable
Enhanced fallback responses if the LLM model fails
User-friendly error messages for any system failures
Requirements
The following packages are required for the web scraping functionality:

beautifulsoup4>=4.10.0
requests>=2.25.0
These have been added to the requirements.txt file.

Security Considerations
The web scraper follows responsible web scraping practices
User-Agent headers are properly set to identify the application
Rate limiting is implemented to avoid overloading source websites
Content is properly attributed with source information
Future Improvements
Potential enhancements to the web scraping functionality:

Integration with more specialized disaster information APIs
Caching frequently requested information to reduce external requests
More sophisticated content extraction and cleaning
Entity extraction to better structure disaster information
