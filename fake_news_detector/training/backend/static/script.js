/**
 * Enhanced Fake News Detector with Card Grid Interface
 * Integrates with Pinterest-like card layout and advanced API endpoints
 */

// Global application state
const AppState = {
  articleList: null,
  currentFilter: '',
  currentSort: 'timestamp',
  searchQuery: '',
  isLoading: false,
  stats: { total: 0, real: 0, fake: 0 },
  isAuthenticated: false,
  username: null
};

// API Configuration
const API_BASE = 'http://localhost:5000';
const API_ENDPOINTS = {
  cards: `${API_BASE}/api/cards`,
  predict: `${API_BASE}/api/predict`,
  search: `${API_BASE}/api/cards/search`,
  stats: `${API_BASE}/api/cards/stats`,
  cardDetail: (id) => `${API_BASE}/api/cards/${id}`,
  login: `${API_BASE}/login`,
  register: `${API_BASE}/register`,
  logout: `${API_BASE}/logout`
};

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp);

async function initializeApp() {
  try {
    // Initialize article list
    initializeArticleList();

    // Setup event listeners
    setupEventListeners();

    // Check authentication status
    const isAuthenticated = await checkAuthenticationStatus();

    // Load initial data only if authenticated
    if (isAuthenticated && AppState.articleList) {
      AppState.articleList.loadArticles();
    }

    console.log('App initialized successfully');
  } catch (error) {
    console.error('Failed to initialize app:', error);
    showToast('Failed to initialize application', 'error');
  }
}

function initializeArticleList() {
  // Initialize the new ArticleList component
  AppState.articleList = new ArticleList('articleList');

  // Make it globally available for other functions
  window.articleList = AppState.articleList;

  console.log('Article list initialized');
}

function setupEventListeners() {
  // Navigation buttons
  // document.getElementById('addNewsBtn').addEventListener('click', showAddNewsModal);
  document.getElementById('loginBtn').addEventListener('click', showLoginModal);
  document.getElementById('signupBtn').addEventListener('click', showSignupModal);
  document.getElementById('userBtn').addEventListener('click', showUserMenu);
  // Layout button removed - using fixed list layout

  // Search functionality removed from setupEventListeners (replaced by Analysis Form)

  // Filter and sort controls
  document.getElementById('predictionFilter').addEventListener('change', handleFilterChange);
  document.getElementById('sortSelect').addEventListener('change', handleSortChange);

  // Modal event listeners
  setupModalEventListeners();

  // Keyboard shortcuts
  document.addEventListener('keydown', handleKeyboardShortcuts);

  console.log('Event listeners setup complete');
}

// Note: loadInitialData is now handled by ArticleList component
// This function is kept for backward compatibility and API health checks
async function loadInitialData() {
  try {
    // Test API connection first
    const healthResponse = await fetch(`${API_BASE}/health`);
    if (!healthResponse.ok) {
      throw new Error('Backend API is not responding');
    }

    const healthData = await healthResponse.json();
    console.log('✅ Backend connection successful:', healthData);

  } catch (error) {
    console.error('Failed to connect to backend:', error);

    if (error.message.includes('Backend API')) {
      showToast('Cannot connect to backend. Please start the server.', 'error');
      showConnectionError();
    }
  }
}

function showConnectionError() {
  const emptyState = document.getElementById('emptyState');
  emptyState.style.display = 'flex';
  emptyState.innerHTML = `
    <div class="empty-state-content">
      <div class="empty-state-icon">🔌</div>
      <h2 class="empty-state-title">Connection Error</h2>
      <p class="empty-state-description">
        Cannot connect to the backend server. Please make sure the server is running.
      </p>
      <div style="margin-top: 1rem;">
        <button class="empty-state-btn" onclick="location.reload()">
          Retry Connection
        </button>
        <div style="margin-top: 1rem; font-size: 0.9rem; color: #6b7280;">
          <p><strong>To start the server:</strong></p>
          <p>1. Open terminal in project directory</p>
          <p>2. Run: <code style="background: #f3f4f6; padding: 2px 6px; border-radius: 4px;">python start_server.py</code></p>
          <p>3. Wait for "Server started" message</p>
          <p>4. Refresh this page</p>
        </div>
      </div>
    </div>
  `;
}

async function updateStats() {
  try {
    const response = await fetch(API_ENDPOINTS.stats);
    if (!response.ok) return;

    const stats = await response.json();

    AppState.stats = {
      total: stats.total_predictions || 0,
      real: stats.by_prediction?.REAL?.count || 0,
      fake: stats.by_prediction?.FAKE?.count || 0
    };

    updateStatsDisplay();
  } catch (error) {
    console.error('Failed to update stats:', error);
  }
}

function updateStatsDisplay() {
  document.getElementById('totalCount').textContent = AppState.stats.total;
  document.getElementById('realCount').textContent = AppState.stats.real;
  document.getElementById('fakeCount').textContent = AppState.stats.fake;
}

// Modal Management - Removed Add News Modal
// function showAddNewsModal() ... removed
// function closeAddNewsModal() ... removed

function setupModalEventListeners() {
  // Close modal on backdrop click
  document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
        const modal = backdrop.closest('.modal');
        if (modal.id === 'cardModal') {
          closeCardModal();
        } else if (modal.id === 'loginModal') {
          closeLoginModal();
        } else if (modal.id === 'signupModal') {
          closeSignupModal();
        }
      }
    });
  });

  // Close modal on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const openModal = document.querySelector('.modal.show');
      if (openModal) {
        if (openModal.id === 'cardModal') {
          closeCardModal();
        } else if (openModal.id === 'loginModal') {
          closeLoginModal();
        } else if (openModal.id === 'signupModal') {
          closeSignupModal();
        }
      }
    }
  });
}

// Global Tab State
let currentTab = 'text';

// Expose to global scope for HTML onclick access
window.switchTab = function (tab) {
  currentTab = tab;

  // UI Updates
  const textBtn = document.getElementById('tab-text');
  const urlBtn = document.getElementById('tab-url');
  const textGroup = document.getElementById('text-input-group');
  const urlGroup = document.getElementById('url-input-group');

  if (tab === 'text') {
    textBtn.classList.add('active');
    urlBtn.classList.remove('active');
    textGroup.style.display = 'block';
    urlGroup.style.display = 'none';

    // Auto-focus after small delay for animation
    setTimeout(() => document.getElementById('newsTextarea').focus(), 100);
  } else {
    urlBtn.classList.add('active');
    textBtn.classList.remove('active');
    urlGroup.style.display = 'block';
    textGroup.style.display = 'none';

    setTimeout(() => document.getElementById('newsUrlInput').focus(), 100);
  }
};

// News submission
async function submitNews(event) {
  event.preventDefault();

  const textarea = document.getElementById('newsTextarea');
  const urlInput = document.getElementById('newsUrlInput');
  const text = textarea.value.trim();
  const url = urlInput.value.trim();

  // Validation based on active tab
  if (currentTab === 'text') {
    const validationResult = validateNewsInput(text);
    if (!validationResult.isValid) {
      showFormError(validationResult.message, 'newsTextarea');
      return;
    }
  } else {
    if (!url) {
      showFormError('Please enter a valid URL.', 'newsUrlInput');
      return;
    }
    // Simple URL regex check
    try {
      new URL(url);
    } catch (_) {
      showFormError('Please enter a valid URL (e.g., https://example.com)', 'newsUrlInput');
      return;
    }
  }

  try {
    setAnalysisLoadingState(true);

    let response;

    if (currentTab === 'text') {
      // Text Analysis
      response = await fetch(API_ENDPOINTS.predict, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text })
      });
    } else {
      // URL Analysis
      response = await fetch(`${API_BASE}/api/analyze-url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url })
      });
    }

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.message || `Analysis failed: ${response.status}`);
    }

    const data = await response.json();

    if (data.success && data.card) {
      // Add new article to list
      if (AppState.articleList) {
        AppState.articleList.addArticle(data.card);
      }

      showSuccessAnimation();

      // Clear Inputs
      textarea.value = '';
      urlInput.value = '';

      const predictionText = data.card.prediction === 'REAL' ? 'Real News' : 'Fake News';
      const confidence = Math.round(data.card.confidence * 100);
      showToast(`✅ Analysis Complete: ${predictionText} (${confidence}% confidence)`, 'success');

      hideEmptyState();

      // Scroll to the new card
      setTimeout(() => {
        const articleList = document.getElementById('articleList');
        if (articleList.firstChild) {
          articleList.firstChild.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 500);
    }

  } catch (error) {
    console.error('Analysis failed:', error);
    showFormError(error.message || 'Failed to analyze article.', currentTab);
  } finally {
    setAnalysisLoadingState(false);
  }
}

// Enhanced validation function
function validateNewsInput(text) {
  if (!text) {
    return { isValid: false, message: 'Please enter some news text to analyze.' };
  }

  if (text.length < 20) {
    return { isValid: false, message: 'Please enter at least 20 characters for accurate analysis.' };
  }

  if (text.length > 10000) {
    return { isValid: false, message: 'Text is too long. Please limit to 10,000 characters.' };
  }

  // Check for meaningful content
  const wordCount = text.split(/\s+/).length;
  if (wordCount < 3) {
    return { isValid: false, message: 'Please enter at least 3 words for analysis.' };
  }

  return { isValid: true };
}

// Enhanced loading state management
function setAnalysisLoadingState(isLoading) {
  const analyzeBtn = document.getElementById('analyzeBtn');
  const btnText = analyzeBtn.querySelector('.btn-text');
  const btnSpinner = analyzeBtn.querySelector('.btn-spinner');
  const textarea = document.getElementById('newsTextarea');
  const formContainer = document.querySelector('.analysis-form-container');

  if (isLoading) {
    analyzeBtn.disabled = true;
    btnText.textContent = 'Analyzing...';
    btnSpinner.style.display = 'inline-block';
    textarea.disabled = true;
    if (formContainer) formContainer.classList.add('processing');

    // Add progress indicator
    showAnalysisProgress();
  } else {
    analyzeBtn.disabled = false;
    btnText.textContent = 'Analyze Article';
    btnSpinner.style.display = 'none';
    textarea.disabled = false;
    if (formContainer) formContainer.classList.remove('processing');

    // Remove progress indicator
    hideAnalysisProgress();
  }
}

// Show form errors with better styling
function showFormError(message) {
  // Remove existing error
  const existingError = document.querySelector('.form-error');
  if (existingError) {
    existingError.remove();
  }

  // Create error element
  const errorDiv = document.createElement('div');
  errorDiv.className = 'form-error';
  errorDiv.innerHTML = `
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
    </svg>
    ${message}
  `;

  // Insert after textarea
  const textarea = document.getElementById('newsTextarea');
  textarea.parentNode.insertBefore(errorDiv, textarea.nextSibling);

  // Add error styling to textarea
  textarea.classList.add('error');

  // Auto-remove error on input
  textarea.addEventListener('input', function removeError() {
    errorDiv.remove();
    textarea.classList.remove('error');
    textarea.removeEventListener('input', removeError);
  });
}

// Show analysis progress
function showAnalysisProgress() {
  const formContainer = document.querySelector('.analysis-form-container');
  if (!formContainer) return;

  const progressDiv = document.createElement('div');
  progressDiv.className = 'analysis-progress';
  progressDiv.innerHTML = `
    <div class="progress-bar">
      <div class="progress-fill"></div>
    </div>
    <div class="progress-text">Analyzing article content...</div>
  `;

  // existing progress check to avoid duplicates
  if (formContainer.querySelector('.analysis-progress')) return;

  formContainer.appendChild(progressDiv);
}

// Hide analysis progress
function hideAnalysisProgress() {
  const progress = document.querySelector('.analysis-progress');
  if (progress) {
    progress.remove();
  }
}

// Show success animation
function showSuccessAnimation() {
  const formContainer = document.querySelector('.analysis-form-container');
  if (!formContainer) return;

  const successDiv = document.createElement('div');
  successDiv.className = 'success-animation';
  successDiv.innerHTML = `
    <div class="success-checkmark">
      <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
        <polyline points="22,4 12,14.01 9,11.01"/>
      </svg>
    </div>
    <div class="success-text">Analysis Complete!</div>
  `;

  formContainer.appendChild(successDiv);

  // Auto remove after animation
  setTimeout(() => {
    successDiv.remove();
  }, 2000);
}

// Enhanced Search functionality
async function handleSearch() {
  const searchInput = document.getElementById('searchInput');
  const query = searchInput.value.trim();

  AppState.searchQuery = query;

  // Add visual feedback during search
  searchInput.classList.add('searching');

  if (AppState.articleList) {
    AppState.articleList.search(query);

    // Show search feedback
    if (query) {
      showToast(`Searching for "${query}"...`, 'info');
    } else {
      showToast('Showing all articles', 'info');
    }
  }

  // Remove visual feedback
  setTimeout(() => {
    searchInput.classList.remove('searching');
  }, 500);
}

// Filter and sort handlers
async function handleFilterChange(event) {
  AppState.currentFilter = event.target.value;

  if (AppState.articleList) {
    AppState.articleList.filter(event.target.value);
  }
}

async function handleSortChange(event) {
  AppState.currentSort = event.target.value;

  if (AppState.articleList) {
    AppState.articleList.sort(event.target.value);
  }
}

async function applyFiltersAndSort() {
  try {
    showLoadingOverlay(true);

    const params = new URLSearchParams({
      page: 1,
      limit: 50,
      sort: AppState.currentSort,
      order: 'desc'
    });

    if (AppState.currentFilter) {
      params.append('filter', AppState.currentFilter);
    }

    if (AppState.searchQuery) {
      params.append('search', AppState.searchQuery);
    }

    const response = await fetch(`${API_ENDPOINTS.cards}?${params}`);
    if (!response.ok) throw new Error('Failed to apply filters');

    const data = await response.json();

    AppState.cardGrid.refresh();

    if (data.cards && data.cards.length > 0) {
      AppState.cardGrid.addCards(data.cards);
      hideEmptyState();
    } else {
      showEmptyState();
    }

  } catch (error) {
    console.error('Failed to apply filters:', error);
    showToast('Failed to apply filters', 'error');
  } finally {
    showLoadingOverlay(false);
  }
}

// Card interaction handlers
async function handleCardClick(cardData, cardElement) {
  try {
    // Show detailed modal
    await showCardModal(cardData.id);
  } catch (error) {
    console.error('Failed to show card details:', error);
    showToast('Failed to load article details', 'error');
  }
}

async function showCardModal(cardId) {
  try {
    const response = await fetch(API_ENDPOINTS.cardDetail(cardId));
    if (!response.ok) throw new Error('Failed to load card details');

    const cardData = await response.json();

    const modal = document.getElementById('cardModal');
    const modalContent = modal.querySelector('.modal-content');

    modalContent.innerHTML = `
      <header class="modal-header">
        <h2 id="cardModalTitle" class="modal-title">${cardData.title}</h2>
        <button class="modal-close" aria-label="Close modal" onclick="closeCardModal()">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
          </svg>
        </button>
      </header>
      
      <div class="modal-body">
        <div class="card-detail-content">
          <div class="detail-prediction">
            <div class="prediction-badge ${cardData.prediction.toLowerCase()}">
              <span class="prediction-icon">${cardData.prediction === 'REAL' ? '✓' : '⚠'}</span>
              <div class="prediction-details">
                <span class="prediction-label">${cardData.prediction}</span>
                <div class="confidence-bar">
                  <div class="confidence-fill" style="width: ${cardData.confidence * 100}%"></div>
                </div>
                <span class="confidence-text">${Math.round(cardData.confidence * 100)}%</span>
              </div>
            </div>
          </div>
          
          <div class="detail-metadata">
            <p><strong>Author:</strong> ${cardData.username}</p>
            <p><strong>Analyzed:</strong> ${new Date(cardData.timestamp).toLocaleString()}</p>
            <p><strong>Word Count:</strong> ${cardData.word_count || 'N/A'}</p>
          </div>
          
          <div class="detail-content">
            <h3>Full Article Text</h3>
            <div class="article-text">${cardData.full_content || cardData.content}</div>
          </div>
          
          ${cardData.tags && cardData.tags.length > 0 ? `
            <div class="detail-tags">
              <h4>Tags</h4>
              <div class="tags-list">
                ${cardData.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
              </div>
            </div>
          ` : ''}
        </div>
      </div>
    `;

    modal.classList.add('show');
    modal.setAttribute('aria-hidden', 'false');

    // Focus on close button
    setTimeout(() => {
      modal.querySelector('.modal-close').focus();
    }, 100);

  } catch (error) {
    throw error;
  }
}

function closeCardModal() {
  const modal = document.getElementById('cardModal');
  modal.classList.remove('show');
  modal.setAttribute('aria-hidden', 'true');
}

// Layout management - removed for fixed list layout
// function toggleLayout() - no longer needed with ArticleList

// Utility functions
function showEmptyState() {
  document.getElementById('emptyState').style.display = 'flex';
  document.getElementById('articleList').style.display = 'none';
}

function hideEmptyState() {
  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('articleList').style.display = 'flex';
}

function showLoadingOverlay(show) {
  const overlay = document.getElementById('loadingOverlay');
  overlay.style.display = show ? 'flex' : 'none';
  AppState.isLoading = show;
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;

  container.appendChild(toast);

  // Show toast
  setTimeout(() => toast.classList.add('show'), 100);

  // Remove toast after 3 seconds
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

function trapFocus(element) {
  const focusableElements = element.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );

  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  element.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement.focus();
          e.preventDefault();
        }
      }
    }
  });
}

function handleKeyboardShortcuts(e) {
  // Ctrl/Cmd + K for search
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault();
    document.getElementById('searchInput').focus();
  }

  // Ctrl/Cmd + N for new article
  if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
    e.preventDefault();
    showAddNewsModal();
  }

  // Layout toggle removed - using fixed list layout
}

// Authentication Functions
function showLoginModal() {
  const modal = document.getElementById('loginModal');
  modal.classList.add('show');
  modal.setAttribute('aria-hidden', 'false');

  setTimeout(() => {
    document.getElementById('loginUsername').focus();
  }, 100);
}

function closeLoginModal() {
  const modal = document.getElementById('loginModal');
  modal.classList.remove('show');
  modal.setAttribute('aria-hidden', 'true');
  document.getElementById('loginForm').reset();
}

function showSignupModal() {
  const modal = document.getElementById('signupModal');
  modal.classList.add('show');
  modal.setAttribute('aria-hidden', 'false');

  setTimeout(() => {
    document.getElementById('signupUsername').focus();
  }, 100);
}

function closeSignupModal() {
  const modal = document.getElementById('signupModal');
  modal.classList.remove('show');
  modal.setAttribute('aria-hidden', 'true');
  document.getElementById('signupForm').reset();
}

async function submitLogin(event) {
  event.preventDefault();

  const username = document.getElementById('loginUsername').value.trim();
  const password = document.getElementById('loginPassword').value.trim();

  if (!username || !password) {
    showToast('Please enter both username and password', 'error');
    return;
  }

  try {
    setLoginLoadingState(true);

    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(API_ENDPOINTS.login, {
      method: 'POST',
      body: formData
    });

    if (response.redirected) {
      window.location.href = response.url;
      return;
    }

    const html = await response.text();
    if (html.includes('Invalid username or password')) {
      showToast('Invalid username or password', 'error');
    } else {
      // Check if logged in
      await checkAuthenticationStatus();
      closeLoginModal();
      showToast('Successfully logged in!', 'success');
    }

  } catch (error) {
    console.error('Login failed:', error);
    showToast('Login failed', 'error');
  } finally {
    setLoginLoadingState(false);
  }
}
