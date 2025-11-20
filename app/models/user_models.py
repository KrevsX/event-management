from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ORGANIZER = "organizer"
    PARTICIPANT = "participant"


class UserBase(BaseModel):
    username: str
    email: str
    full_name: str
    role: UserRole = UserRole.PARTICIPANT


class UserCreate(UserBase):
    password: str

    @validator('role', pre=True)
    def validate_role(cls, v):
        if isinstance(v, UserRole):
            return v.value
        return v


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class SocialAuth(BaseModel):
    provider: str
    provider_id: str
    email: str
    full_name: str
    role: UserRole = UserRole.PARTICIPANT