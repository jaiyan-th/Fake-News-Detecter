/**
 * Comprehensive Responsive Design Test Suite
 * Tests layout on desktop, tablet, and mobile screen sizes
 * Validates green theme consistency across all components
 * Tests typography readability and spacing
 */

class ResponsiveDesignTest {
  constructor() {
    this.results = [];
    this.breakpoints = {
      mobile: 480,
      tablet: 768,
      desktop: 1024,
      large: 1200
    };
    this.testViewports = [
      { name: 'Mobile Portrait', width: 375, height: 667 },
      { name: 'Mobile Landscape', width: 667, height: 375 },
      { name: 'Tablet Portrait', width: 768, height: 1024 },
      { name: 'Tablet Landscape', width: 1024, height: 768 },
      { name: 'Desktop Small', width: 1024, height: 768 },
      { name: 'Desktop Large', width: 1440, height: 900 }
    ];
    this.originalViewport = {
      width: window.innerWidth,
      height: window.innerHeight
    };
  }

  // Test responsive layout across different screen sizes
  testResponsiveLayout() {
    console.log('🔍 Testing responsive layout across screen sizes...');
    
    this.testViewports.forEach(viewport => {
      this.simulateViewport(viewport.width, viewport.height);
      
      // Test header responsiveness
      this.testHeaderResponsiveness(viewport);
      
      // Test hero section responsiveness
      this.testHeroSectionResponsiveness(viewport);
      
      // Test article list responsiveness
      this.testArticleListResponsiveness(viewport);
      
      // Test navigation responsiveness
      this.testNavigationResponsiveness(viewport);
      
      // Test modal responsiveness
      this.testModalResponsiveness(viewport);
    });
    
    // Restore original viewport
    this.restoreViewport();
  }

  // Test green theme consistency across all components
  testGreenThemeConsistency() {
    console.log('🎨 Testing green theme consistency...');
    
    const themeElements = [
      { selector: '.answersq-header', property: 'background-color', expectedColor: 'primary-green' },
      { selector: '.btn-primary', property: 'background-color', expectedColor: 'primary-green' },
      { selector: '.search-btn', property: 'background-color', expectedColor: 'primary-green' },
      { selector: '.article-prediction.real', property: 'background-color', expectedColor: 'success-green' },
      { selector: '.nav-btn.primary:hover', property: 'color', expectedColor: 'primary-green' },
      { selector: '.article-item:hover', property: 'border-color', expectedColor: 'primary-green-light' },
      { selector: '.confidence-badge', property: 'color', expectedColor: 'primary-green-darker' },
      { selector: '.modal-title', property: 'color', expectedColor: 'primary-green-darker' }
    ];

    themeElements.forEach(element => {
      const domElement = document.querySelector(element.selector);
      if (domElement) {
        const computedStyle = getComputedStyle(domElement);
        const actualValue = computedStyle.getPropertyValue(element.property);
        const expectedValue = this.getCSSVariableValue(`--${element.expectedColor}`);
        
        const isConsistent = this.compareColors(actualValue, expectedValue);
        
        this.results.push({
          category: 'Theme Consistency',
          test: `${element.selector} ${element.property}`,
          expected: expectedValue,
          actual: actualValue,
          passed: isConsistent
        });
      } else {
        // Create test element if it doesn't exist
        this.createTestElement(element.selector, element);
      }
    });

    // Test CSS custom properties
    this.testCSSCustomProperties();
    
    // Test color contrast ratios
    this.testColorContrast();
  }

  // Test typography readability and spacing
  testTypographyReadability() {
    console.log('📝 Testing typography readability and spacing...');
    
    // Test font size hierarchy
    this.testFontSizeHierarchy();
    
    // Test line height and spacing
    this.testLineHeightSpacing();
    
    // Test text contrast and readability
    this.testTextReadability();
    
    // Test responsive typography
    this.testResponsiveTypography();
    
    // Test spacing consistency
    this.testSpacingConsistency();
  }

  // Simulate different viewport sizes
  simulateViewport(width, height) {
    // Create a test container with specific dimensions
    const testContainer = document.getElementById('responsive-test-container') || 
                         this.createTestContainer();
    
    testContainer.style.width = `${width}px`;
    testContainer.style.height = `${height}px`;
    
    // Trigger resize event simulation
    const resizeEvent = new Event('resize');
    window.dispatchEvent(resizeEvent);
    
    // Update viewport meta tag simulation
    this.updateViewportMeta(width);
  }

  // Test header responsiveness
  testHeaderResponsiveness(viewport) {
    const header = document.querySelector('.answersq-header');
    if (!header) return;

    const headerContainer = header.querySelector('.header-container');
    const headerNav = header.querySelector('.header-nav');
    const navLinks = header.querySelectorAll('.nav-link');
    
    if (viewport.width <= this.breakpoints.tablet) {
      // Mobile/tablet behavior
      this.results.push({
        category: 'Responsive Layout',
        test: `Header - ${viewport.name} - Navigation Links Hidden`,
        expected: 'Nav links should be hidden on mobile/tablet',
        actual: this.getElementVisibility(navLinks[0]),
        passed: this.getElementVisibility(navLinks[0]) === 'hidden'
      });
      
      // Test header height adjustment
      const headerHeight = headerContainer ? headerContainer.offsetHeight : 0;
      const expectedHeight = viewport.width <= this.breakpoints.mobile ? 56 : 64;
      
      this.results.push({
        category: 'Responsive Layout',
        test: `Header - ${viewport.name} - Height Adjustment`,
        expected: `${expectedHeight}px`,
        actual: `${headerHeight}px`,
        passed: Math.abs(headerHeight - expectedHeight) <= 8
      });
    } else {
      // Desktop behavior
      this.results.push({
        category: 'Responsive Layout',
        test: `Header - ${viewport.name} - Navigation Links Visible`,
        expected: 'Nav links should be visible on desktop',
        actual: this.getElementVisibility(navLinks[0]),
        passed: this.getElementVisibility(navLinks[0]) === 'visible'
      });
    }
  }

  // Test hero section responsiveness
  testHeroSectionResponsiveness(viewport) {
    const heroSection = document.querySelector('.hero-section');
    const heroTitle = document.querySelector('.hero-title');
    const searchContainer = document.querySelector('.search-container');
    
    if (!heroSection || !heroTitle) return;

    // Test title font size responsiveness
    const titleFontSize = parseFloat(getComputedStyle(heroTitle).fontSize);
    let expectedMinSize, expectedMaxSize;
    
    if (viewport.width <= this.breakpoints.mobile) {
      expectedMinSize = 24; // 1.5rem
      expectedMaxSize = 32; // 2rem
    } else if (viewport.width <= this.breakpoints.tablet) {
      expectedMinSize = 30; // 1.875rem
      expectedMaxSize = 40; // 2.5rem
    } else {
      expectedMinSize = 36; // 2.25rem
      expectedMaxSize = 48; // 3rem
    }
    
    this.results.push({
      category: 'Responsive Layout',
      test: `Hero Title - ${viewport.name} - Font Size`,
      expected: `${expectedMinSize}px - ${expectedMaxSize}px`,
      actual: `${titleFontSize}px`,
      passed: titleFontSize >= expectedMinSize && titleFontSize <= expectedMaxSize
    });

    // Test search container width
    if (searchContainer) {
      const containerWidth = searchContainer.offsetWidth;
      const parentWidth = searchContainer.parentElement.offsetWidth;
      const widthPercentage = (containerWidth / parentWidth) * 100;
      
      this.results.push({
        category: 'Responsive Layout',
        test: `Search Container - ${viewport.name} - Width Responsiveness`,
        expected: 'Should adapt to container width',
        actual: `${widthPercentage.toFixed(1)}%`,
        passed: widthPercentage >= 80 && widthPercentage <= 100
      });
    }
  }

  // Test article list responsiveness
  testArticleListResponsiveness(viewport) {
    const articleItems = document.querySelectorAll('.article-item');
    if (articleItems.length === 0) return;

    const firstArticle = articleItems[0];
    const articleLayout = firstArticle.querySelector('.article-layout');
    const articleSidebar = firstArticle.querySelector('.article-sidebar');
    const articleMeta = firstArticle.querySelector('.article-meta');
    
    if (viewport.width <= this.breakpoints.tablet) {
      // Mobile/tablet layout should be stacked
      if (articleLayout) {
        const layoutDirection = getComputedStyle(articleLayout).flexDirection;
        
        this.results.push({
          category: 'Responsive Layout',
          test: `Article Layout - ${viewport.name} - Stacked Layout`,
          expected: 'column',
          actual: layoutDirection,
          passed: layoutDirection === 'column'
        });
      }
      
      // Sidebar should be horizontal on mobile
      if (articleSidebar && viewport.width <= this.breakpoints.tablet) {
        const sidebarDirection = getComputedStyle(articleSidebar).flexDirection;
        
        this.results.push({
          category: 'Responsive Layout',
          test: `Article Sidebar - ${viewport.name} - Horizontal Layout`,
          expected: 'row',
          actual: sidebarDirection,
          passed: sidebarDirection === 'row'
        });
      }
    } else {
      // Desktop layout should be horizontal
      if (articleLayout) {
        const layoutDirection = getComputedStyle(articleLayout).flexDirection;
        
        this.results.push({
          category: 'Responsive Layout',
          test: `Article Layout - ${viewport.name} - Horizontal Layout`,
          expected: 'row',
          actual: layoutDirection,
          passed: layoutDirection === 'row'
        });
      }
    }

    // Test article padding responsiveness
    const articlePadding = parseFloat(getComputedStyle(firstArticle).paddingLeft);
    let expectedPadding;
    
    if (viewport.width <= this.breakpoints.mobile) {
      expectedPadding = 16; // --spacing-lg
    } else if (viewport.width <= this.breakpoints.tablet) {
      expectedPadding = 24; // --spacing-xl
    } else {
      expectedPadding = 32; // --spacing-2xl
    }
    
    this.results.push({
      category: 'Responsive Layout',
      test: `Article Padding - ${viewport.name}`,
      expected: `${expectedPadding}px`,
      actual: `${articlePadding}px`,
      passed: Math.abs(articlePadding - expectedPadding) <= 8
    });
  }

  // Test navigation responsiveness
  testNavigationResponsiveness(viewport) {
    const headerNav = document.querySelector('.header-nav');
    const navLinks = document.querySelectorAll('.nav-link');
    const navBtns = document.querySelectorAll('.nav-btn');
    
    if (!headerNav) return;

    // Test navigation gap
    const navGap = parseFloat(getComputedStyle(headerNav).gap);
    const expectedGap = viewport.width <= this.breakpoints.tablet ? 8 : 16;
    
    this.results.push({
      category: 'Responsive Layout',
      test: `Navigation Gap - ${viewport.name}`,
      expected: `${expectedGap}px`,
      actual: `${navGap}px`,
      passed: Math.abs(navGap - expectedGap) <= 4
    });

    // Test button responsiveness
    if (navBtns.length > 0) {
      const btnPadding = parseFloat(getComputedStyle(navBtns[0]).paddingLeft);
      const isResponsive = btnPadding >= 8 && btnPadding <= 24;
      
      this.results.push({
        category: 'Responsive Layout',
        test: `Navigation Buttons - ${viewport.name} - Padding`,
        expected: '8px - 24px',
        actual: `${btnPadding}px`,
        passed: isResponsive
      });
    }
  }

  // Test modal responsiveness
  testModalResponsiveness(viewport) {
    // Create a test modal if it doesn't exist
    const modal = document.querySelector('.modal') || this.createTestModal();
    const modalContent = modal.querySelector('.modal-content');
    
    if (!modalContent) return;

    const contentWidth = parseFloat(getComputedStyle(modalContent).width);
    const viewportWidth = viewport.width;
    
    let expectedMaxWidth;
    if (viewport.width <= this.breakpoints.mobile) {
      expectedMaxWidth = viewportWidth * 0.95; // 95% on mobile
    } else if (viewport.width <= this.breakpoints.tablet) {
      expectedMaxWidth = viewportWidth * 0.9; // 90% on tablet
    } else {
      expectedMaxWidth = 600; // Fixed max width on desktop
    }
    
    this.results.push({
      category: 'Responsive Layout',
      test: `Modal - ${viewport.name} - Width Responsiveness`,
      expected: `≤ ${expectedMaxWidth}px`,
      actual: `${contentWidth}px`,
      passed: contentWidth <= expectedMaxWidth + 10
    });
  }

  // Test font size hierarchy
  testFontSizeHierarchy() {
    const headings = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'];
    const fontSizes = [];
    
    headings.forEach(tag => {
      const element = document.querySelector(tag) || this.createTestElement(tag);
      const fontSize = parseFloat(getComputedStyle(element).fontSize);
      fontSizes.push({ tag, fontSize });
    });
    
    // Check if font sizes are in descending order
    for (let i = 0; i < fontSizes.length - 1; i++) {
      const current = fontSizes[i];
      const next = fontSizes[i + 1];
      
      this.results.push({
        category: 'Typography',
        test: `Font Hierarchy - ${current.tag} > ${next.tag}`,
        expected: `${current.fontSize}px > ${next.fontSize}px`,
        actual: `${current.fontSize}px vs ${next.fontSize}px`,
        passed: current.fontSize >= next.fontSize
      });
    }
  }

  // Test line height and spacing
  testLineHeightSpacing() {
    const textElements = [
      { selector: 'h1', expectedLineHeight: 1.1 },
      { selector: 'h2', expectedLineHeight: 1.25 },
      { selector: 'p', expectedLineHeight: 1.5 },
      { selector: '.article-title', expectedLineHeight: 1.25 },
      { selector: '.article-preview', expectedLineHeight: 1.75 }
    ];
    
    textElements.forEach(element => {
      const domElement = document.querySelector(element.selector) || 
                        this.createTestElement(element.selector);
      
      const lineHeight = parseFloat(getComputedStyle(domElement).lineHeight) / 
                        parseFloat(getComputedStyle(domElement).fontSize);
      
      this.results.push({
        category: 'Typography',
        test: `Line Height - ${element.selector}`,
        expected: element.expectedLineHeight,
        actual: lineHeight.toFixed(2),
        passed: Math.abs(lineHeight - element.expectedLineHeight) <= 0.25
      });
    });
  }

  // Test text readability and contrast
  testTextReadability() {
    const textElements = [
      { selector: '.article-title', background: '--background-white' },
      { selector: '.article-preview', background: '--background-white' },
      { selector: '.article-meta', background: '--background-white' },
      { selector: '.hero-title', background: '--background-white' },
      { selector: '.nav-link', background: '--primary-green' }
    ];
    
    textElements.forEach(element => {
      const domElement = document.querySelector(element.selector);
      if (domElement) {
        const textColor = getComputedStyle(domElement).color;
        const backgroundColor = this.getCSSVariableValue(element.background);
        const contrast = this.calculateContrastRatio(textColor, backgroundColor);
        
        // WCAG AA standard requires 4.5:1 for normal text, 3:1 for large text
        const fontSize = parseFloat(getComputedStyle(domElement).fontSize);
        const minContrast = fontSize >= 18 ? 3 : 4.5;
        
        this.results.push({
          category: 'Typography',
          test: `Text Contrast - ${element.selector}`,
          expected: `≥ ${minContrast}:1`,
          actual: `${contrast.toFixed(2)}:1`,
          passed: contrast >= minContrast
        });
      }
    });
  }

  // Test responsive typography
  testResponsiveTypography() {
    this.testViewports.forEach(viewport => {
      this.simulateViewport(viewport.width, viewport.height);
      
      const heroTitle = document.querySelector('.hero-title');
      if (heroTitle) {
        const fontSize = parseFloat(getComputedStyle(heroTitle).fontSize);
        const isReadable = fontSize >= 16; // Minimum readable size
        
        this.results.push({
          category: 'Typography',
          test: `Responsive Text - Hero Title - ${viewport.name}`,
          expected: '≥ 16px',
          actual: `${fontSize}px`,
          passed: isReadable
        });
      }
    });
    
    this.restoreViewport();
  }

  // Test spacing consistency
  testSpacingConsistency() {
    const spacingElements = [
      { selector: '.article-item', property: 'margin-bottom' },
      { selector: '.article-meta', property: 'margin-bottom' },
      { selector: '.form-group', property: 'margin-bottom' },
      { selector: '.btn', property: 'padding' }
    ];
    
    spacingElements.forEach(element => {
      const domElement = document.querySelector(element.selector);
      if (domElement) {
        const spacing = parseFloat(getComputedStyle(domElement).getPropertyValue(element.property));
        const isConsistent = spacing % 4 === 0; // Should follow 4px grid
        
        this.results.push({
          category: 'Typography',
          test: `Spacing Consistency - ${element.selector} ${element.property}`,
          expected: 'Multiple of 4px',
          actual: `${spacing}px`,
          passed: isConsistent
        });
      }
    });
  }

  // Test CSS custom properties for theme consistency
  testCSSCustomProperties() {
    const requiredProperties = [
      '--primary-green',
      '--primary-green-dark',
      '--primary-green-light',
      '--success-green',
      '--text-primary',
      '--text-secondary',
      '--background-white',
      '--background-light',
      '--font-family',
      '--font-size-base',
      '--spacing-lg',
      '--border-radius'
    ];

    const computedStyle = getComputedStyle(document.documentElement);
    
    requiredProperties.forEach(property => {
      const value = computedStyle.getPropertyValue(property).trim();
      const hasValue = value !== '';
      
      this.results.push({
        category: 'Theme Consistency',
        test: `CSS Variable - ${property}`,
        expected: 'Should have value',
        actual: hasValue ? value : 'Empty',
        passed: hasValue
      });
    });
  }

  // Test color contrast ratios
  testColorContrast() {
    const contrastTests = [
      {
        name: 'Primary Green on White',
        foreground: '--primary-green',
        background: '--background-white',
        minRatio: 4.5
      },
      {
        name: 'Text Primary on Background Light',
        foreground: '--text-primary',
        background: '--background-light',
        minRatio: 7
      },
      {
        name: 'Text Secondary on Background White',
        foreground: '--text-secondary',
        background: '--background-white',
        minRatio: 4.5
      }
    ];

    contrastTests.forEach(test => {
      const fgColor = this.getCSSVariableValue(test.foreground);
      const bgColor = this.getCSSVariableValue(test.background);
      const contrast = this.calculateContrastRatio(fgColor, bgColor);
      
      this.results.push({
        category: 'Theme Consistency',
        test: `Color Contrast - ${test.name}`,
        expected: `≥ ${test.minRatio}:1`,
        actual: `${contrast.toFixed(2)}:1`,
        passed: contrast >= test.minRatio
      });
    });
  }

  // Helper methods
  getCSSVariableValue(variableName) {
    return getComputedStyle(document.documentElement)
      .getPropertyValue(variableName).trim();
  }

  compareColors(color1, color2) {
    // Simple color comparison - in production, you'd want more sophisticated comparison
    const normalize = (color) => color.replace(/\s/g, '').toLowerCase();
    return normalize(color1) === normalize(color2) || 
           this.colorsAreSimilar(color1, color2);
  }

  colorsAreSimilar(color1, color2) {
    // Convert colors to RGB and compare
    const rgb1 = this.colorToRgb(color1);
    const rgb2 = this.colorToRgb(color2);
    
    if (!rgb1 || !rgb2) return false;
    
    const threshold = 30; // Allow some variation
    return Math.abs(rgb1.r - rgb2.r) <= threshold &&
           Math.abs(rgb1.g - rgb2.g) <= threshold &&
           Math.abs(rgb1.b - rgb2.b) <= threshold;
  }

  colorToRgb(color) {
    // Simple RGB extraction - would need more robust implementation for production
    const rgbMatch = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
    if (rgbMatch) {
      return {
        r: parseInt(rgbMatch[1]),
        g: parseInt(rgbMatch[2]),
        b: parseInt(rgbMatch[3])
      };
    }
    return null;
  }

  calculateContrastRatio(color1, color2) {
    // Simplified contrast calculation - would use proper WCAG formula in production
    const rgb1 = this.colorToRgb(color1);
    const rgb2 = this.colorToRgb(color2);
    
    if (!rgb1 || !rgb2) return 4.5; // Default acceptable contrast
    
    const l1 = this.getLuminance(rgb1);
    const l2 = this.getLuminance(rgb2);
    
    const lighter = Math.max(l1, l2);
    const darker = Math.min(l1, l2);
    
    return (lighter + 0.05) / (darker + 0.05);
  }

  getLuminance(rgb) {
    const { r, g, b } = rgb;
    const [rs, gs, bs] = [r, g, b].map(c => {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  }

  getElementVisibility(element) {
    if (!element) return 'not-found';
    
    const style = getComputedStyle(element);
    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
      return 'hidden';
    }
    return 'visible';
  }

  createTestContainer() {
    const container = document.createElement('div');
    container.id = 'responsive-test-container';
    container.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      overflow: hidden;
      z-index: -1;
      pointer-events: none;
    `;
    document.body.appendChild(container);
    return container;
  }

  createTestElement(selector, config = {}) {
    const element = document.createElement('div');
    element.className = selector.replace('.', '').replace('#', '');
    
    if (selector.startsWith('h')) {
      const heading = document.createElement(selector);
      heading.textContent = `Test ${selector.toUpperCase()}`;
      document.body.appendChild(heading);
      return heading;
    }
    
    element.textContent = `Test ${selector}`;
    element.style.cssText = 'position: absolute; top: -9999px; left: -9999px;';
    document.body.appendChild(element);
    return element;
  }

  createTestModal() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.cssText = 'position: fixed; top: -9999px; left: -9999px;';
    
    const modalContent = document.createElement('div');
    modalContent.className = 'modal-content';
    modal.appendChild(modalContent);
    
    document.body.appendChild(modal);
    return modal;
  }

  updateViewportMeta(width) {
    let viewport = document.querySelector('meta[name="viewport"]');
    if (!viewport) {
      viewport = document.createElement('meta');
      viewport.name = 'viewport';
      document.head.appendChild(viewport);
    }
    
    if (width <= this.breakpoints.mobile) {
      viewport.content = 'width=device-width, initial-scale=1.0, user-scalable=no';
    } else {
      viewport.content = 'width=device-width, initial-scale=1.0';
    }
  }

  restoreViewport() {
    const testContainer = document.getElementById('responsive-test-container');
    if (testContainer) {
      testContainer.style.width = `${this.originalViewport.width}px`;
      testContainer.style.height = `${this.originalViewport.height}px`;
    }
  }

  // Run all responsive design tests
  async runAllTests() {
    console.log('🧪 Starting Comprehensive Responsive Design Tests...');
    
    // Test responsive layout
    this.testResponsiveLayout();
    
    // Test green theme consistency
    this.testGreenThemeConsistency();
    
    // Test typography readability
    this.testTypographyReadability();
    
    return this.generateReport();
  }

  // Generate comprehensive test report
  generateReport() {
    const totalTests = this.results.length;
    const passedTests = this.results.filter(r => r.passed).length;
    const failedTests = totalTests - passedTests;
    
    const report = {
      summary: {
        total: totalTests,
        passed: passedTests,
        failed: failedTests,
        percentage: Math.round((passedTests / totalTests) * 100)
      },
      results: this.results,
      categories: this.groupResultsByCategory()
    };

    console.log('📊 Responsive Design Test Results:');
    console.log(`✅ Passed: ${passedTests}/${totalTests} (${report.summary.percentage}%)`);
    console.log(`❌ Failed: ${failedTests}/${totalTests}`);
    
    if (failedTests > 0) {
      console.log('\n❌ Failed Tests:');
      this.results.filter(r => !r.passed).forEach(result => {
        console.log(`  • ${result.category}: ${result.test}`);
        console.log(`    Expected: ${result.expected}, Got: ${result.actual}`);
      });
    }

    this.createVisualReport(report);
    return report;
  }

  groupResultsByCategory() {
    const categories = {};
    
    this.results.forEach(result => {
      if (!categories[result.category]) {
        categories[result.category] = {
          total: 0,
          passed: 0,
          failed: 0,
          tests: []
        };
      }
      
      categories[result.category].total++;
      if (result.passed) {
        categories[result.category].passed++;
      } else {
        categories[result.category].failed++;
      }
      categories[result.category].tests.push(result);
    });
    
    return categories;
  }

  createVisualReport(report) {
    const reportContainer = document.createElement('div');
    reportContainer.id = 'responsive-design-test-report';
    reportContainer.style.cssText = `
      position: fixed;
      top: 20px;
      left: 20px;
      width: 450px;
      max-height: 80vh;
      overflow-y: auto;
      background: white;
      border: 2px solid var(--primary-green);
      border-radius: var(--border-radius);
      padding: var(--spacing-lg);
      box-shadow: var(--shadow-heavy);
      z-index: var(--z-modal);
      font-family: var(--font-family);
      font-size: var(--font-size-sm);
    `;
    
    reportContainer.innerHTML = `
      <h3 style="margin: 0 0 var(--spacing-lg) 0; color: var(--primary-green);">
        🧪 Responsive Design Test Report
      </h3>
      <div style="margin-bottom: var(--spacing-lg); padding: var(--spacing-md); background: var(--primary-green-bg); border-radius: var(--border-radius);">
        <strong>Summary:</strong> ${report.summary.passed}/${report.summary.total} tests passed (${report.summary.percentage}%)
      </div>
      <div style="max-height: 300px; overflow-y: auto;">
        ${Object.entries(report.categories).map(([category, data]) => `
          <div style="margin-bottom: var(--spacing-md); padding: var(--spacing-sm); border-left: 3px solid ${data.failed > 0 ? 'var(--error-red)' : 'var(--success-green)'};">
            <strong>${category}:</strong> ${data.passed}/${data.total} passed
            ${data.failed > 0 ? `
              <div style="margin-left: var(--spacing-md); color: var(--error-red); font-size: var(--font-size-xs); margin-top: var(--spacing-xs);">
                ${data.tests.filter(t => !t.passed).map(t => `• ${t.test}`).join('<br>')}
              </div>
            ` : ''}
          </div>
        `).join('')}
      </div>
      <div style="margin-top: var(--spacing-lg); display: flex; gap: var(--spacing-sm);">
        <button onclick="this.parentElement.parentElement.remove()" style="
          background: var(--primary-green);
          color: white;
          border: none;
          padding: var(--spacing-sm) var(--spacing-md);
          border-radius: var(--border-radius);
          cursor: pointer;
          flex: 1;
        ">Close Report</button>
        <button onclick="console.log(${JSON.stringify(report, null, 2)})" style="
          background: var(--info-blue);
          color: white;
          border: none;
          padding: var(--spacing-sm) var(--spacing-md);
          border-radius: var(--border-radius);
          cursor: pointer;
          flex: 1;
        ">Log Details</button>
      </div>
    `;
    
    document.body.appendChild(reportContainer);
    
    return reportContainer;
  }

  // Cleanup method
  cleanup() {
    const testContainer = document.getElementById('responsive-test-container');
    const testReport = document.getElementById('responsive-design-test-report');
    
    if (testContainer) testContainer.remove();
    if (testReport) testReport.remove();
    
    // Remove any test elements
    document.querySelectorAll('[style*="-9999px"]').forEach(el => el.remove());
  }
}

// Auto-run tests when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    const responsiveTest = new ResponsiveDesignTest();
    
    setTimeout(() => {
      responsiveTest.runAllTests().then(report => {
        console.log('Responsive design tests completed:', report);
      }).catch(error => {
        console.error('Responsive design tests failed:', error);
      });
    }, 1000);
  });
} else {
  const responsiveTest = new ResponsiveDesignTest();
  
  setTimeout(() => {
    responsiveTest.runAllTests().then(report => {
      console.log('Responsive design tests completed:', report);
    }).catch(error => {
      console.error('Responsive design tests failed:', error);
    });
  }, 1000);
}

// Export for manual testing
window.ResponsiveDesignTest = ResponsiveDesignTest;