from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ----------------
# Auth / Users
# ----------------

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ----------------
# Settings
# ----------------

class Settings(BaseModel):
    country: str = "us"
    location: str = "Kansas City, MO"
    keywords: str = "export coordinator,logistics coordinator,supply chain,import export,freight,shipping coordinator,logistics assistant"
    exclude_keywords: str = "manager,senior,director,lead"
    model_config = ConfigDict(from_attributes=True)

class SettingsUpdate(BaseModel):
    country: Optional[str] = None
    location: Optional[str] = None
    keywords: Optional[str] = None
    exclude_keywords: Optional[str] = None


# ----------------
# Jobs
# ----------------

class JobOut(BaseModel):
    # Internal DB uses snake_case; API returns camelCase to match your React
    id: int

    title: str
    company: str
    location: str
    source: str

    url: Optional[str] = None
    postedDate: Optional[str] = Field(default=None, alias="posted_date")

    hrEmail: Optional[str] = Field(default=None, alias="hr_email")
    recruiterLinkedin: Optional[str] = Field(default=None, alias="recruiter_linkedin")

    saved: bool = False
    applied: bool = False
    matchScore: Optional[int] = Field(default=None, alias="match_score")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class JobCreate(BaseModel):
    title: str
    company: str
    location: str
    source: str
    url: str
    posted_date: Optional[str] = None
    hr_email: Optional[str] = None
    recruiter_linkedin: Optional[str] = None
    match_score: int = 0
