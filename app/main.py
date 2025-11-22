from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# VERY TOP of app/main.py - must run before other imports
import warnings
# optional: suppress the one noisy pydub startup warning (safe if you configure below)
warnings.filterwarnings(
    "ignore",
    message="Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work"
)

from dotenv import load_dotenv
load_dotenv()

import os, pathlib
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]

_ffmpeg_rel = os.getenv("FFMPEG_PATH")
_ffprobe_rel = os.getenv("FFPROBE_PATH")

FFMPEG_PATH = str((PROJECT_ROOT / _ffmpeg_rel).resolve()) if _ffmpeg_rel else None
FFPROBE_PATH = str((PROJECT_ROOT / _ffprobe_rel).resolve()) if _ffprobe_rel else None

if FFMPEG_PATH:
    ff_bin = os.path.dirname(FFMPEG_PATH)
    os.environ["PATH"] = ff_bin + os.pathsep + os.environ.get("PATH", "")
    os.environ["FFMPEG_BINARY"] = FFMPEG_PATH
if FFPROBE_PATH:
    os.environ["FFPROBE_BINARY"] = FFPROBE_PATH

# now safe to import pydub
from pydub import AudioSegment
if FFMPEG_PATH:
    AudioSegment.converter = FFMPEG_PATH
if FFPROBE_PATH:
    try:
        AudioSegment.ffprobe = FFPROBE_PATH
    except Exception:
        pass

# print("FFMPEG_PATH resolved to:", FFMPEG_PATH)
# print("FFPROBE_PATH resolved to:", FFPROBE_PATH)


from app.routes.learning import router as learning_router
from app.routes.users import router as users_router
from app.routes.progress import router as progress_router
from app.routes.phoneme import router as phoneme_router
from app.database.connection import Base, engine
from app.models.user import User
from app.models.word import Word
from app.models.progress import UserProgress
from app.models.level import Level
from app.models.level_word import LevelWord
from app.routes.speech import router as speech_router
from pydub import AudioSegment
import os



Base.metadata.create_all(bind=engine)

app = FastAPI(title="LEARN Phonetics API")
_ffmpeg_rel = os.getenv("FFMPEG_PATH")
_ffprobe_rel = os.getenv("FFPROBE_PATH")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(users_router, prefix="/api", tags=["users"])
app.include_router(learning_router, prefix="/api/learning", tags=["learning"])
app.include_router(progress_router, prefix="/api/learning", tags=["progress"])
app.include_router(speech_router, prefix="/api", tags=["speech"])
app.include_router(phoneme_router, prefix="/api", tags=["phoneme"])


