/**
 * Image Optimization Utilities
 * Handles lazy loading, responsive images, and performance optimization
 */

class ImageOptimizer {
  constructor(options = {}) {
    this.options = {
      rootMargin: '50px',
      threshold: 0.1,
      enableWebP: true,
      placeholderQuality: 10,
      ...options
    };
    
    this.observer = null;
    this.init();
  }
  
  init() {
    this.setupIntersectionObserver();
    this.detectWebPSupport();
  }
  
  setupIntersectionObserver() {
    if (!('IntersectionObserver' in window)) {
      // Fallback for older browsers
      this.loadAllImages();
      return;
    }
    
    this.observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          this.loadImage(entry.target);
          this.observer.unobserve(entry.target);
        }
      });
    }, {
      rootMargin: this.options.rootMargin,
      threshold: this.options.threshold
    });
  }
  
  detectWebPSupport() {
    const canvas = document.createElement('canvas');
    canvas.width = 1;
    canvas.height = 1;
    
    this.supportsWebP = canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
  }
  
  observeImage(img) {
    if (this.observer) {
      this.observer.observe(img);
    } else {
      this.loadImage(img);
    }
  }
  
  loadImage(img) {
    const src = this.getOptimizedSrc(img);
    const skeleton = img.parentElement?.querySelector('.card-image-skeleton');
    
    if (!src) return;
    
    // Create a new image to preload
    const tempImg = new Image();
    
    tempImg.onload = () => {
      img.src = src;
      img.style.opacity = '1';
      if (skeleton) skeleton.style.display = 'none';
      img.classList.add('loaded');
      
      // Dispatch load event
      img.dispatchEvent(new CustomEvent('imageLoaded', {
        detail: { src, element: img }
      }));
    };
    
    tempImg.onerror = () => {
      const fallbackSrc = this.getFallbackSrc(img);
      img.src = fallbackSrc;
      img.style.opacity = '1';
      if (skeleton) skeleton.style.display = 'none';
      img.classList.add('error');
      
      // Dispatch error event
      img.dispatchEvent(new CustomEvent('imageError', {
        detail: { originalSrc: src, fallbackSrc, element: img }
      }));
    };
    
    // Start loading
    tempImg.src = src;
  }
  
  getOptimizedSrc(img) {
    const dataSrc = img.dataset.src;
    if (!dataSrc) return null;
    
    // If it's already a data URL or external URL, return as-is
    if (dataSrc.startsWith('data:') || dataSrc.startsWith('http')) {
      return dataSrc;
    }
    
    // Generate responsive image URL based on container size
    const containerWidth = img.parentElement?.offsetWidth || 300;
    const devicePixelRatio = window.devicePixelRatio || 1;
    const targetWidth = Math.ceil(containerWidth * devicePixelRatio);
    
    // Create optimized URL (assuming a backend service)
    let optimizedUrl = dataSrc;
    
    // Add width parameter
    const separator = dataSrc.includes('?') ? '&' : '?';
    optimizedUrl += `${separator}w=${targetWidth}`;
    
    // Add WebP format if supported
    if (this.supportsWebP && this.options.enableWebP) {
      optimizedUrl += '&format=webp';
    }
    
    // Add quality parameter
    optimizedUrl += '&q=85';
    
    return optimizedUrl;
  }
  
  getFallbackSrc(img) {
    // Return a placeholder SVG
    const width = img.parentElement?.offsetWidth || 300;
    const height = Math.floor(width * 0.6); // 3:2 aspect ratio
    
    return `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='${width}' height='${height}' viewBox='0 0 ${width} ${height}'%3E%3Crect width='${width}' height='${height}' fill='%23f0f0f0'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23999' font-family='Arial, sans-serif' font-size='14'%3EImage not available%3C/text%3E%3C/svg%3E`;
  }
  
  generatePlaceholder(width, height, text = 'Loading...') {
    return `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='${width}' height='${height}' viewBox='0 0 ${width} ${height}'%3E%3Crect width='${width}' height='${height}' fill='%23f8f9fa'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23adb5bd' font-family='Arial, sans-serif' font-size='12'%3E${encodeURIComponent(text)}%3C/text%3E%3C/svg%3E`;
  }
  
  loadAllImages() {
    // Fallback for browsers without IntersectionObserver
    const images = document.querySelectorAll('img[data-src]');
    images.forEach(img => this.loadImage(img));
  }
  
  preloadImage(src) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = reject;
      img.src = src;
    });
  }
  
  preloadImages(srcArray) {
    return Promise.all(srcArray.map(src => this.preloadImage(src)));
  }
  
  destroy() {
    if (this.observer) {
      this.observer.disconnect();
    }
  }
}

// Utility functions for responsive images
const ImageUtils = {
  // Generate srcset for responsive images
  generateSrcSet(baseSrc, widths = [300, 600, 900, 1200]) {
    return widths.map(width => {
      const separator = baseSrc.includes('?') ? '&' : '?';
      return `${baseSrc}${separator}w=${width} ${width}w`;
    }).join(', ');
  },
  
  // Generate sizes attribute based on breakpoints
  generateSizes(breakpoints = {
    mobile: '100vw',
    tablet: '50vw',
    desktop: '33vw'
  }) {
    return [
      `(max-width: 768px) ${breakpoints.mobile}`,
      `(max-width: 1024px) ${breakpoints.tablet}`,
      breakpoints.desktop
    ].join(', ');
  },
  
  // Extract dominant color from image for placeholder
  async getDominantColor(imgSrc) {
    return new Promise((resolve) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = img.width;
        canvas.height = img.height;
        
        ctx.drawImage(img, 0, 0);
        
        try {
          const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
          const data = imageData.data;
          
          let r = 0, g = 0, b = 0;
          const pixelCount = data.length / 4;
          
          for (let i = 0; i < data.length; i += 4) {
            r += data[i];
            g += data[i + 1];
            b += data[i + 2];
          }
          
          r = Math.floor(r / pixelCount);
          g = Math.floor(g / pixelCount);
          b = Math.floor(b / pixelCount);
          
          resolve(`rgb(${r}, ${g}, ${b})`);
        } catch (e) {
          resolve('#f0f0f0'); // Fallback color
        }
      };
      
      img.onerror = () => resolve('#f0f0f0');
      img.src = imgSrc;
    });
  },
  
  // Create blur placeholder from image
  createBlurPlaceholder(imgSrc, quality = 10) {
    return new Promise((resolve) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // Small canvas for blur effect
        canvas.width = quality;
        canvas.height = Math.floor((img.height / img.width) * quality);
        
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        
        try {
          const dataUrl = canvas.toDataURL('image/jpeg', 0.5);
          resolve(dataUrl);
        } catch (e) {
          resolve(null);
        }
      };
      
      img.onerror = () => resolve(null);
      img.src = imgSrc;
    });
  }
};

// Global instance
const imageOptimizer = new ImageOptimizer();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ImageOptimizer, ImageUtils, imageOptimizer };
}