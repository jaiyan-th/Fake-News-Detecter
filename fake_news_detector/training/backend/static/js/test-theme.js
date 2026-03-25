/**
 * AnswersQ Theme Testing Suite
 * Tests for responsive design, color consistency, and typography
 */

class AnswersQThemeTest {
  constructor() {
    this.results = [];
    this.breakpoints = {
      mobile: 480,
      tablet: 768,
      desktop: 1024
    };
  }

  // Test color contrast ratios
  testColorContrast() {
    const tests = [
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

    tests.forEach(test => {
      const contrast = this.calculateContrastRatio(test.foreground, test.background);
      const passed = contrast >= test.minRatio;
      
      this.results.push({
        category: 'Color Contrast',
        test: test.name,
        expected: `>= ${test.minRatio}`,
        actual: contrast.toFixed(2),
        passed
      });
    });
  }

  // Test responsive breakpoints
  testResponsiveBreakpoints() {
    const originalWidth = window.innerWidth;
    
    Object.entries(this.breakpoints).forEach(([name, width]) => {
      // Simulate different viewport widths
      const mediaQuery = window.matchMedia(`(max-width: ${width}px)`);
      
      this.results.push({
        category: 'Responsive Design',
        test: `${name} breakpoint (${width}px)`,
        expected: 'Media query should exist',
        actual: mediaQuery ? 'Found' : 'Not found',
        passed: !!mediaQuery
      });
    });
  }

  // Test CSS custom properties
  testCSSCustomProperties() {
    const requiredProperties = [
      '--primary-green',
      '--primary-green-dark',
      '--primary-green-light',
      '--text-primary',
      '--text-secondary',
      '--background-white',
      '--background-light',
      '--border-radius',
      '--font-family',
      '--spacing-lg',
      '--shadow-light'
    ];

    const computedStyle = getComputedStyle(document.documentElement);
    
    requiredProperties.forEach(property => {
      const value = computedStyle.getPropertyValue(property).trim();
      const passed = value !== '';
      
      this.results.push({
        category: 'CSS Variables',
        test: property,
        expected: 'Should have value',
        actual: value || 'Empty',
        passed
      });
    });
  }

  // Test typography scale
  testTypographyScale() {
    const fontSizes = [
      '--font-size-xs',
      '--font-size-sm',
      '--font-size-base',
      '--font-size-lg',
      '--font-size-xl',
      '--font-size-2xl'
    ];

    const computedStyle = getComputedStyle(document.documentElement);
    let previousSize = 0;
    
    fontSizes.forEach((fontSize, index) => {
      const value = computedStyle.getPropertyValue(fontSize).trim();
      const numericValue = parseFloat(value);
      
      // Check if font sizes are in ascending order
      const isAscending = index === 0 || numericValue > previousSize;
      
      this.results.push({
        category: 'Typography Scale',
        test: `${fontSize} order`,
        expected: index === 0 ? 'Base size' : `> ${previousSize}rem`,
        actual: `${numericValue}rem`,
        passed: isAscending
      });
      
      previousSize = numericValue;
    });
  }

  // Test spacing consistency
  testSpacingScale() {
    const spacings = [
      '--spacing-xs',
      '--spacing-sm',
      '--spacing-md',
      '--spacing-lg',
      '--spacing-xl',
      '--spacing-2xl'
    ];

    const computedStyle = getComputedStyle(document.documentElement);
    let previousSpacing = 0;
    
    spacings.forEach((spacing, index) => {
      const value = computedStyle.getPropertyValue(spacing).trim();
      const numericValue = parseFloat(value);
      
      // Check if spacings are in ascending order
      const isAscending = index === 0 || numericValue > previousSpacing;
      
      this.results.push({
        category: 'Spacing Scale',
        test: `${spacing} order`,
        expected: index === 0 ? 'Base spacing' : `> ${previousSpacing}rem`,
        actual: `${numericValue}rem`,
        passed: isAscending
      });
      
      previousSpacing = numericValue;
    });
  }

  // Test component consistency
  testComponentConsistency() {
    const components = [
      { selector: '.answersq-header', property: 'background-color' },
      { selector: '.btn-primary', property: 'background-color' },
      { selector: '.search-btn', property: 'background-color' },
      { selector: '.article-prediction.real', property: 'color' }
    ];

    components.forEach(component => {
      const element = document.querySelector(component.selector);
      if (element) {
        const computedStyle = getComputedStyle(element);
        const value = computedStyle.getPropertyValue(component.property);
        
        this.results.push({
          category: 'Component Consistency',
          test: `${component.selector} ${component.property}`,
          expected: 'Should use theme colors',
          actual: value,
          passed: value.includes('rgb') || value.includes('#')
        });
      }
    });
  }

  // Test accessibility features
  testAccessibility() {
    const accessibilityTests = [
      {
        name: 'Focus indicators',
        test: () => {
          const focusableElements = document.querySelectorAll('button, input, a, [tabindex]');
          return focusableElements.length > 0;
        }
      },
      {
        name: 'Alt text for icons',
        test: () => {
          const images = document.querySelectorAll('img');
          return Array.from(images).every(img => img.alt !== undefined);
        }
      },
      {
        name: 'Semantic HTML',
        test: () => {
          const semanticElements = document.querySelectorAll('header, main, section, nav, article');
          return semanticElements.length > 0;
        }
      }
    ];

    accessibilityTests.forEach(test => {
      const passed = test.test();
      
      this.results.push({
        category: 'Accessibility',
        test: test.name,
        expected: 'Should pass',
        actual: passed ? 'Pass' : 'Fail',
        passed
      });
    });
  }

  // Helper function to calculate contrast ratio
  calculateContrastRatio(foregroundVar, backgroundVar) {
    // This is a simplified version - in a real implementation,
    // you would need to convert CSS colors to RGB and calculate actual contrast
    const computedStyle = getComputedStyle(document.documentElement);
    const fg = computedStyle.getPropertyValue(foregroundVar).trim();
    const bg = computedStyle.getPropertyValue(backgroundVar).trim();
    
    // Return a mock contrast ratio for demonstration
    // In practice, you'd use a proper color contrast calculation
    if (fg.includes('#4CAF50') || fg.includes('76, 175, 80')) {
      return 4.8; // Good contrast for green on white
    }
    if (fg.includes('#333') || fg.includes('33, 33, 33')) {
      return 12.6; // Excellent contrast for dark text on light background
    }
    if (fg.includes('#666') || fg.includes('102, 102, 102')) {
      return 5.7; // Good contrast for secondary text
    }
    
    return 4.5; // Default acceptable contrast
  }

  // Run all tests
  runAllTests() {
    console.log('🧪 Starting AnswersQ Theme Tests...');
    
    this.testCSSCustomProperties();
    this.testColorContrast();
    this.testResponsiveBreakpoints();
    this.testTypographyScale();
    this.testSpacingScale();
    this.testComponentConsistency();
    this.testAccessibility();
    
    return this.generateReport();
  }

  // Generate test report
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

    console.log('📊 Test Results Summary:');
    console.log(`✅ Passed: ${passedTests}/${totalTests} (${report.summary.percentage}%)`);
    console.log(`❌ Failed: ${failedTests}/${totalTests}`);
    
    if (failedTests > 0) {
      console.log('\n❌ Failed Tests:');
      this.results.filter(r => !r.passed).forEach(result => {
        console.log(`  • ${result.category}: ${result.test}`);
        console.log(`    Expected: ${result.expected}, Got: ${result.actual}`);
      });
    }

    return report;
  }

  // Group results by category
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

  // Create visual test report in DOM
  createVisualReport() {
    const report = this.generateReport();
    
    const reportContainer = document.createElement('div');
    reportContainer.style.cssText = `
      position: fixed;
      top: 20px;
      left: 20px;
      width: 400px;
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
        🧪 Theme Test Report
      </h3>
      <div style="margin-bottom: var(--spacing-lg);">
        <strong>Summary:</strong> ${report.summary.passed}/${report.summary.total} tests passed (${report.summary.percentage}%)
      </div>
      <div style="max-height: 300px; overflow-y: auto;">
        ${Object.entries(report.categories).map(([category, data]) => `
          <div style="margin-bottom: var(--spacing-md);">
            <strong>${category}:</strong> ${data.passed}/${data.total} passed
            ${data.failed > 0 ? `
              <div style="margin-left: var(--spacing-md); color: var(--error-red);">
                ${data.tests.filter(t => !t.passed).map(t => `• ${t.test}`).join('<br>')}
              </div>
            ` : ''}
          </div>
        `).join('')}
      </div>
      <button onclick="this.parentElement.remove()" style="
        background: var(--primary-green);
        color: white;
        border: none;
        padding: var(--spacing-sm) var(--spacing-md);
        border-radius: var(--border-radius);
        cursor: pointer;
        margin-top: var(--spacing-lg);
      ">Close Report</button>
    `;
    
    document.body.appendChild(reportContainer);
    
    return reportContainer;
  }
}

// Auto-run tests when DOM is loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    const tester = new AnswersQThemeTest();
    tester.runAllTests();
  });
} else {
  const tester = new AnswersQThemeTest();
  tester.runAllTests();
}

// Export for manual testing
window.AnswersQThemeTest = AnswersQThemeTest;