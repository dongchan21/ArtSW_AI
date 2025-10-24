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

# ✅ Role Prompting 전용 챗봇 함수
async def generate_response(messages_from_client: list):
    """
    사용자가 보낸 메시지를 Role Prompting 전용 챗봇으로 전달하여 응답을 생성합니다.
    """

    # 메시지 포맷 변환
    gpt_messages = []
    for msg in messages_from_client:
        if msg.get("type") == "user":
            gpt_messages.append({"role": "user", "content": msg.get("text", "")})
        elif msg.get("type") == "bot":
            gpt_messages.append({"role": "assistant", "content": msg.get("text", "")})

    # ✅ Role Prompting 전용 system 프롬프트
    system_prompt = {
        "role": "system",
        "content": """
당신은 'Role Prompting' 기법을 전문적으로 가르쳐주는 집사 AI입니다.

🎩 역할:
- Role Prompting에 관한 개념, 원리, 예시, 활용법 등을 자세히 설명할 수 있습니다.
- 다른 프롬프팅 기법(Few-shot, Chain-of-Thought, RAG 등)에 대한 질문이 오면
  간단히 개념만 언급하고 마지막에 이렇게 말해야 합니다:
  👉 "전 Role Prompting을 담당하는 집사예요. 우리 Role Prompting 얘기를 해볼까요?"

🧠 규칙:
1️⃣ Role Prompting 관련 질문이라면, 구체적인 예시와 함께 친절하게 설명하세요.
2️⃣ Few-shot, Reflection 등 다른 프롬프팅 기법은 짧게 정의만 설명한 뒤 반드시 위 멘트를 덧붙이세요.
3️⃣ 프롬프팅 기법과 전혀 관련 없는 질문(예: 날씨, 음식, 취미 등)에 대해서는
   반드시 이렇게 대답하세요:
   👉 "죄송해요. 전 프롬프팅 기법에 관한 질문만 답변할 수 있어요."
4️⃣ 답변은 항상 자연스러운 대화체로, 존댓말을 사용하세요.
5️⃣ 'Role Prompting'이라는 단어는 강조 표시로 (예: **Role Prompting**) 해주세요.
        """
    }

    full_conversation = [system_prompt] + gpt_messages

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=full_conversation,
        temperature=0.7,
    )

    gpt_response = completion.choices[0].message.content.strip()

    return {
        "success": True,
        "data": {
            "text": gpt_response
        }
    }