"""
Verification History API Routes: List, Detail Replay, and Deletion
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.db.models import User
from backend.schemas.history import HistoryList, HistoryDetail
from backend.services.history_service import HistoryService
from backend.api.deps import get_db, get_history_service, get_current_user

router = APIRouter(prefix="/api/v1/history", tags=["Verification History"])


@router.get(
    "",
    response_model=HistoryList,
    summary="Get paginated verification history for authenticated user"
)
async def list_verification_history(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=50, description="Items per page"),
    verdict: Optional[str] = Query(default=None, description="Optional verdict filter: REAL, FALSE, MISLEADING, UNVERIFIED"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    history_service: HistoryService = Depends(get_history_service)
) -> HistoryList:
    return history_service.get_user_history(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        verdict_filter=verdict
    )


@router.get(
    "/{history_id}",
    response_model=HistoryDetail,
    summary="Get full evidence verification report for a past run"
)
async def get_history_detail(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    history_service: HistoryService = Depends(get_history_service)
) -> HistoryDetail:
    detail = history_service.get_history_detail(
        db=db,
        history_id=history_id,
        user_id=current_user.id
    )
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification history record not found."
        )
    return detail


@router.delete(
    "/{history_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a single verification history record"
)
async def delete_history_item(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    history_service: HistoryService = Depends(get_history_service)
):
    deleted = history_service.delete_history_item(
        db=db,
        history_id=history_id,
        user_id=current_user.id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification history record not found."
        )
    return None


@router.delete(
    "",
    summary="Clear all verification history for current user"
)
async def clear_all_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    history_service: HistoryService = Depends(get_history_service)
):
    count = history_service.clear_all_history(db=db, user_id=current_user.id)
    return {"message": f"Successfully cleared {count} verification history records."}
