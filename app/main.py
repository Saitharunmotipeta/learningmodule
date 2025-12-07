from fastapi import FastAPI
from app.database.connection import Base, engine
from app.auth.routes import router as auth_router
from app.learning.routes import router as learning_router
from fastapi.security import OAuth2PasswordBearer

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dyslexia Backend")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

app.include_router(auth_router)
app.include_router(learning_router)

@app.get("/")
def health():
    return {"status": "Auth system running"}
