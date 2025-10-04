# # index_papers_from_url.py

# import json
# import os
# import re
# import requests
# from pathlib import Path
# from typing import List, Dict, Any

# # LangChain 문서 로더와 텍스트 분할기 임포트
# from langchain_community.document_loaders import PyMuPDFLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter

# # 기존 모듈 재사용
# from app.core import embeddings, vectorstore
# from app.core.vectorstore import VectorTuple
# from app.core.settings import get_settings

# # --- 설정 ---
# # 논문 메타데이터가 담긴 JSON 파일 경로를 지정합니다.
# PAPER_METADATA_PATH = Path(__file__).parent.parent / "data" / "papers_metadata.json"
# print(f"논문 메타데이터 파일 경로: {PAPER_METADATA_PATH.resolve()}")
# # 다운로드할 파일을 임시로 저장할 디렉토리를 지정합니다.
# TEMP_DOC_DIR = "./temp_docs"

# # ⚠️ 최소 청크 길이 설정 (50자 미만은 유의미한 문맥이 부족하다고 판단하여 제외)
# MIN_CHUNK_LENGTH = 50

# # -----------------------------------------------------------------------------
# # 노이즈 판단 헬퍼 함수
# # -----------------------------------------------------------------------------

# def is_structural_noise(text: str) -> bool:
#     """
#     텍스트가 목차, 헤더, 페이지 번호, 또는 웹사이트 탐색 메뉴/광고와 같은
#     구조적 노이즈인지 판단합니다.
#     """
#     cleaned_text = text.strip()
#     if not cleaned_text:
#         return True

#     lines = cleaned_text.split('\n')
#     num_lines = len(lines)

#     # 1. (기존 유지) 텍스트에 연속적인 점(....)이나 공백이 많은지 확인 (단순 목차 패턴)
#     if re.search(r'[\. \-]{10,}', cleaned_text) and len(cleaned_text) < 200:
#         return True

#     # --- 🚨 웹사이트 스크랩 노이즈 감지 (새로 추가/강화된 로직) ---
    
#     # 2. 🚨 광고/프로모션 및 링크 패턴 검사 (가장 확실한 노이즈 유형)
#     # 이모지(🚀), 할인, 등록, 소셜 미디어 링크 등 광고성 키워드 감지
#     noise_patterns = [
#         r'(new courses|off|enroll now|subscribe|join|20%)', # 광고/상업적 문구
#         r'(github|discord|a new tab|social media|guideabout|aboutabout)', # 링크/소셜 미디어/탐색
#         r'[\U0001F600-\U0001F6FF\U00002600-\U000027BF]+', # 이모지 포함
#     ]
#     for pattern in noise_patterns:
#         if re.search(pattern, cleaned_text, re.IGNORECASE | re.DOTALL):
#             print(f"   -> 💥 구조적 노이즈 감지 (광고/링크): {cleaned_text[:30]}...")
#             return True

#     # 3. 🚨 탐색 메뉴/전체 목차 블록 감지 (줄 바꿈 및 짧은 라인 비율)
#     # 청크가 5줄 이상이고, 30자 미만의 짧은 라인이 60% 이상인 경우
#     short_line_count = sum(1 for line in lines if len(line.strip()) < 30 and line.strip() != '')
#     if num_lines >= 5 and (short_line_count / num_lines) >= 0.6: 
#         print(f"   -> 💥 구조적 노이즈 감지 (짧은 줄 반복): {cleaned_text[:30]}...")
#         return True

#     # --- 📚 학술/단순 노이즈 감지 (기존 로직 유지) ---

#     # 4. (기존 유지) 텍스트가 매우 짧고, 오직 숫자, 로마 숫자, 대문자 알파벳으로만 구성된 경우
#     if len(cleaned_text) < 100:
#         # 'I.', 'II.', 'A.', 'B.', 'CHAPTER ONE' 같은 패턴 필터링
#         if re.fullmatch(r'[\s\dIVXLCDM\.\(\)]+', cleaned_text.upper().replace(' ', '')):
#             print("   -> 구조적 노이즈 감지 (로마 숫자/대문자):", cleaned_text)
#             return True
#         # 줄 바꿈과 페이지 번호 패턴만 있는 경우
#         if re.match(r'^[\s\d]*$', cleaned_text):
#             print("   -> 구조적 노이즈 감지 (페이지 번호):", cleaned_text)
#             return True
        
#     return False



# # ----------------------------------------------------------------------
# # 1. 파일 다운로드 및 텍스트 추출 (핵심 로직)
# # ----------------------------------------------------------------------

# def download_and_parse_pdf(paper_metadata: Dict[str, Any]) -> List[str]:
#     """URL에서 PDF를 다운로드하고, 텍스트를 추출하여 유효한 청크만 반환합니다."""
    
#     url = paper_metadata["url"]
#     doc_id = paper_metadata["id"]
#     temp_file_path = Path(TEMP_DOC_DIR) / f"{doc_id}.pdf"
    
#     # 1. 디렉토리 생성
#     Path(TEMP_DOC_DIR).mkdir(exist_ok=True)

#     try:
#         # 2. PDF 다운로드
#         print(f"   -> {doc_id}: 파일 다운로드 중...")
#         response = requests.get(url, stream=True)
#         response.raise_for_status() # HTTP 오류 시 예외 발생
        
#         with open(temp_file_path, 'wb') as f:
#             for chunk in response.iter_content(chunk_size=8192):
#                 f.write(chunk)

#         # 3. PDF 텍스트 추출 및 재귀적 청킹
#         print(f"   -> {doc_id}: 텍스트 추출 및 청킹 중...")
#         loader = PyMuPDFLoader(str(temp_file_path))
#         documents = loader.load()
        
#         # 재귀적 청킹 적용
#         text_splitter = RecursiveCharacterTextSplitter(
#             separators=["\n\n", "\n", ".", " "], 
#             chunk_size=750, 
#             chunk_overlap=150 
#         )
#         split_docs = text_splitter.split_documents(documents)
        
#         # 4. 청크 필터링 및 텍스트 리스트 반환
#         filtered_chunk_texts = []
#         for doc in split_docs:
#             chunk_text = doc.page_content.strip()
            
#             # 💡 1차 필터링: 구조적 노이즈 제거 (강화된 로직 적용)
#             if is_structural_noise(chunk_text):
#                 # print(f"   -> 경고: 구조적 노이즈 제외됨 (목차/광고 추정): {chunk_text[:30]}...")
#                 continue
            
#             # 💡 2차 필터링: 최소 길이 확인
#             if len(chunk_text) >= MIN_CHUNK_LENGTH:
#                 filtered_chunk_texts.append(chunk_text)
#             else:
#                 # print(f"   -> 경고: 너무 짧은 청크 제외됨 (길이: {len(chunk_text)}): {chunk_text[:30]}...")
#                 continue
                
#         print(f"   -> {doc_id}: 총 {len(split_docs)}개 청크 중 {len(filtered_chunk_texts)}개 저장.")
#         return filtered_chunk_texts

#     except Exception as e:
#         print(f"❌ 오류 발생 ({doc_id}): {e}")
#         return []

#     finally:
#         # 5. 임시 파일 정리
#         if temp_file_path.exists():
#             try:
#                 os.remove(temp_file_path)
#             except OSError as e:
#                 print(f"❌ 임시 파일 정리 실패: {e}")




# # ----------------------------------------------------------------------
# # 2. 메인 색인 함수
# # ----------------------------------------------------------------------

# async def index_papers_from_json():
    
#     # 1. JSON 메타데이터 로드
#     if not Path(PAPER_METADATA_PATH).exists():
#         print(f"❌ 메타데이터 파일이 없습니다: {PAPER_METADATA_PATH}")
#         return
    
#     with open(PAPER_METADATA_PATH, 'r', encoding='utf-8') as f:
#         paper_metadata_list = json.load(f)

#     all_vectors_to_upsert: List[VectorTuple] = []
    
#     print(f"총 {len(paper_metadata_list)}개의 논문 메타데이터를 발견했습니다. 색인을 시작합니다.")
    
#     for metadata in paper_metadata_list:
#         paper_id = metadata["id"]
        
#         # 2. 다운로드 및 청킹
#         chunks = download_and_parse_pdf(metadata)
        
#         if not chunks:
#             continue
            
#         print(f"  -> {paper_id}: 최종 {len(chunks)}개의 청크 준비 완료.")

#         # 3. 청크 임베딩
#         vectors = embeddings.embed_texts(chunks) 

#         # 4. Upsert 데이터 준비 (JSON의 메타데이터를 포함)
#         for i, (chunk_text, vector) in enumerate(zip(chunks, vectors)):
#             vector_id = f"{paper_id}_{i}"
            
#             # JSON의 모든 메타데이터를 Pinecone에 저장
#             metadata_for_pinecone = metadata.copy()
#             metadata_for_pinecone["text"] = chunk_text # 실제 텍스트 내용
#             metadata_for_pinecone["chunk_index"] = i   # 청크 순서
            
#             # Pinecone에 저장할 데이터 크기 제한을 위해 큰 필드는 제외할 수 있음
#             metadata_for_pinecone.pop("notes", None) 
            
#             all_vectors_to_upsert.append((vector_id, vector, metadata_for_pinecone))
    
#     # 5. Pinecone에 업로드
#     BATCH_SIZE = 100 # 한 번에 업로드할 벡터의 개수를 100개로 제한 (안전을 위해 50~100 권장)
#     total_vectors = len(all_vectors_to_upsert)

#     print(f"\n총 {total_vectors}개의 벡터를 {BATCH_SIZE}개씩 배치로 Pinecone에 업로드합니다...")

#     for i in range(0, total_vectors, BATCH_SIZE):
#         batch = all_vectors_to_upsert[i:i + BATCH_SIZE]
        
#         # vectorstore.py의 upsert_vectors 함수를 사용하여 배치 업로드
#         try:
#             vectorstore.upsert_vectors(batch)
#             print(f"✅ 배치 {i//BATCH_SIZE + 1} ({len(batch)}개) 업로드 완료.")
#         except Exception as e:
#             print(f"❌ 배치 {i//BATCH_SIZE + 1} 업로드 중 오류 발생: {e}")
#             # 오류 발생 시 다음 배치를 건너뛰지 않고 계속 시도할지 결정해야 합니다.
#             break # 치명적인 오류라면 여기서 중단합니다.

#     print("✅ 논문 데이터 색인 완료.")



# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(index_papers_from_json())

import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core import embeddings, vectorstore
from app.core.vectorstore import VectorTuple

TEMP_DOC_DIR = "./temp_docs"
MIN_CHUNK_LENGTH = 80
PAPER_PATH = Path(__file__).parent.parent / "data" / "Prompt_Engineering.pdf"

# --- 1️⃣ 섹션 제목 패턴 사전 ---
TECHNIQUE_KEYWORDS = {
    "zero-shot": "zero_shot",
    "few-shot": "few_shot",
    "chain-of-thought": "chain_of_thought",
    "react": "react",
    "reflection": "reflection",
    "role prompting": "role_prompting",
    "contextual prompting": "contextual_prompting",
    "knowledge generation": "knowledge_generation",
    "tree of thoughts": "tree_of_thoughts",
    "automatic prompt engineering": "ape"
}


# --- 2️⃣ 노이즈 감지 ---
def is_noise(text: str) -> bool:
    text = text.strip()
    if not text:
        return True
    if re.match(r"^(Prompt Engineering|Author:|February 2025|Table of contents)", text):
        return True
    if len(text) < 40 and re.match(r"^[\s\dIVXLCDM\.\-]+$", text):
        return True
    if text.count("\n") > 6 and sum(len(l) < 25 for l in text.splitlines()) / len(text.splitlines()) > 0.6:
        return True
    return False


# --- 3️⃣ 본문 의미 판단 ---
def is_meaningful(text: str) -> bool:
    ratio_letters = sum(c.isalpha() for c in text) / max(1, len(text))
    if ratio_letters < 0.4:
        return False
    if text.count(".") + text.count("?") + text.count("!") < 1:
        return False
    return True


# --- 4️⃣ PDF 로드 및 청킹 ---
def parse_pdf_to_chunks(pdf_path: str) -> List[Dict[str, Any]]:
    loader = PyMuPDFLoader(pdf_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=120,
        separators=["\n\n", "\n", ".", " "],
    )
    split_docs = splitter.split_documents(documents)

    chunks = []
    current_section = None
    for doc in split_docs:
        text = doc.page_content.strip()
        if is_noise(text):
            continue
        if not is_meaningful(text):
            continue

        # 섹션 제목 감지
        for k in TECHNIQUE_KEYWORDS.keys():
            if re.search(k, text, re.IGNORECASE):
                current_section = k
                break

        chunks.append({
            "text": text,
            "section": current_section or "general",
            "page": getattr(doc.metadata, "page", None)
        })

    print(f"✅ 유효 청크 수: {len(chunks)}")
    return chunks


# --- 5️⃣ 인덱싱 메인 함수 ---
async def index_prompt_engineering_pdf():
    chunks = parse_pdf_to_chunks(str(PAPER_PATH))
    all_vectors: List[VectorTuple] = []

    print("🔄 임베딩 생성 중...")
    texts = [c["text"] for c in chunks]
    vectors = embeddings.embed_texts(texts)

    for i, (vector, chunk) in enumerate(zip(vectors, chunks)):
        section = chunk["section"]
        meta = {
            "title": "Prompt Engineering (Google Cloud, 2025)",
            "section": section,
            "technique": TECHNIQUE_KEYWORDS.get(section, "general"),
            "page": str(chunk["page"]) if chunk.get("page") is not None else "unknown",
            "text": chunk["text"]
        }
        all_vectors.append((f"pe2025_{i}", vector, meta))

    print(f"📤 총 {len(all_vectors)}개 벡터 업로드 중...")
    BATCH_SIZE = 100
    for i in range(0, len(all_vectors), BATCH_SIZE):
        batch = all_vectors[i:i + BATCH_SIZE]
        vectorstore.upsert_vectors(batch)
        print(f"✅ 배치 {i//BATCH_SIZE + 1} 완료.")

    print("🎯 Prompt Engineering PDF 인덱싱 완료!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(index_prompt_engineering_pdf())
