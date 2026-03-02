from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

import httpx
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ----------------
# Users / Auth
# ----------------
def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, username: str, password: str) -> models.User:
    hashed_password = pwd_context.hash(password)
    user = models.User(username=username, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ----------------
# Settings
# ----------------
def get_or_create_settings(db: Session) -> models.Settings:
    s = db.query(models.Settings).filter(models.Settings.id == 1).first()
    if s:
        return s
    s = models.Settings(id=1, country="us")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def update_settings(db: Session, payload: schemas.SettingsUpdate) -> models.Settings:
    s = get_or_create_settings(db)

    if payload.country is not None:
        s.country = payload.country.strip().lower()

    if payload.location is not None:
        s.location = payload.location
    if payload.keywords is not None:
        s.keywords = payload.keywords
    if payload.exclude_keywords is not None:
        s.exclude_keywords = payload.exclude_keywords

    db.add(s)
    db.commit()
    db.refresh(s)
    return s


# ----------------
# Jobs
# ----------------
def get_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 200,
    posted_within: Optional[str] = None,  # "24h" | "1d" | "1w" | None
) -> list[models.Job]:
    query = db.query(models.Job)

    if posted_within:
        now = datetime.utcnow()
        cutoff: Optional[datetime] = None

        if posted_within == "24h":
            cutoff = now - timedelta(hours=24)
        elif posted_within == "1d":
            cutoff = now - timedelta(days=1)
        elif posted_within == "1w":
            cutoff = now - timedelta(weeks=1)

        if cutoff is not None:
            query = query.filter(models.Job.created_at >= cutoff)

    return (
        query.order_by(models.Job.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_job(db: Session, job: schemas.JobCreate) -> models.Job:
    data = job.model_dump() if hasattr(job, "model_dump") else job.dict()
    db_job = models.Job(**data)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def toggle_save(db: Session, job_id: int) -> Optional[models.Job]:
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        return None
    job.saved = not bool(job.saved)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def mark_applied(db: Session, job_id: int) -> Optional[models.Job]:
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        return None
    job.applied = True
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


# ----------------
# Fetch trigger (JSearch)
# ----------------
def fetch_jobs_now(db: Session):
    """
    Fetch jobs from OpenWebNinja JSearch and store them in models.Job.
    Dedup: first by url (if present), else by (title, company, location).
    Exclude: keywords in settings.exclude_keywords (CSV), defaults to manager/senior/director/lead.
    """
    api_key = os.getenv("OPENWEBNINJA_API_KEY")
    base_url = os.getenv("JSEARCH_BASE_URL", "https://api.openwebninja.com/jsearch")

    if not api_key:
        return {"status": "error", "message": "OPENWEBNINJA_API_KEY missing in environment/.env"}

    settings = get_or_create_settings(db)
    query = (settings.keywords or "").strip()
    if not query:
        return {"status": "error", "message": "Settings.keywords is empty. Update PUT /settings first."}

    exclude_csv = (settings.exclude_keywords or "manager,senior,director,lead").lower()
    exclude_words = [w.strip() for w in exclude_csv.split(",") if w.strip()]

    # JSearch uses x-api-key and /search endpoint.
    url = f"{base_url}/search"
    headers = {"x-api-key": api_key}
    params = {
        "query": query,
        "page": 1,
        "num_pages": 1,
        "country": (settings.country or "us").lower(),
        "language": "en",
        # If JSearch supports a page-size parameter (like "num_jobs"),
        # you can add it here to pull more jobs per fetch.
    }

    resp = httpx.get(url, headers=headers, params=params, timeout=60)
    resp.raise_for_status()
    payload = resp.json()

    items = payload.get("data") or payload.get("jobs") or []
    inserted, updated, skipped = 0, 0, 0

    for item in items:
        title = (item.get("job_title") or "").strip()
        if not title:
            skipped += 1
            continue

        t_low = title.lower()
        if any(w in t_low for w in exclude_words):
            skipped += 1
            continue

        company = (item.get("employer_name") or "").strip()
        job_url = (item.get("job_apply_link") or item.get("job_google_link") or "").strip()

        loc_parts = [
            (item.get("job_city") or "").strip(),
            (item.get("job_state") or "").strip(),
            (item.get("job_country") or "").strip(),
        ]
        location = ", ".join([p for p in loc_parts if p]) or (item.get("job_location") or "").strip()

        posted = item.get("job_posted_at_datetime_utc") or item.get("job_posted_at") or None

        existing = None
        if job_url:
            existing = db.query(models.Job).filter(models.Job.url == job_url).first()

        if not existing:
            existing = (
                db.query(models.Job)
                .filter(
                    models.Job.title == title,
                    models.Job.company == company,
                    models.Job.location == location,
                )
                .first()
            )

        if existing:
            existing.title = title
            existing.company = company
            existing.location = location
            if job_url:
                existing.url = job_url
            if posted:
                existing.posted_date = posted
            if hasattr(existing, "updated_at"):
                existing.updated_at = datetime.utcnow()

            db.add(existing)
            updated += 1
        else:
            new_job = models.Job(
                title=title,
                company=company,
                location=location,
                url=job_url,
                source="jsearch",
                posted_date=posted,
                saved=False,
                applied=False,
                match_score=0,
            )
            db.add(new_job)
            inserted += 1

    db.commit()
    total = db.query(models.Job).count()
    return {
        "status": "ok",
        "fetched": len(items),
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "total_in_db": total,
    }
