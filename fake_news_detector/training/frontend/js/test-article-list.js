/**
 * Article List Component Test Suite
 * Tests for list layout, responsiveness, and interactive states
 */

class ArticleListTest {
  constructor() {
    this.results = [];
    this.testContainer = null;
    this.articleList = null;
    this.mockArticles = this.generateMockArticles();
  }

  // Generate mock articles for testing
  generateMockArticles() {
    return [
      {
        _id: 'test1',
        title: 'Sample Real News Article for Testing Layout and Typography',
        text: 'This is a sample article text that should be long enough to test the preview truncation functionality. It contains multiple sentences to ensure proper testing of the text clipping and ellipsis display.',
        username: 'TestAuthor1',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
        prediction: 'REAL',
        confidence: 0.95,
        source: 'Test News Source',
        likes: 42
      },
      {
        _id: 'test2',
        title: 'Sample Fake News Article',
        text: 'This is another sample article with fake news prediction to test different styling states.',
        username: 'TestAuthor2',
        timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
        prediction: 'FAKE',
        confidence: 0.87,
        source: 'Another Test Source',
        likes: 15
      },
      {
        _id: 'test3',
        title: 'Low Confidence Article',
        text: 'This article has low confidence to test warning states.',
        username: 'TestAuthor3',
        timestamp: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 1 week ago
        prediction: 'REAL',
        confidence: 0.55,
        source: 'Test Source 3',
        likes: 8
      }
    ];
  }

  // Setup test environment
  setupTestEnvironment() {
    // Create test container
    this.testContainer = document.createElement('div');
    this.testContainer.id = 'test-article-list';
    this.testContainer.style.cssText = `
      position: fixed;
      top: 50px;
      right: 20px;
      width: 400px;
      max-height: 70vh;
      overflow-y: auto;
      background: white;
      border: 2px solid var(--primary-green);
      border-radius: var(--border-radius);
      padding: var(--spacing-lg);
      box-shadow: var(--shadow-heavy);
      z-index: var(--z-modal);
      font-family: var(--font-family);
    `;
    
    document.body.appendChild(this.testContainer);
    
    // Create article list instance
    this.articleList = new ArticleList('test-article-list');
    
    return this.testContainer;
  }

  // Test article rendering
  testArticleRendering() {
    const testName = 'Article Rendering';
    
    try {
      // Add mock articles
      this.mockArticles.forEach(article => {
        this.articleList.addArticle(article);
      });
      
      // Check if articles are rendered
      const renderedArticles = this.testContainer.querySelectorAll('.article-item');
      const expectedCount = this.mockArticles.length;
      
      this.results.push({
        category: 'Rendering',
        test: `${testName} - Article Count`,
        expected: expectedCount,
        actual: renderedArticles.length,
        passed: renderedArticles.length === expectedCount
      });
      
      // Test article structure
      renderedArticles.forEach((articleElement, index) => {
        const article = this.mockArticles[index];
        
        // Test title rendering
        const titleElement = articleElement.querySelector('.article-title');
        const titleMatch = titleElement && titleElement.textContent.includes(article.title);
        
        this.results.push({
          category: 'Rendering',
          test: `${testName} - Title ${index + 1}`,
          expected: article.title,
          actual: titleElement ? titleElement.textContent : 'Not found',
          passed: titleMatch
        });
        
        // Test prediction badge
        const predictionElement = articleElement.querySelector('.article-prediction');
        const predictionClass = article.prediction === 'REAL' ? 'real' : 'fake';
        const predictionMatch = predictionElement && predictionElement.classList.contains(predictionClass);
        
        this.results.push({
          category: 'Rendering',
          test: `${testName} - Prediction ${index + 1}`,
          expected: predictionClass,
          actual: predictionElement ? predictionElement.className : 'Not found',
          passed: predictionMatch
        });
        
        // Test metadata rendering
        const metaElements = articleElement.querySelectorAll('.article-meta-item');
        const hasMetadata = metaElements.length >= 3; // author, timestamp, source, reading-time
        
        this.results.push({
          category: 'Rendering',
          test: `${testName} - Metadata ${index + 1}`,
          expected: 'At least 3 meta items',
          actual: `${metaElements.length} meta items`,
          passed: hasMetadata
        });
      });
      
    } catch (error) {
      this.results.push({
        category: 'Rendering',
        test: testName,
        expected: 'No errors',
        actual: error.message,
        passed: false
      });
    }
  }

  // Test responsive layout
  testResponsiveLayout() {
    const testName = 'Responsive Layout';
    
    try {
      const originalWidth = window.innerWidth;
      
      // Test desktop layout
      const desktopArticle = this.testContainer.querySelector('.article-item');
      if (desktopArticle) {
        const layout = desktopArticle.querySelector('.article-layout');
        const sidebar = desktopArticle.querySelector('.article-sidebar');
        
        this.results.push({
          category: 'Responsive',
          test: `${testName} - Desktop Layout`,
          expected: 'Flex layout with sidebar',
          actual: layout ? 'Layout found' : 'Layout not found',
          passed: !!(layout && sidebar)
        });
      }
      
      // Test mobile breakpoint simulation
      const mobileQuery = window.matchMedia('(max-width: 768px)');
      
      this.results.push({
        category: 'Responsive',
        test: `${testName} - Mobile Media Query`,
        expected: 'Media query exists',
        actual: mobileQuery ? 'Found' : 'Not found',
        passed: !!mobileQuery
      });
      
    } catch (error) {
      this.results.push({
        category: 'Responsive',
        test: testName,
        expected: 'No errors',
        actual: error.message,
        passed: false
      });
    }
  }

  // Test interactive states
  testInteractiveStates() {
    const testName = 'Interactive States';
    
    try {
      const firstArticle = this.testContainer.querySelector('.article-item');
      
      if (firstArticle) {
        // Test hover state
        const hoverEvent = new MouseEvent('mouseenter', { bubbles: true });
        firstArticle.dispatchEvent(hoverEvent);
        
        // Check if hover classes or styles are applied
        const computedStyle = getComputedStyle(firstArticle);
        const hasHoverEffect = computedStyle.transform !== 'none' || 
                              computedStyle.boxShadow !== 'none';
        
        this.results.push({
          category: 'Interaction',
          test: `${testName} - Hover Effect`,
          expected: 'Transform or shadow change',
          actual: hasHoverEffect ? 'Effect applied' : 'No effect',
          passed: hasHoverEffect
        });
        
        // Test click handler
        let clickHandled = false;
        const originalOpenModal = this.articleList.openArticleModal;
        this.articleList.openArticleModal = () => { clickHandled = true; };
        
        const clickEvent = new MouseEvent('click', { bubbles: true });
        firstArticle.dispatchEvent(clickEvent);
        
        this.results.push({
          category: 'Interaction',
          test: `${testName} - Click Handler`,
          expected: 'Modal should open',
          actual: clickHandled ? 'Handler called' : 'Handler not called',
          passed: clickHandled
        });
        
        // Restore original function
        this.articleList.openArticleModal = originalOpenModal;
        
        // Test engagement buttons
        const likeBtn = firstArticle.querySelector('.like-btn');
        if (likeBtn) {
          const likeEvent = new MouseEvent('click', { bubbles: true });
          likeBtn.dispatchEvent(likeEvent);
          
          const isActive = likeBtn.classList.contains('active');
          
          this.results.push({
            category: 'Interaction',
            test: `${testName} - Like Button`,
            expected: 'Button should toggle active state',
            actual: isActive ? 'Active state applied' : 'No state change',
            passed: isActive
          });
        }
      }
      
    } catch (error) {
      this.results.push({
        category: 'Interaction',
        test: testName,
        expected: 'No errors',
        actual: error.message,
        passed: false
      });
    }
  }

  // Test article metadata formatting
  testMetadataFormatting() {
    const testName = 'Metadata Formatting';
    
    try {
      const articles = this.testContainer.querySelectorAll('.article-item');
      
      articles.forEach((articleElement, index) => {
        const article = this.mockArticles[index];
        
        // Test timestamp formatting
        const timestampElement = articleElement.querySelector('.timestamp');
        const hasTimestamp = timestampElement && timestampElement.textContent.trim() !== '';
        
        this.results.push({
          category: 'Metadata',
          test: `${testName} - Timestamp ${index + 1}`,
          expected: 'Formatted timestamp',
          actual: timestampElement ? timestampElement.textContent : 'Not found',
          passed: hasTimestamp
        });
        
        // Test confidence display
        const confidenceElement = articleElement.querySelector('.confidence-badge');
        const expectedConfidence = Math.round(article.confidence * 100) + '%';
        const confidenceMatch = confidenceElement && 
                               confidenceElement.textContent.includes(expectedConfidence);
        
        this.results.push({
          category: 'Metadata',
          test: `${testName} - Confidence ${index + 1}`,
          expected: expectedConfidence,
          actual: confidenceElement ? confidenceElement.textContent : 'Not found',
          passed: confidenceMatch
        });
        
        // Test reading time calculation
        const readingTimeElement = articleElement.querySelector('.reading-time');
        const hasReadingTime = readingTimeElement && 
                              readingTimeElement.textContent.includes('min read');
        
        this.results.push({
          category: 'Metadata',
          test: `${testName} - Reading Time ${index + 1}`,
          expected: 'X min read format',
          actual: readingTimeElement ? readingTimeElement.textContent : 'Not found',
          passed: hasReadingTime
        });
      });
      
    } catch (error) {
      this.results.push({
        category: 'Metadata',
        test: testName,
        expected: 'No errors',
        actual: error.message,
        passed: false
      });
    }
  }

  // Test article tags generation
  testArticleTags() {
    const testName = 'Article Tags';
    
    try {
      const articles = this.testContainer.querySelectorAll('.article-item');
      
      articles.forEach((articleElement, index) => {
        const article = this.mockArticles[index];
        
        // Test tag container
        const tagsContainer = articleElement.querySelector('.article-tags');
        const hasTags = tagsContainer && tagsContainer.children.length > 0;
        
        this.results.push({
          category: 'Tags',
          test: `${testName} - Tags Container ${index + 1}`,
          expected: 'Tags should be present',
          actual: hasTags ? `${tagsContainer.children.length} tags` : 'No tags',
          passed: hasTags
        });
        
        // Test prediction-based tags
        const predictionTag = tagsContainer ? 
          tagsContainer.querySelector('.tag-verified, .tag-flagged') : null;
        const expectedTagClass = article.prediction === 'REAL' ? 'tag-verified' : 'tag-flagged';
        const hasCorrectPredictionTag = predictionTag && 
                                       predictionTag.classList.contains(expectedTagClass);
        
        this.results.push({
          category: 'Tags',
          test: `${testName} - Prediction Tag ${index + 1}`,
          expected: expectedTagClass,
          actual: predictionTag ? predictionTag.className : 'Not found',
          passed: hasCorrectPredictionTag
        });
        
        // Test confidence-based tags
        if (article.confidence > 0.9) {
          const confidenceTag = tagsContainer ? 
            tagsContainer.querySelector('.tag-confidence') : null;
          
          this.results.push({
            category: 'Tags',
            test: `${testName} - High Confidence Tag ${index + 1}`,
            expected: 'High confidence tag',
            actual: confidenceTag ? 'Found' : 'Not found',
            passed: !!confidenceTag
          });
        }
      });
      
    } catch (error) {
      this.results.push({
        category: 'Tags',
        test: testName,
        expected: 'No errors',
        actual: error.message,
        passed: false
      });
    }
  }

  // Test accessibility features
  testAccessibility() {
    const testName = 'Accessibility';
    
    try {
      const articles = this.testContainer.querySelectorAll('.article-item');
      
      // Test keyboard navigation
      const firstArticle = articles[0];
      if (firstArticle) {
        firstArticle.setAttribute('tabindex', '0');
        firstArticle.focus();
        
        const isFocusable = document.activeElement === firstArticle;
        
        this.results.push({
          category: 'Accessibility',
          test: `${testName} - Keyboard Focus`,
          expected: 'Article should be focusable',
          actual: isFocusable ? 'Focusable' : 'Not focusable',
          passed: isFocusable
        });
      }
      
      // Test ARIA labels
      const buttons = this.testContainer.querySelectorAll('button[title]');
      const hasAriaLabels = buttons.length > 0;
      
      this.results.push({
        category: 'Accessibility',
        test: `${testName} - ARIA Labels`,
        expected: 'Buttons should have titles',
        actual: `${buttons.length} buttons with titles`,
        passed: hasAriaLabels
      });
      
      // Test semantic structure
      const headings = this.testContainer.querySelectorAll('h1, h2, h3, h4, h5, h6');
      const hasSemanticHeadings = headings.length > 0;
      
      this.results.push({
        category: 'Accessibility',
        test: `${testName} - Semantic Headings`,
        expected: 'Proper heading structure',
        actual: `${headings.length} headings found`,
        passed: hasSemanticHeadings
      });
      
    } catch (error) {
      this.results.push({
        category: 'Accessibility',
        test: testName,
        expected: 'No errors',
        actual: error.message,
        passed: false
      });
    }
  }

  // Test performance aspects
  testPerformance() {
    const testName = 'Performance';
    
    try {
      const startTime = performance.now();
      
      // Test rendering performance with multiple articles
      const manyArticles = Array.from({ length: 20 }, (_, i) => ({
        ...this.mockArticles[0],
        _id: `perf-test-${i}`,
        title: `Performance Test Article ${i + 1}`
      }));
      
      manyArticles.forEach(article => {
        this.articleList.addArticle(article);
      });
      
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      const isPerformant = renderTime < 100; // Should render in under 100ms
      
      this.results.push({
        category: 'Performance',
        test: `${testName} - Render Time`,
        expected: '< 100ms',
        actual: `${renderTime.toFixed(2)}ms`,
        passed: isPerformant
      });
      
      // Test memory usage (simplified)
      const articleElements = this.testContainer.querySelectorAll('.article-item');
      const memoryEfficient = articleElements.length <= 25; // Should not create too many DOM elements
      
      this.results.push({
        category: 'Performance',
        test: `${testName} - DOM Elements`,
        expected: '≤ 25 elements',
        actual: `${articleElements.length} elements`,
        passed: memoryEfficient
      });
      
    } catch (error) {
      this.results.push({
        category: 'Performance',
        test: testName,
        expected: 'No errors',
        actual: error.message,
        passed: false
      });
    }
  }

  // Run all tests
  async runAllTests() {
    console.log('🧪 Starting Article List Component Tests...');
    
    // Setup test environment
    this.setupTestEnvironment();
    
    // Wait for component to initialize
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Run test suites
    this.testArticleRendering();
    this.testResponsiveLayout();
    this.testInteractiveStates();
    this.testMetadataFormatting();
    this.testArticleTags();
    this.testAccessibility();
    this.testPerformance();
    
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

    console.log('📊 Article List Test Results:');
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

  // Create visual test report
  createVisualReport(report) {
    const reportHeader = document.createElement('div');
    reportHeader.innerHTML = `
      <h3 style="margin: 0 0 var(--spacing-lg) 0; color: var(--primary-green);">
        🧪 Article List Test Report
      </h3>
      <div style="margin-bottom: var(--spacing-lg); padding: var(--spacing-md); background: var(--primary-green-bg); border-radius: var(--border-radius);">
        <strong>Summary:</strong> ${report.summary.passed}/${report.summary.total} tests passed (${report.summary.percentage}%)
      </div>
      <div style="max-height: 200px; overflow-y: auto; margin-bottom: var(--spacing-lg);">
        ${Object.entries(report.categories).map(([category, data]) => `
          <div style="margin-bottom: var(--spacing-sm); padding: var(--spacing-sm); border-left: 3px solid ${data.failed > 0 ? 'var(--error-red)' : 'var(--success-green)'};">
            <strong>${category}:</strong> ${data.passed}/${data.total} passed
            ${data.failed > 0 ? `
              <div style="margin-left: var(--spacing-md); color: var(--error-red); font-size: var(--font-size-xs);">
                ${data.tests.filter(t => !t.passed).map(t => `• ${t.test}`).join('<br>')}
              </div>
            ` : ''}
          </div>
        `).join('')}
      </div>
      <button onclick="this.parentElement.parentElement.remove()" style="
        background: var(--primary-green);
        color: white;
        border: none;
        padding: var(--spacing-sm) var(--spacing-md);
        border-radius: var(--border-radius);
        cursor: pointer;
        margin-right: var(--spacing-sm);
      ">Close Report</button>
      <button onclick="console.log(${JSON.stringify(report)})" style="
        background: var(--info-blue);
        color: white;
        border: none;
        padding: var(--spacing-sm) var(--spacing-md);
        border-radius: var(--border-radius);
        cursor: pointer;
      ">Log Details</button>
    `;
    
    this.testContainer.insertBefore(reportHeader, this.testContainer.firstChild);
  }

  // Cleanup test environment
  cleanup() {
    if (this.testContainer && this.testContainer.parentNode) {
      this.testContainer.parentNode.removeChild(this.testContainer);
    }
  }
}

// Auto-run tests when ArticleList is available
if (typeof ArticleList !== 'undefined') {
  const articleListTest = new ArticleListTest();
  
  // Run tests after a short delay to ensure DOM is ready
  setTimeout(() => {
    articleListTest.runAllTests().then(report => {
      console.log('Article List tests completed:', report);
    }).catch(error => {
      console.error('Article List tests failed:', error);
    });
  }, 1000);
} else {
  console.warn('ArticleList class not found. Tests will not run automatically.');
}

// Export for manual testing
window.ArticleListTest = ArticleListTest;