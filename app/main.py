
from fastapi import FastAPI
from app.routes.evaluate import router as evaluate_router
from app.routes.problem_router import router as problem_router

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
app.include_router(evaluate_router)

# ✅ CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용: 모든 origin 허용. 실제 서비스 시엔 도메인 명시!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(problem_router, prefix="/api")
