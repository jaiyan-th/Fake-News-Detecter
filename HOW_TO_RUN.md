# 🚀 How to Run the Fake News Detection System

## Quick Start (3 Steps)

### Step 1: Open Terminal in Backend Directory
```powershell
cd fake_news_detector\training\backend
```

### Step 2: Start the Server
```powershell
..\..\..\venv\Scripts\python.exe api_enhanced.py
```

### Step 3: Open Your Browser
Navigate to: **http://localhost:5000**

---

## 📊 What You'll See

When the server starts, you'll see:

```
============================================================
🚀 Fake News Detection System - Enhanced API
============================================================

📊 System Architecture:
  1️⃣  Data Collection Layer
  2️⃣  Data Preprocessing
  3️⃣  Feature Extraction
  4️⃣  Machine Learning Model
  5️⃣  Verification Layer
  6️⃣  Result Dashboard

============================================================

✓ Pipeline Status:
  • data_collection: Active
  • preprocessing: Active
  • feature_extraction: Active
  • ml_model: Active (PassiveAggressiveClassifier)
  • verification: Active
  • dashboard: Active

============================================================
🌐 Server starting at http://localhost:5000
============================================================
```

---

## 🌐 Access Points

### 1. Web Dashboard
**URL**: http://localhost:5000  
**Features**:
- Text input analysis
- URL scraping and analysis
- Real-time results
- Visual indicators
- Detailed breakdown

### 2. API Endpoints

#### Health Check
```bash
GET http://localhost:5000/api/health
```

#### Analyze Text
```bash
POST http://localhost:5000/api/analyze/text
Content-Type: application/json

{
  "text": "Your article text here...",
  "title": "Article Title"
}
```

#### Analyze URL
```bash
POST http://localhost:5000/api/analyze/url
Content-Type: application/json

{
  "url": "https://example.com/article"
}
```

#### Pipeline Info
```bash
GET http://localhost:5000/api/pipeline/info
```

---

## 🧪 Testing the System

### Test 1: Using the Web Interface

1. Open http://localhost:5000
2. Click on "Text Input" tab
3. Paste this sample text:
   ```
   BREAKING: Scientists discover shocking truth that will change everything! 
   This UNBELIEVABLE revelation will SHOCK you! Share before it's deleted!!!
   ```
4. Click "Analyze Article"
5. View the results showing it's likely FAKE news

### Test 2: Using curl (Command Line)

```bash
curl -X POST http://localhost:5000/api/analyze/text ^
  -H "Content-Type: application/json" ^
  -d "{\"text\": \"Breaking news: Scientists discover shocking truth!\", \"title\": \"Shocking Discovery\"}"
```

### Test 3: Using Python

```python
import requests

response = requests.post(
    'http://localhost:5000/api/analyze/text',
    json={
        'text': 'Your article text here...',
        'title': 'Article Title'
    }
)

result = response.json()
print(f"Prediction: {result['result']['prediction']}")
print(f"Confidence: {result['result']['confidence']}")
```

---

## 🎯 Example Results

### Fake News Example
**Input**: "BREAKING: Shocking discovery will change EVERYTHING!!!"

**Output**:
```json
{
  "success": true,
  "result": {
    "prediction": "FAKE",
    "confidence": "87.5%",
    "verdict": "LIKELY FAKE"
  },
  "details": {
    "analysis": {
      "feature_signals": [
        "sensational headline",
        "emotional tone",
        "excessive punctuation"
      ]
    },
    "recommendations": [
      "⚠️ Exercise caution before sharing",
      "🔍 Verify claims with trusted sources"
    ]
  }
}
```

### Real News Example
**Input**: "Economic report shows steady growth in third quarter"

**Output**:
```json
{
  "success": true,
  "result": {
    "prediction": "REAL",
    "confidence": "82.3%",
    "verdict": "LIKELY REAL"
  },
  "details": {
    "analysis": {
      "feature_signals": []
    },
    "recommendations": [
      "✓ Article appears credible based on analysis"
    ]
  }
}
```

---

## 🛑 Stopping the Server

Press **Ctrl + C** in the terminal where the server is running.

---

## 🔧 Troubleshooting

### Issue: "Module not found"
**Solution**: Make sure you're in the backend directory
```powershell
cd fake_news_detector\training\backend
```

### Issue: "Port already in use"
**Solution**: Kill the process using port 5000 or change the port in api_enhanced.py

### Issue: "NLTK data not found"
**Solution**: Download NLTK data
```powershell
..\..\..\venv\Scripts\python.exe -c "import nltk; nltk.download('punkt_tab'); nltk.download('stopwords'); nltk.download('wordnet')"
```

### Issue: Server won't start
**Solution**: Check if Python and all dependencies are installed
```powershell
..\..\..\venv\Scripts\python.exe -m pip list
```

---

## 📱 Alternative Access Methods

### Method 1: Double-click HTML File
Open `OPEN_DASHBOARD.html` in your browser for quick access links

### Method 2: Use the Batch Script (Windows)
Run `START_HERE.bat` and select option 4

### Method 3: Direct Python Execution
```powershell
.\venv\Scripts\python.exe start_api.py
```

---

## 🎨 Dashboard Features

When you open http://localhost:5000, you'll see:

1. **6-Stage Pipeline Visualization**
   - Shows the complete analysis flow

2. **Input Tabs**
   - Text Input: Paste article text
   - URL Input: Enter article URL

3. **Real-time Analysis**
   - Loading animation during processing
   - Progress through 6 stages

4. **Color-Coded Results**
   - 🔴 Red: FAKE news
   - 🟢 Green: REAL news
   - 🟡 Yellow: UNCERTAIN

5. **Detailed Breakdown**
   - Article information
   - Analysis details
   - Feature signals detected
   - Source verification
   - Recommendations

---

## 📊 System Requirements

- ✅ Python 3.8+
- ✅ Windows/Linux/Mac
- ✅ 2GB RAM minimum
- ✅ Internet connection (for URL analysis)

---

## 🎉 You're Ready!

The system is now running and ready to detect fake news. Open your browser to:

**http://localhost:5000**

Enjoy using the Fake News Detection System! 🚀
