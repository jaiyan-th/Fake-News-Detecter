/**
 * NewsCard Component - Individual card for displaying news articles
 * Handles card interactions, animations, and accessibility
 */
class NewsCard {
  constructor(cardData, options = {}) {
    this.data = cardData;
    this.options = {
      enableHover: true,
      enableKeyboard: true,
      truncateLength: 120,
      ...options
    };

    this.element = null;
    this.isImageLoaded = false;

    this.init();
  }

  init() {
    this.createElement();
    this.setupEventListeners();
    this.setupAccessibility();
  }

  createElement() {
    this.element = document.createElement('article');
    this.element.className = 'news-card';
    this.element.dataset.cardId = this.data.id;

    this.element.innerHTML = `
      <div class="card-container">
        <div class="card-image-wrapper">
          <div class="card-image-skeleton" aria-hidden="true"></div>
          <img class="card-image" 
               data-src="${this.data.imageUrl || this.getPlaceholderImage()}" 
               alt="${this.data.title}"
               loading="lazy">
          <div class="card-overlay"></div>
        </div>
        
        <div class="card-content">
          <header class="card-header">
            <h3 class="card-title" title="${this.data.title}">
              ${this.data.title}
            </h3>
            ${this.data.source ? `<span class="card-source">${this.data.source}</span>` : ''}
          </header>
          
          <div class="card-body">
            <p class="card-excerpt">
              ${this.truncateText(this.data.content, this.options.truncateLength)}
            </p>
            
            ${this.data.tags ? this.renderTags() : ''}
          </div>
          
          <footer class="card-footer">
            <div class="prediction-container">
              <div class="prediction-badge ${this.data.prediction.toLowerCase()}" 
                   role="img"
                   aria-label="Prediction: ${this.data.prediction}, Confidence: ${Math.round(this.data.confidence * 100)}%">
                <span class="prediction-icon">${this.getPredictionIcon()}</span>
                <div class="prediction-details">
                  <span class="prediction-label">${this.data.prediction}</span>
                  <div class="confidence-bar">
                    <div class="confidence-fill" 
                         style="width: ${this.data.confidence * 100}%"
                         aria-hidden="true"></div>
                  </div>
                  <span class="confidence-text">${Math.round(this.data.confidence * 100)}%</span>
                </div>
              </div>
            </div>
            
            <div class="card-metadata">
              <time class="card-timestamp" 
                    datetime="${this.data.timestamp}"
                    title="${new Date(this.data.timestamp).toLocaleString()}">
                ${this.formatRelativeTime(this.data.timestamp)}
              </time>
              ${this.data.username ? `<span class="card-author">by ${this.data.username}</span>` : ''}
            </div>
          </footer>
        </div>
        
        <div class="card-actions" role="toolbar" aria-label="Card actions">
          <button class="action-btn share-btn" 
                  aria-label="Share article"
                  title="Share this article">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92s2.92-1.31 2.92-2.92-1.31-2.92-2.92-2.92z"/>
            </svg>
          </button>
          
          <button class="action-btn bookmark-btn" 
                  aria-label="Bookmark article"
                  title="Bookmark this article">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M17 3H7c-1.1 0-2 .9-2 2v16l7-3 7 3V5c0-1.1-.9-2-2-2z"/>
            </svg>
          </button>
        </div>
      </div>
    `;

    return this.element;
  }

  setupEventListeners() {
    if (!this.element) return;

    // Hover effects
    if (this.options.enableHover) {
      this.element.addEventListener('mouseenter', this.handleMouseEnter.bind(this));
      this.element.addEventListener('mouseleave', this.handleMouseLeave.bind(this));
    }

    // Click handling
    this.element.addEventListener('click', this.handleClick.bind(this));

    // Keyboard navigation
    if (this.options.enableKeyboard) {
      this.element.addEventListener('keydown', this.handleKeyDown.bind(this));
    }

    // Action buttons
    const shareBtn = this.element.querySelector('.share-btn');
    const bookmarkBtn = this.element.querySelector('.bookmark-btn');

    shareBtn?.addEventListener('click', this.handleShare.bind(this));
    bookmarkBtn?.addEventListener('click', this.handleBookmark.bind(this));

    // Image loading
    this.setupImageLoading();
  }

  setupAccessibility() {
    if (!this.element) return;

    this.element.setAttribute('role', 'button');
    this.element.setAttribute('tabindex', '0');
    this.element.setAttribute('aria-label',
      `News article: ${this.data.title}. Prediction: ${this.data.prediction}. Confidence: ${Math.round(this.data.confidence * 100)}%`
    );

    // Add describedby for screen readers
    const contentId = `card-content-${this.data.id}`;
    this.element.querySelector('.card-content').id = contentId;
    this.element.setAttribute('aria-describedby', contentId);
  }

  setupImageLoading() {
    const img = this.element.querySelector('.card-image');
    const skeleton = this.element.querySelector('.card-image-skeleton');

    if (!img || !skeleton) return;

    // Intersection Observer for lazy loading
    const imageObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting && !this.isImageLoaded) {
          this.loadImage(img, skeleton);
          imageObserver.unobserve(entry.target);
        }
      });
    }, { rootMargin: '50px' });

    imageObserver.observe(img);
  }

  loadImage(img, skeleton) {
    const src = img.dataset.src;
    if (!src) return;

    const tempImg = new Image();
    tempImg.onload = () => {
      img.src = src;
      img.style.opacity = '1';
      skeleton.style.display = 'none';
      this.isImageLoaded = true;
      this.element.classList.add('image-loaded');
    };

    tempImg.onerror = () => {
      img.src = this.getPlaceholderImage();
      img.style.opacity = '1';
      skeleton.style.display = 'none';
      this.element.classList.add('image-error');
    };

    tempImg.src = src;
  }

  // Event Handlers
  handleMouseEnter(e) {
    this.element.classList.add('card-hover');

    // Animate prediction confidence bar
    const confidenceFill = this.element.querySelector('.confidence-fill');
    if (confidenceFill) {
      confidenceFill.style.transform = 'scaleX(1.05)';
    }
  }

  handleMouseLeave(e) {
    this.element.classList.remove('card-hover');

    const confidenceFill = this.element.querySelector('.confidence-fill');
    if (confidenceFill) {
      confidenceFill.style.transform = 'scaleX(1)';
    }
  }

  handleClick(e) {
    // Prevent action button clicks from triggering card click
    if (e.target.closest('.card-actions')) {
      return;
    }

    this.element.classList.add('card-clicked');
    setTimeout(() => {
      this.element.classList.remove('card-clicked');
    }, 200);

    // Emit custom event
    const clickEvent = new CustomEvent('cardClick', {
      detail: { cardData: this.data, element: this.element },
      bubbles: true
    });
    this.element.dispatchEvent(clickEvent);
  }

  handleKeyDown(e) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      this.handleClick(e);
    }
  }

  handleShare(e) {
    e.stopPropagation();

    if (navigator.share) {
      navigator.share({
        title: this.data.title,
        text: this.truncateText(this.data.content, 100),
        url: window.location.href
      });
    } else {
      // Fallback: copy to clipboard
      const shareText = `${this.data.title}\n\n${this.truncateText(this.data.content, 200)}\n\n${window.location.href}`;
      navigator.clipboard.writeText(shareText).then(() => {
        this.showToast('Link copied to clipboard!');
      });
    }
  }

  handleBookmark(e) {
    e.stopPropagation();

    const bookmarkBtn = e.currentTarget;
    const isBookmarked = bookmarkBtn.classList.contains('bookmarked');

    if (isBookmarked) {
      bookmarkBtn.classList.remove('bookmarked');
      bookmarkBtn.setAttribute('aria-label', 'Bookmark article');
      this.showToast('Bookmark removed');
    } else {
      bookmarkBtn.classList.add('bookmarked');
      bookmarkBtn.setAttribute('aria-label', 'Remove bookmark');
      this.showToast('Article bookmarked');
    }

    // Emit bookmark event
    const bookmarkEvent = new CustomEvent('cardBookmark', {
      detail: { cardData: this.data, isBookmarked: !isBookmarked },
      bubbles: true
    });
    this.element.dispatchEvent(bookmarkEvent);
  }

  // Utility Methods
  truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
  }

  formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);

    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  getPredictionIcon() {
    return this.data.prediction === 'REAL' ? '✓' : '⚠';
  }

  getPlaceholderImage() {
    return `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='200' viewBox='0 0 300 200'%3E%3Crect width='300' height='200' fill='%23f0f0f0'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23999' font-family='Arial, sans-serif' font-size='14'%3ENo Image%3C/text%3E%3C/svg%3E`;
  }

  renderTags() {
    if (!this.data.tags || this.data.tags.length === 0) return '';

    return `
      <div class="card-tags">
        ${this.data.tags.slice(0, 3).map(tag =>
      `<span class="tag">${tag}</span>`
    ).join('')}
        ${this.data.tags.length > 3 ? `<span class="tag-more">+${this.data.tags.length - 3}</span>` : ''}
      </div>
    `;
  }

  showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('show');
    }, 100);

    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, 2000);
  }

  // Public API
  updateData(newData) {
    this.data = { ...this.data, ...newData };
    this.refresh();
  }

  refresh() {
    const parent = this.element.parentNode;
    const newElement = this.createElement();
    parent.replaceChild(newElement, this.element);
    this.setupEventListeners();
    this.setupAccessibility();
  }

  destroy() {
    if (this.element && this.element.parentNode) {
      this.element.parentNode.removeChild(this.element);
    }
  }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = NewsCard;
}