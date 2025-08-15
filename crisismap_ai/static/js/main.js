/**
 * CrisisMap AI - Main JavaScript Application
 * Modern, accessible, and performant crisis monitoring interface
 */

class CrisisMapApp {
    constructor() {
        this.init();
        this.bindEvents();
        this.setupAccessibility();
        this.registerServiceWorker();
    }

    init() {
        this.form = document.getElementById('search-form');
        this.queryInput = document.getElementById('query');
        this.resultsContainer = document.getElementById('results');
        this.loadingElement = document.getElementById('loading');
        this.submitButton = this.form.querySelector('button[type="submit"]');
        
        this.isLoading = false;
        this.searchHistory = this.loadSearchHistory();
        this.debounceTimer = null;
        
        // API endpoints
        this.endpoints = {
            search: '/api/search',
            llmResponse: '/api/llm-response',
            health: '/api/health'
        };
        
        console.log('CrisisMap AI initialized successfully');
    }

    bindEvents() {
        // Form submission
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // Input enhancements
        this.queryInput.addEventListener('input', (e) => this.handleInputChange(e));
        this.queryInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        this.queryInput.addEventListener('focus', () => this.handleInputFocus());
        this.queryInput.addEventListener('blur', () => this.handleInputBlur());
        
        // Example questions
        document.querySelectorAll('.welcome-message li').forEach(li => {
            li.addEventListener('click', () => this.fillQuery(li));
        });
        
        // Window events
        window.addEventListener('online', () => this.handleOnlineStatus(true));
        window.addEventListener('offline', () => this.handleOnlineStatus(false));
        window.addEventListener('beforeunload', () => this.saveSearchHistory());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleGlobalKeyboard(e));
    }

    setupAccessibility() {
        // Announce important changes to screen readers
        this.announcer = document.createElement('div');
        this.announcer.setAttribute('aria-live', 'polite');
        this.announcer.setAttribute('aria-atomic', 'true');
        this.announcer.className = 'sr-only';
        document.body.appendChild(this.announcer);
        
        // Focus management
        this.setupFocusManagement();
    }

    setupFocusManagement() {
        // Trap focus in modals/loading states
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab' && this.isLoading) {
                e.preventDefault();
                this.submitButton.focus();
            }
        });
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        if (this.isLoading) {
            return;
        }
        
        const query = this.queryInput.value.trim();
        if (!query) {
            this.showError('Please enter a question about crises or disasters');
            this.queryInput.focus();
            return;
        }
        
        await this.performSearch(query);
    }

    async performSearch(query) {
        try {
            this.setLoadingState(true);
            this.announce('Searching for crisis information...');
            
            // Add to search history
            this.addToSearchHistory(query);
            
            // Clear previous results
            this.clearResults();
            
            // Show query
            this.displayQuery(query);
            
            // Check network status
            if (!navigator.onLine) {
                throw new Error('No internet connection. Please check your network and try again.');
            }
            
            // Perform search with timeout
            const searchPromise = this.searchCrises(query);
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Search timed out. Please try again.')), 30000)
            );
            
            const results = await Promise.race([searchPromise, timeoutPromise]);
            
            if (results && results.length > 0) {
                // Get AI response
                const llmResponse = await this.getLLMResponse(query, results);
                this.displayResults(query, results, llmResponse);
                this.announce(`Found ${results.length} relevant crisis events`);
            } else {
                this.showNoResults(query);
                this.announce('No relevant crisis events found');
            }
            
        } catch (error) {
            console.error('Search error:', error);
            this.showError(error.message || 'An error occurred while searching. Please try again.');
            this.announce('Search failed. Please try again.');
        } finally {
            this.setLoadingState(false);
        }
    }

    async searchCrises(query) {
        const response = await fetch(this.endpoints.search, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                limit: 10,
                threshold: 0.7
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Search failed with status ${response.status}`);
        }
        
        const data = await response.json();
        return data.results || [];
    }

    async getLLMResponse(query, results) {
        try {
            const response = await fetch(this.endpoints.llmResponse, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    context: results.slice(0, 5) // Limit context for performance
                })
            });
            
            if (!response.ok) {
                console.warn('LLM response failed, continuing without AI analysis');
                return null;
            }
            
            const data = await response.json();
            return data.response || null;
        } catch (error) {
            console.warn('LLM response error:', error);
            return null;
        }
    }

    setLoadingState(loading) {
        this.isLoading = loading;
        
        if (loading) {
            this.loadingElement.classList.remove('hidden');
            this.submitButton.disabled = true;
            this.submitButton.innerHTML = '<i class="fas fa-spinner fa-spin" aria-hidden="true"></i> <span>Searching...</span>';
            this.queryInput.setAttribute('aria-busy', 'true');
        } else {
            this.loadingElement.classList.add('hidden');
            this.submitButton.disabled = false;
            this.submitButton.innerHTML = '<i class="fas fa-search" aria-hidden="true"></i> <span>Search</span>';
            this.queryInput.setAttribute('aria-busy', 'false');
        }
    }

    displayQuery(query) {
        const queryContainer = document.createElement('div');
        queryContainer.className = 'query-container fade-in';
        queryContainer.innerHTML = `
            <h3>Your Question</h3>
            <p>"${this.escapeHtml(query)}"</p>
        `;
        this.resultsContainer.appendChild(queryContainer);
    }

    displayResults(query, results, llmResponse) {
        // Display AI response if available
        if (llmResponse) {
            this.displayLLMResponse(llmResponse);
        }
        
        // Display search results
        this.displaySearchResults(results);
        
        // Smooth scroll to results
        this.resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    displayLLMResponse(response) {
        const answerContainer = document.createElement('div');
        answerContainer.className = 'answer-container fade-in';
        
        const formattedResponse = this.formatLLMResponse(response);
        
        answerContainer.innerHTML = `
            <h3>AI Analysis</h3>
            <div class="answer-text">${formattedResponse}</div>
        `;
        
        this.resultsContainer.appendChild(answerContainer);
    }

    displaySearchResults(results) {
        if (!results || results.length === 0) return;
        
        const sourcesContainer = document.createElement('div');
        sourcesContainer.className = 'sources slide-in';
        
        const sourcesList = results.map(result => {
            const title = result.title || result.event_name || 'Crisis Event';
            const score = result.score ? ` (Relevance: ${Math.round(result.score * 100)}%)` : '';
            
            return `
                <li>
                    <strong>${this.escapeHtml(title)}</strong>${score}
                    <br>
                    <small>${this.escapeHtml(this.truncateText(result.description || result.summary || '', 200))}</small>
                    ${result.date ? `<br><small>Date: ${this.formatDate(result.date)}</small>` : ''}
                    ${result.location ? `<br><small>Location: ${this.escapeHtml(result.location)}</small>` : ''}
                </li>
            `;
        }).join('');
        
        sourcesContainer.innerHTML = `
            <h4>Related Crisis Events</h4>
            <ul>${sourcesList}</ul>
        `;
        
        this.resultsContainer.appendChild(sourcesContainer);
    }

    showNoResults(query) {
        const noResultsContainer = document.createElement('div');
        noResultsContainer.className = 'answer-container fade-in';
        noResultsContainer.innerHTML = `
            <h3>No Results Found</h3>
            <div class="answer-text">
                <p>We couldn't find any crisis events matching your query: <strong>"${this.escapeHtml(query)}"</strong></p>
                <p>Try:</p>
                <ul>
                    <li>Using different keywords</li>
                    <li>Being more specific about location or time period</li>
                    <li>Checking the spelling of your query</li>
                    <li>Using one of the example questions above</li>
                </ul>
            </div>
        `;
        this.resultsContainer.appendChild(noResultsContainer);
    }

    showError(message) {
        this.clearResults();
        
        const errorContainer = document.createElement('div');
        errorContainer.className = 'error-container fade-in';
        errorContainer.innerHTML = `
            <h3>Error</h3>
            <p>${this.escapeHtml(message)}</p>
        `;
        this.resultsContainer.appendChild(errorContainer);
    }

    clearResults() {
        this.resultsContainer.innerHTML = '';
    }

    formatLLMResponse(response) {
        if (!response) return '';
        
        // Convert markdown-like formatting to HTML
        return response
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/^/, '<p>')
            .replace(/$/, '</p>');
    }

    fillQuery(element) {
        const query = element.textContent.trim();
        this.queryInput.value = query;
        this.queryInput.focus();
        this.announce(`Query filled: ${query}`);
    }

    handleKeyPress(event, element) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            this.fillQuery(element);
        }
    }

    handleInputChange(e) {
        // Debounced input validation
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            this.validateInput(e.target.value);
        }, 300);
    }

    handleKeyDown(e) {
        // Enter to submit
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.form.dispatchEvent(new Event('submit'));
        }
        
        // Escape to clear
        if (e.key === 'Escape') {
            this.queryInput.value = '';
            this.clearResults();
        }
    }

    handleInputFocus() {
        this.queryInput.parentElement.classList.add('focused');
    }

    handleInputBlur() {
        this.queryInput.parentElement.classList.remove('focused');
    }

    handleGlobalKeyboard(e) {
        // Ctrl/Cmd + K to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            this.queryInput.focus();
        }
        
        // Ctrl/Cmd + Enter to submit from anywhere
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            this.form.dispatchEvent(new Event('submit'));
        }
    }

    handleOnlineStatus(online) {
        const status = online ? 'online' : 'offline';
        this.announce(`Connection ${status}`);
        
        if (!online) {
            this.showError('You are currently offline. Please check your internet connection.');
        }
    }

    validateInput(value) {
        const isValid = value.trim().length >= 3;
        this.submitButton.disabled = !isValid || this.isLoading;
        
        if (value.trim().length > 0 && value.trim().length < 3) {
            this.queryInput.setCustomValidity('Please enter at least 3 characters');
        } else {
            this.queryInput.setCustomValidity('');
        }
    }

    // Search History Management
    loadSearchHistory() {
        try {
            const history = localStorage.getItem('crisismap_search_history');
            return history ? JSON.parse(history) : [];
        } catch (error) {
            console.warn('Failed to load search history:', error);
            return [];
        }
    }

    addToSearchHistory(query) {
        try {
            this.searchHistory = this.searchHistory.filter(item => item !== query);
            this.searchHistory.unshift(query);
            this.searchHistory = this.searchHistory.slice(0, 10); // Keep last 10
            this.saveSearchHistory();
        } catch (error) {
            console.warn('Failed to save search history:', error);
        }
    }

    saveSearchHistory() {
        try {
            localStorage.setItem('crisismap_search_history', JSON.stringify(this.searchHistory));
        } catch (error) {
            console.warn('Failed to save search history:', error);
        }
    }

    // Utility Methods
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    truncateText(text, length) {
        if (text.length <= length) return text;
        return text.substring(0, length) + '...';
    }

    formatDate(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        } catch (error) {
            return dateString;
        }
    }

    announce(message) {
        this.announcer.textContent = message;
        setTimeout(() => {
            this.announcer.textContent = '';
        }, 1000);
    }

    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                await navigator.serviceWorker.register('/static/js/sw.js');
                console.log('Service Worker registered successfully');
            } catch (error) {
                console.warn('Service Worker registration failed:', error);
            }
        }
    }
}

// Global functions for accessibility
window.fillQuery = function(element) {
    window.app?.fillQuery(element);
};

window.handleKeyPress = function(event, element) {
    window.app?.handleKeyPress(event, element);
};

// Performance monitoring
window.addEventListener('load', () => {
    const loadTime = performance.now();
    console.log(`Page loaded in ${Math.round(loadTime)}ms`);
});

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new CrisisMapApp();
});

// Error tracking
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    // Could send to error tracking service
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    // Could send to error tracking service
});

export default CrisisMapApp; 