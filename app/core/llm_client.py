# app/core/llm_client.py

from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from app.core.settings import get_settings

# -----------------------------------------------------------------------------
# 1. OpenAI 클라이언트 초기화 (싱글톤)
# -----------------------------------------------------------------------------

# 전역 변수로 OpenAI 클라이언트 인스턴스를 저장합니다.
_openai_client: Optional[OpenAI] = None

def get_openai_client() -> OpenAI:
    """
    OpenAI 클라이언트를 초기화하고 싱글톤 인스턴스를 반환합니다.
    API 키는 settings.py에서 로드됩니다.
    """
    global _openai_client
    settings = get_settings()
    
    if _openai_client is None:
        try:
            # settings.py에서 로드된 API 키를 사용하여 클라이언트 초기화
            _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            # print("OpenAI client initialized.") # 디버깅 시 활용
        except Exception as e:
            # API 키가 유효하지 않거나 로딩에 실패한 경우
            raise RuntimeError(f"OpenAI client initialization failed: {e}")
            
    return _openai_client

# -----------------------------------------------------------------------------
# 2. LLM 응답 생성 함수
# -----------------------------------------------------------------------------

async def generate_response(
    full_conversation: List[ChatCompletionMessageParam],
    model_name: Optional[str] = None
) -> str:
    """
    구성된 전체 대화 목록(system prompt 포함)을 OpenAI API에 전송하고 
    LLM의 텍스트 응답을 반환합니다.
    
    Input:
        full_conversation (List[ChatCompletionMessageParam]): 
            {"role": "system"/"user"/"assistant", "content": "..."} 형태의 메시지 목록
        model_name (str, optional): 사용할 모델 이름. 지정하지 않으면 settings.py의 기본값 사용.
        
    Output:
        str: LLM의 응답 텍스트.
    """
    client = get_openai_client()
    settings = get_settings()
    
    # 사용할 모델 결정 (함수 인자가 우선, 없으면 설정값 사용)
    target_model = model_name if model_name else settings.LLM_MODEL_NAME

    try:
        # Chat Completion API 호출
        completion = client.chat.completions.create(
            model=target_model,
            messages=full_conversation
        )
        
        # 응답 텍스트 추출
        gpt_response_text = completion.choices[0].message.content
        
        # 응답이 None일 경우 예외 처리
        if gpt_response_text is None:
             raise ValueError("LLM returned an empty response.")
        
        return gpt_response_text
        
    except Exception as e:
        # API 통신 오류, 모델 오류 등 발생 시
        print(f"Error calling OpenAI API ({target_model}): {e}")
        # 실제 서비스에서는 에러 로깅 후 사용자에게 적절한 메시지를 반환해야 합니다.
        raise HTTPException(status_code=500, detail="LLM 응답 생성 중 오류가 발생했습니다.")


# -----------------------------------------------------------------------------
# 3. 개발 편의를 위한 메시지 포맷 변환 함수
# -----------------------------------------------------------------------------

def format_messages_for_openai(messages_from_client: List[Dict[str, str]]) -> List[ChatCompletionMessageParam]:
    """
    프론트엔드에서 받은 메시지 포맷을 OpenAI API 형식으로 변환합니다.
    
    Input 메시지 형식 예시: 
    [{"type": "user", "text": "안녕?"}, {"type": "bot", "text": "안녕하세요!"}]
    
    Output 메시지 형식 예시:
    [{"role": "user", "content": "안녕?"}, {"role": "assistant", "content": "안녕하세요!"}]
    """
    gpt_messages: List[ChatCompletionMessageParam] = []
    
    for msg in messages_from_client:
        msg_type = msg.get('type')
        msg_text = msg.get('text')
        
        # 'bot' 타입을 'assistant'로 변환
        role = 'user' if msg_type == 'user' else 'assistant' if msg_type == 'bot' else None
        
        if role and msg_text:
            gpt_messages.append({"role": role, "content": msg_text})
            
    return gpt_messages