from sqlalchemy.orm import Session
from datetime import datetime, date

from app.auth.models import User
from app.auth.utils import hash_password, verify_password, create_access_token


def register_user(db: Session, name: str, email: str, password: str):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return None

    user = User(
        name=name,
        email=email,
        password=hash_password(password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.password):
        return None

    today = date.today()

    # ✅ STREAK LOGIC (CORPORATE STANDARD)
    if user.last_login_at:
        last_login_date = user.last_login_at.date()

        if today == last_login_date:
            pass  # same-day login → no change
        elif (today - last_login_date).days == 1:
            user.streak_days += 1
        else:
            user.streak_days = 1
    else:
        user.streak_days = 1

    user.last_login_at = datetime.utcnow()
    user.last_active_at = datetime.utcnow()
    user.total_login_days += 1

    db.commit()

    token = create_access_token({"sub": str(user.id)})

    return token, user
