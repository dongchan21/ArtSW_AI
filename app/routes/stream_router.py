# app/routes/stream_router.py
from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse
from openai import OpenAI
import os, json

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/chat/stream")
def chat_stream(payload = Body(...)):
    messages = payload.get("messages", [])
    model = payload.get("model", "gpt-4o-mini")

    def sse_events():
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and getattr(delta, "content", None):
                yield f"data: {json.dumps({'delta': delta.content})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_events(), media_type="text/event-stream")
