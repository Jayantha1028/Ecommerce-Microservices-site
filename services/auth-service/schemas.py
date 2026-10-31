"""Pydantic Request & Response Schemas for Auth Service."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    """Payload for user account registration."""
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    """Payload for user login authentication."""
    email: EmailStr
    password: str


class VerifyEmailIn(BaseModel):
    """Payload for verifying an email address with a 6-digit one-time code."""
    email: EmailStr
    code: str = Field(min_length=5, max_length=10)


class TokenIn(BaseModel):
    """Payload for JWT token introspection / verification."""
    token: str


class UserProfileIn(BaseModel):
    """Payload for creating a customer user profile."""
    authUserId: str
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=30)
    address: Optional[str] = Field(default=None, max_length=255)


class UpdateProfileIn(BaseModel):
    """Payload for updating user profile and credentials."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    address: Optional[str] = Field(default=None, max_length=255)
    current_password: Optional[str] = Field(default=None, max_length=128)
    new_password: Optional[str] = Field(default=None, min_length=8, max_length=128)
