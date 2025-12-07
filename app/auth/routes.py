from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.auth import schemas, service
from app.auth.utils import decode_token
from app.auth.models import User

router = APIRouter(prefix="/auth", tags=["Auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login/swagger")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ REGISTER (JSON)
@router.post("/register")
def register(data: schemas.RegisterIn, db: Session = Depends(get_db)):
    user = service.register_user(db, data.name, data.email, data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Email already registered")

    return {
        "message": "User registered successfully",
        "user_id": user.id
    }


# ✅ LOGIN FOR FRONTEND (JSON ✅)
@router.post("/login")
def login_json(data: schemas.LoginIn, db: Session = Depends(get_db)):
    result = service.login_user(db, data.email, data.password)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token, user = result

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "streak_days": user.streak_days,
        "total_login_days": user.total_login_days
    }


# ✅ LOGIN FOR SWAGGER AUTHORIZE BUTTON (FORM ✅)
@router.post("/login/swagger")
def login_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    result = service.login_user(db, form_data.username, form_data.password)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token, user = result

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# ✅ PROFILE (BEARER TOKEN REQUIRED ✅)
@router.get("/profile")
def get_profile(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "streak_days": user.streak_days,
        "total_login_days": user.total_login_days,
        "points": user.points,
        "total_time_spent": user.total_time_spent,
        "courses_completed": user.courses_completed,
        "badges": user.badges,
        "achievements": user.achievements
    }
