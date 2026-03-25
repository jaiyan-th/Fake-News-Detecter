# 🚀 Quick Start Guide - Fake News Detection System

## 📋 Overview

This is a complete, production-ready fake news detection system with 6 integrated modules:

1. **Data Collection** - Gather news from URLs, APIs, or text input
2. **Data Preprocessing** - Clean and normalize text
3. **Feature Extraction** - Convert text to numerical features
4. **ML Classification** - Predict FAKE or REAL with confidence scores
5. **Verification Layer** - Cross-check with trusted sources
6. **Result Dashboard** - Beautiful, informative results

---

## ⚡ Installation

### Step 1: Install Dependencies

```bash
cd fake_news_detector
pip install -r requirements.txt
```

### Step 2: Download NLTK Data

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
```

---

## 🎯 Usage Options

### Option 1: Run Enhanced API Server

```bash
cd training/backend
python api_enhanced.py
```

Then open your browser to: `http://localhost:5000`

Or use the dashboard: `http://localhost:5000/dashboard.html`

### Option 2: Test the Pipeline

```bash
cd training/backend
python test_pipeline.py
```

This runs comprehensive tests on the 6-module pipeline.

### Option 3: Use in Your Code

```python
from modules.pipeline import FakeNewsDetectionPipeline

# Initialize
pipeline = FakeNewsDetectionPipeline(
    model_path='model/model.pkl',
    vectorizer_path='model/vectorizer.pkl'
)

# Analyze text
result = pipeline.analyze_text(
    text="Your article text here...",
    title="Article Title"
)

print(result['result']['prediction'])  # FAKE or REAL
print(result['result']['confidence'])   # e.g., "87.5%"
```

---

## 🌐 API Endpoints

### Analyze Text
```bash
curl -X POST http://localhost:5000/api/analyze/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Article content...", "title": "Title"}'
```

### Analyze URL
```bash
curl -X POST http://localhost:5000/api/analyze/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'
```

### Health Check
```bash
curl http://localhost:5000/api/health
```

### Pipeline Info
```bash
curl http://localhost:5000/api/pipeline/info
```

---

## 📊 Response Format

```json
{
  "success": true,
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

## 🧪 Example Tests

### Test 1: Sensational Fake News
```python
result = pipeline.analyze_text(
    title="BREAKING: Shocking Discovery Will Change Everything!!!",
    text="Scientists have made an UNBELIEVABLE discovery..."
)
# Expected: FAKE with high confidence
```

### Test 2: Credible News
```python
result = pipeline.analyze_text(
    title="Economic Report Shows Steady Growth",
    text="According to the latest economic data released by the Federal Reserve..."
)
# Expected: REAL with high confidence
```

### Test 3: URL Analysis
```python
result = pipeline.analyze_url("https://www.reuters.com/article/...")
# Scrapes and analyzes the article
```

---

## 📁 Project Structure

```
fake_news_detector/
├── training/
│   └── backend/
│       ├── modules/                    # 🆕 New modular system
│       │   ├── __init__.py
│       │   ├── data_collection.py     # Module 1
│       │   ├── data_preprocessing.py  # Module 2
│       │   ├── feature_extraction.py  # Module 3
│       │   ├── ml_model.py            # Module 4
│       │   ├── verification.py        # Module 5
│       │   ├── dashboard.py           # Module 6
│       │   └── pipeline.py            # Integration
│       ├── model/
│       │   ├── model.pkl
│       │   └── vectorizer.pkl
│       ├── templates/
│       │   ├── index.html
│       │   └── dashboard.html         # 🆕 New dashboard
│       ├── api_enhanced.py            # 🆕 Enhanced API
│       ├── test_pipeline.py           # 🆕 Test script
│       └── app.py                     # Original app
├── SYSTEM_ARCHITECTURE.md             # 🆕 Complete docs
├── QUICK_START.md                     # 🆕 This file
└── requirements.txt
```

---

## 🎨 Features

### ✅ What's Included

- **Multi-source data collection** (URL, text, News API)
- **Advanced text preprocessing** (NLTK-powered)
- **TF-IDF feature extraction**
- **Sentiment analysis**
- **Linguistic feature detection**
- **ML classification** (supports multiple models)
- **Source credibility checking**
- **Fact-checking integration**
- **Beautiful dashboard UI**
- **RESTful API**
- **Comprehensive testing**

### 🎯 Detection Capabilities

The system detects:
- Sensational headlines
- Emotional manipulation
- Excessive punctuation/capitalization
- Extreme sentiment
- Unusual word patterns
- Unreliable sources
- Grammatical anomalies

---

## 🔧 Configuration

### Environment Variables (Optional)

```bash
# For News API integration
export NEWS_API_KEY="your_api_key_here"
```

### Model Paths

Edit in `api_enhanced.py`:
```python
MODEL_PATH = 'model/model.pkl'
VECTORIZER_PATH = 'model/vectorizer.pkl'
```

---

## 📈 Performance

The system uses a weighted scoring system:
- **ML Model**: 50% weight
- **Source Credibility**: 30% weight
- **Fact-Checking**: 20% weight

**Verdict Thresholds**:
- Score > 0.7: LIKELY REAL
- Score 0.3-0.7: UNCERTAIN
- Score < 0.3: LIKELY FAKE

---

## 🐛 Troubleshooting

### Issue: NLTK data not found
```bash
python -c "import nltk; nltk.download('all')"
```

### Issue: Model not found
Make sure `model.pkl` and `vectorizer.pkl` exist in `training/backend/model/`

### Issue: Import errors
```bash
pip install -r requirements.txt --upgrade
```

---

## 📚 Documentation

- **Full Architecture**: See `SYSTEM_ARCHITECTURE.md`
- **API Documentation**: Run server and visit `/api/docs`
- **Module Documentation**: Check docstrings in each module file

---

## 🚀 Next Steps

1. **Run the test**: `python test_pipeline.py`
2. **Start the API**: `python api_enhanced.py`
3. **Open dashboard**: Visit `http://localhost:5000`
4. **Test with your data**: Use the API or Python interface
5. **Integrate**: Use the pipeline in your application

---

## 💡 Tips

- Use the dashboard for interactive testing
- Use the API for integration with other apps
- Use the Python pipeline directly for batch processing
- Check `test_pipeline.py` for usage examples

---

## 🤝 Support

For issues or questions:
1. Check `SYSTEM_ARCHITECTURE.md` for detailed documentation
2. Review the test script for examples
3. Check module docstrings for API details

---

## ✨ What Makes This Special

- **Modular Design**: Each component is independent and testable
- **Production Ready**: Error handling, logging, validation
- **Comprehensive**: 6-stage pipeline with verification
- **Easy to Use**: Simple API, clear documentation
- **Extensible**: Easy to add new features or models
- **Beautiful UI**: Professional dashboard interface

---

Enjoy detecting fake news! 🎉
