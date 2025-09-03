from pathlib import Path
from dotenv import load_dotenv
import os

# 프로젝트 루트( app/ 상위 )의 .env 강제 지정
ROOT = Path(__file__).resolve().parents[2]   # .../project-root/
ENV_PATH = ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)

def get_openai_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        # 디버깅 편의를 위한 명확한 에러
        raise RuntimeError(f"OPENAI_API_KEY not found. Looked at: {ENV_PATH}")
    return key
