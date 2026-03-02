from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.db import crud, schemas
from app.db.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.User)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)) -> schemas.User:
    db_user = crud.get_user_by_username(db, username=user_data.username)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    return crud.create_user(db=db, username=user_data.username, password=user_data.password)


@router.post("/login", response_model=schemas.Token)
def login_json(payload: schemas.LoginRequest, db: Session = Depends(get_db)) -> schemas.Token:
    user = crud.get_user_by_username(db, username=payload.username)
    if not user or not crud.verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


# Keep OAuth2 standard token endpoint (Swagger uses this nicely)
@router.post("/token", response_model=schemas.Token)
def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> schemas.Token:
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not crud.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}
