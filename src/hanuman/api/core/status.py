from fastapi import APIRouter

router = APIRouter(prefix="/status", tags=["status"])

@router.get("/")
@router.get("")
def get_status() -> dict:
    # le test attend "status": "ok"
    return {"status": "ok", "ok": True, "message": "Hanuman up", "version": "v5-dev"}

@router.get("/ping")
def ping() -> dict:
    return {"ok": True}
