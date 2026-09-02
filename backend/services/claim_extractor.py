"""
Claim Extraction Service using Groq LLM
Extracts central factual claims, sub-claims, entities, and timeframe from text/article.
"""

import logging
from typing import Dict, Any, List
from backend.services.groq_service import GroqService
from backend.schemas.verification import ClaimInfo

logger = logging.getLogger("news_verification.claim_extractor")


class ClaimExtractor:
    def __init__(self, groq_service: GroqService):
        self.groq_service = groq_service

    def extract_claims(self, text: str, title: str = "") -> ClaimInfo:
        """
        Extract primary claim, secondary claims, named entities, and timeframe.
        """
        clean_text = text[:4000].strip()
        if not clean_text:
            return ClaimInfo(primary_claim=title or "No content provided")

        system_prompt = (
            "You are a factual claim extraction and search formulation specialist. Your task is to analyze the provided news text, "
            "extract the core verifiable factual assertions, and generate 3 targeted search queries for news verification.\n"
            "Respond ONLY with a JSON object adhering to this schema:\n"
            "{\n"
            '  "primary_claim": "The single most central factual assertion made in the text",\n'
            '  "secondary_claims": ["Additional significant verifiable sub-claims if present"],\n'
            '  "entities": ["Named entities: people, organizations, locations, government bodies"],\n'
            '  "timeframe": "Reported date, event time, or \'Recent\' if not specified",\n'
            '  "search_queries": ["Query 1 with main subject + core action", "Query 2 with entities + event", "Query 3 with main subject + official report"]\n'
            "}\n"
            "RULES FOR QUERIES: Each query must be 3-5 concise words and MUST include the primary subject/person or location."
        )

        user_prompt = f"Headline/Title: {title}\n\nContent:\n{clean_text}"

        try:
            result = self.groq_service.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.05
            )

            primary_claim = result.get("primary_claim", "").strip() or title or clean_text.split("\n")[0][:150]
            secondary_claims = [c.strip() for c in result.get("secondary_claims", []) if isinstance(c, str) and c.strip()]
            entities = [e.strip() for e in result.get("entities", []) if isinstance(e, str) and e.strip()]
            timeframe = result.get("timeframe")
            raw_queries = result.get("search_queries", [])
            extracted_queries = [q.strip() for q in raw_queries if isinstance(q, str) and len(q.strip()) > 3]

            claim_info = ClaimInfo(
                primary_claim=primary_claim,
                secondary_claims=secondary_claims,
                entities=entities,
                timeframe=timeframe
            )
            # Store generated queries on claim_info if attribute exists, or return as metadata
            setattr(claim_info, "_cached_queries", extracted_queries)
            return claim_info
        except Exception as e:
            logger.warning(f"LLM claim extraction failed ({e}), using heuristic fallback")
            first_sentence = clean_text.split(".")[0].strip()
            return ClaimInfo(
                primary_claim=title or first_sentence[:200],
                secondary_claims=[],
                entities=[],
                timeframe="Recent"
            )
