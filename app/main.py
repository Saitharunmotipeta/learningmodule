# app/main.py
import os
import pathlib
import warnings

# ================================
# 1. Load .env very early
# ================================
from dotenv import load_dotenv
load_dotenv()

# ================================
# 2. Suppress only noisy pydub warnings
# ================================
warnings.filterwarnings(
    "ignore",
    message="Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work",
)
warnings.filterwarnings(
    "ignore",
    message="Couldn't find ffprobe or avprobe - defaulting to ffprobe, but may not work",
)

# ================================
# 3. Compute absolute FFmpeg paths
# ================================
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]

_ffmpeg_rel = os.getenv("FFMPEG_PATH")
_ffprobe_rel = os.getenv("FFPROBE_PATH")

FFMPEG_PATH = str((PROJECT_ROOT / _ffmpeg_rel).resolve()) if _ffmpeg_rel else None
FFPROBE_PATH = str((PROJECT_ROOT / _ffprobe_rel).resolve()) if _ffprobe_rel else None

# ================================
# 4. Export FFmpeg binaries to PATH
# ================================
if FFMPEG_PATH:
    bin_dir = os.path.dirname(FFMPEG_PATH)
    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
    os.environ["FFMPEG_BINARY"] = FFMPEG_PATH

if FFPROBE_PATH:
    os.environ["FFPROBE_BINARY"] = FFPROBE_PATH

# ================================
# 5. Configure pydub AFTER exporting FFmpeg
# ================================
from pydub import AudioSegment

if FFMPEG_PATH:
    AudioSegment.converter = FFMPEG_PATH

if FFPROBE_PATH:
    try:
        AudioSegment.ffprobe = FFPROBE_PATH
    except Exception:
        # some pydub versions don't have this attribute
        pass

# ================================
# 6. FastAPI + DB setup
# ================================
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.connection import Base, engine

# import models so SQLAlchemy knows them before create_all()
from app.models.user import User
from app.models.word import Word
from app.models.progress import UserProgress
from app.models.level import Level
from app.models.level_word import LevelWord

# import routers
from app.routes.users import router as users_router
from app.routes.learning import router as learning_router
from app.routes.progress import router as progress_router
from app.routes.speech import router as speech_router

# If you later add adaptive-specific routes, import and include here:
# from app.routes.adaptive import router as adaptive_router

# Create DB tables (only if they don't exist)
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="LEARN Phonetics API")

# ================================
# 7. CORS configuration
# ================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================
# 8. Register API routers
# ================================
# Auth / users
app.include_router(users_router, prefix="/api", tags=["users"])

# Learning / levels / word analysis
app.include_router(learning_router, prefix="/api/learning", tags=["learning"])

# Progress + recommendation
app.include_router(progress_router, prefix="/api/learning", tags=["progress"])

# Speech analysis (STT + scoring)
app.include_router(speech_router, prefix="/api", tags=["speech"])

# If you add adaptive router:
# app.include_router(adaptive_router, prefix="/api/learning", tags=["adaptive"])

# ================================
# 9. Optional debug logs
# ================================
print("FFMPEG_PATH resolved to:", FFMPEG_PATH)
print("FFPROBE_PATH resolved to:", FFPROBE_PATH)
