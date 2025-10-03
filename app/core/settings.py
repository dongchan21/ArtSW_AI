# app/core/settings.py

from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv
import os
from typing import Optional

# --- 1. 환경 변수 파일 강제 지정 로직 (사용자 코드 기반) ---
def load_env():
    """환경 변수를 강제 로드합니다."""
    try:
        ROOT = Path(__file__).resolve().parents[2]   # .../project-root/
        ENV_PATH = ROOT / ".env"
        load_dotenv(dotenv_path=ENV_PATH)
    
    except IndexError :
        print("Failed to determine project root for .env loading.")

    except Exception as e:
        print("Failed to load .env file:", e)
    
# --- 2. Pydantic 설정 모델 정의 ---
class Settings(BaseSettings):
    """
    RAG 시스템에 필요한 모든 설정을 정의합니다.
    """
    
    # 1. LLM (OpenAI) 설정
    OPENAI_API_KEY: str = Field(..., description="OpenAI API Key.")
    LLM_MODEL_NAME: str = "gpt-4o"
    
    # 2. Embeddings 설정
    EMBEDDING_MODEL_NAME: str = "text-embedding-3-large"
    
    # 3. Pinecone Vector DB 설정 (추가됨)
    PINECONE_API_KEY: str = Field(..., description="Pinecone API Key.")
    PINECONE_INDEX_NAME: str = Field("my-tutorial-index", description="Pinecone Index Name.")
    PINECONE_CLOUD: str = Field("aws", description="Pinecone Cloud Provider (예: gcp, aws, azure).")
    PINECONE_REGION: str = Field("us-east-1", description="Pinecone Region (예: us-east1).")
    
    # 4. RAG 및 기타 설정
    RAG_TOP_K: int = 3 # 유사 청크 검색 시 반환할 개수

# --- 3. 싱글톤 설정 인스턴스 관리 ---

_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """
    애플리케이션 전체에서 설정 객체를 단일 인스턴스로 반환합니다.
    """
    global _settings
    
    if _settings is None:
        # 1. .env 파일을 먼저 로드하여 환경 변수를 준비합니다.
        load_env()
        
        try:
            # 2. 환경 변수가 로드된 후 Settings 인스턴스를 생성하고 필수 필드를 검증합니다.
            _settings = Settings() 
        except Exception as e:
            # 필수 환경 변수가 누락된 경우 명확하게 에러를 발생시킵니다.
            raise RuntimeError(f"필수 설정 로드에 실패했습니다. (.env 파일 확인 필요): {e}")

    return _settings
