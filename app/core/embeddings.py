# app/core/embeddings.py

from typing import List, Union, Optional
from openai import OpenAI
from app.core.settings import get_settings

# -----------------------------------------------------------------------------
# 1. OpenAI 클라이언트 초기화 (싱글톤)
# -----------------------------------------------------------------------------

# 전역 변수로 임베딩용 OpenAI 클라이언트 인스턴스를 저장합니다.
_openai_client_for_embedding: Optional[OpenAI] = None

def get_openai_client_for_embedding() -> OpenAI:
    """
    임베딩 API 호출에 사용될 OpenAI 클라이언트를 초기화하고 싱글톤 인스턴스를 반환합니다.
    """
    global _openai_client_for_embedding
    settings = get_settings()
    
    if _openai_client_for_embedding is None:
        try:
            # settings.py에서 로드된 API 키를 사용하여 클라이언트 초기화
            _openai_client_for_embedding = OpenAI(api_key=settings.OPENAI_API_KEY)
        except Exception as e:
            raise RuntimeError(f"OpenAI client initialization failed for embeddings: {e}")
            
    return _openai_client_for_embedding

# -----------------------------------------------------------------------------
# 2. 임베딩 생성 함수
# -----------------------------------------------------------------------------

def embed_texts(texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
    """
    주어진 텍스트(단일 문자열 또는 문자열 리스트)를 OpenAI 임베딩 API를 사용하여 
    벡터로 변환합니다.
    
    Input:
        texts (str | List[str]): 임베딩할 텍스트(들).
        
    Output:
        List[float] | List[List[float]]: 임베딩된 단일 벡터 또는 벡터 리스트.
    """
    
    client = get_openai_client_for_embedding()
    settings = get_settings()
    is_single_text = isinstance(texts, str)
    
    # OpenAI API는 항상 리스트 입력을 요구하므로 단일 텍스트도 리스트로 변환합니다.
    texts_to_embed = [texts] if is_single_text else texts
    
    if not texts_to_embed:
        # 입력이 비어있으면 빈 리스트를 반환합니다.
        return []
    
    try:
        # OpenAI 임베딩 API 호출
        response = client.embeddings.create(
            model=settings.EMBEDDING_MODEL_NAME, # text-embedding-3-large 사용
            input=texts_to_embed
        )
        
        # 응답 데이터에서 임베딩 벡터 리스트를 추출합니다.
        embeddings = [data.embedding for data in response.data]
        
        # ⚠️ 입력이 단일 텍스트였으면 첫 번째 벡터만 반환합니다. (query_vectorstore에 사용)
        if is_single_text:
            return embeddings[0]
        
        # ⚠️ 입력이 리스트였으면 벡터 리스트를 반환합니다. (upsert_vectors에 사용)
        return embeddings

    except Exception as e:
        print(f"Error during OpenAI embeddings API call: {e}")
        # 임베딩 실패는 RAG 검색 실패로 이어지므로 명확히 에러를 발생시킵니다.
        raise RuntimeError(f"Failed to generate embeddings: {e}")