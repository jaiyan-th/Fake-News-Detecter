# 🔍 AI News Verification System

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-dc2626.svg)](https://qdrant.tech)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.1_Inference-f97316.svg)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An **LLM + RAG-based evidence verification system** that verifies news URLs and viral text claims against real-time reporting from global and regional news sources without relying on a traditional supervised fake-news classifier.

---

## 🎯 Core Product Objective

When encountering a suspicious claim on social media or browsing the web, users should not have to manually visit multiple news portals one by one. 

**VerifyNews** automates this multi-source investigation:
1. **Ingests** a news article URL or pasted text claim.
2. **Extracts** the core verifiable claim(s) and named entities using **Groq LLM**.
3. **Formulates** targeted search queries across multiple angles.
4. **Retrieves** real-time news articles from **NewsAPI** and **Google News (SerpAPI)**.
5. **Deduplicates** cross-publisher syndicated wire stories.
6. **Indexes & Semantically Searches** evidence using **FastEmbed (`BAAI/bge-small-en-v1.5`)** and a stable **Qdrant** collection (`news_evidence`).
7. **Evaluates** stance (`SUPPORT`, `CONTRADICT`, `NEUTRAL`) and context for each retrieved source using Groq LLM.
8. **Synthesizes** a transparent verdict: `REAL`, `FALSE`, `MISLEADING`, or `UNVERIFIED` with evidence snippets and confidence breakdown.

---

## 🏗️ Architecture

```
USER INPUT (URL or Text)
       │
       ▼
 FastAPI Backend (/api/v1/verify)
       │
       ├─► [If URL] Article Extractor (newspaper3k + bs4)
       │
       ▼
 Groq LLM — Claim Extraction (Primary claim, Sub-claims, Entities)
       │
       ▼
 Groq LLM — Search Query Generation (3-5 targeted queries)
       │
       ├─────────────────────────┬─────────────────────────┐
       ▼                         ▼                         ▼
   NewsAPI Search         SerpAPI Google News        Fallback Store
       │                         │                         │
       └─────────────────────────┼─────────────────────────┘
                                 ▼
                     Source Normalization & Wire Deduplication
                                 ▼
                     FastEmbed (384-dim Dense Vectors)
                                 ▼
                     Qdrant Vector Database (`news_evidence`)
                                 ▼
                     Semantic Evidence Retrieval (Top-K)
                                 ▼
                     Groq LLM — Stance & Nuance Analysis (SUPPORT / CONTRADICT / NEUTRAL)
                                 ▼
                     Groq LLM — Final Verdict & Transparent Synthesis
                                 │
                                 ▼
                     REAL / FALSE / MISLEADING / UNVERIFIED
                                 │
                                 ▼
                     Interactive Single-Page UI
```

---

## 🏷️ Verdict Definitions

- **`REAL`**: Multiple authoritative retrieved sources independently confirm and support the central claim.
- **`FALSE`**: Authoritative retrieved evidence directly contradicts or refutes the central claim.
- **`MISLEADING`**: The claim contains partial truth but has missing context, exaggerates numbers, or presents outdated events as current.
- **`UNVERIFIED`**: Retrieved evidence is insufficient, inconclusive, or completely neutral.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- Free [Groq API Key](https://console.groq.com)
- Free [NewsAPI Key](https://newsapi.org)
- (Optional) [SerpAPI Key](https://serpapi.com)
- (Optional) Qdrant running locally via Docker or in-memory fallback

### 2. Installation
```bash
git clone https://github.com/jaiyan-th/Fake-News-Detecter.git
cd Fake-News-Detecter

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your-groq-api-key
NEWS_API_KEY=your-news-api-key
SERPAPI_KEY=your-serpapi-key-optional

# Qdrant (defaults to in-memory if no local server running)
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=news_evidence
```

### 4. Start the Application
```bash
# Start FastAPI backend & UI
uvicorn backend.main:app --reload --port 8000
```

Open your browser at:
- **Interactive UI:** [http://localhost:8000](http://localhost:8000)
- **Swagger / OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **System Health Diagnostics:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 📡 API Reference

### `POST /api/v1/verify`
Verify a news URL or text claim.

**Request Body:**
```json
{
  "url": "https://reuters.com/world/india/example-article",
  "text": null
}
```

**Response (200 OK):**
```json
{
  "verdict": "REAL",
  "confidence": 88,
  "confidence_label": "Verification Confidence",
  "claim": {
    "primary_claim": "India launched new solar energy initiative.",
    "secondary_claims": [],
    "entities": ["India", "Solar Mission"],
    "timeframe": "Recent"
  },
  "summary": "Multiple reputable sources confirm the government announcement.",
  "explanation": "Reuters and The Hindu both report that the cabinet approved the solar outlay today.",
  "evidence_summary": {
    "supporting": 2,
    "contradicting": 0,
    "neutral": 1,
    "total_sources_evaluated": 3
  },
  "sources": [
    {
      "source_name": "Reuters",
      "domain": "reuters.com",
      "title": "Cabinet Clears Solar Plan",
      "url": "https://reuters.com/...",
      "stance": "SUPPORT",
      "relevance_score": 0.94,
      "evidence_snippet": "The government approved the funding.",
      "credibility_tier": "WIRE_AND_PRIMARY_AGENCY"
    }
  ],
  "source_agreement_percentage": 100.0,
  "limitations": [
    "Analysis based on English-language articles available at query time."
  ],
  "pipeline_stages": [
    { "stage": "article_extraction", "status": "COMPLETED", "duration_ms": 350 },
    { "stage": "claim_extraction", "status": "COMPLETED", "duration_ms": 480 },
    { "stage": "multi_source_search", "status": "COMPLETED", "duration_ms": 1100 },
    { "stage": "qdrant_semantic_retrieval", "status": "COMPLETED", "duration_ms": 120 },
    { "stage": "verdict_synthesis", "status": "COMPLETED", "duration_ms": 650 }
  ],
  "processing_time_ms": 2700
}
```

---

## 🧪 Running Tests
```bash
python -m pytest backend/tests/ -v
```

---

## 📄 License
MIT License. Created for AI-powered news verification and claim investigation.
