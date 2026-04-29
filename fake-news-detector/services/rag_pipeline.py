"""
Enhanced RAG Pipeline for Fake News Detection
12-Step pipeline with Query Expansion, Multi-Source Retrieval, RAG Fallback,
Semantic Re-ranking, Grounded Reasoning, and full observability.
"""

import uuid, time, re, logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum

from groq import Groq
from services.extractor import ArticleContent
from services.news_fetcher import NewsFetcher
from services.similarity import SimilarityEngine, SimilarityScore
from services.keyword_extractor import KeywordExtractor


# ---------------------------------------------------------------------------
# Enums & Dataclasses
# ---------------------------------------------------------------------------

class Stance(Enum):
    SUPPORT    = "support"
    CONTRADICT = "contradict"
    NEUTRAL    = "neutral"


@dataclass
class ClaimEntity:
    claim: str
    entities: List[str]
    topic: str
    normalized_claim: str


@dataclass
class NewsAPIEvidence:
    title: str
    source: str
    summary: str
    stance: Stance
    url: str
    similarity_score: float
    published_date: Optional[str] = None


@dataclass
class RAGEvidence:
    content: str
    similarity: float
    stance: Stance
    source: str
    url: str


@dataclass
class StepMetrics:
    step_name: str
    duration_ms: float
    details: Dict = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class PipelineMetrics:
    latency_ms: float
    retrieval_accuracy: float
    confidence_score: float
    evidence_coverage: int
    news_api_latency_ms: float
    rag_db_latency_ms: float
    rerank_latency_ms: float
    llm_latency_ms: float
    confidence_components: Dict = field(default_factory=dict)


@dataclass
class RAGPipelineResult:
    request_id: str
    verdict: str
    confidence: float
    claim_summary: str
    expanded_queries: List[str]
    retrieval_stats: Dict
    news_api_evidence: List[NewsAPIEvidence]
    rag_evidence: List[RAGEvidence]
    gap_analysis: str
    reasoning: str
    final_explanation: str
    processing_time: float
    metrics: PipelineMetrics
    step_logs: List[StepMetrics] = field(default_factory=list)

# ---------------------------------------------------------------------------
# RAGPipeline
# ---------------------------------------------------------------------------

class RAGPipeline:
    """
    12-Step enhanced RAG pipeline:
    1. Input Analysis
    2. Query Expansion (NEW - critical for recall)
    3. Multi-Source Retrieval (News API + SerpAPI, broad)
    4. RAG Fallback (Vector DB when retrieval is weak)
    5. Hybrid Merging
    6. Semantic Re-ranking
    7. Evidence Analysis (stance per doc)
    8. Gap Analysis
    9. Grounded Reasoning
    10. Confidence Scoring
    11. Final Verdict
    12. JSON Output
    """

    TRUSTED_SOURCES = {
        'bbc', 'reuters', 'associated press', 'cnn', 'npr',
        'the guardian', 'new york times', 'washington post',
        'wall street journal', 'bloomberg', 'the hindu', 'ndtv',
        'times of india', 'indian express', 'hindustan times',
        'al jazeera', 'france 24', 'dw', 'pbs', 'abc news',
        'cbs news', 'nbc news', 'financial times', 'india today',
        'news18', 'firstpost', 'the quint', 'scroll', 'the print',
        'mint', 'livemint', 'moneycontrol', 'economic times',
        'deccan herald', 'telegraph india', 'tribune india',
    }

    def __init__(self, groq_api_key: str, news_api_key: str, serpapi_key: str = None):
        self.logger = logging.getLogger('fake_news_detector.rag_pipeline')
        self.groq_client = Groq(api_key=groq_api_key) if groq_api_key else None
        self.similarity_engine = SimilarityEngine()

        self.news_fetcher = None
        if news_api_key:
            try:
                self.news_fetcher = NewsFetcher(news_api_key, limit=15, serpapi_key=serpapi_key)
            except Exception as e:
                self.logger.warning(f"NewsFetcher init failed: {e}")

        self.keyword_extractor = None
        if groq_api_key:
            try:
                self.keyword_extractor = KeywordExtractor(groq_api_key)
            except Exception as e:
                self.logger.warning(f"KeywordExtractor init failed: {e}")

        self.top_k_rag   = 5
        self.top_k_news  = 15
        self.rerank_top  = 5
        self.min_results_threshold = 3   # trigger RAG fallback below this

    # -----------------------------------------------------------------------
    # Public entry point
    # -----------------------------------------------------------------------

    def analyze(self, article: ArticleContent) -> RAGPipelineResult:
        request_id, start_ts, step_logs = self._step1_request_tracking(article)
        pipeline_start = time.time()

        try:
            # STEP 1: Input Analysis
            claim_entity = self._step1_input_analysis(request_id, article, step_logs)

            # STEP 2: Query Expansion
            expanded_queries = self._step2_query_expansion(request_id, claim_entity, step_logs)

            # STEP 3: Multi-Source Retrieval (broad, no domain filter)
            t_news = time.time()
            news_articles, used_sources = self._step3_retrieval(
                request_id, claim_entity, expanded_queries, step_logs
            )
            news_ms = (time.time() - t_news) * 1000

            # STEP 4: RAG Fallback
            t_rag = time.time()
            rag_scores = self._step4_rag_fallback(
                request_id, article, news_articles, step_logs
            )
            rag_ms = (time.time() - t_rag) * 1000
            if "rag" not in used_sources and rag_scores:
                used_sources.append("rag")

            retrieval_stats = {
                "total_results": len(news_articles) + len(rag_scores),
                "news_api_results": len(news_articles),
                "rag_results": len(rag_scores),
                "used_sources": used_sources,
            }

            # STEP 5: Hybrid Merging
            rerank_start = time.time()
            merged = self._step5_merge(news_articles, rag_scores)

            # STEP 6: Semantic Re-ranking
            reranked = self._step6_rerank(merged, claim_entity, article)
            rerank_ms = (time.time() - rerank_start) * 1000
            self._log_step(step_logs, "step6_rerank", rerank_ms, {
                "merged_total": len(merged),
                "top_k_selected": len(reranked),
                "ranking_scores": [round(d.get("_rank_score", 0), 4) for d in reranked],
            })
            self.logger.info(
                f"[{request_id}] STEP 6 – {len(merged)} merged -> {len(reranked)} reranked"
            )

            # STEP 7: Evidence Analysis
            llm_start = time.time()
            evidence = self._step7_evidence_analysis(request_id, reranked, claim_entity, step_logs)
            llm_ms = (time.time() - llm_start) * 1000

            # STEP 8: Gap Analysis
            gap = self._step8_gap_analysis(request_id, evidence, step_logs)

            # STEP 9: Grounded Reasoning
            r_start = time.time()
            reasoning = self._step9_grounded_reasoning(
                request_id, claim_entity, evidence, gap, step_logs
            )
            llm_ms += (time.time() - r_start) * 1000

            # STEP 10: Confidence Scoring
            confidence, conf_components = self._step10_confidence(
                request_id, evidence, step_logs
            )

            # STEP 11: Final Verdict
            verdict = self._step11_verdict(gap, confidence)
            self.logger.info(
                f"[{request_id}] STEP 11 – verdict={verdict} confidence={confidence:.1f}%"
            )

            # Metrics
            total_ms = (time.time() - pipeline_start) * 1000
            metrics = self._collect_metrics(
                evidence, confidence, conf_components,
                total_ms, news_ms, rag_ms, rerank_ms, llm_ms
            )
            self.logger.info(
                f"[{request_id}] Metrics – latency={metrics.latency_ms:.0f}ms "
                f"accuracy={metrics.retrieval_accuracy:.2f} "
                f"coverage={metrics.evidence_coverage}"
            )

            # DB Storage
            self._store_to_db(
                request_id, article, claim_entity, verdict,
                confidence, evidence, gap, metrics
            )

            final_explanation = self._build_explanation(
                verdict, confidence, evidence, reasoning
            )

            result = RAGPipelineResult(
                request_id=request_id,
                verdict=verdict,
                confidence=confidence,
                claim_summary=claim_entity.normalized_claim,
                expanded_queries=expanded_queries,
                retrieval_stats=retrieval_stats,
                news_api_evidence=evidence["news_api"],
                rag_evidence=evidence["rag"],
                gap_analysis=gap,
                reasoning=reasoning,
                final_explanation=final_explanation,
                processing_time=total_ms / 1000,
                metrics=metrics,
                step_logs=step_logs,
            )
            self.logger.info(f"[{request_id}] Pipeline complete in {total_ms:.0f}ms")
            return result

        except Exception as exc:
            total_ms = (time.time() - pipeline_start) * 1000
            self.logger.error(
                f"[{request_id}] Pipeline failed after {total_ms:.0f}ms: {exc}",
                exc_info=True
            )
            raise

    # -----------------------------------------------------------------------
    # STEP 1: Input Analysis
    # -----------------------------------------------------------------------

    def _step1_request_tracking(self, article: ArticleContent):
        request_id = str(uuid.uuid4())
        start_ts   = time.time()
        step_logs: List[StepMetrics] = []
        self.logger.info(
            f"[{request_id}] STEP 1 – input_type={'url' if article.url else 'text'} "
            f"input_len={len(article.content)}"
        )
        self._log_step(step_logs, "step1_request_tracking", 0, {
            "request_id": request_id,
            "input_type": "url" if article.url else "text",
            "input_length": len(article.content),
            "timestamp": start_ts,
        })
        return request_id, start_ts, step_logs

    def _step1_input_analysis(self, request_id: str, article: ArticleContent,
                               step_logs: list) -> ClaimEntity:
        t0 = time.time()
        text = f"{article.title} {article.content}".strip()
        entities         = self._extract_entities(text)
        topic            = self._identify_topic(text)
        normalized_claim = self._build_normalized_claim(article)
        ms = (time.time() - t0) * 1000
        self._log_step(step_logs, "step1_input_analysis", ms, {
            "entities_found": len(entities),
            "entities": entities[:5],
            "topic": topic,
            "normalized_claim": normalized_claim[:120],
            "content_length": len(article.content),
        })
        self.logger.info(
            f"[{request_id}] STEP 1 – entities={len(entities)} topic={topic} "
            f"claim='{normalized_claim[:80]}'"
        )
        return ClaimEntity(
            claim=article.title,
            entities=entities,
            topic=topic,
            normalized_claim=normalized_claim,
        )

    def _build_normalized_claim(self, article: ArticleContent) -> str:
        title   = (article.title   or "").strip()
        content = (article.content or "").strip()
        if len(content) >= 200:
            sentences = re.split(r'(?<=[.!?])\s+', content)
            for sent in sentences:
                sent = sent.strip()
                if len(sent) > 40:
                    if title and title.lower() not in sent.lower():
                        return f"{title}. {sent}"
                    return sent
            return title or content[:200]
        if len(content) >= 50:
            return f"{title}. {content}" if title else content
        if title and len(title) > 10:
            expanded = self._expand_claim_from_title(title, article.url)
            return expanded if expanded else title
        return title or article.url or "Unknown claim"

    def _expand_claim_from_title(self, title: str, url: str) -> str:
        slug_keywords = ""
        if url:
            from urllib.parse import urlparse
            path = urlparse(url).path
            slug = re.sub(r'[/_\-]+', ' ', path).strip()
            slug = re.sub(r'\d{4,}', '', slug).strip()
            if len(slug) > 10:
                slug_keywords = f" URL context: {slug[:150]}"
        if not self.groq_client:
            return title
        try:
            resp = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content":
                    f"Convert this news headline into a clear, verifiable factual claim "
                    f"(1-2 sentences). Be specific.\n\n"
                    f"Headline: {title}{slug_keywords}\n\nFactual claim:"}],
                temperature=0.1, max_tokens=80,
            )
            result = resp.choices[0].message.content.strip()
            if len(result) > 20 and result.lower() != title.lower():
                return result
        except Exception as e:
            self.logger.debug(f"Claim expansion failed: {e}")
        return title

    def _extract_entities(self, text: str) -> List[str]:
        if not self.groq_client:
            return []
        try:
            resp = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content":
                    f"Extract key entities (people, orgs, locations, events). "
                    f"Return ONLY a comma-separated list.\n\nText: {text[:1000]}\n\nEntities:"}],
                temperature=0.1, max_tokens=100,
            )
            raw = resp.choices[0].message.content.strip()
            return [e.strip() for e in raw.split(",") if e.strip()][:10]
        except Exception as e:
            self.logger.debug(f"Entity extraction failed: {e}")
            return []

    def _identify_topic(self, text: str) -> str:
        topics = {
            "politics":   ["election","government","president","minister","parliament","vote","policy","opec","oil","sanctions"],
            "health":     ["covid","vaccine","disease","medical","health","hospital","drug"],
            "technology": ["ai","tech","software","computer","digital","cyber","data"],
            "business":   ["economy","market","stock","company","business","trade","gdp","opec","oil","energy"],
            "sports":     ["game","player","team","match","championship","sport","tournament"],
            "science":    ["research","study","scientist","discovery","experiment","nasa","space"],
            "crime":      ["arrest","police","murder","fraud","court","sentence","crime"],
        }
        tl = text.lower()
        scores = {t: sum(1 for kw in kws if kw in tl) for t, kws in topics.items()}
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "general"

    # -----------------------------------------------------------------------
    # STEP 2: Query Expansion (CRITICAL)
    # -----------------------------------------------------------------------

    def _step2_query_expansion(self, request_id: str, claim_entity: ClaimEntity,
                                step_logs: list) -> List[str]:
        """
        Generate 5-10 enriched search queries using:
        - Synonyms and related terms
        - Entity variations
        - Contextual keywords
        - Domain-specific terms
        - Multiple angles of the claim
        """
        t0 = time.time()
        queries = []

        # Always include the normalized claim as base query
        base = claim_entity.normalized_claim
        queries.append(base)

        # LLM-based expansion (primary method)
        if self.groq_client:
            try:
                prompt = f"""You are a search query expert for a news fact-checking system.

Given this claim, generate 6 diverse search queries to find related news articles.
Rules:
- Each query should be 3-7 words
- Cover different angles: who, what, where, when, why
- Use synonyms and related terms
- Include entity names, locations, organizations
- Be specific, not generic
- Return ONLY the queries, one per line, no numbering

Claim: {base}
Entities: {', '.join(claim_entity.entities[:5]) if claim_entity.entities else 'none'}
Topic: {claim_entity.topic}

Queries:"""

                resp = self.groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,
                    max_tokens=200,
                )
                raw = resp.choices[0].message.content.strip()
                llm_queries = [
                    q.strip().strip('-').strip('*').strip()
                    for q in raw.split('\n')
                    if q.strip() and len(q.strip()) > 5
                ]
                queries.extend(llm_queries[:7])
            except Exception as e:
                self.logger.warning(f"[{request_id}] LLM query expansion failed: {e}")

        # Fallback: entity-based queries
        if len(queries) < 3 and claim_entity.entities:
            for i in range(0, min(len(claim_entity.entities), 6), 2):
                chunk = claim_entity.entities[i:i+2]
                if chunk:
                    queries.append(' '.join(chunk))

        # Fallback: keyword-based queries
        if len(queries) < 3 and self.keyword_extractor:
            try:
                kws = self.keyword_extractor.extract_keywords(base)
                if kws:
                    queries.append(' '.join(kws[:5]))
                    queries.append(' '.join(kws[:3]))
            except Exception:
                pass

        # Deduplicate while preserving order
        seen, unique = set(), []
        for q in queries:
            q_lower = q.lower().strip()
            if q_lower and q_lower not in seen and len(q_lower) > 4:
                seen.add(q_lower)
                unique.append(q.strip())

        # Cap at 10 queries
        final_queries = unique[:10]

        ms = (time.time() - t0) * 1000
        self._log_step(step_logs, "step2_query_expansion", ms, {
            "queries_generated": len(final_queries),
            "queries": final_queries,
        })
        self.logger.info(
            f"[{request_id}] STEP 2 – {len(final_queries)} expanded queries: "
            f"{final_queries[:3]}..."
        )
        return final_queries

    # -----------------------------------------------------------------------
    # STEP 3: Multi-Source Retrieval (broad, no domain restriction)
    # -----------------------------------------------------------------------

    def _step3_retrieval(self, request_id: str, claim_entity: ClaimEntity,
                          expanded_queries: List[str],
                          step_logs: list):
        """
        Retrieve broadly using ALL expanded queries.
        DO NOT restrict to limited domains initially.
        Deduplicate results across queries.
        """
        t0 = time.time()
        all_articles: List[ArticleContent] = []
        seen_urls: set = set()
        used_sources: List[str] = []

        if not self.news_fetcher:
            self._log_step(step_logs, "step3_retrieval", 0,
                           {"total": 0, "reason": "no news fetcher"})
            return [], []

        # Use top 4 expanded queries to maximize recall
        queries_to_use = expanded_queries[:4]

        for i, query in enumerate(queries_to_use):
            try:
                articles = self.news_fetcher.fetch_related_news(query, [])
                new_count = 0
                for a in articles:
                    # Accept articles with at least a title (SerpAPI often has title-only)
                    if a.url not in seen_urls and (len(a.content) >= 20 or len(a.title) >= 10):
                        seen_urls.add(a.url)
                        all_articles.append(a)
                        new_count += 1
                self.logger.info(
                    f"[{request_id}] STEP 3 query[{i}] '{query[:50]}' "
                    f"-> {len(articles)} raw, {new_count} new"
                )
                # Track which sources were used
                for a in articles:
                    src = "serpapi" if hasattr(self.news_fetcher, 'serpapi_fetcher') \
                          and self.news_fetcher.serpapi_fetcher else "news_api"
                    if src not in used_sources:
                        used_sources.append(src)
                # Stop early if we have enough
                if len(all_articles) >= self.top_k_news:
                    break
            except Exception as e:
                self.logger.warning(f"[{request_id}] Query '{query[:40]}' failed: {e}")
                continue

        if not used_sources:
            used_sources = ["news_api"]

        ms = (time.time() - t0) * 1000
        self._log_step(step_logs, "step3_retrieval", ms, {
            "queries_used": len(queries_to_use),
            "total_results": len(all_articles),
            "used_sources": used_sources,
        })
        self.logger.info(
            f"[{request_id}] STEP 3 – {len(all_articles)} total articles "
            f"from {len(queries_to_use)} queries"
        )
        return all_articles, used_sources

    # -----------------------------------------------------------------------
    # STEP 4: RAG Fallback
    # -----------------------------------------------------------------------

    def _step4_rag_fallback(self, request_id: str, article: ArticleContent,
                             news_articles: List[ArticleContent],
                             step_logs: list) -> List[SimilarityScore]:
        """
        Always query Vector DB.
        If news retrieval is weak (< threshold), increase top_k.
        """
        t0 = time.time()
        top_k = self.top_k_rag
        if len(news_articles) < self.min_results_threshold:
            top_k = min(10, top_k * 2)  # Double the RAG results when news is weak
            self.logger.info(
                f"[{request_id}] STEP 4 – weak news retrieval ({len(news_articles)}), "
                f"increasing RAG top_k to {top_k}"
            )

        try:
            scores = self.similarity_engine.search_knowledge_base(article, top_k=top_k)
        except Exception as e:
            self.logger.warning(f"[{request_id}] RAG fallback failed: {e}")
            scores = []

        ms = (time.time() - t0) * 1000
        self._log_step(step_logs, "step4_rag_fallback", ms, {
            "rag_results": len(scores),
            "top_k_used": top_k,
            "triggered_by_weak_news": len(news_articles) < self.min_results_threshold,
        })
        self.logger.info(
            f"[{request_id}] STEP 4 – RAG returned {len(scores)} docs in {ms:.0f}ms"
        )
        return scores

    # -----------------------------------------------------------------------
    # STEP 5: Hybrid Merging
    # -----------------------------------------------------------------------

    def _step5_merge(self, news_articles: List[ArticleContent],
                     rag_scores: List[SimilarityScore]) -> List[Dict]:
        merged, seen = [], set()
        for a in news_articles:
            url = a.url or f"__no_url_{a.title[:30]}"
            if url not in seen:
                merged.append({
                    "type": "news_api", "title": a.title, "content": a.content,
                    "source": a.source, "url": url,
                    "published_date": a.published_date,
                    "similarity": 0.0,
                    "is_trusted": self._is_trusted(a.source),
                })
                seen.add(url)
        for s in rag_scores:
            if s.article_url not in seen:
                merged.append({
                    "type": "rag", "title": s.article_title, "content": "",
                    "source": s.source, "url": s.article_url,
                    "published_date": None,
                    "similarity": s.score,
                    "is_trusted": s.is_trusted,
                })
                seen.add(s.article_url)
        return merged

    # -----------------------------------------------------------------------
    # STEP 6: Semantic Re-ranking
    # -----------------------------------------------------------------------

    def _step6_rerank(self, merged: List[Dict], claim_entity: ClaimEntity,
                      article: ArticleContent) -> List[Dict]:
        for doc in merged:
            sim = doc["similarity"]
            if sim == 0.0 and doc["content"]:
                doc_art = ArticleContent(
                    title=doc["title"], content=doc["content"],
                    url=doc["url"], source=doc["source"]
                )
                sim = self._cosine_sim(article, doc_art)
                doc["similarity"] = sim

            kw_score   = self._keyword_overlap(
                claim_entity.normalized_claim,
                doc["title"] + " " + doc["content"]
            )
            cred_score = 0.25 if doc["is_trusted"] else 0.0
            rec_score  = 0.15 if doc["type"] == "news_api" else 0.05

            doc["_rank_score"] = sim * 0.4 + kw_score * 0.2 + cred_score + rec_score

        merged.sort(key=lambda d: d["_rank_score"], reverse=True)
        return merged[:self.rerank_top]

    def _cosine_sim(self, a1: ArticleContent, a2: ArticleContent) -> float:
        try:
            e1 = self.similarity_engine.generate_embedding(f"{a1.title} {a1.content}")
            e2 = self.similarity_engine.generate_embedding(f"{a2.title} {a2.content}")
            return float(self.similarity_engine._cosine_similarity(e1, e2))
        except Exception:
            return 0.0

    def _keyword_overlap(self, claim: str, doc_text: str) -> float:
        stop = {"the","a","an","and","or","but","in","on","at","to","for",
                "of","is","was","are","were","be","been","that","this"}
        cw = set(claim.lower().split()) - stop
        dw = set(doc_text.lower().split()) - stop
        if not cw:
            return 0.0
        return len(cw & dw) / len(cw)

    # -----------------------------------------------------------------------
    # STEP 7: Evidence Analysis
    # -----------------------------------------------------------------------

    def _step7_evidence_analysis(self, request_id: str, reranked: List[Dict],
                                   claim_entity: ClaimEntity, step_logs: list) -> Dict:
        t0 = time.time()
        news_ev, rag_ev = [], []
        stance_dist = {"support": 0, "contradict": 0, "neutral": 0}

        for doc in reranked:
            stance = self._determine_stance(claim_entity.normalized_claim, doc)
            stance_dist[stance.value] += 1
            if doc["type"] == "news_api":
                news_ev.append(NewsAPIEvidence(
                    title=doc["title"], source=doc["source"],
                    summary=doc["content"][:200], stance=stance,
                    url=doc["url"], similarity_score=doc["similarity"],
                    published_date=doc.get("published_date"),
                ))
            else:
                rag_ev.append(RAGEvidence(
                    content=doc["title"], similarity=doc["similarity"],
                    stance=stance, source=doc["source"], url=doc["url"],
                ))

        ms = (time.time() - t0) * 1000
        self._log_step(step_logs, "step7_evidence_analysis", ms, {
            "evidence_count": len(news_ev) + len(rag_ev),
            "stance_distribution": stance_dist,
        })
        self.logger.info(
            f"[{request_id}] STEP 7 – evidence={len(news_ev)+len(rag_ev)} "
            f"stance={stance_dist}"
        )
        return {"news_api": news_ev, "rag": rag_ev, "stance_dist": stance_dist}

    def _determine_stance(self, claim: str, doc: Dict) -> Stance:
        if not self.groq_client:
            return Stance.NEUTRAL
        try:
            doc_text = f"{doc['title']} {doc['content'][:400]}"
            resp = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content":
                    f"Does this DOCUMENT support, contradict, or is neutral to the CLAIM?\n"
                    f"CLAIM: {claim}\nDOCUMENT: {doc_text}\n"
                    f"Reply with ONE word only: SUPPORT, CONTRADICT, or NEUTRAL"}],
                temperature=0.1, max_tokens=10,
            )
            r = resp.choices[0].message.content.strip().upper()
            if "SUPPORT" in r:   return Stance.SUPPORT
            if "CONTRADICT" in r: return Stance.CONTRADICT
            return Stance.NEUTRAL
        except Exception:
            return Stance.NEUTRAL

    # -----------------------------------------------------------------------
    # STEP 8: Gap Analysis
    # -----------------------------------------------------------------------

    def _step8_gap_analysis(self, request_id: str, evidence: Dict,
                             step_logs: list) -> str:
        t0 = time.time()
        sd = evidence["stance_dist"]
        total = sd["support"] + sd["contradict"] + sd["neutral"]
        if total == 0:
            gap = "Unsupported"
        else:
            sup_r = sd["support"]    / total
            con_r = sd["contradict"] / total
            if con_r > 0.5:
                gap = "Contradicted"
            elif sup_r >= 0.7:
                gap = "Fully Supported"
            elif sup_r >= 0.4:
                gap = "Partially Supported"
            else:
                gap = "Unsupported"
        ms = (time.time() - t0) * 1000
        self._log_step(step_logs, "step8_gap_analysis", ms, {"gap_result": gap})
        self.logger.info(f"[{request_id}] STEP 8 – gap={gap}")
        return gap

    # -----------------------------------------------------------------------
    # STEP 9: Grounded Reasoning
    # -----------------------------------------------------------------------

    def _step9_grounded_reasoning(self, request_id: str, claim_entity: ClaimEntity,
                                   evidence: Dict, gap: str, step_logs: list) -> str:
        t0 = time.time()
        if not self.groq_client:
            return f"Evidence analysis: {gap}"

        ev_lines = []
        for ev in evidence["news_api"][:3]:
            ev_lines.append(f"[{ev.stance.value.upper()}] {ev.source}: {ev.summary}")
        for ev in evidence["rag"][:2]:
            ev_lines.append(f"[{ev.stance.value.upper()}] {ev.source}: {ev.content}")
        ev_text = "\n".join(ev_lines) if ev_lines else "No evidence retrieved."
        sources_used = len(ev_lines)

        try:
            resp = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content":
                        "You are a fact-checker. Use ONLY the provided evidence. "
                        "Do NOT add external information or hallucinate. "
                        "Evaluate logical consistency, source trustworthiness, "
                        "and detect clickbait, exaggeration, or misleading framing."},
                    {"role": "user", "content":
                        f"CLAIM: {claim_entity.normalized_claim}\n\n"
                        f"EVIDENCE:\n{ev_text}\n\n"
                        f"GAP: {gap}\n\n"
                        f"Write 2-3 sentences of reasoning based ONLY on the evidence above."},
                ],
                temperature=0.2, max_tokens=200,
            )
            reasoning = resp.choices[0].message.content.strip()
        except Exception as e:
            self.logger.warning(f"[{request_id}] LLM reasoning failed: {e}")
            reasoning = f"Based on {sources_used} sources, the evidence indicates: {gap}."

        ms = (time.time() - t0) * 1000
        self._log_step(step_logs, "step9_grounded_reasoning", ms, {
            "reasoning_length": len(reasoning),
            "sources_used": sources_used,
        })
        self.logger.info(
            f"[{request_id}] STEP 9 – reasoning_len={len(reasoning)} "
            f"sources_used={sources_used}"
        )
        return reasoning

    # -----------------------------------------------------------------------
    # STEP 10: Confidence Scoring
    # -----------------------------------------------------------------------

    def _step10_confidence(self, request_id: str, evidence: Dict,
                            step_logs: list):
        t0 = time.time()
        all_ev = evidence["news_api"] + evidence["rag"]
        if not all_ev:
            components = {"stance_ratio": 0.2, "avg_similarity": 0.0,
                          "reliability": 0.0, "agreement": 0.5}
            confidence = 20.0
        else:
            sd = evidence["stance_dist"]
            total = len(all_ev)
            sup_r = sd["support"]    / total
            con_r = sd["contradict"] / total
            stance_score = max(sup_r, con_r)

            sims = ([e.similarity_score for e in evidence["news_api"]] +
                    [e.similarity       for e in evidence["rag"]])
            avg_sim = sum(sims) / len(sims) if sims else 0.0

            trusted_n = (
                sum(1 for e in evidence["news_api"] if self._is_trusted(e.source)) +
                sum(1 for e in evidence["rag"] if "Knowledge Base" in e.source)
            )
            reliability = trusted_n / total

            n_total = len(evidence["news_api"])
            r_total = len(evidence["rag"])
            if n_total > 0 and r_total > 0:
                n_sup = sum(1 for e in evidence["news_api"] if e.stance == Stance.SUPPORT)
                r_sup = sum(1 for e in evidence["rag"]      if e.stance == Stance.SUPPORT)
                agreement = 1.0 - abs(n_sup / n_total - r_sup / r_total)
            else:
                agreement = 0.5

            components = {
                "stance_ratio":   round(stance_score, 4),
                "avg_similarity": round(avg_sim, 4),
                "reliability":    round(reliability, 4),
                "agreement":      round(agreement, 4),
            }
            raw = (stance_score * 0.4 + avg_sim * 0.3 +
                   reliability * 0.2 + agreement * 0.1)
            confidence = min(100.0, max(10.0, raw * 100))

        ms = (time.time() - t0) * 1000
        self._log_step(step_logs, "step10_confidence", ms, {
            "confidence": round(confidence, 2),
            "components": components,
        })
        self.logger.info(
            f"[{request_id}] STEP 10 – confidence={confidence:.1f}% "
            f"components={components}"
        )
        return confidence, components

    # -----------------------------------------------------------------------
    # STEP 11: Final Verdict
    # -----------------------------------------------------------------------

    def _step11_verdict(self, gap: str, confidence: float) -> str:
        if gap == "Fully Supported"     and confidence >= 60: return "REAL"
        if gap == "Contradicted"        and confidence >= 60: return "FAKE"
        if gap == "Partially Supported" and confidence >= 70: return "REAL"
        return "UNCERTAIN"

    # -----------------------------------------------------------------------
    # Metrics + DB Storage
    # -----------------------------------------------------------------------

    def _collect_metrics(self, evidence: Dict, confidence: float,
                          conf_components: Dict, total_ms: float,
                          news_ms: float, rag_ms: float,
                          rerank_ms: float, llm_ms: float) -> PipelineMetrics:
        all_ev = evidence["news_api"] + evidence["rag"]
        total_docs = len(all_ev)
        sd = evidence["stance_dist"]
        relevant = sd["support"] + sd["contradict"]
        retrieval_accuracy = relevant / total_docs if total_docs > 0 else 0.0
        return PipelineMetrics(
            latency_ms=round(total_ms, 1),
            retrieval_accuracy=round(retrieval_accuracy, 4),
            confidence_score=round(confidence, 2),
            evidence_coverage=sd["support"],
            news_api_latency_ms=round(news_ms, 1),
            rag_db_latency_ms=round(rag_ms, 1),
            rerank_latency_ms=round(rerank_ms, 1),
            llm_latency_ms=round(llm_ms, 1),
            confidence_components=conf_components,
        )

    def _store_to_db(self, request_id: str, article: ArticleContent,
                      claim_entity: ClaimEntity, verdict: str,
                      confidence: float, evidence: Dict,
                      gap: str, metrics: PipelineMetrics):
        try:
            from models.rag_analysis_log import RAGAnalysisLog, RAGMetrics
            from models.user import db
            sd = evidence["stance_dist"]
            log = RAGAnalysisLog(
                request_id=request_id,
                input_text=article.content[:500],
                claim=claim_entity.normalized_claim[:500],
                verdict=verdict,
                confidence=round(confidence / 100, 4),
                latency_ms=metrics.latency_ms,
                retrieval_count=len(evidence["news_api"]) + len(evidence["rag"]),
                support_count=sd["support"],
                contradict_count=sd["contradict"],
                gap_type=gap,
            )
            db.session.add(log)
            met = RAGMetrics(
                request_id=request_id,
                retrieval_accuracy=metrics.retrieval_accuracy,
                latency_ms=metrics.latency_ms,
                confidence_score=metrics.confidence_score,
                evidence_coverage=metrics.evidence_coverage,
            )
            db.session.add(met)
            db.session.commit()
            self.logger.info(f"[{request_id}] DB stored")
        except Exception as e:
            self.logger.warning(f"[{request_id}] DB storage failed: {e}")
            try:
                from models.user import db
                db.session.rollback()
            except Exception:
                pass

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _is_trusted(self, source: str) -> bool:
        sl = source.lower()
        return any(t in sl for t in self.TRUSTED_SOURCES)

    def _build_explanation(self, verdict: str, confidence: float,
                            evidence: Dict, reasoning: str) -> str:
        sd = evidence["stance_dist"]
        sup, con = sd["support"], sd["contradict"]
        base = f"Verdict: {verdict} (Confidence: {confidence:.0f}%). "
        if verdict == "REAL":
            base += f"Supported by {sup} source(s). "
        elif verdict == "FAKE":
            base += f"Contradicted by {con} source(s). "
        else:
            base += f"Mixed evidence: {sup} supporting, {con} contradicting. "
        return base + reasoning

    @staticmethod
    def _log_step(step_logs: list, name: str, ms: float, details: Dict,
                  error: str = None):
        step_logs.append(StepMetrics(
            step_name=name,
            duration_ms=round(ms, 2),
            details=details,
            error=error,
        ))

    # -----------------------------------------------------------------------
    # STEP 12: JSON Output
    # -----------------------------------------------------------------------

    def to_json(self, result: RAGPipelineResult) -> Dict:
        return {
            "request_id":       result.request_id,
            "verdict":          result.verdict,
            "confidence":       f"{result.confidence:.0f}%",
            "claim_summary":    result.claim_summary,
            "expanded_queries": result.expanded_queries,
            "retrieval_stats":  result.retrieval_stats,
            "news_api_evidence": [
                {
                    "title":      ev.title,
                    "source":     ev.source,
                    "summary":    ev.summary,
                    "stance":     ev.stance.value,
                    "url":        ev.url,
                    "similarity": f"{ev.similarity_score:.2f}",
                }
                for ev in result.news_api_evidence
            ],
            "rag_evidence": [
                {
                    "content":    ev.content,
                    "similarity": f"{ev.similarity:.2f}",
                    "stance":     ev.stance.value,
                    "source":     ev.source,
                }
                for ev in result.rag_evidence
            ],
            "gap_analysis":      result.gap_analysis,
            "reasoning":         result.reasoning,
            "final_explanation": result.final_explanation,
            "metrics": {
                "latency_ms":            result.metrics.latency_ms,
                "retrieval_accuracy":    result.metrics.retrieval_accuracy,
                "evidence_coverage":     result.metrics.evidence_coverage,
                "confidence_score":      result.metrics.confidence_score,
                "news_api_latency_ms":   result.metrics.news_api_latency_ms,
                "rag_db_latency_ms":     result.metrics.rag_db_latency_ms,
                "rerank_latency_ms":     result.metrics.rerank_latency_ms,
                "llm_latency_ms":        result.metrics.llm_latency_ms,
                "confidence_components": result.metrics.confidence_components,
            },
            "processing_time": round(result.processing_time, 2),
        }
