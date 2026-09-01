"""
Verification Route Handler: POST /api/v1/verify
Analyzes claims against real-time news and automatically records history for logged-in users.
"""

from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.db.models import User
from backend.schemas.verification import VerificationRequest, VerificationResponse
from backend.core.pipeline import VerificationPipeline
from backend.services.history_service import HistoryService
from backend.api.deps import (
    get_verification_pipeline, get_db, get_history_service, get_optional_current_user
)

router = APIRouter(prefix="/api/v1", tags=["Verification"])


@router.post(
    "/verify",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify a news URL or text claim",
    description=(
        "Analyzes a submitted news URL or text claim against real-time retrieved news sources, "
        "indexes and retrieves evidence via Qdrant semantic search, and evaluates claim support/contradiction "
        "using Groq LLM to return a transparent verdict (REAL, FALSE, MISLEADING, UNVERIFIED). "
        "If the user is authenticated via Bearer token, the verification is automatically saved to their history."
    )
)
async def verify_news_claim(
    request: VerificationRequest,
    pipeline: VerificationPipeline = Depends(get_verification_pipeline),
    db: Session = Depends(get_db),
    history_service: HistoryService = Depends(get_history_service),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> VerificationResponse:
    # 1. Execute verification pipeline
    response = await pipeline.verify(request)

    # 2. If user is logged in, automatically save to verification history
    if current_user:
        try:
            input_type = "url" if request.url else "text"
            input_content = request.url or request.text
            # Extract verification_id from pipeline stages if present
            verif_id = "v_" + str(response.processing_time_ms)
            for stage in response.pipeline_stages:
                if stage.details and "verification_id" in stage.details:
                    verif_id = stage.details["verification_id"]
                    break

            history_service.record_verification(
                db=db,
                user_id=current_user.id,
                input_type=input_type,
                input_content=input_content,
                response=response,
                verification_id=verif_id
            )
        except Exception as e:
            # History recording error shouldn't crash the verification response
            import logging
            logging.getLogger("news_verification.api").warning(f"Failed to record user history: {e}")

    return response
