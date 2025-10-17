/**
 * Enhanced Fake News Detector with Card Grid Interface
 * Integrates with Pinterest-like card layout and advanced API endpoints
 */

// Global application state
const AppState = {
  cardGrid: null,
  currentFilter: '',
  currentSort: 'timestamp',
  searchQuery: '',
  isLoading: false,
  stats: { total: 0, real: 0, fake: 0 }
};

// API Configuration
const API_BASE = 'http://127.0.0.1:5000/api';
const API_ENDPOINTS = {
  cards: `${API_BASE}/cards`,
  predict: `${API_BASE}/predict`,
  search: `${API_BASE}/cards/search`,
  stats: `${API_BASE}/cards/stats`,
  cardDetail: (id) => `${API_BASE}/cards/${id}`
};

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp);

async function initializeApp() {
  try {
    // Initialize card grid
    initializeCardGrid();
    
    // Setup event listeners
    setupEventListeners();
    
    // Load initial data
    await loadInitialData();
    
    // Update stats
    await updateStats();
    
    console.log('App initialized successfully');
  } catch (error) {
    console.error('Failed to initialize app:', error);
    showToast('Failed to initialize application', 'error');
  }
}

function initializeCardGrid() {
  const gridContainer = document.getElementById('cardGrid');
  
  AppState.cardGrid = new CardGrid(gridContainer, {
    minCardWidth: 300,
    gap: 20,
    loadMoreThreshold: 200,
    virtualScrollBuffer: 10,
    onCardClick: handleCardClick
  });
  
  console.log('Card grid initialized');
}

function setupEventListeners() {
  // Navigation buttons
  document.getElementById('addNewsBtn').addEventListener('click', showAddNewsModal);
  document.getElementById('layoutBtn').addEventListener('click', toggleLayout);
  
  // Search functionality
  const searchInput = document.getElementById('searchInput');
  const searchBtn = document.getElementById('searchBtn');
  
  searchInput.addEventListener('input', debounce(handleSearch, 300));
  searchBtn.addEventListener('click', () => handleSearch());
  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSearch();
    }
  });
  
  // Filter and sort controls
  document.getElementById('predictionFilter').addEventListener('change', handleFilterChange);
  document.getElementById('sortSelect').addEventListener('change', handleSortChange);
  
  // Modal event listeners
  setupModalEventListeners();
  
  // Keyboard shortcuts
  document.addEventListener('keydown', handleKeyboardShortcuts);
  
  console.log('Event listeners setup complete');
}

async function loadInitialData() {
  try {
    showLoadingOverlay(true);
    
    // Test API connection first
    const healthResponse = await fetch(`${API_BASE}/health`);
    if (!healthResponse.ok) {
      throw new Error('Backend API is not responding');
    }
    
    const healthData = await healthResponse.json();
    console.log('✅ Backend connection successful:', healthData);
    
    const response = await fetch(`${API_ENDPOINTS.cards}?page=1&limit=20`);
    if (!response.ok) throw new Error('Failed to load cards');
    
    const data = await response.json();
    
    if (data.cards && data.cards.length > 0) {
      AppState.cardGrid.addCards(data.cards);
      hideEmptyState();
      showToast(`Loaded ${data.cards.length} articles`, 'success');
    } else {
      showEmptyState();
      showToast('No articles found. Add your first article!', 'info');
    }
    
  } catch (error) {
    console.error('Failed to load initial data:', error);
    
    if (error.message.includes('Backend API')) {
      showToast('Cannot connect to backend. Please start the server.', 'error');
      showConnectionError();
    } else {
      showToast('Failed to load articles', 'error');
      showEmptyState();
    }
  } finally {
    showLoadingOverlay(false);
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

// Modal Management
function showAddNewsModal() {
  const modal = document.getElementById('addNewsModal');
  modal.classList.add('show');
  modal.setAttribute('aria-hidden', 'false');
  
  // Focus on textarea
  setTimeout(() => {
    document.getElementById('newsTextarea').focus();
  }, 100);
  
  // Trap focus in modal
  trapFocus(modal);
}

function closeAddNewsModal() {
  const modal = document.getElementById('addNewsModal');
  modal.classList.remove('show');
  modal.setAttribute('aria-hidden', 'true');
  
  // Clear form
  document.getElementById('newsForm').reset();
  
  // Return focus to add button
  document.getElementById('addNewsBtn').focus();
}

function setupModalEventListeners() {
  // Close modal on backdrop click
  document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
        const modal = backdrop.closest('.modal');
        if (modal.id === 'addNewsModal') {
          closeAddNewsModal();
        } else if (modal.id === 'cardModal') {
          closeCardModal();
        }
      }
    });
  });
  
  // Close modal on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const openModal = document.querySelector('.modal.show');
      if (openModal) {
        if (openModal.id === 'addNewsModal') {
          closeAddNewsModal();
        } else if (openModal.id === 'cardModal') {
          closeCardModal();
        }
      }
    }
  });
}

// News submission
async function submitNews(event) {
  event.preventDefault();
  
  const textarea = document.getElementById('newsTextarea');
  const text = textarea.value.trim();
  
  if (!text) {
    showToast('Please enter some news text', 'error');
    return;
  }
  
  const analyzeBtn = document.getElementById('analyzeBtn');
  const btnText = analyzeBtn.querySelector('.btn-text');
  const btnSpinner = analyzeBtn.querySelector('.btn-spinner');
  
  try {
    // Show loading state
    analyzeBtn.disabled = true;
    btnText.textContent = 'Analyzing...';
    btnSpinner.style.display = 'inline-block';
    
    const response = await fetch(API_ENDPOINTS.predict, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ text })
    });
    
    if (!response.ok) {
      throw new Error('Analysis failed');
    }
    
    const data = await response.json();
    
    if (data.success && data.card) {
      // Add new card to grid
      AppState.cardGrid.addCards([data.card]);
      
      // Update stats
      await updateStats();
      
      // Close modal
      closeAddNewsModal();
      
      // Show success message
      showToast(`Article analyzed: ${data.prediction.result}`, 'success');
      
      // Hide empty state if it was showing
      hideEmptyState();
      
      // Scroll to new card
      setTimeout(() => {
        AppState.cardGrid.scrollToCard(data.card.id);
      }, 500);
    }
    
  } catch (error) {
    console.error('Analysis failed:', error);
    showToast('Failed to analyze article', 'error');
  } finally {
    // Reset button state
    analyzeBtn.disabled = false;
    btnText.textContent = 'Analyze Article';
    btnSpinner.style.display = 'none';
  }
}

// Search functionality
async function handleSearch() {
  const searchInput = document.getElementById('searchInput');
  const query = searchInput.value.trim();
  
  AppState.searchQuery = query;
  
  if (!query) {
    // Reset to show all cards
    await loadInitialData();
    return;
  }
  
  try {
    showLoadingOverlay(true);
    
    const response = await fetch(`${API_ENDPOINTS.search}?q=${encodeURIComponent(query)}&limit=50`);
    if (!response.ok) throw new Error('Search failed');
    
    const data = await response.json();
    
    // Clear existing cards and show search results
    AppState.cardGrid.refresh();
    
    if (data.cards && data.cards.length > 0) {
      AppState.cardGrid.addCards(data.cards);
      hideEmptyState();
      showToast(`Found ${data.cards.length} results for "${query}"`, 'info');
    } else {
      showEmptyState();
      showToast(`No results found for "${query}"`, 'info');
    }
    
  } catch (error) {
    console.error('Search failed:', error);
    showToast('Search failed', 'error');
  } finally {
    showLoadingOverlay(false);
  }
}

// Filter and sort handlers
async function handleFilterChange(event) {
  AppState.currentFilter = event.target.value;
  await applyFiltersAndSort();
}

async function handleSortChange(event) {
  AppState.currentSort = event.target.value;
  await applyFiltersAndSort();
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

// Layout management
function toggleLayout() {
  const layouts = ['normal', 'compact', 'spacious'];
  const currentLayout = AppState.cardGrid.options.currentLayout || 'normal';
  const currentIndex = layouts.indexOf(currentLayout);
  const nextLayout = layouts[(currentIndex + 1) % layouts.length];
  
  AppState.cardGrid.setLayout(nextLayout);
  AppState.cardGrid.options.currentLayout = nextLayout;
  
  showToast(`Layout changed to ${nextLayout}`, 'info');
}

// Utility functions
function showEmptyState() {
  document.getElementById('emptyState').style.display = 'flex';
  document.getElementById('cardGrid').style.display = 'none';
}

function hideEmptyState() {
  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('cardGrid').style.display = 'block';
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
  
  // Ctrl/Cmd + L for layout toggle
  if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
    e.preventDefault();
    toggleLayout();
  }
}

// Legacy function for backward compatibility
async function checkNews() {
  console.warn('checkNews() is deprecated. Use the new card grid interface.');
}
