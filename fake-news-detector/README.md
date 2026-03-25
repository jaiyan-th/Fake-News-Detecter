# Fake News Detection Backend

A Flask-based backend service for detecting fake news using AI-powered analysis.

## Features

- URL-based news article analysis
- Content extraction using newspaper3k
- AI-powered summarization and claim extraction (Groq/Mistral)
- Semantic similarity analysis using sentence transformers
- Cross-referencing with News API
- Credibility assessment against trusted sources
- Contradiction detection
- SQLite-based caching and persistence

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables:
   ```bash
   cp .env.template .env
   # Edit .env with your API keys
   ```

3. Run the application:
   ```bash
   python app.py
   ```

## API Endpoints

### POST /analyze-url
Analyze a news article URL for authenticity.

**Request:**
```json
{
  "url": "https://example.com/news-article"
}
```

**Response:**
```json
{
  "verdict": "REAL|FAKE|UNCERTAIN",
  "confidence": "85%",
  "explanation": "Analysis explanation...",
  "matched_articles": [...],
  "processing_time": 2.5
}
```

### GET /health
Health check endpoint.

## Environment Variables

- `GROQ_API_KEY`: Required - Groq API key for LLM services
- `NEWS_API_KEY`: Required - News API key for article fetching
- `FLASK_DEBUG`: Optional - Enable debug mode (default: false)
- `DATABASE_PATH`: Optional - SQLite database path (default: database/news.db)
- `NEWS_API_LIMIT`: Optional - Max articles to fetch (default: 15)
- `REQUEST_TIMEOUT`: Optional - Request timeout in seconds (default: 10)

## Project Structure

```
fake-news-detector/
├── app.py                 # Main Flask application
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables (template)
├── routes/
│   └── analyze.py       # Analysis API routes
├── services/            # Core business logic
│   ├── extractor.py     # Content extraction
│   ├── summarizer.py    # Article summarization
│   ├── keyword_extractor.py  # Keyword extraction
│   ├── news_fetcher.py  # News API integration
│   ├── similarity.py    # Semantic similarity
│   ├── contradiction_checker.py  # Contradiction detection
│   ├── credibility.py   # Source credibility assessment
│   ├── decision.py      # Final verdict logic
│   └── cache.py         # Caching service
├── models/
│   └── database.py      # Database operations
└── database/
    └── news.db          # SQLite database (created at runtime)
```

## Development Status

This is the initial project structure setup. The core analysis pipeline is implemented but not yet fully integrated. Next steps involve connecting all services in the main application flow.