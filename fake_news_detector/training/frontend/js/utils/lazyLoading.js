/**
 * Lazy Loading Utilities
 * Advanced lazy loading with intersection observer and performance optimization
 */

class LazyLoader {
  constructor(options = {}) {
    this.options = {
      rootMargin: '50px',
      threshold: 0.1,
      enableDataSaver: true,
      retryAttempts: 3,
      retryDelay: 1000,
      ...options
    };
    
    this.loadedElements = new Set();
    this.failedElements = new Set();
    this.retryCount = new Map();
    
    this.init();
  }
  
  init() {
    this.setupIntersectionObserver();
    this.detectConnectionSpeed();
    this.setupEventListeners();
  }
  
  setupIntersectionObserver() {
    if (!('IntersectionObserver' in window)) {
      console.warn('IntersectionObserver not supported, falling back to immediate loading');
      this.loadAllElements();
      return;
    }
    
    this.observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          this.loadElement(entry.target);
        }
      });
    }, {
      rootMargin: this.options.rootMargin,
      threshold: this.options.threshold
    });
  }
  
  detectConnectionSpeed() {
    this.isSlowConnection = false;
    
    if ('connection' in navigator) {
      const connection = navigator.connection;
      this.isSlowConnection = connection.effectiveType === 'slow-2g' || 
                             connection.effectiveType === '2g' ||
                             connection.saveData;
    }
  }
  
  setupEventListeners() {
    // Handle visibility change to pause/resume loading
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.pauseLoading();
      } else {
        this.resumeLoading();
      }
    });
    
    // Handle connection change
    if ('connection' in navigator) {
      navigator.connection.addEventListener('change', () => {
        this.detectConnectionSpeed();
        this.adjustLoadingStrategy();
      });
    }
  }
  
  observe(element) {
    if (this.loadedElements.has(element) || this.failedElements.has(element)) {
      return;
    }
    
    if (this.observer) {
      this.observer.observe(element);
    } else {
      this.loadElement(element);
    }
  }
  
  unobserve(element) {
    if (this.observer) {
      this.observer.unobserve(element);
    }
  }
  
  async loadElement(element) {
    if (this.loadedElements.has(element) || this.failedElements.has(element)) {
      return;
    }
    
    // Check if we should defer loading on slow connections
    if (this.isSlowConnection && this.options.enableDataSaver) {
      if (!element.dataset.priority || element.dataset.priority !== 'high') {
        this.deferLoading(element);
        return;
      }
    }
    
    const elementType = this.getElementType(element);
    
    try {
      await this.loadByType(element, elementType);
      this.onLoadSuccess(element);
    } catch (error) {
      this.onLoadError(element, error);
    }
  }
  
  getElementType(element) {
    if (element.tagName === 'IMG') return 'image';
    if (element.tagName === 'VIDEO') return 'video';
    if (element.tagName === 'IFRAME') return 'iframe';
    if (element.dataset.src) return 'background';
    return 'unknown';
  }
  
  async loadByType(element, type) {
    switch (type) {
      case 'image':
        return this.loadImage(element);
      case 'video':
        return this.loadVideo(element);
      case 'iframe':
        return this.loadIframe(element);
      case 'background':
        return this.loadBackground(element);
      default:
        throw new Error(`Unknown element type: ${type}`);
    }
  }
  
  loadImage(img) {
    return new Promise((resolve, reject) => {
      const src = img.dataset.src;
      if (!src) {
        reject(new Error('No data-src attribute found'));
        return;
      }
      
      // Show loading state
      this.showLoadingState(img);
      
      const tempImg = new Image();
      
      tempImg.onload = () => {
        img.src = src;
        
        // Handle srcset if available
        if (img.dataset.srcset) {
          img.srcset = img.dataset.srcset;
        }
        
        // Handle sizes if available
        if (img.dataset.sizes) {
          img.sizes = img.dataset.sizes;
        }
        
        this.hideLoadingState(img);
        resolve();
      };
      
      tempImg.onerror = () => {
        reject(new Error(`Failed to load image: ${src}`));
      };
      
      tempImg.src = src;
    });
  }
  
  loadVideo(video) {
    return new Promise((resolve, reject) => {
      const src = video.dataset.src;
      if (!src) {
        reject(new Error('No data-src attribute found'));
        return;
      }
      
      this.showLoadingState(video);
      
      video.addEventListener('loadeddata', () => {
        this.hideLoadingState(video);
        resolve();
      }, { once: true });
      
      video.addEventListener('error', () => {
        reject(new Error(`Failed to load video: ${src}`));
      }, { once: true });
      
      video.src = src;
      video.load();
    });
  }
  
  loadIframe(iframe) {
    return new Promise((resolve, reject) => {
      const src = iframe.dataset.src;
      if (!src) {
        reject(new Error('No data-src attribute found'));
        return;
      }
      
      this.showLoadingState(iframe);
      
      iframe.addEventListener('load', () => {
        this.hideLoadingState(iframe);
        resolve();
      }, { once: true });
      
      iframe.addEventListener('error', () => {
        reject(new Error(`Failed to load iframe: ${src}`));
      }, { once: true });
      
      iframe.src = src;
    });
  }
  
  loadBackground(element) {
    return new Promise((resolve, reject) => {
      const src = element.dataset.src;
      if (!src) {
        reject(new Error('No data-src attribute found'));
        return;
      }
      
      this.showLoadingState(element);
      
      const tempImg = new Image();
      
      tempImg.onload = () => {
        element.style.backgroundImage = `url(${src})`;
        this.hideLoadingState(element);
        resolve();
      };
      
      tempImg.onerror = () => {
        reject(new Error(`Failed to load background image: ${src}`));
      };
      
      tempImg.src = src;
    });
  }
  
  showLoadingState(element) {
    element.classList.add('lazy-loading');
    
    // Add skeleton loader if not present
    if (!element.querySelector('.lazy-skeleton')) {
      const skeleton = document.createElement('div');
      skeleton.className = 'lazy-skeleton';
      element.appendChild(skeleton);
    }
  }
  
  hideLoadingState(element) {
    element.classList.remove('lazy-loading');
    element.classList.add('lazy-loaded');
    
    // Remove skeleton loader
    const skeleton = element.querySelector('.lazy-skeleton');
    if (skeleton) {
      skeleton.remove();
    }
  }
  
  onLoadSuccess(element) {
    this.loadedElements.add(element);
    this.unobserve(element);
    
    // Dispatch success event
    element.dispatchEvent(new CustomEvent('lazyLoaded', {
      detail: { element, success: true }
    }));
  }
  
  async onLoadError(element, error) {
    console.warn('Lazy loading failed:', error);
    
    const retryCount = this.retryCount.get(element) || 0;
    
    if (retryCount < this.options.retryAttempts) {
      // Retry after delay
      this.retryCount.set(element, retryCount + 1);
      
      setTimeout(() => {
        this.loadElement(element);
      }, this.options.retryDelay * (retryCount + 1));
      
      return;
    }
    
    // Max retries reached
    this.failedElements.add(element);
    this.unobserve(element);
    this.showErrorState(element);
    
    // Dispatch error event
    element.dispatchEvent(new CustomEvent('lazyLoadError', {
      detail: { element, error, retryCount }
    }));
  }
  
  showErrorState(element) {
    element.classList.add('lazy-error');
    this.hideLoadingState(element);
    
    // Add retry button for images
    if (element.tagName === 'IMG') {
      const retryBtn = document.createElement('button');
      retryBtn.className = 'lazy-retry-btn';
      retryBtn.textContent = 'Retry';
      retryBtn.onclick = () => {
        this.retryCount.delete(element);
        this.failedElements.delete(element);
        element.classList.remove('lazy-error');
        retryBtn.remove();
        this.loadElement(element);
      };
      
      element.parentElement?.appendChild(retryBtn);
    }
  }
  
  deferLoading(element) {
    // Create a "Load" button for deferred content
    const loadBtn = document.createElement('button');
    loadBtn.className = 'lazy-load-btn';
    loadBtn.textContent = 'Load Content';
    loadBtn.onclick = () => {
      loadBtn.remove();
      this.loadElement(element);
    };
    
    element.parentElement?.appendChild(loadBtn);
  }
  
  adjustLoadingStrategy() {
    if (this.isSlowConnection) {
      // Reduce concurrent loading
      this.options.rootMargin = '20px';
    } else {
      // Increase preloading distance
      this.options.rootMargin = '100px';
    }
    
    // Recreate observer with new options
    if (this.observer) {
      this.observer.disconnect();
      this.setupIntersectionObserver();
      
      // Re-observe unloaded elements
      document.querySelectorAll('[data-src]').forEach(element => {
        if (!this.loadedElements.has(element) && !this.failedElements.has(element)) {
          this.observe(element);
        }
      });
    }
  }
  
  pauseLoading() {
    if (this.observer) {
      this.observer.disconnect();
    }
  }
  
  resumeLoading() {
    this.setupIntersectionObserver();
    
    // Re-observe elements
    document.querySelectorAll('[data-src]').forEach(element => {
      if (!this.loadedElements.has(element) && !this.failedElements.has(element)) {
        this.observe(element);
      }
    });
  }
  
  loadAllElements() {
    // Fallback for browsers without IntersectionObserver
    document.querySelectorAll('[data-src]').forEach(element => {
      this.loadElement(element);
    });
  }
  
  // Public API methods
  refresh() {
    document.querySelectorAll('[data-src]').forEach(element => {
      if (!this.loadedElements.has(element) && !this.failedElements.has(element)) {
        this.observe(element);
      }
    });
  }
  
  reset() {
    this.loadedElements.clear();
    this.failedElements.clear();
    this.retryCount.clear();
    
    if (this.observer) {
      this.observer.disconnect();
      this.setupIntersectionObserver();
    }
  }
  
  destroy() {
    if (this.observer) {
      this.observer.disconnect();
    }
    
    this.loadedElements.clear();
    this.failedElements.clear();
    this.retryCount.clear();
  }
  
  // Static utility methods
  static setupElement(element, src, options = {}) {
    element.dataset.src = src;
    
    if (options.srcset) {
      element.dataset.srcset = options.srcset;
    }
    
    if (options.sizes) {
      element.dataset.sizes = options.sizes;
    }
    
    if (options.priority) {
      element.dataset.priority = options.priority;
    }
    
    element.classList.add('lazy-element');
  }
}

// CSS for lazy loading states
const lazyLoadingCSS = `
.lazy-element {
  transition: opacity 0.3s ease;
}

.lazy-loading {
  position: relative;
  overflow: hidden;
}

.lazy-skeleton {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.lazy-loaded {
  opacity: 1;
}

.lazy-error {
  opacity: 0.5;
  filter: grayscale(100%);
}

.lazy-retry-btn,
.lazy-load-btn {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: #3b82f6;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  z-index: 10;
}

.lazy-retry-btn:hover,
.lazy-load-btn:hover {
  background: #2563eb;
}

@media (prefers-reduced-motion: reduce) {
  .lazy-skeleton {
    animation: none;
    background: #f0f0f0;
  }
}
`;

// Inject CSS
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = lazyLoadingCSS;
  document.head.appendChild(style);
}

// Global instance
const lazyLoader = new LazyLoader();

// Auto-initialize on DOM ready
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      lazyLoader.refresh();
    });
  } else {
    lazyLoader.refresh();
  }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { LazyLoader, lazyLoader };
}