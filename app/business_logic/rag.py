# app/business_logic/rag.py

from typing import List, Dict, Any
# 이전 단계에서 구현한 코어 모듈을 임포트합니다.
from app.core import llm_client, vectorstore
from app.core.llm_client import ChatCompletionMessageParam
import logging
# logging 모듈을 임포트하고 로거를 설정합니다.
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # INFO 레벨 이상을 출력하도록 설정


# -----------------------------------------------------------------------------
# 1. 시스템 프롬프트 및 컨텍스트 포맷팅
# -----------------------------------------------------------------------------

def get_base_system_prompt(technique_name: str, tutorial_full_text: str) -> str:
    """
    RAG 시스템의 기본 역할, 규칙, 그리고 전체 튜토리얼 텍스트를 정의합니다.
    """
    # 튜토리얼 텍스트를 프롬프트에 직접 삽입하여 LLM의 배경 지식을 강화합니다.
    tutorial_section = f"""
    사용자는 이미 다음과 같은 내용을 튜토리얼로 숙지한 상황입니다.
    '{tutorial_full_text}'
    """

    return f"""
    당신은 '{technique_name}' 기법을 전문적으로 가르쳐주는 친절한 튜터 AI입니다.
    사용자는 생성형 AI를 처음 사용해 보는 초보 사용자입니다.
    {tutorial_section}
    
    [규칙]
    1. 당신에게 제공되는 [검색된 지식] 섹션을 **최우선 근거**로 사용하여 답변을 생성해야 합니다.
    2. 답변은 사용자가 이해할 수 있게 쉽고 재미있게, 단계별로 설명해주세요.
    3. {technique_name}에 관련없는 질문에는 **최대한 간단하게 답변**하고, 
       "우리 {technique_name}에 대한 얘기를 해볼까요?" 라고 대답해주세요.
    """

def format_context_for_llm(retrieved_chunks: List[Dict[str, Any]]) -> str:
    """
    vectorstore에서 검색된 청크들을 LLM에게 전달할 포맷으로 변환합니다.
    """
    context_text = "--- [검색된 지식] ---\n"
    
    if not retrieved_chunks:
        context_text += "검색된 관련 지식이 없습니다. LLM의 일반 지식으로 답변을 시도합니다.\n"
        return context_text
        
    for i, match in enumerate(retrieved_chunks):
        # vectorstore.py에서 metadata에 저장한 'text' 필드를 사용합니다.
        chunk_text = match.metadata.get('text', '텍스트를 찾을 수 없음')
        # 청크 점수(score)도 함께 표시하면 디버깅에 유용합니다.
        score = match.score
        context_text += f"[{i+1}. 근거 (유사도: {score:.3f})] {chunk_text}\n"
    
    context_text += "----------------------"
    return context_text

# -----------------------------------------------------------------------------
# 2. RAG 파이프라인 함수
# -----------------------------------------------------------------------------

async def generate_rag_response(
    query_text: str, 
    technique_key: str, 
    messages_from_client: List[Dict[str, str]],
    technique_name: str,
    tutorial_full_text: str
) -> str:
    """
    RAG 파이프라인을 실행하여 답변을 생성합니다.
    """
    
    # 1. 지식 근거 검색 (Retrieval)
    # query_vectorstore 함수는 Pinecone에서 관련 청크를 검색합니다.
    retrieved_chunks = vectorstore.query_vectorstore(query_text)
    
        # ⚠️ 로그 출력 로직 추가 ⚠️
    logger.info("-" * 50)
    logger.info(f"RAG 요청 처리 시작 - 질문: {query_text[:50]}...")
    logger.info(f"튜토리얼 키: {technique_key}, 이름: {technique_name}")
    
    if not retrieved_chunks:
        logger.warning("검색된 관련 지식이 없습니다. LLM의 일반 지식으로 답변을 시도합니다.")
    else:
        logger.info(f"총 {len(retrieved_chunks)}개의 청크 검색 성공:")
        for i, match in enumerate(retrieved_chunks):
            # 검색된 텍스트와 점수(score)를 로그에 출력합니다.
            chunk_text = match.metadata.get('text', '텍스트 없음')
            score = match.score
            logger.info(f"  [{i+1}] SCORE: {score:.4f}, TEXT: {chunk_text[:70]}...")

    logger.info("-" * 50)

    # 2. LLM에게 전달할 프롬프트 구성 (Augmentation)
    
    # 2-1. 시스템 프롬프트 + 검색된 컨텍스트 통합
    system_prompt_content = get_base_system_prompt(technique_name, tutorial_full_text)
    context_content = format_context_for_llm(retrieved_chunks)
    final_system_prompt = system_prompt_content + "\n\n" + context_content
    
    system_message: ChatCompletionMessageParam = {
        "role": "system", 
        "content": final_system_prompt
    }
    
    # 2-2. 대화 기록 포맷 변환
    gpt_conversation = llm_client.format_messages_for_openai(messages_from_client)
    
    # 최종 대화 목록: [시스템 프롬프트 (RAG 근거 포함), 이전 대화 기록]
    full_conversation = [system_message] + gpt_conversation
    
    # 3. LLM 호출 및 답변 생성 (Generation)
    response_text = await llm_client.generate_response(full_conversation)
    
    return response_text