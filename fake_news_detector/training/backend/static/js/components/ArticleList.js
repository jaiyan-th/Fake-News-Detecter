/**
 * ArticleList Component - AnswersQ-style list layout for news articles
 * Replaces the card grid with a clean vertical list format
 */

class ArticleList {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.articles = [];
    this.filteredArticles = [];
    this.currentPage = 1;
    this.articlesPerPage = 10;
    this.isLoading = false;

    this.init();
  }

  init() {
    if (!this.container) {
      console.error('ArticleList container not found');
      return;
    }

    // Set up intersection observer for infinite scroll
    this.setupInfiniteScroll();

    // Load initial articles
    this.loadArticles();
  }

  setupInfiniteScroll() {
    // Create a sentinel element for intersection observer
    this.sentinel = document.createElement('div');
    this.sentinel.className = 'scroll-sentinel';
    this.sentinel.style.height = '1px';
    this.container.appendChild(this.sentinel);

    // Set up intersection observer
    this.observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting && !this.isLoading) {
          this.loadMoreArticles();
        }
      });
    }, {
      rootMargin: '100px'
    });

    this.observer.observe(this.sentinel);
  }

  async loadArticles() {
    if (this.isLoading) return;

    this.isLoading = true;
    this.showLoading();

    try {
      const response = await fetch('/api/cards?page=1&limit=' + this.articlesPerPage);
      const data = await response.json();

      if (data.success) {
        this.articles = data.cards || [];
        this.filteredArticles = [...this.articles];
        this.renderArticles();
        this.updateStats();
      } else {
        console.warn('Failed to load articles');
        this.showEmptyState();
      }
    } catch (error) {
      console.error('Error loading articles:', error);
      this.showError('Error loading articles');
    } finally {
      this.isLoading = false;
      this.hideLoading();
    }
  }

  async loadMoreArticles() {
    if (this.isLoading) return;

    this.isLoading = true;
    this.currentPage++;

    try {
      const response = await fetch(`/api/cards?page=${this.currentPage}&limit=${this.articlesPerPage}`);
      const data = await response.json();

      if (data.success && data.cards && data.cards.length > 0) {
        this.articles = [...this.articles, ...data.cards];
        this.applyCurrentFilters();
        this.renderNewArticles(data.cards);
        this.updateStats();
      }
    } catch (error) {
      console.error('Error loading more articles:', error);
    } finally {
      this.isLoading = false;
    }
  }

  renderArticles() {
    // Clear existing content except sentinel
    const existingArticles = this.container.querySelectorAll('.article-item');
    existingArticles.forEach(article => article.remove());

    if (this.filteredArticles.length === 0) {
      this.showEmptyState();
      return;
    }

    this.hideEmptyState();

    // Render all filtered articles
    this.filteredArticles.forEach(article => {
      const articleElement = this.createArticleElement(article);
      this.container.insertBefore(articleElement, this.sentinel);
    });
  }

  renderNewArticles(newArticles) {
    // Apply current filters to new articles
    const filteredNewArticles = this.filterArticles(newArticles);

    // Render only the new filtered articles
    filteredNewArticles.forEach(article => {
      const articleElement = this.createArticleElement(article);
      this.container.insertBefore(articleElement, this.sentinel);
    });
  }

  createArticleElement(article) {
    const articleDiv = document.createElement('div');
    articleDiv.className = 'article-item';
    articleDiv.dataset.articleId = article._id;

    // Format timestamp
    const timestamp = this.formatTimestamp(article.timestamp);

    // Format confidence score
    const confidence = Math.round(article.confidence * 100);

    // Determine prediction class and text
    const predictionClass = article.prediction === 'REAL' ? 'real' : 'fake';
    const predictionText = article.prediction === 'REAL' ? 'Real News' : 'Fake News';
    const predictionIcon = article.prediction === 'REAL' ? '✓' : '⚠';

    // Create preview text (first 200 characters for better readability)
    const previewText = article.text ?
      (article.text.length > 200 ? article.text.substring(0, 200) + '...' : article.text) :
      'No preview available';

    // Calculate reading time estimate
    const wordCount = article.text ? article.text.split(' ').length : 0;
    const readingTime = Math.max(1, Math.ceil(wordCount / 200)); // 200 words per minute

    // Format article source if available
    const source = article.source || 'Unknown Source';

    articleDiv.innerHTML = `
      <div class="article-layout">
        <div class="article-main">
          <div class="article-header">
            <div class="article-prediction ${predictionClass}">
              <span class="prediction-icon">${predictionIcon}</span>
              ${predictionText}
            </div>
            <div class="article-stats">
              <span class="confidence-badge" title="AI Confidence Score">
                ${confidence}%
              </span>
            </div>
          </div>
          
          <div class="article-content">
            <h3 class="article-title">${this.currentSearchTerm ?
        this.highlightSearchTerms(this.escapeHtml(article.title || 'Untitled Article'), this.currentSearchTerm) :
        this.escapeHtml(article.title || 'Untitled Article')}</h3>
            
            <div class="article-meta">
              <span class="article-meta-item author">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                </svg>
                <span class="meta-label">By</span>
                <strong>${this.escapeHtml(article.username || 'Anonymous')}</strong>
              </span>
              
              <span class="article-meta-item timestamp">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z"/>
                  <path d="M12.5 7H11v6l5.25 3.15.75-1.23-4.5-2.67z"/>
                </svg>
                ${timestamp}
              </span>
              
              <span class="article-meta-item source">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
                <span class="meta-label">Source:</span>
                ${this.escapeHtml(source)}
              </span>
              
              <span class="article-meta-item reading-time">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
                ${readingTime} min read
              </span>
            </div>
            
            <p class="article-preview">${this.currentSearchTerm ?
        this.highlightSearchTerms(this.escapeHtml(previewText), this.currentSearchTerm) :
        this.escapeHtml(previewText)}</p>
            
            <div class="article-tags">
              ${this.generateArticleTags(article)}
            </div>
          </div>
        </div>
        
        <div class="article-sidebar">
          <div class="article-engagement">
            <button class="engagement-btn like-btn" title="Like this article" data-action="like">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
              </svg>
              <span class="engagement-count">${article.likes || 0}</span>
            </button>
            
            <button class="engagement-btn bookmark-btn" title="Bookmark this article" data-action="bookmark">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M17 3H7c-1.1 0-1.99.9-1.99 2L5 21l7-3 7 3V5c0-1.1-.9-2-2-2z"/>
              </svg>
            </button>
          </div>
          
          <div class="article-actions">
            <button class="article-btn primary" onclick="viewArticleDetails('${article._id}')" title="View full article">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
              </svg>
              View Details
            </button>
            
            <button class="article-btn secondary" onclick="shareArticle('${article._id}')" title="Share this article">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92s2.92-1.31 2.92-2.92-1.31-2.92-2.92-2.92z"/>
              </svg>
              Share
            </button>
          </div>
        </div>
      </div>
    `;

    // Add click handler for the entire article
    articleDiv.addEventListener('click', (e) => {
      // Don't trigger if clicking on buttons or interactive elements
      if (!e.target.closest('.article-btn, .engagement-btn')) {
        this.openArticleModal(article);
      }
    });

    // Add engagement button handlers
    this.setupEngagementHandlers(articleDiv, article);

    return articleDiv;
  }

  // Generate article tags based on content analysis
  generateArticleTags(article) {
    const tags = [];

    // Add prediction-based tag
    if (article.prediction === 'REAL') {
      tags.push({ name: 'verified', class: 'tag-verified' });
    } else {
      tags.push({ name: 'flagged', class: 'tag-flagged' });
    }

    // Add confidence-based tag
    if (article.confidence > 0.9) {
      tags.push({ name: 'high-confidence', class: 'tag-confidence' });
    } else if (article.confidence < 0.6) {
      tags.push({ name: 'low-confidence', class: 'tag-warning' });
    }

    // Add content-based tags (simplified analysis)
    if (article.text) {
      const text = article.text.toLowerCase();
      if (text.includes('politics') || text.includes('election') || text.includes('government')) {
        tags.push({ name: 'politics', class: 'tag-category' });
      }
      if (text.includes('health') || text.includes('medical') || text.includes('covid')) {
        tags.push({ name: 'health', class: 'tag-category' });
      }
      if (text.includes('technology') || text.includes('tech') || text.includes('ai')) {
        tags.push({ name: 'technology', class: 'tag-category' });
      }
    }

    return tags.map(tag =>
      `<span class="article-tag ${tag.class}">${tag.name}</span>`
    ).join('');
  }

  // Setup engagement button handlers
  setupEngagementHandlers(articleElement, article) {
    const likeBtn = articleElement.querySelector('.like-btn');
    const bookmarkBtn = articleElement.querySelector('.bookmark-btn');

    if (likeBtn) {
      likeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.handleEngagement(article._id, 'like', likeBtn);
      });
    }

    if (bookmarkBtn) {
      bookmarkBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.handleEngagement(article._id, 'bookmark', bookmarkBtn);
      });
    }
  }

  // Handle engagement actions (like, bookmark)
  async handleEngagement(articleId, action, buttonElement) {
    try {
      // Toggle active state
      const isActive = buttonElement.classList.contains('active');

      if (isActive) {
        buttonElement.classList.remove('active');
      } else {
        buttonElement.classList.add('active');
      }

      // Update count for likes
      if (action === 'like') {
        const countElement = buttonElement.querySelector('.engagement-count');
        if (countElement) {
          let count = parseInt(countElement.textContent) || 0;
          count = isActive ? Math.max(0, count - 1) : count + 1;
          countElement.textContent = count;
        }
      }

      // Here you would typically make an API call to save the engagement
      // For now, we'll just store it locally
      const engagementKey = `${action}_${articleId}`;
      if (isActive) {
        localStorage.removeItem(engagementKey);
      } else {
        localStorage.setItem(engagementKey, 'true');
      }

      // Show feedback
      if (typeof showToast === 'function') {
        const message = isActive ?
          `Removed from ${action}s` :
          `Added to ${action}s`;
        showToast(message, 'info');
      }

    } catch (error) {
      console.error(`Error handling ${action}:`, error);
      // Revert the visual change on error
      buttonElement.classList.toggle('active');
    }
  }

  formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown time';

    const date = new Date(timestamp);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);

    if (diffInSeconds < 60) {
      return 'Just now';
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 604800) {
      const days = Math.floor(diffInSeconds / 86400);
      return `${days} day${days > 1 ? 's' : ''} ago`;
    } else {
      return date.toLocaleDateString();
    }
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  openArticleModal(article) {
    // This will integrate with the existing modal system
    if (typeof openCardModal === 'function') {
      openCardModal(article);
    }
  }

  filterArticles(articles = this.articles) {
    const predictionFilter = document.getElementById('predictionFilter')?.value || '';
    const searchTerm = document.getElementById('searchInput')?.value.toLowerCase() || '';

    return articles.filter(article => {
      // Apply prediction filter
      if (predictionFilter && article.prediction !== predictionFilter) {
        return false;
      }

      // Apply search filter
      if (searchTerm) {
        const searchableText = [
          article.title || '',
          article.text || '',
          article.username || ''
        ].join(' ').toLowerCase();

        if (!searchableText.includes(searchTerm)) {
          return false;
        }
      }

      return true;
    });
  }

  applyCurrentFilters() {
    this.filteredArticles = this.filterArticles();
  }

  search(searchTerm) {
    // Update the search input if it exists
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
      searchInput.value = searchTerm;
    }

    this.currentSearchTerm = searchTerm;
    this.applyCurrentFilters();
    this.renderArticles();
    this.updateStats();

    // Show search results feedback
    if (searchTerm) {
      const resultCount = this.filteredArticles.length;
      this.showSearchFeedback(searchTerm, resultCount);
    }
  }

  // Show search feedback
  showSearchFeedback(searchTerm, resultCount) {
    // Remove existing feedback
    const existingFeedback = this.container.querySelector('.search-feedback');
    if (existingFeedback) {
      existingFeedback.remove();
    }

    // Create new feedback element
    const feedback = document.createElement('div');
    feedback.className = 'search-feedback';
    feedback.innerHTML = `
      <div class="search-results-info">
        <span class="search-term">Showing ${resultCount} result${resultCount !== 1 ? 's' : ''} for "${this.escapeHtml(searchTerm)}"</span>
        <button class="clear-search-btn" onclick="window.articleList.search('')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
          </svg>
          Clear search
        </button>
      </div>
    `;

    this.container.insertBefore(feedback, this.container.firstChild);
  }

  // Highlight search terms in text
  highlightSearchTerms(text, searchTerm) {
    if (!searchTerm || !text) return text;

    const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(regex, '<mark class="search-highlight">$1</mark>');
  }

  filter(predictionType) {
    // Update the filter select if it exists
    const predictionFilter = document.getElementById('predictionFilter');
    if (predictionFilter) {
      predictionFilter.value = predictionType;
    }

    this.applyCurrentFilters();
    this.renderArticles();
    this.updateStats();
  }

  sort(sortBy) {
    const sortedArticles = [...this.filteredArticles];

    switch (sortBy) {
      case 'timestamp':
        sortedArticles.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        break;
      case 'confidence':
        sortedArticles.sort((a, b) => b.confidence - a.confidence);
        break;
      case 'username':
        sortedArticles.sort((a, b) => (a.username || '').localeCompare(b.username || ''));
        break;
    }

    this.filteredArticles = sortedArticles;
    this.renderArticles();
  }

  updateStats() {
    const totalCount = document.getElementById('totalCount');
    const realCount = document.getElementById('realCount');
    const fakeCount = document.getElementById('fakeCount');

    if (totalCount) totalCount.textContent = this.filteredArticles.length;

    if (realCount) {
      const realArticles = this.filteredArticles.filter(a => a.prediction === 'REAL');
      realCount.textContent = realArticles.length;
    }

    if (fakeCount) {
      const fakeArticles = this.filteredArticles.filter(a => a.prediction === 'FAKE');
      fakeCount.textContent = fakeArticles.length;
    }
  }

  showLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
      loadingOverlay.style.display = 'flex';
    }
  }

  hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
      loadingOverlay.style.display = 'none';
    }
  }

  showEmptyState() {
    const emptyState = document.getElementById('emptyState');
    if (emptyState) {
      emptyState.style.display = 'block';
    }
  }

  hideEmptyState() {
    const emptyState = document.getElementById('emptyState');
    if (emptyState) {
      emptyState.style.display = 'none';
    }
  }

  showError(message) {
    // Create or update error message
    let errorDiv = this.container.querySelector('.error-message');
    if (!errorDiv) {
      errorDiv = document.createElement('div');
      errorDiv.className = 'error-message';
      errorDiv.style.cssText = `
        background-color: #ffebee;
        color: #c62828;
        padding: 16px;
        border-radius: 8px;
        margin: 20px 0;
        text-align: center;
      `;
      this.container.appendChild(errorDiv);
    }
    errorDiv.textContent = message;
  }

  // Public methods for external integration
  refresh() {
    this.currentPage = 1;
    this.articles = [];
    this.filteredArticles = [];
    this.loadArticles();
  }

  addArticle(article) {
    this.articles.unshift(article);
    this.applyCurrentFilters();
    this.renderArticles();
    this.updateStats();
  }
}

// Global functions for backward compatibility
function viewArticleDetails(articleId) {
  const article = window.articleList?.articles.find(a => a._id === articleId);
  if (article && typeof openCardModal === 'function') {
    openCardModal(article);
  }
}

function shareArticle(articleId) {
  const article = window.articleList?.articles.find(a => a._id === articleId);
  if (article) {
    const shareData = {
      title: article.title || 'News Article Analysis',
      text: `Check out this ${article.prediction === 'REAL' ? 'verified' : 'flagged'} news article analysis`,
      url: window.location.href
    };

    if (navigator.share) {
      navigator.share(shareData);
    } else {
      // Fallback to clipboard
      navigator.clipboard.writeText(shareData.url).then(() => {
        // Show toast notification if available
        if (typeof showToast === 'function') {
          showToast('Link copied to clipboard!');
        }
      });
    }
  }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ArticleList;
}