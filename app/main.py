from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.chat_router import router as chat_router

import os
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
from getpass import getpass

from app.core.settings import get_openai_api_key


app = FastAPI()

try:
    ok = bool(get_openai_api_key())
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

@app.get("/")
def read_root():
    return {"message": "Welcome to the Pizza Tutorial API!"}