from datetime import timedelta
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

from app.core.config import settings
from app.core.security import get_current_user
from app.db.database import Base, engine, get_db
from app.db import schemas, crud
from app.api import routes_auth

load_dotenv()

Base.metadata.create_all(bind=engine)

print("DB URL:", engine.url)
print("CWD:", os.getcwd())

app = FastAPI(
    title=getattr(settings, "PROJECT_NAME", "LogistiApply AI Pro"),
    swagger_ui_parameters={"syntaxHighlight": False},
)

# -------------------------
# CORS
# -------------------------
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",

    # GitHub Pages (keep if you still want it to work)
    "https://gokul6638.github.io",
    "https://gokul6638.github.io/logistics-apply-frontend",

    # Custom domain (THIS fixes your current error)
    "https://apply.gokulravikumar.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Public: Health
# -------------------------
@app.get("/api/health")
def health_check():
    return {"status": "ok"}

# -------------------------
# Public: Auth routes
# -------------------------
app.include_router(routes_auth.router, prefix="/api")

# -------------------------
# Protected: Settings
# -------------------------
@app.get("/api/settings", response_model=schemas.Settings)
def get_settings(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return crud.get_or_create_settings(db)

@app.put("/api/settings", response_model=schemas.Settings)
def update_settings(
    payload: schemas.SettingsUpdate,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return crud.update_settings(db, payload)

# -------------------------
# Protected: Jobs
# -------------------------
@app.get("/api/jobs", response_model=list[schemas.JobOut])
def read_jobs(
    skip: int = 0,
    limit: int = 200,
    posted_within: Optional[str] = None,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return crud.get_jobs(db, skip=skip, limit=limit, posted_within=posted_within)

@app.post("/api/jobs/{job_id}/save")
def toggle_save_job(
    job_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    job = crud.toggle_save(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"ok": True, "saved": job.saved}

@app.post("/api/jobs/{job_id}/applied")
def mark_job_applied(
    job_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    job = crud.mark_applied(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"ok": True, "applied": job.applied}

# -------------------------
# Protected: Fetch trigger
# -------------------------
@app.post("/api/fetch-jobs")
def fetch_jobs_now(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    result = crud.fetch_jobs_now(db)
    return {"ok": True, "result": result}
