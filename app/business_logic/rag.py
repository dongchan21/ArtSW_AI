import logging
from typing import List, Dict, Any

from app.core import llm_client, vectorstore
from app.core.llm_client import ChatCompletionMessageParam

# logging 모듈을 임포트하고 로거를 설정합니다.
logging.basicConfig(
    level=logging.INFO, # 최하위 출력 레벨을 INFO로 설정
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # INFO 레벨 이상을 출력하도록 설정


# -----------------------------------------------------------------------------
# 1. 시스템 프롬프트 및 컨텍스트 포맷팅 (역할과 규칙만 정의)
# -----------------------------------------------------------------------------

def get_base_system_prompt(technique_name: str) -> str:
    """
    RAG 시스템의 기본 역할과, LLM의 행동 규칙을 정의합니다.
    튜토리얼 내용 및 검색된 지식은 'user' 메시지로 전달됩니다.
    """
    return f"""
    당신은 '{technique_name}' 기법을 전문적으로 가르쳐주는 친절하고 유능한 튜터 AI입니다.
    사용자는 생성형 AI를 처음 사용해 보는 초보 사용자입니다. 쉽고 재미있게, 단계별로 설명해주세요.
    
    ### [핵심 임무 및 근거 사용 규칙]
    1. **최우선 근거:** 답변은 반드시 사용자가 마지막으로 전달하는 **[검색된 외부 지식]** 섹션을 **최우선 근거**로 삼아 생성하십시오.
    2. **내부 지식 조건부 사용:**
        - **검색된 지식이 있다면:** 오직 검색된 외부 지식만을 사용해야 하며, 당신의 내부 학습 지식을 추가하거나 혼합하여 지어내지 마십시오.
        - **검색된 지식이 없다면:** 당신이 이미 학습한 **내부 지식**을 활용하여 답변을 생성할 수 있습니다.
    3. **주제 이탈 시:** {technique_name}에 관련 없는 질문은 **최대한 간결하게** 답변하고, "우리 {technique_name}에 대한 얘기를 해볼까요?"라고 마무리합니다.
    """

def format_context_for_llm(retrieved_chunks: List[Dict[str, Any]]) -> str:
    """
    vectorstore에서 검색된 청크들을 LLM에게 전달할 포맷으로 변환합니다.
    (이 함수는 필터링된 청크를 입력받습니다.)
    """
    context_text = "--- [검색된 외부 지식] ---\n"
    
    if not retrieved_chunks:
        # 검색된 지식이 없을 경우, 내부 지식 사용을 유도하는 문구를 추가
        context_text += "검색된 관련 외부 지식이 없습니다. LLM은 이 경우 내부 지식을 사용할 수 있습니다.\n"
        return context_text
        
    for i, match in enumerate(retrieved_chunks):
        # 문서 ID도 출력하여 근거의 출처를 명확히 합니다.
        doc_id = match.metadata.get('doc_id', '알 수 없음')
        chunk_text = match.metadata.get('text', '텍스트를 찾을 수 없음')
        score = match.score
        # 근거 텍스트를 명확하게 구분합니다.
        context_text += f"[근거 {i+1} - {doc_id} (유사도: {score:.3f})]\n{chunk_text}\n---\n"
    
    # 마지막 줄 바꿈 제거
    context_text = context_text.rstrip('-\n') 
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
    # Pinecone에서 관련 청크를 검색합니다.
    all_retrieved_chunks = vectorstore.query_vectorstore(query_text)
    
    # 1-1. ⭐️⭐️ 필터링 로직 제거: 모든 검색 결과를 사용하도록 수정 ⭐️⭐️
    # 이전의 TARGET_DOC_ID 필터링을 제거하고, 검색된 모든 청크를 사용합니다.
    retrieved_chunks = all_retrieved_chunks
    
    # ⚠️ 로그 출력 로직 (유지)
    logger.info("-" * 50)
    logger.info(f"RAG 요청 처리 시작 - 질문: {query_text[:50]}...")
    logger.info(f"검색된 모든 청크 수: {len(retrieved_chunks)}") 

    if not retrieved_chunks:
        logger.warning(f"검색된 관련 지식이 없습니다. (총 0개 검색됨)")
    else:
        logger.info(f"총 {len(retrieved_chunks)}개의 청크 검색 성공:")
        for i, match in enumerate(retrieved_chunks):
            doc_id = match.metadata.get('doc_id', '알 수 없음')
            chunk_text = match.metadata.get('text', '텍스트 없음')
            score = match.score
            logger.info(f"  [{i+1}] DOC ID: {doc_id}, SCORE: {score:.4f}, TEXT: {chunk_text[:70]}...")

    logger.info("-" * 50)

    # 2. LLM에게 전달할 프롬프트 구성 (Augmentation)
    
    # 2-1. 시스템 메시지: 역할과 규칙만 정의 
    system_prompt_content = get_base_system_prompt(technique_name)
    system_message: ChatCompletionMessageParam = {
        "role": "system", 
        "content": system_prompt_content
    }
    
    # 2-2. 검색 결과 및 튜토리얼 텍스트를 User 메시지 컨텍스트에 추가
    context_content = format_context_for_llm(retrieved_chunks)
    
    # 기존 대화 기록 포맷 변환
    gpt_conversation = llm_client.format_messages_for_openai(messages_from_client)
    
    # 사용자 원본 쿼리 텍스트를 사용
    user_query = query_text 
    
    # 새로운 최종 사용자 질문 (RAG에 필요한 모든 정보를 담습니다)
    final_user_content = f"""
### [사용자 숙지 내용]
사용자는 이미 다음과 같은 내용을 튜토리얼로 숙지한 상황입니다.
'{tutorial_full_text}'

---

{context_content}

---

### [사용자 질문]
{user_query}
"""
    # 최종 사용자 메시지로 교체
    final_user_message: ChatCompletionMessageParam = {
        "role": "user",
        "content": final_user_content
    }
    
    # 최종 대화 목록: [시스템 프롬프트, 이전 대화 기록 (마지막 질문 전까지), 새로운 최종 질문]
    # 이전 대화 목록에서 마지막 User 질문을 제거하고 새로운 final_user_message로 대체합니다.
    full_conversation = [system_message] + gpt_conversation[:-1] + [final_user_message]
    
    # 3. LLM 호출 및 답변 생성 (Generation)
    response_text = await llm_client.generate_response(full_conversation)
    
    return response_text
