"""
Verification History Service
Manages storing, retrieving, paginating, and deleting user verification records.
"""

import logging
import math
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from backend.db.models import VerificationHistory, User
from backend.schemas.verification import VerificationResponse
from backend.schemas.history import HistoryItem, HistoryList, HistoryDetail

logger = logging.getLogger("news_verification.history_service")


class HistoryService:
    def record_verification(
        self,
        db: Session,
        user_id: int,
        input_type: str,
        input_content: str,
        response: VerificationResponse,
        verification_id: str
    ) -> VerificationHistory:
        """Save a verification run to the database linked to user_id"""
        try:
            history_record = VerificationHistory(
                user_id=user_id,
                verification_id=verification_id,
                input_type=input_type,
                input_content=input_content,
                verdict=response.verdict.value,
                confidence=response.confidence,
                primary_claim=response.claim.primary_claim,
                summary=response.summary,
                explanation=response.explanation,
                evidence_summary_json=response.evidence_summary.model_dump(),
                sources_json=[s.model_dump() for s in response.sources],
                pipeline_stages_json=[p.model_dump() for p in response.pipeline_stages],
                limitations_json=response.limitations,
                source_agreement_percentage=response.source_agreement_percentage,
                processing_time_ms=response.processing_time_ms
            )
            db.add(history_record)
            db.commit()
            db.refresh(history_record)
            logger.info(f"Recorded verification {history_record.id} for user {user_id}")
            return history_record
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to record verification history: {e}")
            raise

    def get_user_history(
        self,
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
        verdict_filter: Optional[str] = None
    ) -> HistoryList:
        """Fetch paginated history items for a user"""
        query = db.query(VerificationHistory).filter(VerificationHistory.user_id == user_id)

        if verdict_filter and verdict_filter.upper() != "ALL":
            query = query.filter(VerificationHistory.verdict == verdict_filter.upper())

        total = query.count()
        total_pages = max(1, math.ceil(total / page_size))
        page = max(1, min(page, total_pages)) if total > 0 else 1

        records = query.order_by(desc(VerificationHistory.created_at))\
                       .offset((page - 1) * page_size)\
                       .limit(page_size)\
                       .all()

        items = []
        for r in records:
            total_src = 0
            if r.evidence_summary_json and isinstance(r.evidence_summary_json, dict):
                total_src = r.evidence_summary_json.get("total_sources_evaluated", 0)
            elif r.sources_json and isinstance(r.sources_json, list):
                total_src = len(r.sources_json)

            items.append(HistoryItem(
                id=r.id,
                verification_id=r.verification_id,
                input_type=r.input_type,
                input_content=r.input_content,
                verdict=r.verdict,
                confidence=r.confidence,
                primary_claim=r.primary_claim,
                summary=r.summary,
                source_agreement_percentage=r.source_agreement_percentage or 0.0,
                total_sources=total_src,
                processing_time_ms=r.processing_time_ms or 0.0,
                created_at=r.created_at
            ))

        return HistoryList(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    def get_history_detail(self, db: Session, history_id: int, user_id: int) -> Optional[HistoryDetail]:
        """Fetch full evidence verification detail by ID"""
        record = db.query(VerificationHistory).filter(
            VerificationHistory.id == history_id,
            VerificationHistory.user_id == user_id
        ).first()

        if not record:
            return None

        # Reconstruct claim info
        claim_info = {
            "primary_claim": record.primary_claim,
            "secondary_claims": [],
            "entities": [],
            "timeframe": None
        }

        return HistoryDetail(
            id=record.id,
            verification_id=record.verification_id,
            input_type=record.input_type,
            input_content=record.input_content,
            verdict=record.verdict,
            confidence=record.confidence,
            confidence_label="Verification Confidence",
            claim=claim_info,
            summary=record.summary or "",
            explanation=record.explanation or "",
            evidence_summary=record.evidence_summary_json or {},
            sources=record.sources_json or [],
            source_agreement_percentage=record.source_agreement_percentage or 0.0,
            limitations=record.limitations_json or [],
            pipeline_stages=record.pipeline_stages_json or [],
            processing_time_ms=record.processing_time_ms or 0.0,
            created_at=record.created_at
        )

    def delete_history_item(self, db: Session, history_id: int, user_id: int) -> bool:
        """Delete a single history entry"""
        record = db.query(VerificationHistory).filter(
            VerificationHistory.id == history_id,
            VerificationHistory.user_id == user_id
        ).first()

        if not record:
            return False

        db.delete(record)
        db.commit()
        return True

    def clear_all_history(self, db: Session, user_id: int) -> int:
        """Clear all verification records for a user"""
        deleted_count = db.query(VerificationHistory).filter(
            VerificationHistory.user_id == user_id
        ).delete()
        db.commit()
        return deleted_count

    def get_user_stats(self, db: Session, user_id: int) -> Tuple[int, Dict[str, int]]:
        """Get total verification count and verdict breakdown for user"""
        total = db.query(func.count(VerificationHistory.id)).filter(
            VerificationHistory.user_id == user_id
        ).scalar() or 0

        verdict_counts = db.query(
            VerificationHistory.verdict,
            func.count(VerificationHistory.id)
        ).filter(
            VerificationHistory.user_id == user_id
        ).group_by(VerificationHistory.verdict).all()

        stats = {"REAL": 0, "FALSE": 0, "MISLEADING": 0, "UNVERIFIED": 0}
        for v, c in verdict_counts:
            if v in stats:
                stats[v] = c

        return total, stats
