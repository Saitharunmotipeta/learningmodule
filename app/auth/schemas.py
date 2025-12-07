from pydantic import BaseModel, EmailStr


class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ProfileOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    streak_days: int
    total_login_days: int
    points: int
    total_time_spent: int
    courses_completed: int
    badges: str
    achievements: str
