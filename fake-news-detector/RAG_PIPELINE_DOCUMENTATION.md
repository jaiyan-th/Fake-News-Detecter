# Production-Grade RAG Pipeline for Fake News Detection

## Overview

This document describes the implementation of a production-grade Retrieval-Augmented Generation (RAG) pipeline for fake news detection. The system uses a strict 11-step verification process combining real-time news retrieval, vector database search, hybrid ranking, and grounded LLM reasoning.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     RAG PIPELINE ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  INPUT → [1] Parse → [2] News API → [3] Vector DB               │
│                ↓                                                  │
│         [4] Hybrid Merge → [5] Re-rank                           │
│                ↓                                                  │
│         [6] Evidence Analysis → [7] Gap Classification           │
│                ↓                                                  │
│         [8] Grounded Reasoning → [9] Confidence Score            │
│                ↓                                                  │
│         [10] Final Verdict → [11] JSON Output                    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## 11-Step Pipeline

### STEP 1: INPUT ANALYSIS
**Purpose**: Parse user input and extract structured information

**Process**:
- Parse text or URL content
- Extract core claim(s)
- Identify key entities (people, organizations, locations)
- Determine topic/domain
- Normalize claim into clear, verifiable statement

**Output**: `ClaimEntity` object with:
- `claim`: Original claim text
- `entities`: List of extracted entities
- `topic`: Domain classification (politics, health, tech, etc.)
- `normalized_claim`: Clean, verifiable statement

**Implementation**:
```python
def _parse_input(self, article: ArticleContent) -> ClaimEntity:
    entities = self._extract_entities(text)  # LLM-based extraction
    topic = self._identify_topic(text)       # Keyword-based classification
    normalized_claim = self._normalize_claim(title, content)
    return ClaimEntity(...)
```

---

### STEP 2: REAL-TIME RETRIEVAL (NEWS API)
**Purpose**: Retrieve recent, relevant articles from news sources

**Process**:
- Query News API using extracted keywords
- Retrieve recent articles (last 30 days)
- Filter duplicates and low-quality sources
- Prioritize trusted publishers (BBC, Reuters, etc.)
- Keep only recent data

**Trusted Sources**:
- International: BBC, Reuters, AP, CNN, NPR, The Guardian, NYT, WSJ
- Indian: The Hindu, Indian Express, Times of India, NDTV, Hindustan Times

**Output**: List of `ArticleContent` objects (top 10)

**Implementation**:
```python
def _retrieve_news_api(self, claim_entity: ClaimEntity) -> List[ArticleContent]:
    keywords = self.keyword_extractor.extract_keywords(claim)
    articles = self.news_fetcher.fetch_related_news(claim, keywords)
    filtered = self._filter_news_articles(articles)
    prioritized = self._prioritize_trusted(filtered)
    return prioritized[:10]
```

---

### STEP 3: RAG RETRIEVAL (VECTOR DB)
**Purpose**: Retrieve historical fact-checks and verified articles

**Process**:
- Perform semantic similarity search in vector database
- Retrieve top-k relevant historical documents
- Use pgvector for efficient similarity search
- Filter by similarity threshold (>0.6)

**Vector Database**:
- Technology: PostgreSQL + pgvector
- Embedding Model: all-MiniLM-L6-v2 (384 dimensions)
- Storage: `knowledge_articles` table

**Output**: List of `SimilarityScore` objects (top 5)

**Implementation**:
```python
def _retrieve_vector_db(self, article: ArticleContent) -> List[SimilarityScore]:
    rag_scores = self.similarity_engine.search_knowledge_base(
        article, top_k=5
    )
    return rag_scores
```

---

### STEP 4: HYBRID MERGING
**Purpose**: Combine News API and Vector DB results

**Process**:
- Merge results from both sources
- Deduplicate by URL
- Normalize format for consistent processing
- Tag source type (news_api vs rag)

**Output**: Unified list of documents with metadata

**Implementation**:
```python
def _merge_results(self, news_articles, rag_results) -> List[Dict]:
    merged = []
    seen_urls = set()
    
    # Add News API results
    for article in news_articles:
        if article.url not in seen_urls:
            merged.append({
                'type': 'news_api',
                'title': article.title,
                'content': article.content,
                'source': article.source,
                'url': article.url,
                'is_trusted': self._is_trusted_source(article.source)
            })
            seen_urls.add(article.url)
    
    # Add RAG results (similar logic)
    return merged
```

---

### STEP 5: RE-RANKING
**Purpose**: Rank documents using multiple relevance factors

**Ranking Factors**:
1. **Semantic Similarity** (40%): Cosine similarity between embeddings
2. **Keyword Overlap** (20%): Shared keywords between claim and document
3. **Source Credibility** (25%): Trusted source bonus
4. **Recency** (15%): Higher weight for News API (recent) vs RAG (historical)

**Formula**:
```
score = (similarity × 0.4) + (keyword_overlap × 0.2) + 
        (credibility × 0.25) + (recency × 0.15)
```

**Output**: Top 5 re-ranked documents

**Implementation**:
```python
def _rerank_documents(self, merged_docs, claim_entity, article) -> List[Dict]:
    scored_docs = []
    for doc in merged_docs:
        score = (
            doc['similarity'] * 0.4 +
            keyword_overlap * 0.2 +
            (0.25 if doc['is_trusted'] else 0) +
            (0.15 if doc['type'] == 'news_api' else 0.05)
        )
        scored_docs.append((doc, score))
    
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, score in scored_docs[:5]]
```

---

### STEP 6: EVIDENCE ANALYSIS
**Purpose**: Analyze each document's stance relative to the claim

**Stance Classification**:
- **SUPPORT**: Document confirms/supports the claim
- **CONTRADICT**: Document disputes/contradicts the claim
- **NEUTRAL**: Document is unrelated or ambiguous

**Process**:
- For each document, use LLM to determine stance
- Classify as Support, Contradict, or Neutral
- Store evidence with stance label

**Output**: 
- `news_api_evidence`: List of `NewsAPIEvidence` objects
- `rag_evidence`: List of `RAGEvidence` objects

**Implementation**:
```python
def _determine_stance(self, claim: str, doc: Dict) -> Stance:
    prompt = f"""Analyze if this DOCUMENT supports, contradicts, or is neutral to the CLAIM.
    
    CLAIM: {claim}
    DOCUMENT: {doc_text}
    
    Respond with ONLY: SUPPORT, CONTRADICT, or NEUTRAL"""
    
    response = self.groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    result = response.choices[0].message.content.strip().upper()
    return Stance.SUPPORT if 'SUPPORT' in result else ...
```

---

### STEP 7: CLAIM-EVIDENCE GAP CLASSIFICATION
**Purpose**: Classify the overall relationship between claim and evidence

**Classifications**:
1. **Fully Supported**: ≥70% supporting evidence
2. **Partially Supported**: 40-70% supporting evidence
3. **Unsupported**: <40% supporting evidence, no contradictions
4. **Contradicted**: >50% contradicting evidence

**Logic**:
```python
support_ratio = support_count / total
contradict_ratio = contradict_count / total

if contradict_ratio > 0.5:
    return "Contradicted"
elif support_ratio >= 0.7:
    return "Fully Supported"
elif support_ratio >= 0.4:
    return "Partially Supported"
else:
    return "Unsupported"
```

**Output**: Gap classification string

---

### STEP 8: GROUNDED REASONING
**Purpose**: Generate explanation using ONLY retrieved evidence

**Strict Rules**:
- ✅ Use ONLY retrieved evidence
- ❌ NO hallucination
- ❌ NO external information
- ✅ Cite specific sources

**Process**:
- Format evidence for LLM prompt
- Request reasoning based ONLY on provided evidence
- Validate output for groundedness

**Implementation**:
```python
def _grounded_reasoning(self, claim_entity, evidence_analysis, gap_classification) -> str:
    evidence_summary = self._format_evidence_for_llm(evidence_analysis)
    
    prompt = f"""You are a fact-checker. Analyze this claim using ONLY the provided evidence.
    
    CLAIM: {claim}
    EVIDENCE: {evidence_summary}
    GAP CLASSIFICATION: {gap_classification}
    
    Provide brief reasoning (2-3 sentences) based ONLY on the evidence above.
    Do NOT add external information."""
    
    response = self.groq_client.chat.completions.create(...)
    return response.choices[0].message.content.strip()
```

---

### STEP 9: CONFIDENCE SCORING
**Purpose**: Compute numerical confidence score (0-100%)

**Factors**:
1. **Support vs Contradiction Ratio** (40%): Stance distribution
2. **Average Similarity Score** (30%): Semantic relevance
3. **Source Reliability** (20%): Trusted source count
4. **Agreement between News API and RAG** (10%): Cross-source consistency

**Formula**:
```python
confidence = (
    stance_score * 0.4 +
    avg_similarity * 0.3 +
    reliability_score * 0.2 +
    agreement_score * 0.1
) * 100
```

**Output**: Confidence percentage (10-100%)

---

### STEP 10: FINAL VERDICT
**Purpose**: Determine final classification

**Verdict Logic**:
```python
if gap_classification == "Fully Supported" and confidence >= 60:
    return "REAL"
elif gap_classification == "Contradicted" and confidence >= 60:
    return "FAKE"
elif gap_classification == "Partially Supported" and confidence >= 70:
    return "REAL"
elif gap_classification == "Unsupported":
    return "UNCERTAIN"
else:
    return "UNCERTAIN"
```

**Verdicts**:
- **REAL**: Strong supporting evidence
- **FAKE**: Strong contradictions
- **UNCERTAIN**: Mixed or insufficient evidence

---

### STEP 11: OUTPUT (STRICT JSON)
**Purpose**: Return structured, standardized output

**JSON Schema**:
```json
{
  "verdict": "REAL | FAKE | UNCERTAIN",
  "confidence": "0–100%",
  "claim_summary": "Normalized claim statement",
  "news_api_evidence": [
    {
      "title": "Article title",
      "source": "Source name",
      "summary": "Brief summary",
      "stance": "support | contradict | neutral",
      "url": "Article URL",
      "similarity": "0.85"
    }
  ],
  "rag_evidence": [
    {
      "content": "Historical article content",
      "similarity": "0.78",
      "stance": "support | contradict | neutral",
      "source": "Knowledge Base (Source Name)"
    }
  ],
  "gap_analysis": "Fully Supported | Partially Supported | Unsupported | Contradicted",
  "reasoning": "Evidence-based reasoning (2-3 sentences)",
  "final_explanation": "Clear, concise explanation",
  "processing_time": 2.5
}
```

---

## API Endpoints

### 1. Analyze URL
```http
POST /rag-analyze-url
Content-Type: application/json

{
  "url": "https://example.com/news-article"
}
```

**Response**: Full RAG pipeline JSON output

### 2. Analyze Text
```http
POST /rag-analyze-text
Content-Type: application/json

{
  "text": "News content to analyze..."
}
```

**Response**: Full RAG pipeline JSON output

### 3. Health Check
```http
GET /rag-health
```

**Response**:
```json
{
  "status": "healthy",
  "pipeline": "RAG Pipeline v1.0",
  "components": {
    "groq_llm": true,
    "news_api": true,
    "vector_db": true,
    "keyword_extractor": true
  }
}
```

---

## Configuration

### Environment Variables
```bash
# Required
GROQ_API_KEY=your_groq_api_key
NEWS_API_KEY=your_news_api_key

# Optional
SERPAPI_KEY=your_serpapi_key  # For Google News (better coverage)
SUPABASE_DB_URL=postgresql://...  # For vector database
```

### Pipeline Parameters
```python
# In rag_pipeline.py
self.top_k_rag = 5          # Top K from vector DB
self.top_k_news = 10        # Top K from News API
self.rerank_top = 5         # Final top documents after re-ranking
```

---

## Strict Rules

### ✅ DO:
1. **ALWAYS** use retrieved data (News API + RAG)
2. **NEVER** hallucinate facts
3. **Prioritize** accuracy over fluency
4. **Keep** output explainable and structured
5. **Use** only evidence-based reasoning
6. **Cite** sources in explanations

### ❌ DON'T:
1. **Never** add information not in retrieved documents
2. **Never** make assumptions without evidence
3. **Never** ignore contradicting evidence
4. **Never** use outdated information when recent data exists
5. **Never** trust unverified sources equally with trusted ones

---

## Performance Metrics

### Typical Processing Times
- Input Analysis: 0.5-1s
- News API Retrieval: 2-4s
- Vector DB Retrieval: 0.3-0.5s
- Re-ranking: 0.5-1s
- Evidence Analysis: 1-2s
- LLM Reasoning: 1-2s
- **Total**: 5-10s per analysis

### Accuracy Targets
- Precision: >85% for REAL/FAKE verdicts
- Recall: >80% for detecting fake news
- F1 Score: >82% overall

---

## Error Handling

### Graceful Degradation
1. **News API Failure**: Continue with RAG only, reduce confidence
2. **Vector DB Failure**: Continue with News API only
3. **LLM Failure**: Use rule-based reasoning fallback
4. **No Evidence Found**: Return UNCERTAIN with low confidence

### Error Response Format
```json
{
  "error": "Error message",
  "step": "pipeline_step_name",
  "processing_time": 2.5
}
```

---

## Testing

### Unit Tests
```bash
pytest tests/test_rag_pipeline.py
```

### Integration Tests
```bash
pytest tests/test_rag_integration.py
```

### Example Test Cases
1. **Known Real News**: Should return REAL with high confidence
2. **Known Fake News**: Should return FAKE with high confidence
3. **Ambiguous Content**: Should return UNCERTAIN
4. **No Evidence**: Should return UNCERTAIN with low confidence

---

## Monitoring

### Key Metrics to Track
1. **Verdict Distribution**: REAL/FAKE/UNCERTAIN ratios
2. **Confidence Scores**: Average and distribution
3. **Processing Times**: Per step and total
4. **API Success Rates**: News API, Vector DB, LLM
5. **Evidence Quality**: Similarity scores, source reliability

### Logging
```python
# Automatic logging at each step
print("STEP 1: Input Analysis...")
print("STEP 2: Real-time News API Retrieval...")
# ... etc
```

---

## Future Enhancements

### Planned Features
1. **Multi-language Support**: Extend beyond English
2. **Image Analysis**: OCR + visual fake news detection
3. **Social Media Integration**: Twitter, Facebook fact-checking
4. **Real-time Alerts**: Notify users of trending fake news
5. **Explainability Dashboard**: Visual evidence presentation

### Optimization Opportunities
1. **Caching**: Cache News API results for 1 hour
2. **Batch Processing**: Analyze multiple articles simultaneously
3. **Model Fine-tuning**: Train custom models on fact-checking data
4. **Hybrid Ranking**: Experiment with BM25 + semantic search

---

## References

### Technologies Used
- **LLM**: Groq (Llama 3.1 8B Instant)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Vector DB**: PostgreSQL + pgvector
- **News API**: NewsAPI.org + SerpAPI (Google News)
- **Framework**: Flask + SQLAlchemy

### Research Papers
1. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (Lewis et al., 2020)
2. "Fact-Checking Meets Fauxtography: Verifying Claims About Images" (Zlatkova et al., 2019)
3. "Hybrid Retrieval for Open-Domain Question Answering" (Ma et al., 2021)

---

## Support

For issues or questions:
- GitHub Issues: [repository]/issues
- Documentation: This file
- API Reference: `/rag-health` endpoint

---

**Version**: 1.0  
**Last Updated**: 2024  
**Maintainer**: Fake News Detection Team
