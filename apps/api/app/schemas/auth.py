"""Authentication-related schemas."""

from pydantic import BaseModel, EmailStr, Field, field_validator


def _validate_bcrypt_password_bytes(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 UTF-8 bytes")
    return password


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    nickname: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        return _validate_bcrypt_password_bytes(value)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=72)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_bytes(cls, value: str) -> str:
        return _validate_bcrypt_password_bytes(value)
