import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    display_name: str = Field(min_length=2, max_length=80)
    intro: str = Field(min_length=20, max_length=1200)

    @field_validator("display_name", "intro", mode="before")
    @classmethod
    def strip_profile_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ProfileUpdate(BaseModel):
    display_name: str = Field(min_length=2, max_length=80)
    intro: str = Field(min_length=20, max_length=1200)

    @field_validator("display_name", "intro", mode="before")
    @classmethod
    def strip_profile_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: EmailStr
    display_name: str
    intro: str
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
