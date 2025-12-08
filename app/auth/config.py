# app/auth/config.py
from datetime import timedelta
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# ✅ JWT SETTINGS
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-dev-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24)  # default = 24 hours
)


def get_access_token_expiry():
    return timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
