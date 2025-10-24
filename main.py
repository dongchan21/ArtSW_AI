#uvicorn app.main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.chat_router import router as chat_router
from app.api import chat

import os
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
from getpass import getpass

from app.core.settings import get_settings


app = FastAPI(
    title="RAG Tutorial Chatbot API",
    version="1.0.0",
    description="튜토리얼 지식 기반 RAG 챗봇 서비스"
)

try:
    ok = bool(get_settings())
    print("OPENAI_API_KEY loaded?", ok)
except Exception as e:
    print("ENV LOAD ERROR:", e)

# ✅ CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용: 모든 origin 허용. 실제 서비스 시엔 도메인 명시!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")
# app.include_router(chat.router, prefix="/api/chat", tags=["rag_chat"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Pizza Tutorial API!"}