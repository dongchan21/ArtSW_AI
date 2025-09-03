from openai import OpenAI
from app.core.settings import get_openai_api_key

_client = None  # 모듈 전역 캐시

def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=get_openai_api_key())
    return _client

def chat_complete(messages, model="gpt-4o-mini", temperature=0.7, max_tokens=800):
    client = get_client()
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()
