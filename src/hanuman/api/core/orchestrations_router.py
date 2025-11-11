from fastapi import APIRouter
from hanuman.orchestrations import __all__ as _  # assure import side-effects if needed

router = APIRouter(prefix="/orchestrations", tags=["orchestrations"])

@router.get("/ping")
def orchestration_ping():
    return {"ok": True}
