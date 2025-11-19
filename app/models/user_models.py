from pydantic import BaseModel
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

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SocialAuth(BaseModel):
    provider: str
    provider_id: str
    email: str
    full_name: str
    role: UserRole = UserRole.PARTICIPANT