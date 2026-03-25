# 🎯 Fake News Detection System - Complete Architecture

## 📐 System Flow Diagram

```
User Input (News / URL / Social Media Post)
             │
             ▼
   ┌─────────────────────┐
   │ Data Collection     │ ← News APIs / Social Media APIs
   │ Layer (Module 1)    │
   └─────────────────────┘
             │
             ▼
   ┌─────────────────────┐
   │ Data Preprocessing  │
   │ (Module 2)          │
   │ • Cleaning          │
   │ • Tokenization      │
   │ • Stopword Removal  │
   │ • Stemming          │
   └─────────────────────┘
             │
             ▼
   ┌─────────────────────┐
   │ Feature Extraction  │
   │ (Module 3)          │
   │ • TF-IDF            │
   │ • Sentiment         │
   │ • Linguistic        │
   └─────────────────────┘
             │
             ▼
   ┌─────────────────────┐
   │ ML Classification   │
   │ (Module 4)          │
   │ • Model Prediction  │
   │ • Confidence Score  │
   └─────────────────────┘
             │
             ▼
   ┌─────────────────────┐
   │ Verification Layer  │
   │ (Module 5)          │
   │ • Source Check      │
   │ • Fact-Checking     │
   │ • Cross-Reference   │
   └─────────────────────┘
             │
             ▼
   ┌─────────────────────┐
   │ Result Dashboard    │
   │ (Module 6)          │
   │ • Fake/Real Status  │
   │ • Confidence Score  │
   │ • Recommendations   │
   └─────────────────────┘
```

## 🔧 Module Descriptions

### 1️⃣ Data Collection Module (`data_collection.py`)

**Purpose**: Collect news data from multiple sources

**Features**:
- Web scraping from URLs
- News API integration
- Social media post processing
- Manual text input handling

**Key Methods**:
- `collect_from_url(url)` - Scrape article from URL
- `collect_from_news_api(query)` - Fetch from News API
- `collect_from_text(text, title)` - Process user input

**Example**:
```python
collector = DataCollector(news_api_key="your_key")
article = collector.collect_from_url("https://example.com/article")
```

---

### 2️⃣ Data Preprocessing Module (`data_preprocessing.py`)

**Purpose**: Clean and normalize text data

**Processing Steps**:
1. **Cleaning**: Remove punctuation, URLs, special characters
2. **Tokenization**: Split text into words
3. **Stopword Removal**: Remove common words (the, a, is, etc.)
4. **Stemming/Lemmatization**: Reduce words to root form

**Example Transformation**:
```
Input:  "Breaking: Government announces new policy today!!!"
Output: "break govern announc new policy today"
```

**Key Methods**:
- `clean_text(text)` - Remove noise
- `tokenize(text)` - Split into tokens
- `remove_stopwords(tokens)` - Filter stopwords
- `preprocess(text)` - Complete pipeline

---

### 3️⃣ Feature Extraction Module (`feature_extraction.py`)

**Purpose**: Convert text to numerical features

**Feature Types**:

1. **TF-IDF Features**
   - Term Frequency-Inverse Document Frequency
   - Main input for ML model

2. **Sentiment Features**
   - Positive/negative word ratios
   - Sensational language detection
   - Emotional intensity

3. **Linguistic Features**
   - Text length
   - Punctuation usage
   - Capitalization patterns
   - Vocabulary richness

**Feature Signals Detected**:
- ⚠️ Sensational headlines
- ⚠️ Emotional tone
- ⚠️ Excessive punctuation
- ⚠️ Unusual word patterns
- ⚠️ Extreme sentiment

---

### 4️⃣ Machine Learning Model Module (`ml_model.py`)

**Purpose**: Classify news as FAKE or REAL

**Supported Models**:
- Logistic Regression
- Random Forest
- Support Vector Machine (SVM)
- Passive Aggressive Classifier
- Neural Networks (LSTM, BERT)

**Output**:
```json
{
  "prediction": "FAKE",
  "confidence": 0.92,
  "confidence_percentage": "92.0%",
  "model_type": "PassiveAggressiveClassifier"
}
```

**Key Methods**:
- `predict(features)` - Get prediction and confidence
- `predict_with_details(article)` - Full analysis with interpretation

---

### 5️⃣ Verification Layer Module (`verification.py`)

**Purpose**: Cross-check predictions with external sources

**Verification Methods**:

1. **Source Credibility Check**
   - Database of trusted sources (Reuters, AP, BBC, etc.)
   - Known unreliable sources flagged
   - Credibility scoring (0.0 - 1.0)

2. **Fact-Checking Sites**
   - Cross-reference with Snopes, FactCheck.org, PolitiFact
   - Search for similar debunked claims

3. **Trusted Source Cross-Reference**
   - Check if major outlets are reporting the story
   - Coverage analysis

**Trusted Sources Database**:
- High credibility (0.90-0.95): Reuters, AP News, BBC
- Medium credibility (0.70-0.85): CNN, Fox News, Time
- Fact-checkers (0.85-0.90): Snopes, FactCheck.org

---

### 6️⃣ Result Dashboard Module (`dashboard.py`)

**Purpose**: Format and present analysis results

**Dashboard Components**:

1. **Classification Status**
   - FAKE / REAL / UNCERTAIN
   - Confidence score with visual indicator
   - Color-coded results

2. **Detailed Analysis**
   - Feature signals detected
   - Sentiment breakdown
   - Linguistic patterns

3. **Verification Results**
   - Source credibility score
   - Fact-check status
   - Final verdict

4. **Recommendations**
   - Action items for users
   - Verification suggestions
   - Sharing warnings

**Example Output**:
```json
{
  "classification": {
    "status": "FAKE",
    "confidence_score": 0.87,
    "confidence_percentage": "87.0%"
  },
  "recommendations": [
    "⚠️ Exercise caution before sharing",
    "🔍 Verify with trusted sources",
    "🚫 Strong indicators of fake news"
  ],
  "visual_indicators": {
    "color": "#dc3545",
    "icon": "🚫",
    "status_text": "FAKE NEWS"
  }
}
```

---

## 🔄 Complete Pipeline Integration

The `pipeline.py` module integrates all 6 modules:

```python
from modules.pipeline import FakeNewsDetectionPipeline

# Initialize pipeline
pipeline = FakeNewsDetectionPipeline(
    model_path='model/model.pkl',
    vectorizer_path='model/vectorizer.pkl',
    news_api_key='optional_api_key'
)

# Analyze text
result = pipeline.analyze_text(
    text="Your article text here",
    title="Article title"
)

# Analyze URL
result = pipeline.analyze_url("https://example.com/article")
```

---

## 🌐 API Endpoints

### Enhanced Flask API (`api_enhanced.py`)

**Base URL**: `http://localhost:5000`

#### 1. Analyze Text
```http
POST /api/analyze/text
Content-Type: application/json

{
  "text": "Article content...",
  "title": "Article title"
}
```

#### 2. Analyze URL
```http
POST /api/analyze/url
Content-Type: application/json

{
  "url": "https://example.com/article"
}
```

#### 3. General Analysis
```http
POST /api/analyze
Content-Type: application/json

{
  "text": "...",  // or "url": "..."
  "title": "..."
}
```

#### 4. Pipeline Info
```http
GET /api/pipeline/info
```

#### 5. Health Check
```http
GET /api/health
```

---

## 📊 Response Format

```json
{
  "success": true,
  "timestamp": "2026-03-11T10:30:00",
  "result": {
    "prediction": "FAKE",
    "confidence": "87.0%",
    "verdict": "LIKELY FAKE"
  },
  "details": {
    "article": {
      "title": "...",
      "source": "...",
      "author": "..."
    },
    "analysis": {
      "model_type": "PassiveAggressiveClassifier",
      "interpretation": "High confidence: Strong indicators of fake news",
      "feature_signals": [
        "sensational headline",
        "emotional tone",
        "unverified source"
      ]
    },
    "verification": {
      "source_credibility": 0.3,
      "fact_check_status": "suspicious"
    },
    "recommendations": [
      "⚠️ Exercise caution before sharing",
      "🔍 Verify claims with trusted sources"
    ]
  },
  "visual": {
    "color": "#dc3545",
    "icon": "🚫",
    "status_text": "FAKE NEWS"
  }
}
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd fake_news_detector
pip install -r requirements.txt
```

### 2. Install NLTK Data (for preprocessing)
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
```

### 3. Run Enhanced API
```bash
cd training/backend
python api_enhanced.py
```

### 4. Test the System
```bash
python test_pipeline.py
```

---

## 🧪 Testing Examples

### Test with Text
```python
result = pipeline.analyze_text(
    text="Breaking news: Scientists discover shocking truth!",
    title="Shocking Discovery"
)
print(result['result']['prediction'])  # FAKE or REAL
print(result['result']['confidence'])   # Confidence score
```

### Test with URL
```python
result = pipeline.analyze_url("https://www.reuters.com/article/...")
```

---

## 📈 Performance Metrics

The system evaluates articles based on:

1. **ML Model Confidence** (50% weight)
2. **Source Credibility** (30% weight)
3. **Fact-Check Results** (20% weight)

**Final Verdict Thresholds**:
- Score > 0.7: LIKELY REAL
- Score 0.3-0.7: UNCERTAIN
- Score < 0.3: LIKELY FAKE

---

## 🔐 Security & Privacy

- No user data is stored without consent
- API keys are environment variables
- Input sanitization on all endpoints
- Rate limiting recommended for production

---

## 📝 Future Enhancements

- [ ] BERT/Transformer model integration
- [ ] Real-time fact-checking API integration
- [ ] Multi-language support
- [ ] Image/video analysis
- [ ] Browser extension
- [ ] Mobile app
- [ ] User feedback loop for model improvement

---

## 📚 Dependencies

- Flask >= 2.0
- scikit-learn >= 1.0
- pandas >= 1.1
- numpy >= 1.19
- nltk >= 3.6
- requests >= 2.25
- beautifulsoup4 >= 4.9

---

## 👥 Contributing

Contributions welcome! Please follow the modular architecture when adding features.

---

## 📄 License

MIT License - See LICENSE file for details
