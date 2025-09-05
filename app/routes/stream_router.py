# app/routes/stream_router.py
from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.responses import JSONResponse
from openai import OpenAI
import os, json

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DATA_PATH = os.path.join("data", "problems.json")

def load_problems():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def make_stream(messages, model="gpt-4o-mini"):
    def sse_events():
        stream = client.chat.completions.create(
            model=model, messages=messages, stream=True
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and getattr(delta, "content", None):
                yield f"data: {json.dumps({'delta': delta.content})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(sse_events(), media_type="text/event-stream")

@router.post("/chat/stream_user")
def chat_stream_user(payload = Body(...)):
    problem_id = payload.get("problem_id", "")
    user_prompt = payload.get("user_prompt", "")
    if not problem_id or not user_prompt:
        raise HTTPException(status_code=422, detail="problem_id, user_prompt 필요")

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_prompt},
    ]
    return make_stream(messages, model=payload.get("model", "gpt-4o-mini"))

@router.post("/chat/stream_reference_by_problem")
def chat_stream_reference_by_problem(payload = Body(...)):
    problem_id = payload.get("problem_id", "")
    if not problem_id:
        raise HTTPException(status_code=422, detail="problem_id 필요")

    problems = load_problems()
    prob = problems.get(problem_id)
    if not prob:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")

    ref_prompt = prob.get("reference_prompt")
    if not ref_prompt:
        raise HTTPException(status_code=404, detail="reference_prompt 없음")

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": ref_prompt},
    ]
    return make_stream(messages, model=payload.get("model", "gpt-4o-mini"))

@router.post("/chat/generate_reference_full")
def generate_reference_full(payload = Body(...)):
    problem_id = payload.get("problem_id")
    model = payload.get("model", "gpt-4o-mini")
    if not problem_id:
        raise HTTPException(status_code=422, detail="problem_id 필요")

    prob = load_problems().get(problem_id)
    if not prob or not prob.get("reference_prompt"):
        raise HTTPException(status_code=404, detail="reference_prompt 없음")

    ref_prompt = prob["reference_prompt"]
    comp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": ref_prompt},
        ],
        stream=False,
    )
    text = comp.choices[0].message.content or ""
    return JSONResponse({"reference_output": text})