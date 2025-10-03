# app/core/vectorstore.py

from pinecone import Pinecone, ServerlessSpec, PodSpec
from pinecone.exceptions import PineconeException
from typing import List, Dict, Any, Optional, Tuple
# 이전 단계에서 구현한 모듈들을 임포트합니다.
from app.core.settings import get_settings
from app.core.embeddings import embed_texts 

# -----------------------------------------------------------------------------
# 1. Pinecone 인스턴스 및 인덱스 (싱글톤 패턴)
# -----------------------------------------------------------------------------

# 전역 변수로 Pinecone 클라이언트와 인덱스 인스턴스를 저장합니다.
_pinecone_client: Optional[Pinecone] = None
_pinecone_index: Optional[Pinecone.Index] = None

def get_pinecone_index() -> Pinecone.Index:
    """
    Pinecone 클라이언트를 초기화하고 설정된 인덱스 객체를 반환합니다.
    (인덱스가 없으면 새로 생성합니다.)
    """
    global _pinecone_client, _pinecone_index
    settings = get_settings()

    
    # 1. Pinecone 클라이언트 초기화 (기존 로직 유지)
    if _pinecone_client is None:
        try:
            _pinecone_client = Pinecone(api_key=settings.PINECONE_API_KEY)
        except Exception as e:
            raise PineconeException(f"Pinecone client initialization failed: {e}")

    # 2. 인덱스 존재 확인 및 생성 로직
    index_name = settings.PINECONE_INDEX_NAME
    
    # 인덱스가 이미 존재하는지 확인
    indexes = _pinecone_client.list_indexes()
    index_names = [idx["name"] for idx in indexes]

    if index_name not in index_names:
        print(f"⚠️ 인덱스 '{index_name}'을 찾을 수 없습니다. 새로운 인덱스를 생성합니다...")
        
        # 인덱스 생성 (임베딩 모델 차원 1536 사용)
        _pinecone_client.create_index(
            name=index_name,
            dimension=3072, # text-embedding-3-large의 차원
            metric='cosine', # 코사인 유사도 사용
            spec=ServerlessSpec("aws", "us-east-1")
        )
        print(f"✅ 인덱스 '{index_name}' 생성 완료.")
    
    else:
        print(f"ℹ️ 인덱스 '{index_name}' 이미 존재합니다. 새로 만들지 않습니다.")

    # 3. 인덱스 연결
    if _pinecone_index is None:
        try:
            _pinecone_index = _pinecone_client.Index(index_name)
        except Exception as e:
            raise PineconeException(f"Failed to connect to index {index_name} after creation: {e}")
            
    return _pinecone_index
# -----------------------------------------------------------------------------
# 2. 벡터 검색 함수 (RAG의 핵심)
# -----------------------------------------------------------------------------

# 참고: embed_texts가 동기 함수이므로 여기서는 await을 제거하거나, 
# 실제 배포 환경을 고려하여 async 함수로 유지하고 내부 호출을 동기 처리합니다.
def query_vectorstore(query_text: str) -> List[Dict[str, Any]]:
    """
    사용자 질문을 벡터로 변환하고 Pinecone 인덱스에서 가장 유사한 문서를 검색합니다.
    
    Args:
        query_text (str): 사용자의 질문 텍스트.
        
    Returns:
        List[Dict[str, Any]]: 검색된 문서(Match) 리스트. 
    """
    settings = get_settings()
    top_k = settings.RAG_TOP_K 
    
    try:
        # 1. 질문 텍스트를 벡터로 변환 (embeddings.py 모듈 사용)
        query_vector = embed_texts(query_text)
        
        # 2. Pinecone 인덱스 객체 가져오기
        index = get_pinecone_index()
        
        # 3. 인덱스에서 유사도 검색 수행
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            include_values=False,
            include_metadata=True # 원본 텍스트(Metadata)를 함께 가져옵니다.
        )
        
        # 4. 검색 결과를 리스트로 정리하여 반환
        return results.matches

    except PineconeException as e:
        print(f"Pinecone query failed: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred during query: {e}")
        return []


# -----------------------------------------------------------------------------
# 3. 벡터 업로드 함수 (데이터 색인)
# -----------------------------------------------------------------------------

# Pinecone이 요구하는 (id, vector, metadata) 튜플 형식입니다.
VectorTuple = Tuple[str, List[float], Dict[str, Any]]

def upsert_vectors(vectors_to_upsert: List[VectorTuple]) -> None:
    """
    주어진 벡터들을 Pinecone 인덱스에 저장하거나 업데이트(Upsert)합니다.
    
    Args:
        vectors_to_upsert (List[VectorTuple]): 업로드할 (id, vector, metadata) 데이터 리스트.
    """
    if not vectors_to_upsert:
        return
        
    index = get_pinecone_index()
    
    try:
        # Pinecone의 upsert 함수는 (id, vector, metadata) 튜플 리스트를 받습니다.
        index.upsert(vectors=vectors_to_upsert)
    except PineconeException as e:
        print(f"Pinecone upsert failed: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred during upsert: {e}")
        raise