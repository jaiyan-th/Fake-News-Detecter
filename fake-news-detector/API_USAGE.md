# Fake News Detection API Usage

## Overview

The Flask application provides a complete fake news detection pipeline that analyzes news articles from URLs and returns verdicts with confidence scores.

## Endpoints

### POST /analyze-url

Analyzes a news article URL for authenticity.

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
  "matched_articles": [
    {
      "url": "https://related-article.com",
      "title": "Related Article Title",
      "source": "BBC",
      "similarity": "87%",
      "is_trusted": true
    }
  ],
  "processing_time": 2.5
}
```

**Error Responses:**
- `400 Bad Request` - Invalid URL format
- `422 Unprocessable Entity` - Content extraction failure
- `503 Service Unavailable` - API failures
- `500 Internal Server Error` - General errors

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "service": "fake-news-detector-backend",
  "services": {
    "cache": "ok",
    "extractor": "ok",
    "summarizer": "ok|unavailable|error",
    "news_fetcher": "ok",
    "similarity": "ok",
    "decision": "ok"
  }
}
```

## Pipeline Flow

1. **Cache Check** - Check for existing analysis results
2. **Content Extraction** - Extract article content from URL
3. **Summarization** - Generate summary and extract key claims
4. **News Fetching** - Fetch related articles from News API
5. **Similarity Analysis** - Compute semantic similarities
6. **Decision Making** - Apply decision rules and generate verdict
7. **Caching** - Store results for future requests

## Running the Server

```bash
cd fake-news-detector
python app.py
```

The server will start on `http://localhost:5000`

## Example Usage

```bash
# Test health endpoint
curl http://localhost:5000/health

# Analyze a news article
curl -X POST http://localhost:5000/analyze-url \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.bbc.com/news/world-12345"}'
```

## Configuration

Set the following environment variables in `.env`:

- `GROQ_API_KEY` - Groq API key for LLM services
- `NEWS_API_KEY` - News API key for fetching related articles
- `DATABASE_PATH` - SQLite database path (default: database/news.db)
- `EMBEDDING_MODEL` - Sentence transformer model (default: all-MiniLM-L6-v2)
- `NEWS_API_LIMIT` - Max articles to fetch (default: 15)
- `REQUEST_TIMEOUT` - Request timeout in seconds (default: 10)