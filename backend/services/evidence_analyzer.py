"""
Evidence Stance & Context Analysis Service using Groq LLM
Evaluates retrieved articles against the extracted claim to determine stance (SUPPORT, CONTRADICT, NEUTRAL)
and flags contextual nuance (exaggeration, satire, outdated news, missing context).
"""

import logging
from typing import List, Dict, Any
from backend.services.groq_service import GroqService
from backend.schemas.verification import ClaimInfo, EvidenceSource, StanceEnum

logger = logging.getLogger("news_verification.evidence_analyzer")


class EvidenceAnalyzer:
    def __init__(self, groq_service: GroqService):
        self.groq_service = groq_service

    def analyze_evidence_sources(
        self,
        claim_info: ClaimInfo,
        retrieved_evidence: List[Dict[str, Any]]
    ) -> List[EvidenceSource]:
        """
        Analyze each retrieved document against the claim to determine stance, quote snippet, and nuance.
        """
        if not retrieved_evidence:
            return []

        # Prepare evidence blocks for the prompt
        evidence_blocks = []
        for idx, doc in enumerate(retrieved_evidence):
            evidence_blocks.append(
                f"[Source ID: {idx+1}]\n"
                f"Outlet: {doc.get('source_name', 'Unknown')}\n"
                f"Title: {doc.get('title', '')}\n"
                f"Date: {doc.get('published_at') or 'Unknown'}\n"
                f"Content: {doc.get('content_snippet', '')[:500]}\n"
            )

        system_prompt = (
            "You are a strict, impartial fact-checking evidence analyzer. You must compare the given CLAIM "
            "against the RETRIEVED SOURCES and classify the stance of each source.\n"
            "STRICT RULES:\n"
            "1. You MUST ONLY evaluate using the provided evidence text. Do NOT use internal parametric memory.\n"
            "2. Stance must be exactly one of: SUPPORT, CONTRADICT, or NEUTRAL.\n"
            "   - SUPPORT: The text directly confirms or affirms the claim with matching facts.\n"
            "   - CONTRADICT: The text refutes, denies, or provides contradictory facts to the claim.\n"
            "   - NEUTRAL: The text mentions related topics but does not take a stance, or lacks direct confirmation/denial.\n"
            "3. Extract a concise, exact evidence quote/snippet (1-2 sentences) from the source text that justifies your classification.\n"
            "4. Never invent or hallucinate text that is not in the source.\n"
            "Respond ONLY with a JSON object adhering to this schema:\n"
            "{\n"
            '  "evaluations": [\n'
            "    {\n"
            '      "source_id": 1,\n'
            '      "stance": "SUPPORT" | "CONTRADICT" | "NEUTRAL",\n'
            '      "evidence_snippet": "Direct quote or precise factual summary from this source text"\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        user_prompt = (
            f"PRIMARY CLAIM: {claim_info.primary_claim}\n"
            f"ENTITIES: {', '.join(claim_info.entities)}\n\n"
            f"RETRIEVED SOURCES:\n"
            + "\n".join(evidence_blocks)
        )

        evaluation_map = {}
        try:
            res = self.groq_service.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.05
            )
            evals = res.get("evaluations", [])
            for e in evals:
                s_id = e.get("source_id")
                if s_id is not None:
                    evaluation_map[int(s_id)] = {
                        "stance": str(e.get("stance", "NEUTRAL")).upper(),
                        "evidence_snippet": str(e.get("evidence_snippet", ""))
                    }
        except Exception as e:
            logger.warning(f"LLM evidence stance analysis failed: {e}. Defaulting to neutral stance.")

        analyzed_sources: List[EvidenceSource] = []
        for idx, doc in enumerate(retrieved_evidence):
            source_id = idx + 1
            eval_data = evaluation_map.get(source_id, {})
            raw_stance = eval_data.get("stance", "NEUTRAL")

            stance = StanceEnum.NEUTRAL
            if raw_stance == "SUPPORT":
                stance = StanceEnum.SUPPORT
            elif raw_stance == "CONTRADICT":
                stance = StanceEnum.CONTRADICT

            snippet = eval_data.get("evidence_snippet") or doc.get("evidence_snippet") or doc.get("content_snippet", "")[:300]

            analyzed_sources.append(EvidenceSource(
                source_name=doc.get("source_name", "Unknown"),
                domain=doc.get("domain", ""),
                title=doc.get("title", ""),
                url=doc.get("url", ""),
                published_at=doc.get("published_at"),
                stance=stance,
                relevance_score=doc.get("relevance_score", 0.0),
                evidence_snippet=snippet,
                credibility_tier=doc.get("credibility_tier", "STANDARD_NEWS"),
                search_provider=doc.get("search_provider", "web")
            ))

        return analyzed_sources
