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
            "content": """당신은 'Few-Shot 기법'에 대해 가르쳐주는 친절한 요리사 AI입니다.
                        사용자는 생성형 AI를 처음 사용해 보는 초보 사용자입니다.
                        사용자가 "Few-Shot"과 관련된 질문을 하면, 이해할 수 있게 쉽고 재미있게 설명해주세요.
                        
                        +++) 개발자 입장에서 : 지금 gpt api를 불러서 쓰는 중이라 메시지가 그냥 string 형태로 와서 가독성이 떨어짐.
                        그래서 프론트단에서 처리하게 편하게 너가 문단 구문하면 좋을 것 같은 부분에 '^^'를 넣어서 보내줘.
                        
                        다른 질문에는 "죄송해요, 저는 Few-Shot에 대한 질문에만 답변할 수 있어요." 라고 대답해주세요."""
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



# @app.post("/api/chat")
# async def chat_handler(request: Request):
#     try:
#         data = await request.json()
#         messages_from_client = data.get("messages", [])

#         # ---- 2. GPT API 호출을 위한 메시지 구성 ----
#         # 클라이언트에서 받은 대화 메시지를 GPT API 형식에 맞게 변환합니다.
#         # 가장 최근 메시지부터 역순으로 최대 3개까지만 전달하여 토큰을 절약합니다.
#         gpt_messages = []
#         for msg in messages_from_client:
#             if msg['type'] == 'user':
#                 gpt_messages.append({"role": "user", "content": msg['text']})
#             elif msg['type'] == 'bot':
#                 gpt_messages.append({"role": "assistant", "content": msg['text']})

#         # Few-Shot 기법을 적용하기 위한 시스템 프롬프트
#         system_prompt = {
#             "role": "system",
#             "content": """당신은 'Few-Shot 기법'에 대해 가르쳐주는 친절한 요리사 AI입니다.
#                         사용자는 생성형 AI를 처음 사용해 보는 초보 사용자입니다.
#                         사용자가 "Few-Shot"과 관련된 질문을 하면, 이해할 수 있게 쉽고 재미있게 설명해주세요.
                        
#                         +++) 개발자 입장에서 : 지금 gpt api를 불러서 쓰는 중이라 메시지가 그냥 string 형태로 와서 가독성이 떨어짐.
#                         그래서 프론트단에서 처리하게 편하게 너가 문단 구문하면 좋을 것 같은 부분에 '^^'를 넣어서 보내줘.
                        
#                         다른 질문에는 "죄송해요, 저는 Few-Shot에 대한 질문에만 답변할 수 있어요." 라고 대답해주세요."""
#         }
        
#         # 시스템 프롬프트와 사용자 메시지를 합칩니다.
#         full_conversation = [system_prompt] + gpt_messages

#         # ---- 3. OpenAI API 호출 ----
#         # gpt-4o 모델을 사용하여 대화를 완료합니다.
#         completion = client.chat.completions.create(
#             model="gpt-4o",
#             messages=full_conversation
#         )
        
#         # GPT 모델의 응답 텍스트를 추출합니다.
#         gpt_response_text = completion.choices[0].message.content

#         return {
#             "success": True,
#             "data": {
#                 "text": gpt_response_text
#             }
#         }

#     except Exception as e:
#         print(f"API 호출 중 오류 발생: {e}")
#         return {
#             "success": False,
#             "error": "API 호출에 실패했습니다. 서버 로그를 확인해주세요."
#         }, 500