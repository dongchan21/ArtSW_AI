from fastapi import APIRouter
from app.core.settings import get_openai_api_key

router = APIRouter()

@router.get("/env/openai")
def env_openai():
    try:
        _ = get_openai_api_key()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
