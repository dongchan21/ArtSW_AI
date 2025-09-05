from fastapi import FastAPI
from app.routes.evaluate import router as evaluate_router
from app.routes.problem_router import router as problem_router
from app.routes.evaluate_router import router as evaluate_router
from app.routes import stream_router, evaluate_only_router

from fastapi.middleware.cors import CORSMiddleware

import os
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
from getpass import getpass

from app.core.settings import get_openai_api_key
from app.routes.debug_router import router as debug_router


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
app.include_router(problem_router, prefix="/api")
app.include_router(evaluate_router, prefix="/api")
app.include_router(debug_router, prefix="/api")
app.include_router(stream_router.router, prefix="/api")
app.include_router(evaluate_only_router.router, prefix="/api")