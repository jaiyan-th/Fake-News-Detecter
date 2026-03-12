"""
Generate ASCII art diagram of the system architecture
"""

def print_system_diagram():
    """Print beautiful ASCII diagram of the system"""
    
    diagram = """
╔══════════════════════════════════════════════════════════════════════════╗
║                   FAKE NEWS DETECTION SYSTEM ARCHITECTURE                ║
╚══════════════════════════════════════════════════════════════════════════╝

                    ┌─────────────────────────────┐
                    │   USER INPUT                │
                    │  • News Article Text        │
                    │  • Article URL              │
                    │  • Social Media Post        │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
        ╔══════════════════════════════════════════════════════════╗
        ║  MODULE 1: DATA COLLECTION LAYER                         ║
        ╠══════════════════════════════════════════════════════════╣
        ║  • Web Scraping (BeautifulSoup)                          ║
        ║  • News API Integration                                  ║
        ║  • Social Media APIs                                     ║
        ║  • Manual Text Input Processing                          ║
        ╚═══════════════════════════╦══════════════════════════════╝
                                    │
                                    ▼
        ╔══════════════════════════════════════════════════════════╗
        ║  MODULE 2: DATA PREPROCESSING                            ║
        ╠══════════════════════════════════════════════════════════╣
        ║  Step 1: Text Cleaning                                   ║
        ║    • Remove punctuation, URLs, special chars             ║
        ║    • Convert to lowercase                                ║
        ║  Step 2: Tokenization                                    ║
        ║    • Split text into words                               ║
        ║  Step 3: Stopword Removal                                ║
        ║    • Filter common words (the, a, is, etc.)              ║
        ║  Step 4: Stemming/Lemmatization                          ║
        ║    • Reduce words to root form                           ║
        ╚═══════════════════════════╦══════════════════════════════╝
                                    │
                                    ▼
        ╔══════════════════════════════════════════════════════════╗
        ║  MODULE 3: FEATURE EXTRACTION                            ║
        ╠══════════════════════════════════════════════════════════╣
        ║  1. TF-IDF Features                                      ║
        ║     • Term Frequency-Inverse Document Frequency          ║
        ║     • Main input for ML model                            ║
        ║  2. Sentiment Features                                   ║
        ║     • Positive/negative word ratios                      ║
        ║     • Sensational language detection                     ║
        ║     • Emotional intensity                                ║
        ║  3. Linguistic Features                                  ║
        ║     • Text length, punctuation patterns                  ║
        ║     • Capitalization, vocabulary richness                ║
        ╚═══════════════════════════╦══════════════════════════════╝
                                    │
                                    ▼
        ╔══════════════════════════════════════════════════════════╗
        ║  MODULE 4: MACHINE LEARNING MODEL                        ║
        ╠══════════════════════════════════════════════════════════╣
        ║  Supported Models:                                       ║
        ║    • Logistic Regression                                 ║
        ║    • Random Forest                                       ║
        ║    • Support Vector Machine (SVM)                        ║
        ║    • Passive Aggressive Classifier                       ║
        ║    • LSTM / BERT (Deep Learning)                         ║
        ║                                                           ║
        ║  Output:                                                 ║
        ║    • Prediction: FAKE or REAL                            ║
        ║    • Confidence Score: 0.0 - 1.0                         ║
        ╚═══════════════════════════╦══════════════════════════════╝
                                    │
                                    ▼
        ╔══════════════════════════════════════════════════════════╗
        ║  MODULE 5: VERIFICATION LAYER                            ║
        ╠══════════════════════════════════════════════════════════╣
        ║  1. Source Credibility Check                             ║
        ║     • Trusted sources database                           ║
        ║     • Known fake sources flagged                         ║
        ║  2. Fact-Checking Sites                                  ║
        ║     • Snopes, FactCheck.org, PolitiFact                  ║
        ║     • Cross-reference claims                             ║
        ║  3. Trusted Source Cross-Reference                       ║
        ║     • Check major outlets coverage                       ║
        ║     • Knowledge graph verification                       ║
        ╚═══════════════════════════╦══════════════════════════════╝
                                    │
                                    ▼
        ╔══════════════════════════════════════════════════════════╗
        ║  MODULE 6: RESULT DASHBOARD                              ║
        ╠══════════════════════════════════════════════════════════╣
        ║  Display Components:                                     ║
        ║    ┌────────────────────────────────────────┐            ║
        ║    │  News Status: FAKE / REAL              │            ║
        ║    │  Confidence Score: 87%                 │            ║
        ║    │  Verdict: LIKELY FAKE                  │            ║
        ║    └────────────────────────────────────────┘            ║
        ║                                                           ║
        ║  Detailed Analysis:                                      ║
        ║    • Feature signals detected                            ║
        ║    • Sentiment breakdown                                 ║
        ║    • Source credibility score                            ║
        ║    • Fact-check results                                  ║
        ║                                                           ║
        ║  Recommendations:                                        ║
        ║    ⚠️  Exercise caution before sharing                   ║
        ║    🔍 Verify with trusted sources                        ║
        ║    📊 Check source credibility                           ║
        ╚══════════════════════════════════════════════════════════╝
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │   USER RECEIVES RESULT      │
                    │  • Clear verdict            │
                    │  • Confidence score         │
                    │  • Actionable advice        │
                    └─────────────────────────────┘

╔══════════════════════════════════════════════════════════════════════════╗
║                           TECHNICAL STACK                                ║
╠══════════════════════════════════════════════════════════════════════════╣
║  Backend:        Python, Flask, Flask-CORS                               ║
║  ML Libraries:   scikit-learn, pandas, numpy                             ║
║  NLP:            NLTK (tokenization, stemming, stopwords)                ║
║  Web Scraping:   BeautifulSoup4, requests                                ║
║  Frontend:       HTML5, CSS3, JavaScript (Vanilla)                       ║
║  Database:       SQLite (optional, for history)                          ║
╚══════════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════════╗
║                           KEY FEATURES                                   ║
╠══════════════════════════════════════════════════════════════════════════╣
║  ✓ Real-time analysis                                                    ║
║  ✓ Multi-source data collection                                          ║
║  ✓ Advanced NLP preprocessing                                            ║
║  ✓ Multiple ML model support                                             ║
║  ✓ Source credibility verification                                       ║
║  ✓ Fact-checking integration                                             ║
║  ✓ Beautiful dashboard UI                                                ║
║  ✓ RESTful API                                                           ║
║  ✓ Comprehensive testing                                                 ║
║  ✓ Modular, extensible architecture                                      ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
    
    print(diagram)


def print_module_details():
    """Print detailed module information"""
    
    modules = """
╔══════════════════════════════════════════════════════════════════════════╗
║                        MODULE DETAILS                                    ║
╚══════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────┐
│ MODULE 1: data_collection.py                                             │
├──────────────────────────────────────────────────────────────────────────┤
│ Class: DataCollector                                                     │
│ Methods:                                                                 │
│   • collect_from_url(url) → Dict                                         │
│   • collect_from_news_api(query, page_size) → List[Dict]                │
│   • collect_from_text(text, title) → Dict                                │
│ Purpose: Gather news data from multiple sources                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ MODULE 2: data_preprocessing.py                                          │
├──────────────────────────────────────────────────────────────────────────┤
│ Class: TextPreprocessor                                                  │
│ Methods:                                                                 │
│   • clean_text(text) → str                                               │
│   • tokenize(text) → List[str]                                           │
│   • remove_stopwords(tokens) → List[str]                                 │
│   • stem_tokens(tokens) → List[str]                                      │
│   • preprocess(text) → str                                               │
│   • preprocess_article(article) → Dict                                   │
│ Purpose: Clean and normalize text data                                   │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ MODULE 3: feature_extraction.py                                          │
├──────────────────────────────────────────────────────────────────────────┤
│ Class: FeatureExtractor                                                  │
│ Methods:                                                                 │
│   • extract_tfidf_features(text) → np.ndarray                            │
│   • extract_sentiment_features(text) → Dict                              │
│   • extract_linguistic_features(text, original) → Dict                   │
│   • extract_all_features(article) → Dict                                 │
│ Purpose: Convert text to numerical features                              │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ MODULE 4: ml_model.py                                                    │
├──────────────────────────────────────────────────────────────────────────┤
│ Class: FakeNewsClassifier                                                │
│ Methods:                                                                 │
│   • load_model(path)                                                     │
│   • predict(features) → Tuple[str, float]                                │
│   • predict_with_details(article) → Dict                                 │
│ Purpose: ML classification of fake vs real news                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ MODULE 5: verification.py                                                │
├──────────────────────────────────────────────────────────────────────────┤
│ Class: NewsVerifier                                                      │
│ Methods:                                                                 │
│   • verify_source_credibility(source) → Dict                             │
│   • check_fact_checking_sites(title, content) → Dict                     │
│   • cross_reference_trusted_sources(title, keywords) → Dict              │
│   • verify_article(article, prediction, confidence) → Dict               │
│ Purpose: Cross-check with external verification sources                  │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ MODULE 6: dashboard.py                                                   │
├──────────────────────────────────────────────────────────────────────────┤
│ Class: ResultDashboard                                                   │
│ Methods:                                                                 │
│   • format_analysis_result(article, prediction, verification) → Dict     │
│   • format_summary_statistics(analyses) → Dict                           │
│   • format_for_api_response(dashboard_result) → Dict                     │
│ Purpose: Format and present analysis results                             │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ INTEGRATION: pipeline.py                                                 │
├──────────────────────────────────────────────────────────────────────────┤
│ Class: FakeNewsDetectionPipeline                                         │
│ Methods:                                                                 │
│   • analyze_text(text, title) → Dict                                     │
│   • analyze_url(url) → Dict                                              │
│   • analyze_news_query(query, article_index) → Dict                      │
│   • batch_analyze(articles) → Dict                                       │
│   • get_pipeline_info() → Dict                                           │
│ Purpose: Integrate all 6 modules into unified system                     │
└──────────────────────────────────────────────────────────────────────────┘
"""
    
    print(modules)


if __name__ == '__main__':
    print_system_diagram()
    print("\n\n")
    print_module_details()
    
    print("\n" + "="*78)
    print("  For more information, see:")
    print("    • SYSTEM_ARCHITECTURE.md - Complete documentation")
    print("    • QUICK_START.md - Getting started guide")
    print("    • test_pipeline.py - Usage examples")
    print("="*78 + "\n")
