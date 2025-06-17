"""
Web scraping module for CrisisMap AI.

This module extracts disaster-related information from the web to supplement
the database content, especially for complex or recent queries.
"""
import sys
from pathlib import Path
import logging
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
import time
import random
import urllib.parse

# Add parent directory to system path for imports
sys.path.append(str(Path(__file__).parent))
from config import EMBEDDING_MODEL

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebScraper:
    """
    Scrapes disaster-related information from the web to enhance responses.
    """
    
    def __init__(self):
        """Initialize the web scraper."""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        # Pre-compile regex patterns
        self.url_pattern = re.compile(r'url\?q=([^&]+)')
        self.reference_pattern = re.compile(r'\[\d+\]')
        self.whitespace_pattern = re.compile(r'\s+')
    
    def search_disaster_info(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search for disaster information based on a query.
        
        Args:
            query: User's query about disasters
            max_results: Maximum number of sources to return
            
        Returns:
            List of dictionaries containing disaster information
        """
        try:
            # Prepare search terms for more accurate results
            search_terms = self._prepare_search_terms(query)
            
            # Extract data from different sources
            results = []
            
            # Try specific disaster site first if applicable
            specific_results = self._search_specific_disaster(query)
            if specific_results:
                results.extend(specific_results)
            
            # Try Wikipedia next for general information
            if len(results) < max_results:
                wiki_data = self._search_wikipedia(search_terms)
                if wiki_data:
                    results.append(wiki_data)
            
            # Try general search as a fallback
            if len(results) < max_results:
                general_results = self._general_search(search_terms, max_results - len(results))
                results.extend(general_results)
            
            # Return the requested number of results
            return results[:max_results]
        
        except Exception as e:
            logger.error(f"Error searching for disaster info: {e}")
            return []
    
    def _search_specific_disaster(self, query: str) -> List[Dict[str, Any]]:
        """Search for specific disaster types like California wildfires."""
        query_lower = query.lower()
        results = []
        
        # Check for California wildfires
        if "california" in query_lower and ("wildfire" in query_lower or "fire" in query_lower):
            year_match = re.search(r'20\d\d', query)
            year = year_match.group(0) if year_match else None
            
            if year:
                # Search for California wildfires in specific year
                cal_fire_data = self._search_cal_fire(year)
                if cal_fire_data:
                    results.append(cal_fire_data)
        
        return results
    
    def _search_cal_fire(self, year: str) -> Optional[Dict[str, Any]]:
        """Extract information about California wildfires from Cal Fire website."""
        try:
            # Try Cal Fire website
            url = f"https://www.fire.ca.gov/incidents/20{year[2:]}/"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                # Try alternative source
                return self._search_wiki_cal_fire(year)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract content
            content = ""
            
            # Look for incident summary
            summary_section = soup.select_one(".incident-summary, .summary, .incident-info")
            if summary_section:
                content += summary_section.get_text().strip() + "\n\n"
            
            # Look for main content
            main_content = soup.select(".incident-content p, .content p, .main-content p")
            if main_content:
                for p in main_content[:5]:  # Get first 5 paragraphs
                    content += p.get_text().strip() + "\n\n"
            
            # Look for statistics
            stats = soup.select(".incident-stats li, .stats li, .statistics li")
            if stats:
                content += "Statistics:\n"
                for stat in stats:
                    content += "- " + stat.get_text().strip() + "\n"
            
            if not content:
                # If we couldn't find specific content, return None
                return self._search_wiki_cal_fire(year)
            
            # Clean the content
            content = self._clean_content(content)
            
            return {
                "title": f"California Wildfires {year}",
                "source": "Cal Fire",
                "url": url,
                "content": content,
                "date_accessed": datetime.now().strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            logger.error(f"Error extracting from Cal Fire: {e}")
            return self._search_wiki_cal_fire(year)
    
    def _search_wiki_cal_fire(self, year: str) -> Optional[Dict[str, Any]]:
        """Extract information about California wildfires from Wikipedia."""
        try:
            search_term = f"California wildfires {year}"
            search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={search_term}&limit=1&namespace=0&format=json"
            response = requests.get(search_url, headers=self.headers)
            
            if response.status_code != 200:
                return None
                
            data = response.json()
            
            if not data or len(data) < 4 or not data[3]:
                return None
                
            # Get the first page URL
            page_url = data[3][0]
            page_title = data[1][0] if data[1] else f"California Wildfires {year}"
            
            # Now get the page content
            page_response = requests.get(page_url, headers=self.headers)
            
            if page_response.status_code != 200:
                return None
                
            soup = BeautifulSoup(page_response.text, 'html.parser')
            
            # Get the main content
            content = ""
            
            # First paragraph is often a good summary
            first_paragraph = soup.select_one("#mw-content-text p:not(.mw-empty-elt)")
            if first_paragraph:
                content += first_paragraph.get_text().strip() + "\n\n"
            
            # Look for casualty information
            casualty_section = None
            
            # Try to find casualty section by heading
            headings = soup.select("h2, h3, h4")
            for heading in headings:
                heading_text = heading.get_text().lower()
                if "casualt" in heading_text or "fatalities" in heading_text or "deaths" in heading_text:
                    casualty_section = heading
                    break
            
            if casualty_section:
                next_element = casualty_section.find_next()
                while next_element and next_element.name not in ["h2", "h3", "h4"]:
                    if next_element.name == "p":
                        content += next_element.get_text().strip() + "\n\n"
                    next_element = next_element.find_next()
            
            # Add any tables that might contain casualty data
            tables = soup.select("table.wikitable")
            for table in tables:
                table_text = table.get_text()
                if "casualt" in table_text.lower() or "fatalities" in table_text.lower() or "deaths" in table_text.lower():
                    # Extract table headings
                    headings = [th.get_text().strip() for th in table.select("th")]
                    
                    # Extract table rows
                    content += "Casualty data:\n"
                    for row in table.select("tr"):
                        cells = [td.get_text().strip() for td in row.select("td")]
                        if cells and len(cells) == len(headings):
                            # Format as key-value pairs
                            for i, heading in enumerate(headings):
                                content += f"{heading}: {cells[i]}\n"
                            content += "\n"
            
            # Clean up the content
            content = self._clean_content(content)
            
            return {
                "title": page_title,
                "source": "Wikipedia",
                "url": page_url,
                "content": content.strip(),
                "date_accessed": datetime.now().strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            logger.error(f"Error extracting California wildfire info from Wikipedia: {e}")
            return None
    
    def _prepare_search_terms(self, query: str) -> str:
        """Prepare search terms to improve results."""
        # Clean the query
        query = query.lower()
        
        # Check for specific disaster types
        if "california" in query and ("wildfire" in query or "fire" in query):
            # Extract year if present
            year_match = re.search(r'20\d\d', query)
            year = year_match.group(0) if year_match else "2020"  # Default to 2020 if no year
            return f"california wildfires {year} casualties deaths statistics"
            
        # Add relevant keywords based on query content
        if any(term in query for term in ["volcano", "eruption", "volcanic"]):
            return f"{query} volcanic eruption disaster information casualties deaths"
        elif any(term in query for term in ["earthquake", "seismic"]):
            return f"{query} earthquake magnitude disaster information casualties deaths"
        elif any(term in query for term in ["tsunami", "tidal wave"]):
            return f"{query} tsunami disaster information casualties deaths"
        elif any(term in query for term in ["hurricane", "cyclone", "typhoon"]):
            return f"{query} hurricane cyclone disaster information casualties deaths"
        elif any(term in query for term in ["flood", "flooding"]):
            return f"{query} flood disaster information casualties deaths"
        elif "wildfire" in query or "fire" in query:
            return f"{query} wildfire disaster information casualties deaths"
        else:
            return f"{query} natural disaster information casualties deaths"
    
    def _search_wikipedia(self, search_term: str) -> Optional[Dict[str, Any]]:
        """Extract information from Wikipedia."""
        try:
            # Encode the search term for URL
            encoded_search = urllib.parse.quote(search_term)
            
            # First, search for Wikipedia pages
            search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={encoded_search}&limit=1&namespace=0&format=json"
            response = requests.get(search_url, headers=self.headers)
            
            if response.status_code != 200:
                return None
                
            data = response.json()
            
            if not data or len(data) < 4 or not data[3]:
                return None
                
            # Get the first page URL
            page_url = data[3][0]
            page_title = data[1][0] if data[1] else "Wikipedia Result"
            
            # Now get the page content
            page_response = requests.get(page_url, headers=self.headers)
            
            if page_response.status_code != 200:
                return None
                
            soup = BeautifulSoup(page_response.text, 'html.parser')
            
            # Get the main content
            content = ""
            
            # First paragraph is often a good summary
            first_paragraph = soup.select_one("#mw-content-text p:not(.mw-empty-elt)")
            if first_paragraph:
                content += first_paragraph.get_text().strip() + "\n\n"
            
            # Add a few more paragraphs for context
            additional_paragraphs = soup.select("#mw-content-text p:not(.mw-empty-elt)")[:3]
            for para in additional_paragraphs:
                if para != first_paragraph:
                    content += para.get_text().strip() + "\n\n"
            
            # Look for casualty information if the query is about a disaster
            if any(term in search_term.lower() for term in ["disaster", "earthquake", "flood", "hurricane", "tsunami", "wildfire", "fire", "casualties"]):
                # Try to find casualty information
                for heading in soup.select("h2, h3, h4"):
                    heading_text = heading.get_text().lower()
                    if "casualt" in heading_text or "fatalities" in heading_text or "deaths" in heading_text:
                        content += f"# {heading.get_text().strip()}\n\n"
                        next_element = heading.find_next()
                        while next_element and next_element.name not in ["h2", "h3", "h4"]:
                            if next_element.name == "p":
                                content += next_element.get_text().strip() + "\n\n"
                            next_element = next_element.find_next()
            
            # Clean up the content
            content = self._clean_content(content)
            
            return {
                "title": page_title,
                "source": "Wikipedia",
                "url": page_url,
                "content": content.strip(),
                "date_accessed": datetime.now().strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            logger.error(f"Error extracting from Wikipedia: {e}")
            return None
    
    def _general_search(self, search_term: str, max_results: int = 2) -> List[Dict[str, Any]]:
        """Perform a general search and extract relevant information."""
        try:
            # Encode the search term for URL
            encoded_search = urllib.parse.quote(search_term)
            
            # Use DuckDuckGo instead of Google for better scraping success
            search_url = f"https://html.duckduckgo.com/html/?q={encoded_search}"
            
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
            
            response = requests.get(search_url, headers=self.headers)
            
            if response.status_code != 200:
                logger.warning(f"Search failed with status code {response.status_code}")
                # Try Google as fallback
                return self._google_search(search_term, max_results)
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            search_results = soup.select(".result")[:max_results*3]  # Get more than needed to filter
            
            for result in search_results:
                if len(results) >= max_results:
                    break
                    
                try:
                    # Extract title
                    title_elem = result.select_one(".result__title")
                    if not title_elem:
                        continue
                        
                    title = title_elem.get_text().strip()
                    
                    # Extract URL
                    link_elem = title_elem.select_one("a")
                    if not link_elem or not link_elem.has_attr('href'):
                        continue
                        
                    url = link_elem['href']
                    
                    # Extract snippet
                    snippet_elem = result.select_one(".result__snippet")
                    snippet = snippet_elem.get_text().strip() if snippet_elem else ""
                    
                    # Only include results that seem disaster-related
                    disaster_keywords = ['disaster', 'earthquake', 'volcano', 'tsunami', 'hurricane', 
                                        'flood', 'wildfire', 'fire', 'eruption', 'cyclone', 'typhoon',
                                        'casualties', 'deaths', 'killed', 'fatalities']
                                        
                    if any(keyword in title.lower() or keyword in snippet.lower() for keyword in disaster_keywords):
                        # Try to extract full content from the URL
                        full_content = ""
                        try:
                            full_content = self.extract_content_from_url(url)
                        except Exception as e:
                            logger.error(f"Error extracting content from URL {url}: {e}")
                            # Fall back to just using the snippet
                            full_content = snippet
                        
                        results.append({
                            "title": title,
                            "source": "Web Search Result",
                            "url": url,
                            "content": full_content if full_content else snippet,
                            "date_accessed": datetime.now().strftime("%Y-%m-%d")
                        })
                
                except Exception as e:
                    logger.error(f"Error processing search result: {e}")
                    continue
            
            # If we didn't find enough results, try Google
            if len(results) < max_results:
                google_results = self._google_search(search_term, max_results - len(results))
                results.extend(google_results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in general search: {e}")
            # Try Google as fallback
            return self._google_search(search_term, max_results)
    
    def _google_search(self, search_term: str, max_results: int = 2) -> List[Dict[str, Any]]:
        """Perform a Google search as a fallback."""
        try:
            # Encode the search term for URL
            encoded_search = urllib.parse.quote(search_term)
            
            search_url = f"https://www.google.com/search?q={encoded_search}"
            
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
            
            response = requests.get(search_url, headers=self.headers)
            
            if response.status_code != 200:
                logger.warning(f"Google search failed with status code {response.status_code}")
                return []
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            search_divs = soup.select("div.g")[:max_results*3]  # Get more than needed to filter
            
            for div in search_divs:
                if len(results) >= max_results:
                    break
                    
                try:
                    # Extract title and URL
                    title_elem = div.select_one("h3")
                    if not title_elem:
                        continue
                        
                    title = title_elem.get_text().strip()
                    
                    # Extract URL
                    link_elem = div.select_one("a")
                    if not link_elem or not link_elem.has_attr('href'):
                        continue
                        
                    url = link_elem['href']
                    if url.startswith('/url?'):
                        url_match = self.url_pattern.search(url)
                        if url_match:
                            url = url_match.group(1)
                        else:
                            continue
                    
                    # Extract snippet
                    snippet_elem = div.select_one("div.VwiC3b, div.IsZvec")
                    snippet = snippet_elem.get_text().strip() if snippet_elem else ""
                    
                    # Only include results that seem disaster-related
                    disaster_keywords = ['disaster', 'earthquake', 'volcano', 'tsunami', 'hurricane', 
                                        'flood', 'wildfire', 'fire', 'eruption', 'cyclone', 'typhoon',
                                        'casualties', 'deaths', 'killed', 'fatalities']
                                        
                    if any(keyword in title.lower() or keyword in snippet.lower() for keyword in disaster_keywords):
                        # Try to extract full content from the URL
                        full_content = ""
                        try:
                            full_content = self.extract_content_from_url(url)
                        except Exception as e:
                            logger.error(f"Error extracting content from URL {url}: {e}")
                            # Fall back to just using the snippet
                            full_content = snippet
                        
                        results.append({
                            "title": title,
                            "source": "Web Search Result",
                            "url": url,
                            "content": full_content if full_content else snippet,
                            "date_accessed": datetime.now().strftime("%Y-%m-%d")
                        })
                
                except Exception as e:
                    logger.error(f"Error processing Google search result: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error in Google search: {e}")
            return []
    
    def extract_content_from_url(self, url: str) -> Optional[str]:
        """Extract main content from a URL."""
        try:
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
            
            response = requests.get(url, headers=self.headers, timeout=5)
            
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts, styles, and comments
            for element in soup(['script', 'style', 'header', 'footer', 'nav']):
                element.extract()
                
            # Extract the main content
            main_content = soup.select_one("main, article, #content, .content, #main, .main")
            
            if main_content:
                text = main_content.get_text()
            else:
                # Fallback to all paragraph text
                paragraphs = soup.select("p")
                text = "\n\n".join(p.get_text().strip() for p in paragraphs)
            
            # Clean the text
            text = self._clean_content(text)
            
            return text
            
        except Exception as e:
            logger.error(f"Error extracting content from URL: {e}")
            return None
    
    def _clean_content(self, text: str) -> str:
        """Clean the extracted content."""
        if not text:
            return ""
            
        # Remove reference numbers
        text = self.reference_pattern.sub('', text)
        
        # Normalize whitespace
        text = self.whitespace_pattern.sub(' ', text)
        
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()

# Create a singleton instance
web_scraper = WebScraper()

def get_web_scraper():
    """Get the web scraper singleton."""
    return web_scraper 