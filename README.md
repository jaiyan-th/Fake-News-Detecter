# Fake News Detector

AI-powered fake news detection system using advanced NLP, semantic analysis, and LLM verification.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Groq API Key ([Get it here](https://console.groq.com))
- News API Key ([Get it here](https://newsapi.org))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Fake-News-Detecter-main
   ```

2. **Install dependencies**
   ```bash
   cd fake-news-detector
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env and add your API keys:
   # GROQ_API_KEY=your-groq-api-key
   # NEWS_API_KEY=your-news-api-key
   ```

4. **Start the server**
   ```bash
   python serve_frontend.py
   ```
   
   Or on Windows, double-click: `start_server.bat`

5. **Open your browser**
   ```
   http://localhost:3000
   ```

## 📋 Features

### Analysis Capabilities
- ✅ **Text Analysis** - Analyze news text with NLP and pattern detection
- ✅ **URL Verification** - Extract and verify news articles from URLs
- ✅ **Multi-language Support** - 10+ languages including English, Spanish, French, German, Hindi, Arabic, Chinese, Japanese

### AI-Powered Detection
- 🤖 **LLM Analysis** - Groq-powered explanations and reasoning
- 🔍 **Semantic Similarity** - Compare with trusted news sources
- 📊 **Pattern Detection** - Identify fake news indicators
- 🎯 **Credibility Assessment** - Evaluate source trustworthiness
- ⚡ **Contradiction Checking** - Detect conflicting claims

### Security & Performance
- 🔐 **User Authentication** - Email/password + Google OAuth
- 🛡️ **Rate Limiting** - Prevent abuse
- 📝 **Comprehensive Logging** - Track all operations
- ⚠️ **Error Handling** - Graceful failure recovery
- 💾 **Caching** - Fast repeated queries

## 🏗️ Project Structure

```
Fake-News-Detecter-main/
├── fake-news-detector/          # Backend (Python/Flask)
│   ├── models/                  # Database models
│   ├── routes/                  # API endpoints
│   ├── services/                # Business logic
│   ├── database/                # SQLite database
│   ├── .env                     # Environment variables
│   ├── serve_frontend.py        # Main server file
│   └── requirements.txt         # Python dependencies
│
├── fake_news_detector/          # Frontend (HTML/CSS/JS)
│   └── frontend/
│       ├── css/                 # Stylesheets
│       ├── js/                  # JavaScript
│       └── index.html           # Main page
│
└── start_server.bat             # Windows startup script
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed structure.

## 📖 API Documentation

### Analysis Endpoints

#### Analyze Text
```bash
POST /analyze-text
Content-Type: application/json
X-API-Key: frontend-client-key

{
  "text": "News content to analyze..."
}
```

#### Analyze URL
```bash
POST /analyze-url
Content-Type: application/json
X-API-Key: frontend-client-key

{
  "url": "https://example.com/news-article"
}
```

#### Response Format
```json
{
  "verdict": "REAL|FAKE|UNCERTAIN",
  "confidence": "85%",
  "explanation": "Analysis explanation...",
  "matched_articles": [
    {
      "title": "Related Article",
      "source": "BBC",
      "similarity": "87%",
      "is_trusted": true
    }
  ],
  "processing_time": 2.5
}
```

See [fake-news-detector/API_USAGE.md](fake-news-detector/API_USAGE.md) for complete API documentation.

## 🔧 Configuration

### Required Environment Variables

```env
# API Keys (Required)
GROQ_API_KEY=your-groq-api-key-here
NEWS_API_KEY=your-news-api-key-here

# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=true

# Database
DATABASE_PATH=database/news.db

# Model Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
NEWS_API_LIMIT=15
REQUEST_TIMEOUT=10

# Development
ALLOW_NO_API_KEY=true
```

### Optional: Email Notifications
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_USE_TLS=true
```

### Optional: Google OAuth
```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/api/auth/google/callback
```

## 🧪 Testing

### Manual Testing with Sample News

Use the provided test samples from today's news (March 21, 2026):

1. **Quantum Optics Discovery** - Scientific breakthrough
2. **CO2 to Fuel Catalyst** - Environmental technology
3. **AI Technology Trends** - Industry analysis
4. **Nvidia Revenue Projection** - Business news

Simply paste any of these topics into the text analysis field and click "Verify Text".

### Health Check
```bash
curl http://localhost:3000/health
```

## 🛠️ Technology Stack

### Backend
- **Framework**: Flask (Python)
- **Database**: SQLite
- **LLM**: Groq API (llama-3.1-8b-instant)
- **News API**: NewsAPI.org
- **Embeddings**: sentence-transformers
- **Authentication**: Flask-Login, Google OAuth

### Frontend
- **Pure JavaScript** (No frameworks)
- **HTML5/CSS3**
- **Responsive Design**

## 📝 License

This project is licensed under the MIT License.

## 👥 Contact

For questions or support:
- Email: jaiyanth.b@outlook.com
- Phone: +91 9345573281
- Location: Karur, Tamil Nadu, India

## 🙏 Acknowledgments

- Groq for LLM API
- NewsAPI.org for news data
- sentence-transformers for embeddings
- All open-source contributors

---

**Note**: This is an educational project demonstrating AI-powered fake news detection. Always verify important information through multiple trusted sources.
