"""
Search Query Generator Service using Groq LLM
Formulates high-precision search queries across multiple angles to retrieve relevant news from NewsAPI & SerpAPI.
"""

import logging
import re
from typing import List
from backend.services.groq_service import GroqService
from backend.schemas.verification import ClaimInfo

logger = logging.getLogger("news_verification.query_generator")


class QueryGenerator:
    def __init__(self, groq_service: GroqService):
        self.groq_service = groq_service

    def generate_queries(self, claim_info: ClaimInfo) -> List[str]:
        """
        Generate 3-5 distinct search queries for news and web APIs.
        """
        system_prompt = (
            "You are a search query formulation expert for news verification. Given a news claim and entities, "
            "generate 3 to 5 targeted search query strings optimized for Google News and NewsAPI.\n"
            "Rules:\n"
            "- Queries should use concise keywords (3 to 6 words each), omitting conversational stop words.\n"
            "- Angle 1: Exact event/claim keywords.\n"
            "- Angle 2: Key entities + action.\n"
            "- Angle 3: Verification / official announcement terms (e.g. 'statement', 'clarification', 'official').\n"
            "Respond ONLY with a JSON object: {\"queries\": [\"query1\", \"query2\", \"query3\"]}"
        )

        user_prompt = (
            f"Primary Claim: {claim_info.primary_claim}\n"
            f"Key Entities: {', '.join(claim_info.entities)}\n"
            f"Timeframe: {claim_info.timeframe or 'Recent'}"
        )

        try:
            result = self.groq_service.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1
            )
            raw_queries = result.get("queries", [])
            valid_queries = [
                re.sub(r'["\']', '', q).strip() for q in raw_queries
                if isinstance(q, str) and len(q.strip()) > 3
            ]
            if valid_queries:
                logger.info(f"Generated {len(valid_queries)} search queries: {valid_queries}")
                return valid_queries[:5]
        except Exception as e:
            logger.warning(f"LLM query generation failed: {e}, falling back to rule-based queries")

        # Heuristic fallback
        stop_words = {"a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or", "is", "was", "are", "that", "this"}
        words = [w for w in re.findall(r'\b\w+\b', claim_info.primary_claim) if w.lower() not in stop_words]
        fallback_query = " ".join(words[:6])
        queries = [fallback_query]
        if claim_info.entities:
            queries.append(" ".join(claim_info.entities[:3]) + " news")
        return queries
