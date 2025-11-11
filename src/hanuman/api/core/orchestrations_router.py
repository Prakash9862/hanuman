from fastapi import APIRouter

router = APIRouter(prefix="/orchestrations", tags=["orchestrations"])

@router.get("/ping")
def orchestration_ping():
    return {"ok": True}
