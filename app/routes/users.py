# app/routes/users.py
"""
User auth routes:

- POST /api/users/register  → register new user
- POST /api/users/login     → login and get JWT
- GET  /api/users/me        → decode token and return user_id

These are used by the frontend; the learning/progress/speech
endpoints just need the user_id (frontend can store it after login).
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.database.connection import SessionLocal
from app.models.user import User
from app.auth.auth_utils import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)

router = APIRouter(prefix="/users", tags=["users"])


class RegisterIn(BaseModel):
    name: str
    email: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str


@router.post("/register")
def register_user(data: RegisterIn):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == data.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed = hash_password(data.password)
        new_user = User(name=data.name, email=data.email, password=hashed)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"message": "User registered", "user_id": new_user.id}
    finally:
        db.close()


@router.post("/login")
def login_user(data: LoginIn):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == data.email).first()
    finally:
        db.close()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "user_id": user.id}


@router.get("/me")
def get_me(token: str):
    """
    Simple helper to check token; frontend can call this if needed.
    """
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"user_id": payload.get("sub")}
