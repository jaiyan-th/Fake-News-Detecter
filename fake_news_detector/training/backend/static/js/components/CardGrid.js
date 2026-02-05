/**
 * CardGrid Component - Pinterest-like masonry grid layout
 * Manages responsive grid layout and card rendering
 */
class CardGrid {
  constructor(container, options = {}) {
    this.container = typeof container === 'string' ? document.querySelector(container) : container;
    this.options = {
      minCardWidth: 280,
      gap: 20,
      loadMoreThreshold: 200,
      virtualScrollBuffer: 10,
      ...options
    };
    
    this.cards = [];
    this.visibleCards = new Set();
    this.isLoading = false;
    this.hasMore = true;
    this.page = 1;
    
    this.init();
  }
  
  init() {
    this.setupContainer();
    this.setupIntersectionObserver();
    this.setupEventListeners();
    this.calculateColumns();
  }
  
  setupContainer() {
    this.container.classList.add('card-grid');
    this.container.innerHTML = `
      <div class="card-grid-content"></div>
      <div class="card-grid-loader" style="display: none;">
        <div class="loading-spinner"></div>
      </div>
    `;
    
    this.gridContent = this.container.querySelector('.card-grid-content');
    this.loader = this.container.querySelector('.card-grid-loader');
  }
  
  setupIntersectionObserver() {
    this.observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        const cardId = entry.target.dataset.cardId;
        if (entry.isIntersecting) {
          this.visibleCards.add(cardId);
          this.loadCardImages(entry.target);
        } else {
          this.visibleCards.delete(cardId);
        }
      });
    }, {
      rootMargin: '50px',
      threshold: 0.1
    });
    
    // Infinite scroll observer
    this.scrollObserver = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && !this.isLoading && this.hasMore) {
        this.loadMore();
      }
    }, {
      rootMargin: `${this.options.loadMoreThreshold}px`
    });
  }
  
  setupEventListeners() {
    // Viewport change detection with debouncing
    this.resizeObserver = new ResizeObserver(this.debounce((entries) => {
      for (let entry of entries) {
        if (entry.target === this.container) {
          this.handleViewportChange();
        }
      }
    }, 250));
    
    this.resizeObserver.observe(this.container);
    
    // Fallback for older browsers
    window.addEventListener('resize', this.debounce(() => {
      this.handleViewportChange();
    }, 250));
    
    // Orientation change detection
    window.addEventListener('orientationchange', () => {
      setTimeout(() => {
        this.handleViewportChange();
      }, 100);
    });
    
    // Handle card interactions
    this.gridContent.addEventListener('click', (e) => {
      const card = e.target.closest('.news-card');
      if (card) {
        this.handleCardClick(card);
      }
    });
    
    // Keyboard navigation
    this.gridContent.addEventListener('keydown', (e) => {
      this.handleKeyboardNavigation(e);
    });
    
    // Focus management
    this.gridContent.addEventListener('focusin', (e) => {
      this.handleFocusChange(e);
    });
    
    // Performance monitoring
    this.setupPerformanceMonitoring();
  }
  
  handleViewportChange() {
    const oldColumnCount = this.columnCount;
    this.calculateColumns();
    
    // Only relayout if column count changed
    if (oldColumnCount !== this.columnCount) {
      this.relayoutCards();
      
      // Recalculate visible cards for virtual scrolling
      if (this.options.virtualScrollBuffer > 0) {
        this.updateVisibleCards();
      }
    }
  }
  
  handleKeyboardNavigation(e) {
    const focusedCard = document.activeElement.closest('.news-card');
    if (!focusedCard) return;
    
    const cards = Array.from(this.gridContent.querySelectorAll('.news-card'));
    const currentIndex = cards.indexOf(focusedCard);
    let targetIndex = currentIndex;
    
    switch (e.key) {
      case 'ArrowRight':
        targetIndex = Math.min(currentIndex + 1, cards.length - 1);
        break;
      case 'ArrowLeft':
        targetIndex = Math.max(currentIndex - 1, 0);
        break;
      case 'ArrowDown':
        targetIndex = Math.min(currentIndex + this.columnCount, cards.length - 1);
        break;
      case 'ArrowUp':
        targetIndex = Math.max(currentIndex - this.columnCount, 0);
        break;
      case 'Home':
        targetIndex = 0;
        break;
      case 'End':
        targetIndex = cards.length - 1;
        break;
      default:
        return;
    }
    
    if (targetIndex !== currentIndex) {
      e.preventDefault();
      cards[targetIndex].focus();
      this.scrollCardIntoView(cards[targetIndex]);
    }
  }
  
  handleFocusChange(e) {
    const card = e.target.closest('.news-card');
    if (card) {
      // Ensure focused card is visible
      this.scrollCardIntoView(card);
      
      // Update ARIA live region for screen readers
      this.updateAriaLiveRegion(card);
    }
  }
  
  scrollCardIntoView(card) {
    const cardRect = card.getBoundingClientRect();
    const containerRect = this.container.getBoundingClientRect();
    
    if (cardRect.top < containerRect.top || cardRect.bottom > containerRect.bottom) {
      card.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest'
      });
    }
  }
  
  updateAriaLiveRegion(card) {
    let liveRegion = document.getElementById('card-grid-live-region');
    if (!liveRegion) {
      liveRegion = document.createElement('div');
      liveRegion.id = 'card-grid-live-region';
      liveRegion.setAttribute('aria-live', 'polite');
      liveRegion.setAttribute('aria-atomic', 'true');
      liveRegion.style.position = 'absolute';
      liveRegion.style.left = '-10000px';
      liveRegion.style.width = '1px';
      liveRegion.style.height = '1px';
      liveRegion.style.overflow = 'hidden';
      document.body.appendChild(liveRegion);
    }
    
    const cardData = this.cards.find(c => c.id === card.dataset.cardId);
    if (cardData) {
      liveRegion.textContent = `Focused on ${cardData.title}. Prediction: ${cardData.prediction}. Confidence: ${Math.round(cardData.confidence * 100)}%`;
    }
  }
  
  setupPerformanceMonitoring() {
    // Monitor scroll performance
    let scrollTimeout;
    this.container.addEventListener('scroll', () => {
      if (!scrollTimeout) {
        this.container.classList.add('scrolling');
      }
      
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        this.container.classList.remove('scrolling');
      }, 150);
    });
    
    // Monitor rendering performance
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach(entry => {
            if (entry.entryType === 'measure' && entry.name.includes('card-render')) {
              if (entry.duration > 16) { // More than one frame
                console.warn(`Slow card rendering detected: ${entry.duration}ms`);
              }
            }
          });
        });
        
        observer.observe({ entryTypes: ['measure'] });
      } catch (e) {
        // PerformanceObserver not fully supported
      }
    }
  }
  
  calculateColumns() {
    const containerWidth = this.container.offsetWidth;
    const availableWidth = containerWidth - (this.options.gap * 2);
    const minCardWidth = this.options.minCardWidth;
    
    // Calculate optimal column count based on viewport
    let columnCount;
    if (containerWidth >= 1400) {
      columnCount = 5;
    } else if (containerWidth >= 1200) {
      columnCount = 4;
    } else if (containerWidth >= 1024) {
      columnCount = 3;
    } else if (containerWidth >= 768) {
      columnCount = 2;
    } else {
      columnCount = 1;
    }
    
    // Ensure minimum card width is respected
    const maxPossibleColumns = Math.floor(availableWidth / (minCardWidth + this.options.gap));
    columnCount = Math.min(columnCount, Math.max(1, maxPossibleColumns));
    
    this.columnCount = columnCount;
    this.cardWidth = (availableWidth - (this.options.gap * (columnCount - 1))) / columnCount;
    
    // Update CSS custom properties
    this.container.style.setProperty('--card-width', `${this.cardWidth}px`);
    this.container.style.setProperty('--gap', `${this.options.gap}px`);
    this.container.style.setProperty('--columns', this.columnCount);
    
    // Update grid class for styling
    this.updateGridClass();
    
    // Dispatch layout change event
    this.container.dispatchEvent(new CustomEvent('gridLayoutChange', {
      detail: {
        columnCount: this.columnCount,
        cardWidth: this.cardWidth,
        containerWidth
      }
    }));
  }
  
  updateGridClass() {
    // Remove existing grid classes
    this.gridContent.classList.remove('grid-cols-1', 'grid-cols-2', 'grid-cols-3', 'grid-cols-4', 'grid-cols-5');
    
    // Add current grid class
    this.gridContent.classList.add(`grid-cols-${this.columnCount}`);
    
    // Add responsive classes
    if (this.columnCount === 1) {
      this.container.classList.add('mobile-layout');
      this.container.classList.remove('tablet-layout', 'desktop-layout');
    } else if (this.columnCount === 2) {
      this.container.classList.add('tablet-layout');
      this.container.classList.remove('mobile-layout', 'desktop-layout');
    } else {
      this.container.classList.add('desktop-layout');
      this.container.classList.remove('mobile-layout', 'tablet-layout');
    }
  }
  
  addCards(newCards) {
    const cardElements = newCards.map(cardData => this.createCardElement(cardData));
    
    cardElements.forEach(cardElement => {
      this.gridContent.appendChild(cardElement);
      this.observer.observe(cardElement);
    });
    
    this.cards.push(...newCards);
    this.relayoutCards();
    
    // Setup scroll observer on last card
    if (cardElements.length > 0) {
      const lastCard = cardElements[cardElements.length - 1];
      this.scrollObserver.observe(lastCard);
    }
  }
  
  createCardElement(cardData) {
    const cardElement = document.createElement('article');
    cardElement.className = 'news-card';
    cardElement.dataset.cardId = cardData.id;
    cardElement.setAttribute('role', 'button');
    cardElement.setAttribute('tabindex', '0');
    cardElement.setAttribute('aria-label', `News article: ${cardData.title}`);
    
    cardElement.innerHTML = `
      <div class="card-image-container">
        <div class="card-image-skeleton"></div>
        <img class="card-image" 
             data-src="${cardData.imageUrl || '/images/placeholder.jpg'}" 
             alt="${cardData.title}"
             loading="lazy">
      </div>
      <div class="card-content">
        <h3 class="card-title">${cardData.title}</h3>
        <p class="card-excerpt">${this.truncateText(cardData.content, 120)}</p>
        <div class="card-metadata">
          <div class="prediction-badge ${cardData.prediction.toLowerCase()}" 
               aria-label="Prediction: ${cardData.prediction}, Confidence: ${Math.round(cardData.confidence * 100)}%">
            <span class="prediction-label">${cardData.prediction}</span>
            <span class="confidence-score">${Math.round(cardData.confidence * 100)}%</span>
          </div>
          <time class="card-timestamp" datetime="${cardData.timestamp}">
            ${this.formatDate(cardData.timestamp)}
          </time>
        </div>
      </div>
    `;
    
    return cardElement;
  }
  
  loadCardImages(cardElement) {
    const img = cardElement.querySelector('.card-image');
    const skeleton = cardElement.querySelector('.card-image-skeleton');
    
    if (img && img.dataset.src && !img.src) {
      img.src = img.dataset.src;
      img.onload = () => {
        skeleton.style.display = 'none';
        img.style.opacity = '1';
      };
      img.onerror = () => {
        skeleton.style.display = 'none';
        img.src = '/images/placeholder.jpg';
        img.style.opacity = '1';
      };
    }
  }
  
  relayoutCards() {
    // Performance measurement
    performance.mark('card-relayout-start');
    
    const cards = this.gridContent.querySelectorAll('.news-card');
    
    // Batch DOM updates for better performance
    requestAnimationFrame(() => {
      cards.forEach((card, index) => {
        // Stagger animation delays
        card.style.setProperty('--animation-order', index);
        card.style.animationDelay = `${(index % (this.columnCount * 2)) * 50}ms`;
        
        // Update card position data for virtual scrolling
        if (this.options.virtualScrollBuffer > 0) {
          this.updateCardPosition(card, index);
        }
      });
      
      // Add stagger animation class
      this.gridContent.classList.add('grid-stagger');
      
      performance.mark('card-relayout-end');
      performance.measure('card-relayout', 'card-relayout-start', 'card-relayout-end');
    });
    
    // Update visible cards after layout
    setTimeout(() => {
      this.updateVisibleCards();
    }, 100);
  }
  
  updateCardPosition(card, index) {
    const rect = card.getBoundingClientRect();
    const containerRect = this.container.getBoundingClientRect();
    
    card.dataset.position = JSON.stringify({
      index,
      top: rect.top - containerRect.top,
      height: rect.height,
      column: index % this.columnCount
    });
  }
  
  updateVisibleCards() {
    if (!this.observer) return;
    
    const containerRect = this.container.getBoundingClientRect();
    const bufferZone = this.options.virtualScrollBuffer * 100; // 100px per buffer unit
    
    const cards = this.gridContent.querySelectorAll('.news-card');
    cards.forEach(card => {
      const cardRect = card.getBoundingClientRect();
      const isInViewport = (
        cardRect.bottom >= containerRect.top - bufferZone &&
        cardRect.top <= containerRect.bottom + bufferZone
      );
      
      if (isInViewport && !this.visibleCards.has(card.dataset.cardId)) {
        this.visibleCards.add(card.dataset.cardId);
        this.loadCardImages(card);
      } else if (!isInViewport && this.visibleCards.has(card.dataset.cardId)) {
        this.visibleCards.delete(card.dataset.cardId);
      }
    });
  }
  
  async loadMore() {
    if (this.isLoading || !this.hasMore) return;
    
    this.isLoading = true;
    this.showLoader();
    
    try {
      const response = await fetch(`/api/cards?page=${this.page}&limit=20`);
      const data = await response.json();
      
      if (data.cards && data.cards.length > 0) {
        this.addCards(data.cards);
        this.page++;
        this.hasMore = data.hasMore;
      } else {
        this.hasMore = false;
      }
    } catch (error) {
      console.error('Error loading more cards:', error);
      this.showError('Failed to load more content');
    } finally {
      this.isLoading = false;
      this.hideLoader();
    }
  }
  
  handleCardClick(cardElement) {
    const cardId = cardElement.dataset.cardId;
    const cardData = this.cards.find(card => card.id === cardId);
    
    if (cardData && this.options.onCardClick) {
      this.options.onCardClick(cardData, cardElement);
    }
  }
  
  showLoader() {
    this.loader.style.display = 'flex';
  }
  
  hideLoader() {
    this.loader.style.display = 'none';
  }
  
  showError(message) {
    // Create error message element
    const errorElement = document.createElement('div');
    errorElement.className = 'error-message';
    errorElement.innerHTML = `
      <p>${message}</p>
      <button onclick="this.parentElement.remove()">Dismiss</button>
    `;
    this.container.appendChild(errorElement);
  }
  
  // Utility methods
  truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
  }
  
  formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
  
  debounce(func, wait) {
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
  
  // Public API methods
  refresh() {
    this.cards = [];
    this.visibleCards.clear();
    this.page = 1;
    this.hasMore = true;
    this.gridContent.innerHTML = '';
    this.calculateColumns();
    this.loadMore();
  }
  
  setLayout(layout) {
    const layouts = {
      compact: { minCardWidth: 250, gap: 12 },
      normal: { minCardWidth: 280, gap: 20 },
      spacious: { minCardWidth: 350, gap: 32 }
    };
    
    if (layouts[layout]) {
      Object.assign(this.options, layouts[layout]);
      this.container.className = this.container.className.replace(/card-grid--\w+/g, '');
      this.container.classList.add(`card-grid--${layout}`);
      this.calculateColumns();
      this.relayoutCards();
    }
  }
  
  setColumns(count) {
    if (count >= 1 && count <= 5) {
      this.columnCount = count;
      this.container.style.setProperty('--columns', count);
      this.updateGridClass();
      this.relayoutCards();
    }
  }
  
  getLayoutInfo() {
    return {
      columnCount: this.columnCount,
      cardWidth: this.cardWidth,
      totalCards: this.cards.length,
      visibleCards: this.visibleCards.size,
      containerWidth: this.container.offsetWidth
    };
  }
  
  scrollToCard(cardId) {
    const card = this.gridContent.querySelector(`[data-card-id="${cardId}"]`);
    if (card) {
      card.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      });
      card.focus();
    }
  }
  
  filterCards(filterFn) {
    const cards = this.gridContent.querySelectorAll('.news-card');
    cards.forEach(card => {
      const cardData = this.cards.find(c => c.id === card.dataset.cardId);
      if (cardData && filterFn(cardData)) {
        card.style.display = '';
      } else {
        card.style.display = 'none';
      }
    });
    
    // Relayout after filtering
    setTimeout(() => this.relayoutCards(), 50);
  }
  
  sortCards(sortFn) {
    this.cards.sort(sortFn);
    
    // Re-render cards in new order
    const cardElements = this.cards.map(cardData => {
      const existingCard = this.gridContent.querySelector(`[data-card-id="${cardData.id}"]`);
      if (existingCard) {
        return existingCard;
      }
      return this.createCardElement(cardData);
    });
    
    // Clear and re-append in sorted order
    this.gridContent.innerHTML = '';
    cardElements.forEach(card => {
      this.gridContent.appendChild(card);
      if (!this.observer.observe) {
        this.observer.observe(card);
      }
    });
    
    this.relayoutCards();
  }
  
  destroy() {
    // Disconnect observers
    if (this.observer) this.observer.disconnect();
    if (this.scrollObserver) this.scrollObserver.disconnect();
    if (this.resizeObserver) this.resizeObserver.disconnect();
    
    // Remove event listeners
    window.removeEventListener('resize', this.handleViewportChange);
    window.removeEventListener('orientationchange', this.handleViewportChange);
    
    // Clean up ARIA live region
    const liveRegion = document.getElementById('card-grid-live-region');
    if (liveRegion) {
      liveRegion.remove();
    }
    
    // Clear data
    this.cards = [];
    this.visibleCards.clear();
    
    // Remove container content
    if (this.container) {
      this.container.innerHTML = '';
    }
  }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = CardGrid;
}