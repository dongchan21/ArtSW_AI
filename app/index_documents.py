# index_documents.py

from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
from pathlib import Path
from app.core import embeddings, vectorstore
from app.core.vectorstore import VectorTuple
from typing import List, Dict, Any

def parse_document(file_path: Path) -> List[str]:
    """긴 텍스트 문서를 읽고 재귀적 청킹을 사용하여 분할합니다."""

    with open(file_path, 'r', encoding='utf-8') as f:
        full_text = f.read()

    
    # ⚠️ 재귀적 청킹 설정 ⚠️
    text_splitter = RecursiveCharacterTextSplitter(
        # 분할 기준으로 시도할 문자들 (우선순위 순서)
        separators=["\n\n", "\n", " ", ""], 
        chunk_size=500, # 청크의 최대 크기
        chunk_overlap=50, # 청크 간 겹치는 길이 (문맥 유지를 도움)
        length_function=len,
        is_separator_regex=False,
    )

    # 텍스트를 분할하고 Doc 객체에서 텍스트만 추출
    docs = text_splitter.create_documents([full_text])
    chunks = [doc.page_content for doc in docs]
    
    return chunks

async def index_documents(data_dir: str):
    """지정된 디렉토리의 모든 문서를 읽어 Pinecone에 색인합니다."""

    doc_paths = list(Path(data_dir).glob("*.txt")) # .txt 파일만 검색
    all_vectors_to_upsert: List[VectorTuple] = []

    print(f"총 {len(doc_paths)}개의 문서를 발견했습니다. 색인을 시작합니다.")

    for doc_path in doc_paths:
        document_name = doc_path.name
        
        # 1. 문서 청킹
        chunks = parse_document(doc_path)
        print(f"  -> {document_name}: 총 {len(chunks)}개의 청크 생성 완료.")

        # 2. 청크 임베딩
        # embed_texts는 텍스트 리스트를 벡터 리스트(List[List[float]])로 반환합니다.
        vectors = embeddings.embed_texts(chunks) 

        # 3. Upsert 데이터 준비
        for i, (chunk_text, vector) in enumerate(zip(chunks, vectors)):
            vector_id = f"{document_name.replace('.', '_')}_{i}"
            
            metadata = {
                "text": chunk_text,
                "source_doc": document_name, # ⚠️ 출처 메타데이터
                "key": "research" # ⚠️ 필터링을 위한 공통 키
            }
            all_vectors_to_upsert.append((vector_id, vector, metadata))
    
    # 4. Pinecone에 업로드
    print(f"\n총 {len(all_vectors_to_upsert)}개의 벡터를 Pinecone에 업로드합니다...")
    vectorstore.upsert_vectors(all_vectors_to_upsert)
    print("✅ 데이터 색인 완료.")

if __name__ == "__main__":
    # 데이터 파일을 저장할 디렉토리를 지정하세요.
    # 예: 프로젝트 루트에 documents/ 라는 폴더를 만들고 그 안에 TXT 파일을 넣음
    DOCUMENTS_DIR = "./documents" 
    
    # 비동기 함수 실행 (FastAPI 환경이 아니므로 단순 실행)
    import asyncio
    asyncio.run(index_documents(DOCUMENTS_DIR))