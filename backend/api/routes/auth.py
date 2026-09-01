"""
Authentication API Routes: Register, Login, Profile & Password Management
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db.models import User
from backend.schemas.auth import UserRegister, UserLogin, UserUpdate, UserOut, Token
from backend.services.auth_service import AuthService
from backend.services.history_service import HistoryService
from backend.api.deps import get_db, get_auth_service, get_history_service, get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & User Profile"])


def _build_user_out(user: User, db: Session, history_service: HistoryService) -> UserOut:
    total, stats = history_service.get_user_stats(db, user.id)
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        total_verifications=total,
        verdict_stats=stats
    )


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account"
)
async def register_user(
    data: UserRegister,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    history_service: HistoryService = Depends(get_history_service)
) -> Token:
    clean_email = data.email.lower().strip()

    # Check for existing email
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists. Please log in."
        )

    # Hash password and create user
    hashed_pwd = auth_service.hash_password(data.password)
    new_user = User(
        email=clean_email,
        full_name=data.full_name.strip(),
        hashed_password=hashed_pwd,
        is_active=True,
        last_login_at=datetime.now(timezone.utc)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate token
    token = auth_service.create_access_token(new_user.id, new_user.email)
    user_out = _build_user_out(new_user, db, history_service)

    return Token(access_token=token, token_type="bearer", user=user_out)


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate and obtain JWT access token"
)
async def login_user(
    data: UserLogin,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    history_service: HistoryService = Depends(get_history_service)
) -> Token:
    clean_email = data.email.lower().strip()
    user = db.query(User).filter(User.email == clean_email).first()

    if not user or not auth_service.verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account has been disabled."
        )

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    token = auth_service.create_access_token(user.id, user.email)
    user_out = _build_user_out(user, db, history_service)

    return Token(access_token=token, token_type="bearer", user=user_out)


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current user details and verification statistics"
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    history_service: HistoryService = Depends(get_history_service)
) -> UserOut:
    return _build_user_out(current_user, db, history_service)


@router.put(
    "/me",
    response_model=UserOut,
    summary="Update current user profile and password"
)
async def update_user_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    history_service: HistoryService = Depends(get_history_service)
) -> UserOut:
    # Handle name change
    if data.full_name and data.full_name.strip():
        current_user.full_name = data.full_name.strip()

    # Handle password change
    if data.new_password:
        if not data.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is required to set a new password."
            )
        if not auth_service.verify_password(data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect."
            )
        current_user.hashed_password = auth_service.hash_password(data.new_password)

    db.commit()
    db.refresh(current_user)

    return _build_user_out(current_user, db, history_service)
