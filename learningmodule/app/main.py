from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routes.learning import router as learning_router
from app.routes.users import router as users_router

load_dotenv()

app = FastAPI(title="LEARN Phonetics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(learning_router, prefix="/api/learning", tags=["learning"])
app.include_router(users_router, prefix="/api/users", tags=["users"])
