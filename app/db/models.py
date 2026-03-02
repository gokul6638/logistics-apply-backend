from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from app.db.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)

    # Optional external id from ATS/platform
    external_id = Column(String, nullable=True, index=True)

    title = Column(String, nullable=False, index=True)
    company = Column(String, nullable=False, index=True)
    location = Column(String, nullable=False, index=True)
    source = Column(String, nullable=False, index=True)

    url = Column(String, unique=True, nullable=False, index=True)

    # Keep as string in DB for now if you want easier ingestion,
    # but you can change to DateTime later.
    posted_date = Column(String, nullable=True)

    hr_email = Column(String, nullable=True)
    recruiter_linkedin = Column(String, nullable=True)

    match_score = Column(Integer, default=0)

    saved = Column(Boolean, default=False, nullable=False)
    applied = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class Settings(Base):
    """
    Single-row settings table (id=1).
    """
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)  # will use 1

    country = Column(String(2), default="us", nullable=False)  # NEW

    location = Column(String, default="Kansas City, MO", nullable=False)

    keywords = Column(
        Text,
        default="export coordinator,logistics coordinator,supply chain,import export,freight,shipping coordinator,logistics assistant",
        nullable=False,
    )

    exclude_keywords = Column(
        Text,
        default="manager,senior,director,lead",
        nullable=False,
    )

    enabled_sources = Column(Text, default="google_jobs,greenhouse,lever", nullable=False)
    daily_email_enabled = Column(Boolean, default=False, nullable=False)
    email_recipient = Column(String, nullable=True)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
