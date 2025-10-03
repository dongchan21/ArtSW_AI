# app/api/chat.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any

# RAG 비즈니스 로직과 데이터 로더를 임포트합니다.
from app.business_logic import rag
from app.utils.data_loader import get_tutorial_full_text, load_tutorial_data_to_cache

# FastAPI 라우터 인스턴스를 생성합니다.
router = APIRouter()

# -----------------------------------------------------------------------------
# 1. 요청/응답 데이터 모델 (Pydantic)
# -----------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """클라이언트로부터 받는 챗봇 요청 데이터 모델."""
    query: str = Field(..., description="사용자의 현재 질문 텍스트.")
    
    # 현재 사용자가 보고 있는 튜토리얼 기술의 고유 키 (예: 'flour', 'tomato')
    technique_key: str = Field(..., description="현재 활성화된 튜토리얼의 고유 키.")
    
    # 이전 대화 기록 (LLM에게 컨텍스트를 제공하기 위함)
    messages: List[Dict[str, str]] = Field(..., description="대화 기록 리스트.")
    
    # 현재 튜토리얼의 한글 이름 (예: 'Few-Shot 기법')
    technique_name: str = Field(..., description="현재 튜토리얼의 사용자 친화적인 이름.")

class ChatResponse(BaseModel):
    """클라이언트에게 반환하는 챗봇 응답 데이터 모델."""
    response: str = Field(..., description="LLM이 생성한 최종 답변 텍스트.")


# -----------------------------------------------------------------------------
# 2. API 엔드포인트: RAG 챗봇
# -----------------------------------------------------------------------------

@router.post("/rag", response_model=ChatResponse)
async def chat_with_rag(request: ChatRequest):
    """
    사용자의 질문을 받아 RAG 파이프라인을 실행하고 답변을 생성합니다.
    """
    
    # 1. 튜토리얼 전체 텍스트 로드
    # data_loader를 사용하여 'technique_key'에 해당하는 전체 텍스트를 메모리에서 빠르게 찾습니다.
    tutorial_full_text = get_tutorial_full_text(request.technique_key)
    
    if not tutorial_full_text:
        # 데이터 로드에 실패하면 500 에러를 반환합니다.
        raise HTTPException(
            status_code=500, 
            detail=f"튜토리얼 키 '{request.technique_key}'에 해당하는 전체 텍스트를 찾을 수 없습니다."
        )

    try:
        # 2. RAG 비즈니스 로직 호출
        # rag.py의 핵심 함수에 필요한 모든 인자(전체 텍스트 포함)를 전달합니다.
        rag_response = await rag.generate_rag_response(
            query_text=request.query,
            technique_key=request.technique_key,
            messages_from_client=request.messages,
            technique_name=request.technique_name,
            tutorial_full_text=tutorial_full_text # 튜토리얼 전체 텍스트 전달
        )
        
        # 3. 응답 반환
        return ChatResponse(response=rag_response)

    except Exception as e:
        # LLM 호출 실패, Pinecone 오류 등 예상치 못한 오류 발생 시
        print(f"RAG 파이프라인 오류 발생: {e}")
        raise HTTPException(
            status_code=500, 
            detail="챗봇 서비스 처리 중 예상치 못한 오류가 발생했습니다."
        )


# -----------------------------------------------------------------------------
# 3. 초기화 로직 (FastAPI 시작 시 데이터 캐싱)
# -----------------------------------------------------------------------------

# FastAPI 애플리케이션 시작 시점에 data_loader를 호출하여 데이터를 메모리에 로드
# (이 코드가 실제 main.py나 main.py가 호출하는 이벤트 핸들러에 있어야 하지만, 
#  라우터 파일에 작성하여 로직을 명확히 합니다.)
try:
    load_tutorial_data_to_cache()
    print("✨ 튜토리얼 데이터 캐싱 완료. RAG 서비스 준비됨.")
except Exception as e:
    print(f"🚨 튜토리얼 데이터 로드 초기화 실패: {e}")