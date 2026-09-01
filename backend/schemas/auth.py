"""
Pydantic Schemas for Authentication and User Profile
"""

import re
from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'


class UserRegister(BaseModel):
    email: str = Field(description="Valid email address")
    password: str = Field(min_length=6, description="Password must be at least 6 characters")
    full_name: str = Field(min_length=2, max_length=100, description="Full name of user")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(EMAIL_REGEX, clean):
            raise ValueError("Please provide a valid email address.")
        return clean


class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.strip().lower()


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    current_password: Optional[str] = None
    new_password: Optional[str] = Field(default=None, min_length=6)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    total_verifications: int = 0
    verdict_stats: Dict[str, int] = Field(default_factory=lambda: {
        "REAL": 0, "FALSE": 0, "MISLEADING": 0, "UNVERIFIED": 0
    })


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
