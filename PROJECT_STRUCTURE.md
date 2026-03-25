# Fake News Detector - Project Structure

## Overview
This project is organized into backend and frontend components with a clean separation of concerns.

## Directory Structure

```
Fake-News-Detecter-main/
│
├── fake-news-detector/              # BACKEND (Python/Flask)
│   ├── models/                      # Database models
│   │   ├── database.py             # Database connection and operations
│   │   └── user.py                 # User model for authentication
│   │
│   ├── routes/                      # API endpoints
│   │   ├── analyze.py              # Analysis endpoints (/analyze-text, /analyze-url, /analyze-image)
│   │   └── auth.py                 # Authentication endpoints
│   │
│   ├── services/                    # Business logic services
│   │   ├── api_keys.py             # API key management
│   │   ├── auth_service.py         # Authentication service
│   │   ├── cache.py                # Caching service
│   │   ├── contradiction_checker.py # Contradiction detection
│   │   ├── credibility.py          # Source credibility assessment
│   │   ├── decision.py             # Decision engine for verdicts
│   │   ├── email_service.py        # Email notifications
│   │   ├── error_handler.py        # Error handling
│   │   ├── extractor.py            # Content extraction from URLs
│   │   ├── keyword_extractor.py    # Keyword extraction
│   │   ├── language_detector.py    # Multi-language support
│   │   ├── logger.py               # Logging service
│   │   ├── news_fetcher.py         # News API integration
│   │   ├── oauth_service.py        # Google OAuth
│   │   ├── password_service.py     # Password hashing
│   │   ├── pattern_detector.py     # Fake news pattern detection
│   │   ├── rate_limiter.py         # Rate limiting
│   │   ├── security.py             # Security validation
│   │   ├── similarity.py           # Semantic similarity analysis
│   │   └── summarizer.py           # Article summarization (Groq LLM)
│   │
│   ├── database/                    # SQLite database
│   │   └── news.db                 # Main database file
│   │
│   ├── logs/                        # Application logs
│   │   └── fake_news_detector.log
│   │
│   ├── .env                         # Environment variables (API keys)
│   ├── .env.example                # Environment template
│   ├── app.py                      # Flask app factory
│   ├── config.py                   # Configuration management
│   ├── serve_frontend.py           # Integrated server (frontend + backend)
│   ├── requirements.txt            # Python dependencies
│   ├── API_USAGE.md                # API documentation
│   ├── AUTH_SETUP.md               # Authentication setup guide
│   └── README.md                   # Backend documentation
│
├── fake_news_detector/              # FRONTEND (HTML/CSS/JavaScript)
│   └── frontend/
│       ├── css/
│       │   └── styles.css          # Main stylesheet
│       │
│       ├── js/
│       │   ├── api.js              # API service layer
│       │   ├── app.js              # Main application logic
│       │   ├── dashboard.js        # Results rendering
│       │   └── uploader.js         # Image upload handling
│       │
│       ├── images/
│       │   └── ai-robot.jpg        # Hero section image
│       │
│       ├── index.html              # Main HTML file
│       └── favicon.ico             # Site icon
│
├── database/                        # Root database (legacy)
│   └── news.db
│
├── logs/                            # Root logs (legacy)
│   └── fake_news_detector.log
│
├── start_server.bat                # Windows startup script
└── README.md                       # Main project documentation
```

## Key Files

### Backend Core
- `fake-news-detector/serve_frontend.py` - **START HERE** - Integrated server
- `fake-news-detector/app.py` - Flask application factory
- `fake-news-detector/config.py` - Configuration management
- `fake-news-detector/.env` - API keys and environment variables

### Frontend Core
- `fake_news_detector/frontend/index.html` - Main UI
- `fake_news_detector/frontend/js/app.js` - Application logic
- `fake_news_detector/frontend/js/api.js` - Backend communication
- `fake_news_detector/frontend/css/styles.css` - Styling

### Configuration
- `fake-news-detector/.env` - **REQUIRED** - Contains:
  - `GROQ_API_KEY` - For LLM analysis
  - `NEWS_API_KEY` - For news verification
  - `SECRET_KEY` - For session management
  - Database and email settings

## How to Run

1. **Install Dependencies**
   ```bash
   cd fake-news-detector
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   - Copy `.env.example` to `.env`
   - Add your API keys

3. **Start Server**
   ```bash
   python serve_frontend.py
   ```
   Or double-click `start_server.bat` (Windows)

4. **Access Application**
   - Open browser to: http://localhost:3000

## Technology Stack

### Backend
- **Framework**: Flask (Python)
- **Database**: SQLite
- **LLM**: Groq API (llama-3.1-8b-instant)
- **News API**: NewsAPI.org
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Authentication**: Flask-Login, Google OAuth

### Frontend
- **HTML5/CSS3/JavaScript** (Vanilla JS)
- **No frameworks** - Pure JavaScript for simplicity
- **Responsive Design** - Mobile-friendly

## API Endpoints

### Analysis
- `POST /analyze-text` - Analyze text content
- `POST /analyze-url` - Analyze news article URL

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user
- `GET /api/auth/google` - Google OAuth initiation
- `GET /api/auth/google/callback` - Google OAuth callback

### Health
- `GET /health` - System health check

## Features

✅ Text analysis with NLP
✅ URL verification with web scraping
✅ Multi-language support (10+ languages)
✅ Pattern detection for fake news indicators
✅ Semantic similarity analysis
✅ LLM-powered explanations
✅ User authentication (email + Google OAuth)
✅ Rate limiting and security
✅ Comprehensive error handling
✅ Performance logging
