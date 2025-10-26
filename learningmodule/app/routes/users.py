from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
def user_status():
    return {"ok": True, "message": "User module alive"}
