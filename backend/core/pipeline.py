"""
Verification Pipeline Orchestrator
Coordinates all pipeline stages: Article Extraction -> Claim Extraction -> Search ->
Normalization & Deduplication -> Vector Embedding & Semantic Retrieval -> Stance Analysis -> Verdict Synthesis.
"""

import time
import uuid
import logging
from typing import Optional, List
from backend.schemas.verification import (
    VerificationRequest, VerificationResponse, ClaimInfo,
    PipelineStage, VerdictEnum, EvidenceSummary
)
from backend.services.article_extractor import ArticleExtractor
from backend.services.claim_extractor import ClaimExtractor
from backend.services.query_generator import QueryGenerator
from backend.services.newsapi_service import NewsAPIService
from backend.services.serpapi_service import SerpAPIService
from backend.services.source_normalizer import SourceNormalizer
from backend.services.vector_service import VectorSearchService
from backend.services.evidence_analyzer import EvidenceAnalyzer
from backend.services.verdict_generator import VerdictGenerator
from backend.core.config import settings

logger = logging.getLogger("news_verification.pipeline")


class VerificationPipeline:
    def __init__(
        self,
        article_extractor: ArticleExtractor,
        claim_extractor: ClaimExtractor,
        query_generator: QueryGenerator,
        newsapi_service: NewsAPIService,
        serpapi_service: SerpAPIService,
        source_normalizer: SourceNormalizer,
        vector_service: VectorSearchService,
        evidence_analyzer: EvidenceAnalyzer,
        verdict_generator: VerdictGenerator
    ):
        self.article_extractor = article_extractor
        self.claim_extractor = claim_extractor
        self.query_generator = query_generator
        self.newsapi_service = newsapi_service
        self.serpapi_service = serpapi_service
        self.source_normalizer = source_normalizer
        self.vector_service = vector_service
        self.evidence_analyzer = evidence_analyzer
        self.verdict_generator = verdict_generator

    async def verify(self, request: VerificationRequest) -> VerificationResponse:
        verification_id = str(uuid.uuid4())
        pipeline_start = time.time()
        pipeline_stages: List[PipelineStage] = []

        logger.info(f"[{verification_id}] Starting news verification pipeline. (type={'URL' if request.url else 'TEXT'})")

        # STAGE 1: Content Extraction / Ingestion
        t0 = time.time()
        raw_text = ""
        article_title = ""
        extracted_article = None

        if request.url:
            extracted = self.article_extractor.extract(request.url)
            extracted_article = extracted
            raw_text = extracted.content.replace('\u202f', ' ').replace('\xa0', ' ')
            article_title = extracted.title.replace('\u202f', ' ').replace('\xa0', ' ')
            stage_duration = round((time.time() - t0) * 1000, 2)
            pipeline_stages.append(PipelineStage(
                stage="article_extraction",
                status="COMPLETED",
                duration_ms=stage_duration,
                details={"url": request.url, "title": article_title, "chars": len(raw_text)}
            ))
        else:
            raw_text = request.text.strip().replace('\u202f', ' ').replace('\xa0', ' ')
            article_title = raw_text.split("\n")[0][:120]
            stage_duration = round((time.time() - t0) * 1000, 2)
            pipeline_stages.append(PipelineStage(
                stage="text_ingestion",
                status="COMPLETED",
                duration_ms=stage_duration,
                details={"chars": len(raw_text)}
            ))

        # STAGE 2: Claim Extraction (Groq)
        t0 = time.time()
        claim_info = self.claim_extractor.extract_claims(raw_text, title=article_title)
        stage_duration = round((time.time() - t0) * 1000, 2)
        pipeline_stages.append(PipelineStage(
            stage="claim_extraction",
            status="COMPLETED",
            duration_ms=stage_duration,
            details={"primary_claim": claim_info.primary_claim, "entities": claim_info.entities}
        ))

        # STAGE 3: Search Query Generation (Groq / Instant Cached)
        t0 = time.time()
        cached = getattr(claim_info, "_cached_queries", None)
        queries = cached if cached else self.query_generator.generate_queries(claim_info)

        # Explicitly target verified newsrooms (Times of India, Indian Express, The Hindu, NDTV, News18, CNN)
        search_queries = list(queries)
        if claim_info.entities:
            top_entity = claim_info.entities[0]
            search_queries.append(f"{top_entity} Times of India OR Indian Express OR The Hindu")
            search_queries.append(f"{top_entity} NDTV OR News18 OR CNN")

        stage_duration = round((time.time() - t0) * 1000, 2)
        pipeline_stages.append(PipelineStage(
            stage="query_generation",
            status="COMPLETED",
            duration_ms=stage_duration,
            details={"generated_queries": queries}
        ))

        # STAGE 4: Multi-Provider Concurrent Search (Google News + NewsAPI)
        t0 = time.time()
        raw_articles = []

        # Include submitted article as verified reference document
        if extracted_article and extracted_article.title and len(extracted_article.content) >= 30:
            raw_articles.append({
                "title": extracted_article.title,
                "url": request.url,
                "source_name": extracted_article.publisher or "Submitted Article",
                "author": extracted_article.author,
                "published_at": extracted_article.published_date,
                "content": f"{extracted_article.title}. {extracted_article.content[:800]}",
                "description": extracted_article.title,
                "search_provider": "submitted_url",
                "matched_query": "direct_input"
            })

        import asyncio
        newsapi_task = asyncio.create_task(self.newsapi_service.search(search_queries))
        serpapi_task = asyncio.create_task(self.serpapi_service.search_google_news(search_queries))

        newsapi_res, serpapi_res = await asyncio.gather(newsapi_task, serpapi_task, return_exceptions=True)

        if isinstance(newsapi_res, list):
            raw_articles.extend(newsapi_res)
        else:
            logger.warning(f"NewsAPI task returned error: {newsapi_res}")

        if isinstance(serpapi_res, list):
            raw_articles.extend(serpapi_res)
        else:
            logger.warning(f"SerpAPI task returned error: {serpapi_res}")

        stage_duration = round((time.time() - t0) * 1000, 2)
        pipeline_stages.append(PipelineStage(
            stage="multi_source_search",
            status="COMPLETED",
            duration_ms=stage_duration,
            details={"raw_sources_found": len(raw_articles)}
        ))

        # STAGE 5: Normalization & Deduplication
        t0 = time.time()
        normalized_articles = self.source_normalizer.normalize_and_deduplicate(raw_articles)
        stage_duration = round((time.time() - t0) * 1000, 2)
        pipeline_stages.append(PipelineStage(
            stage="normalization_and_deduplication",
            status="COMPLETED",
            duration_ms=stage_duration,
            details={"unique_articles": len(normalized_articles)}
        ))

        # STAGE 6: Semantic Vector Indexing & Retrieval
        t0 = time.time()
        self.vector_service.index_evidence(verification_id, normalized_articles)
        retrieved_evidence = self.vector_service.retrieve_relevant_evidence(
            query_text=claim_info.primary_claim,
            verification_id=verification_id,
            top_k=settings.TOP_K_EVIDENCE
        )
        stage_duration = round((time.time() - t0) * 1000, 2)
        pipeline_stages.append(PipelineStage(
            stage="semantic_vector_retrieval",
            status="COMPLETED",
            duration_ms=stage_duration,
            details={"top_k_retrieved": len(retrieved_evidence)}
        ))

        # STAGE 7: Evidence Stance Analysis (Groq)
        t0 = time.time()
        analyzed_sources = self.evidence_analyzer.analyze_evidence_sources(claim_info, retrieved_evidence)
        stage_duration = round((time.time() - t0) * 1000, 2)
        pipeline_stages.append(PipelineStage(
            stage="evidence_stance_analysis",
            status="COMPLETED",
            duration_ms=stage_duration,
            details={"analyzed_count": len(analyzed_sources)}
        ))

        # STAGE 8: Verdict Synthesis & Explanation (Groq)
        t0 = time.time()
        total_time_ms = round((time.time() - pipeline_start) * 1000, 2)

        verdict_response = self.verdict_generator.synthesize_verdict(
            claim_info=claim_info,
            analyzed_sources=analyzed_sources,
            pipeline_stages=pipeline_stages,
            processing_time_ms=total_time_ms
        )

        stage_duration = round((time.time() - t0) * 1000, 2)
        pipeline_stages.append(PipelineStage(
            stage="verdict_synthesis",
            status="COMPLETED",
            duration_ms=stage_duration,
            details={"verdict": verdict_response.verdict.value, "confidence": verdict_response.confidence}
        ))

        # Update final elapsed time
        verdict_response.processing_time_ms = round((time.time() - pipeline_start) * 1000, 2)
        logger.info(
            f"[{verification_id}] Completed verification: verdict={verdict_response.verdict.value} "
            f"confidence={verdict_response.confidence}% ({verdict_response.processing_time_ms}ms)"
        )
        return verdict_response
