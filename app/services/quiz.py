import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import time
from openai import OpenAI # OpenAI 라이브러리 임포트


# ---- 1. API 키 설정 ----
load_dotenv()

# ---- API 키를 환경 변수에서 가져옵니다. ----
openai_api_key = os.getenv("OPENAI_API_KEY")

# API 클라이언트 초기화
client = OpenAI(api_key=openai_api_key)

app = FastAPI()

# CORS(Cross-Origin Resource Sharing) 설정
origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- 5. GPT 채점 함수 ----
async def evaluate_prompt(messages_from_client: list):
    """
    유저가 보낸 Role Prompting 프롬프트를 GPT로 평가하여
    'True' 또는 'False' 중 하나를 반환.
    """
    gpt_messages = []

    # GPT 메시지 포맷으로 변환
    for msg in messages_from_client:
        if msg.get("type") == "user":
            gpt_messages.append({"role": "user", "content": msg.get("text", "")})
        elif msg.get("type") == "bot":
            gpt_messages.append({"role": "assistant", "content": msg.get("text", "")})

    # GPT에게 주는 시스템 프롬프트
    system_prompt = {
        "role": "system",
        "content": """
당신은 프롬프팅 학습 플랫폼의 채점자입니다.
사용자가 Role Prompting 프롬프트를 작성했습니다.

규칙:
1️⃣ 사용자가 역할(Role), 상황(Situation), 목적(Objective)을 포함하여 작성했다면 'True'를 반환.
2️⃣ 이 3가지 중 일부라도 명확하지 않거나 문장이 단순 지시문이라면 'False'를 반환.
3️⃣ **반드시** 'True' 또는 'False' 둘 중 하나의 단어만 출력하세요. 다른 설명이나 문장은 금지합니다.

예시:
- "당신은 취업 준비생이다. 면접관에게 인공지능의 장단점을 설명하라." → True
- "인공지능의 장단점을 설명해줘." → False
        """
    }

    # 전체 대화 구성
    full_conversation = [system_prompt] + gpt_messages

    # GPT 호출
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=full_conversation,
        temperature=0  # 답변 일관성을 위해 0으로 고정
    )

    # GPT 결과 텍스트
    raw_response = completion.choices[0].message.content.strip()

    # 문자열 정리 — True/False 외의 다른 답변 방지
    is_valid = raw_response.lower() == "true"

    # 결과 반환
    return {
        "success": True,
        "data": {
            "text": "True" if is_valid else "False"
        }
    }


# ---- 6. API 엔드포인트 ----
@app.post("/api/evaluate/role-prompting")
async def evaluate_role_prompting(request: Request):
    """
    프론트엔드에서 메시지를 받아 채점 결과(True/False)를 반환하는 엔드포인트.
    """
    try:
        data = await request.json()
        messages = data.get("messages", [])

        result = await evaluate_prompt(messages)
        return result

    except Exception as e:
        print("❌ Error while evaluating prompt:", e)
        return {
            "success": False,
            "error": "서버 처리 중 오류가 발생했습니다."
        }
