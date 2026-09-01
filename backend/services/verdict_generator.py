"""
Verdict Synthesis & Final Explanation Generation Service using Groq LLM
Determines final verdict (REAL, FALSE, MISLEADING, UNVERIFIED), computes verification confidence,
and generates concise evidence-grounded explanations.
"""

import logging
from typing import List, Dict, Any, Tuple
from backend.services.groq_service import GroqService
from backend.schemas.verification import (
    ClaimInfo, EvidenceSource, VerdictEnum, StanceEnum,
    EvidenceSummary, VerificationResponse, PipelineStage
)

logger = logging.getLogger("news_verification.verdict_generator")


class VerdictGenerator:
    def __init__(self, groq_service: GroqService):
        self.groq_service = groq_service

    def synthesize_verdict(
        self,
        claim_info: ClaimInfo,
        analyzed_sources: List[EvidenceSource],
        pipeline_stages: List[PipelineStage],
        processing_time_ms: float
    ) -> VerificationResponse:
        """
        Synthesizes the overall verification verdict, confidence, and explanation based on retrieved evidence.
        """
        # Calculate stance counts
        supporting = [s for s in analyzed_sources if s.stance == StanceEnum.SUPPORT]
        contradicting = [s for s in analyzed_sources if s.stance == StanceEnum.CONTRADICT]
        neutral = [s for s in analyzed_sources if s.stance == StanceEnum.NEUTRAL]

        total_sources = len(analyzed_sources)
        support_count = len(supporting)
        contradict_count = len(contradicting)
        neutral_count = len(neutral)

        evidence_summary = EvidenceSummary(
            supporting=support_count,
            contradicting=contradict_count,
            neutral=neutral_count,
            total_sources_evaluated=total_sources
        )

        # Calculate agreement percentage
        decisive_count = support_count + contradict_count
        if decisive_count > 0:
            agreement_pct = round((max(support_count, contradict_count) / decisive_count) * 100.0, 1)
        else:
            agreement_pct = 0.0

        # Handle zero or low evidence case cleanly
        if total_sources == 0:
            return VerificationResponse(
                verdict=VerdictEnum.UNVERIFIED,
                confidence=40,
                confidence_label="Verification Confidence",
                claim=claim_info,
                summary="Insufficient external evidence was retrieved to verify this claim.",
                explanation=(
                    "No matching authoritative reports or fact-checks were found across the connected "
                    "news and search providers for this specific claim. This frequently occurs for obscure claims, "
                    "very recent rumors, or unindexed topics."
                ),
                evidence_summary=evidence_summary,
                sources=[],
                source_agreement_percentage=0.0,
                limitations=[
                    "No authoritative reporting retrieved from NewsAPI or SerpAPI.",
                    "Verify directly through primary institutional channels or official government press releases."
                ],
                pipeline_stages=pipeline_stages,
                processing_time_ms=processing_time_ms
            )

        # Build summary of sources for LLM reasoning prompt
        evidence_descriptions = []
        for s in analyzed_sources:
            evidence_descriptions.append(
                f"- Source: {s.source_name} ({s.domain})\n"
                f"  Headline: {s.title}\n"
                f"  Stance: {s.stance.value}\n"
                f"  Evidence Snippet: \"{s.evidence_snippet}\"\n"
                f"  Credibility Tier: {s.credibility_tier}"
            )

        system_prompt = (
            "You are the Chief Fact-Checking Officer. Your job is to evaluate the evidence provided by multiple "
            "news sources and deliver a definitive verification verdict and transparent explanation.\n\n"
            "ALLOWED VERDICTS:\n"
            "- REAL: Multiple reputable sources confirm and support the central factual claim.\n"
            "- FALSE: Authoritative evidence directly contradicts or debunks the central claim.\n"
            "- MISLEADING: The claim contains partial truth but has missing context, exaggerates details, or frames old events as new.\n"
            "- UNVERIFIED: Retrieved evidence is insufficient, contradictory with equal weight, or entirely neutral.\n\n"
            "STRICT RULES:\n"
            "1. Base your verdict ONLY on the provided retrieved sources.\n"
            "2. Never use internal parametric memory or hallucinate events/urls/dates.\n"
            "3. If evidence is ambiguous, inconclusive, or absent, assign UNVERIFIED.\n"
            "4. Do NOT output chain of thought or reasoning scratchpads. Provide only the concise explanation and summary.\n"
            "Respond ONLY with a JSON object adhering to this schema:\n"
            "{\n"
            '  "verdict": "REAL" | "FALSE" | "MISLEADING" | "UNVERIFIED",\n'
            '  "summary": "1-2 sentence core finding",\n'
            '  "explanation": "Clear, objective explanation highlighting which sources support/contradict the claim and why",\n'
            '  "limitations": ["Any notable limits, e.g. language scope, breaking nature of story"]\n'
            "}"
        )

        user_prompt = (
            f"PRIMARY CLAIM: {claim_info.primary_claim}\n"
            f"SECONDARY CLAIMS: {', '.join(claim_info.secondary_claims) if claim_info.secondary_claims else 'None'}\n\n"
            f"RETRIEVED EVIDENCE SOURCES ({total_sources} evaluated):\n"
            + "\n".join(evidence_descriptions)
        )

        try:
            llm_result = self.groq_service.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.05
            )

            raw_verdict = str(llm_result.get("verdict", "UNVERIFIED")).upper().strip()
            if raw_verdict not in [v.value for v in VerdictEnum]:
                raw_verdict = "UNVERIFIED"
            verdict = VerdictEnum(raw_verdict)

            summary = llm_result.get("summary", "").strip() or f"Verification completed with verdict: {verdict.value}."
            explanation = llm_result.get("explanation", "").strip() or "Evidence evaluated across retrieved news sources."
            limitations = [str(lim).strip() for lim in llm_result.get("limitations", []) if isinstance(lim, str) and lim.strip()]

            # Verification Confidence Computation (0-100)
            # Factors: Decisive source count, stance agreement ratio, average relevance
            avg_relevance = sum(s.relevance_score for s in analyzed_sources) / max(total_sources, 1)

            if verdict == VerdictEnum.UNVERIFIED:
                confidence = int(max(30, min(65, 40 + (neutral_count * 5))))
            else:
                base = 60
                source_boost = min(decisive_count * 7, 25)
                agreement_boost = int((agreement_pct / 100.0) * 15)
                confidence = int(min(98, max(50, base + source_boost + agreement_boost)))

            if not limitations:
                limitations = [
                    "Analysis based on retrieved English-language articles available at time of query.",
                    "Live breaking news may evolve as additional reports are published."
                ]

            return VerificationResponse(
                verdict=verdict,
                confidence=confidence,
                confidence_label="Verification Confidence",
                claim=claim_info,
                summary=summary,
                explanation=explanation,
                evidence_summary=evidence_summary,
                sources=analyzed_sources,
                source_agreement_percentage=agreement_pct,
                limitations=limitations,
                pipeline_stages=pipeline_stages,
                processing_time_ms=processing_time_ms
            )

        except Exception as e:
            logger.error(f"LLM verdict synthesis error: {e}. Building rule-based fallback response.")

            # Rule-based fallback
            if support_count >= 2 and contradict_count == 0:
                fallback_verdict = VerdictEnum.REAL
                conf = 80
            elif contradict_count >= 1 and support_count == 0:
                fallback_verdict = VerdictEnum.FALSE
                conf = 85
            elif support_count >= 1 and contradict_count >= 1:
                fallback_verdict = VerdictEnum.MISLEADING
                conf = 70
            else:
                fallback_verdict = VerdictEnum.UNVERIFIED
                conf = 45

            return VerificationResponse(
                verdict=fallback_verdict,
                confidence=conf,
                confidence_label="Verification Confidence",
                claim=claim_info,
                summary=f"Analysis concluded with {fallback_verdict.value} based on source agreement.",
                explanation=f"Evaluated {total_sources} sources. Supporting: {support_count}, Contradicting: {contradict_count}, Neutral: {neutral_count}.",
                evidence_summary=evidence_summary,
                sources=analyzed_sources,
                source_agreement_percentage=agreement_pct,
                limitations=["Fallback rule synthesis applied."],
                pipeline_stages=pipeline_stages,
                processing_time_ms=processing_time_ms
            )
