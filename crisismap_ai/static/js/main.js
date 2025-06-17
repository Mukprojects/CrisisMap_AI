// Main JavaScript for CrisisMap AI frontend

// Wait for DOM content to be loaded
document.addEventListener('DOMContentLoaded', () => {
    // Get DOM elements
    const searchForm = document.getElementById('search-form');
    const queryInput = document.getElementById('query');
    const resultsContainer = document.getElementById('results');
    const loadingIndicator = document.getElementById('loading');
    
    // Add event listener for form submission
    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Get query from input
        const query = queryInput.value.trim();
        
        if (query === '') {
            return;
        }
        
        // Show loading indicator
        showLoading();
        
        try {
            // Send request to API
            const response = await fetchLLMResponse(query);
            
            // Display results
            displayResults(query, response);
        } catch (error) {
            // Handle error
            displayError(error);
        } finally {
            // Hide loading indicator
            hideLoading();
        }
    });
    
    /**
     * Fetch LLM response from API
     * @param {string} query - User query
     * @returns {Promise<Object>} - Response from API
     */
    async function fetchLLMResponse(query) {
        const response = await fetch('/api/llm-response', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query }),
        });
        
        if (!response.ok) {
            throw new Error('Failed to get response from API');
        }
        
        return response.json();
    }
    
    /**
     * Display results in the results container
     * @param {string} query - User query
     * @param {Object} response - Response from API
     */
    function displayResults(query, response) {
        // Format the response text for display
        const formattedResponse = formatText(response.response);
        
        // Create sources HTML if available
        let sourcesHTML = '';
        if (response.sources && response.sources.length > 0) {
            sourcesHTML = `
                <div class="sources">
                    <h4>Sources</h4>
                    <ul>
                        ${response.sources.map(source => {
                            // Check if we have a URL to make a link
                            const hasUrl = source.url && source.url.startsWith('http');
                            
                            return `<li>
                                ${hasUrl 
                                    ? `<a href="${escapeHTML(source.url)}" target="_blank" rel="noopener noreferrer">
                                        <strong>${escapeHTML(source.title || 'Unknown Source')}</strong>
                                      </a>`
                                    : `<strong>${escapeHTML(source.title || 'Unknown Source')}</strong>`
                                }
                                ${source.source ? ` (${escapeHTML(source.source)})` : ''}
                            </li>`;
                        }).join('')}
                    </ul>
                </div>
            `;
        }
        
        // Create results HTML
        const resultsHTML = `
            <div class="query-container">
                <h3>Your Question</h3>
                <p>${escapeHTML(query)}</p>
            </div>
            <div class="answer-container">
                <h3>AI Response</h3>
                <div class="answer-text">
                    ${formattedResponse}
                </div>
                ${sourcesHTML}
            </div>
        `;
        
        // Update results container
        resultsContainer.innerHTML = resultsHTML;
    }
    
    /**
     * Display error message
     * @param {Error} error - Error object
     */
    function displayError(error) {
        resultsContainer.innerHTML = `
            <div class="error-container">
                <h3>Error</h3>
                <p>${error.message || 'An unknown error occurred'}</p>
                <p>Please try again later or with a different query.</p>
            </div>
        `;
    }
    
    /**
     * Show loading indicator
     */
    function showLoading() {
        loadingIndicator.classList.remove('hidden');
        resultsContainer.innerHTML = '';
    }
    
    /**
     * Hide loading indicator
     */
    function hideLoading() {
        loadingIndicator.classList.add('hidden');
    }
    
    /**
     * Format text with markdown-like syntax
     * @param {string} text - Text to format
     * @returns {string} - Formatted HTML
     */
    function formatText(text) {
        if (!text) return '';
        
        // Handle Markdown-style formatting
        let formattedText = text;
        
        // Convert ** text ** to <strong>
        formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Split by double newlines for paragraphs
        const paragraphs = formattedText.split(/\n\n+/);
        
        // Process each paragraph
        return paragraphs
            .map(para => {
                // Handle bullet lists (lines starting with - or *)
                if (para.match(/^[-*]\s/m)) {
                    const listItems = para.split(/\n/).map(line => {
                        if (line.match(/^[-*]\s/)) {
                            return `<li>${line.replace(/^[-*]\s/, '')}</li>`;
                        }
                        return line;
                    });
                    return `<ul>${listItems.join('')}</ul>`;
                }
                
                // Handle headers (lines starting with #)
                if (para.match(/^#+\s/)) {
                    const level = (para.match(/^(#+)/) || ['', ''])[1].length;
                    const validLevel = Math.min(Math.max(level, 1), 6);
                    const headerText = para.replace(/^#+\s/, '');
                    return `<h${validLevel + 2}>${headerText}</h${validLevel + 2}>`;
                }
                
                // Regular paragraph
                return `<p>${para.replace(/\n/g, '<br>')}</p>`;
            })
            .join('');
    }
    
    /**
     * Escape HTML special characters
     * @param {string} str - String to escape
     * @returns {string} - Escaped string
     */
    function escapeHTML(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }
}); 