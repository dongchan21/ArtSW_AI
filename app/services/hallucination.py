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


async def generate_response(messages_from_client: list):
    
    gpt_messages = []
    for msg in messages_from_client:
        # GPT API 호출에 맞게 메시지 포맷을 변환합니다.
        if msg['type'] == 'user':
            gpt_messages.append({"role": "user", "content": msg['text']})
        elif msg['type'] == 'bot':
            gpt_messages.append({"role": "assistant", "content": msg['text']})
    
    system_prompt = {
            "role": "system",
            "content": """당신은 '할루시네이션 유도 기법'에 대해 가르쳐주는 친절한 AI입니다.
                        사용자는 생성형 AI를 처음 사용해 보는 초보 사용자입니다.
                        사용자가 "할루시네이션"과 관련된 질문을 하면, 이해할 수 있게 쉽고 재미있게 설명해주세요.

                        **주제 이탈 시:** 할루시네이션에 관련 없는 질문은 **최대한 간결하게** 답변하고, "우리 할루시네이션에 대한 얘기를 해볼까요?"라고 마무리합니다."""
        }
    
    full_conversation = [system_prompt] + gpt_messages


    completion = client.chat.completions.create(
            model="gpt-4o",
            messages=full_conversation
        )

    gpt_response_text = completion.choices[0].message.content

    return {
            "success": True,
            "data": {
                "text": gpt_response_text
            }
        }
