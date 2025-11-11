from fastapi import APIRouter

router = APIRouter(prefix="/log", tags=["log"])

@router.get("/trace")
def trace() -> dict:
    return {"ok": True, "trace": "enabled"}
