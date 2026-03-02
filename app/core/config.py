from typing import List, Optional

from pydantic import EmailStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "LogistiApply AI Pro"

    # Backend routes will be like /auth/login, /jobs, /settings (no /api prefix).
    # Frontend will call /api/... and Vite proxy rewrites to backend /...
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    SQLITE_URL: str = "sqlite:///./logistiapply.db"

    SECRET_KEY: str = "CHANGE_THIS_SECRET_KEY"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ALGORITHM: str = "HS256"

    JOB_FETCH_HOUR: int = 10
    JOB_FETCH_MINUTE: int = 30
    JOB_FETCH_TIMEZONE: str = "America/Chicago"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    EMAIL_FROM: Optional[EmailStr] = None
    EMAIL_TO: Optional[EmailStr] = None

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
