"""
RAG Pipeline Analysis Routes  (Steps 1-13)
Endpoints: /rag-analyze-url  /rag-analyze-text  /rag-health  /rag-metrics
"""

import time
import logging
from flask import Blueprint, request, jsonify
from flask_login import current_user

from config import Config
from services.rag_pipeline import RAGPipeline
from services.extractor import ContentExtractor, ArticleContent
from services.security import security_validator
from services.error_handler import error_handler, ErrorType
from services.logger import performance_logger
from routes.history import save_user_analysis

logger = logging.getLogger("fake_news_detector.rag_route")

rag_analyze_bp = Blueprint("rag_analyze", __name__)

# ── Singleton pipeline ──────────────────────────────────────────────────────
_rag_pipeline: RAGPipeline = None


def get_rag_pipeline() -> RAGPipeline:
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline(
            groq_api_key=Config.GROQ_API_KEY,
            news_api_key=Config.NEWS_API_KEY,
            serpapi_key=Config.SERPAPI_KEY,
        )
    return _rag_pipeline


def _sec(response):
    for k, v in security_validator.get_security_headers().items():
        response.headers[k] = v
    return response


# ── /rag-analyze-url ────────────────────────────────────────────────────────

@rag_analyze_bp.route("/rag-analyze-url", methods=["POST"])
def rag_analyze_url():
    """
    STEP 1-13 pipeline triggered from a URL.

    Request  : { "url": "https://..." }
    Response : STEP 12 JSON schema
    """
    t0 = time.time()
    perf_id = performance_logger.start_analysis("rag_url")

    try:
        data = request.get_json()
        if not data:
            return error_handler.create_error_response(
                ValueError("Missing JSON payload"), ErrorType.VALIDATION_ERROR,
                perf_id, processing_time=time.time() - t0)

        vr = security_validator.validate_json_input(data)
        if not vr["valid"]:
            return error_handler.create_error_response(
                ValueError("; ".join(vr["errors"])), ErrorType.VALIDATION_ERROR,
                perf_id, processing_time=time.time() - t0)

        url = vr["sanitized_data"]["url"]
        logger.info(f"[{perf_id}] RAG URL analysis: {url}")

        extractor = ContentExtractor(timeout=Config.REQUEST_TIMEOUT)
        try:
            article = extractor.extract_content(url)
        except ValueError as e:
            return error_handler.create_error_response(
                e, ErrorType.VALIDATION_ERROR, perf_id,
                {"step": "content_extraction"}, processing_time=time.time() - t0)

        pipeline = get_rag_pipeline()
        result   = pipeline.analyze(article)
        payload  = pipeline.to_json(result)

        # Save to user history
        if current_user.is_authenticated:
            try:
                save_user_analysis(
                    user_id=current_user.id,
                    input_type="url",
                    input_content=url,
                    verdict=result.verdict,
                    confidence=result.confidence / 100,
                    explanation=result.final_explanation,
                    matched_articles_count=(len(result.news_api_evidence) +
                                            len(result.rag_evidence)),
                    processing_time=result.processing_time,
                )
            except Exception as e:
                logger.warning(f"History save failed: {e}")

        performance_logger.complete_analysis(
            perf_id, result.verdict, result.confidence / 100, result.processing_time)

        return _sec(jsonify(payload))

    except Exception as e:
        ms = time.time() - t0
        performance_logger.complete_analysis(perf_id, "ERROR", 0, ms, str(e))
        return error_handler.create_error_response(
            e, ErrorType.INTERNAL_ERROR, perf_id,
            {"step": "rag_pipeline"}, "RAG pipeline failed", ms)


# ── /rag-analyze-text ───────────────────────────────────────────────────────

@rag_analyze_bp.route("/rag-analyze-text", methods=["POST"])
def rag_analyze_text():
    """
    STEP 1-13 pipeline triggered from raw text.

    Request  : { "text": "..." }
    Response : STEP 12 JSON schema
    """
    t0 = time.time()
    perf_id = performance_logger.start_analysis("rag_text")

    try:
        data = request.get_json()
        if not data or "text" not in data:
            return error_handler.create_error_response(
                ValueError("Missing 'text' field"), ErrorType.VALIDATION_ERROR,
                perf_id, processing_time=time.time() - t0)

        text = data["text"].strip()
        if not text:
            return error_handler.create_error_response(
                ValueError("Text cannot be empty"), ErrorType.VALIDATION_ERROR,
                perf_id, processing_time=time.time() - t0)
        if len(text) < 50:
            return error_handler.create_error_response(
                ValueError("Text too short (min 50 chars)"), ErrorType.VALIDATION_ERROR,
                perf_id, processing_time=time.time() - t0)

        title   = text.split("\n")[0][:200]
        article = ArticleContent(title=title, content=text, url="", source="")

        pipeline = get_rag_pipeline()
        result   = pipeline.analyze(article)
        payload  = pipeline.to_json(result)

        if current_user.is_authenticated:
            try:
                save_user_analysis(
                    user_id=current_user.id,
                    input_type="text",
                    input_content=text[:500],
                    verdict=result.verdict,
                    confidence=result.confidence / 100,
                    explanation=result.final_explanation,
                    matched_articles_count=(len(result.news_api_evidence) +
                                            len(result.rag_evidence)),
                    processing_time=result.processing_time,
                )
            except Exception as e:
                logger.warning(f"History save failed: {e}")

        performance_logger.complete_analysis(
            perf_id, result.verdict, result.confidence / 100, result.processing_time)

        return _sec(jsonify(payload))

    except Exception as e:
        ms = time.time() - t0
        performance_logger.complete_analysis(perf_id, "ERROR", 0, ms, str(e))
        return error_handler.create_error_response(
            e, ErrorType.INTERNAL_ERROR, perf_id,
            {"step": "rag_pipeline"}, "RAG pipeline failed", ms)


# ── /rag-health ─────────────────────────────────────────────────────────────

@rag_analyze_bp.route("/rag-health", methods=["GET"])
def rag_health():
    try:
        p = get_rag_pipeline()
        return jsonify({
            "status":   "healthy",
            "pipeline": "RAG Pipeline v2.0 (13-step)",
            "components": {
                "groq_llm":          p.groq_client        is not None,
                "news_api":          p.news_fetcher        is not None,
                "vector_db":         p.similarity_engine   is not None,
                "keyword_extractor": p.keyword_extractor   is not None,
            },
        })
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


# ── /rag-metrics ─────────────────────────────────────────────────────────────

@rag_analyze_bp.route("/rag-metrics", methods=["GET"])
def rag_metrics():
    """Return aggregate metrics from the rag_metrics table."""
    try:
        from models.rag_analysis_log import RAGAnalysisLog, RAGMetrics as RMet
        from models.user import db
        from sqlalchemy import func

        total = db.session.query(func.count(RAGAnalysisLog.id)).scalar() or 0
        avg_lat = db.session.query(func.avg(RMet.latency_ms)).scalar() or 0
        avg_acc = db.session.query(func.avg(RMet.retrieval_accuracy)).scalar() or 0
        avg_cov = db.session.query(func.avg(RMet.evidence_coverage)).scalar() or 0
        avg_conf= db.session.query(func.avg(RMet.confidence_score)).scalar() or 0

        verdict_rows = db.session.query(
            RAGAnalysisLog.verdict,
            func.count(RAGAnalysisLog.id)
        ).group_by(RAGAnalysisLog.verdict).all()

        return jsonify({
            "total_analyses":       total,
            "avg_latency_ms":       round(avg_lat, 1),
            "avg_retrieval_accuracy": round(avg_acc, 4),
            "avg_evidence_coverage":  round(avg_cov, 2),
            "avg_confidence":         round(avg_conf, 2),
            "verdict_distribution":   {v: c for v, c in verdict_rows},
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
