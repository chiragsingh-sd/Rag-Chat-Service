from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Payload used to create a user account."""

    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=128)]


class UserResponse(BaseModel):
    """Public user representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime


class TokenResponse(BaseModel):
    """OAuth2 bearer token response."""

    access_token: str
    token_type: Literal["bearer"]

