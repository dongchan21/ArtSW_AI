from fastapi import APIRouter, HTTPException, Request
from app.services import few_shot, role_prompting, rag, reflexion, markdown_template, hallucination

router = APIRouter()

@router.post("/chat/{ingredient_name}")
async def handle_chat(ingredient_name: str, request: Request):
    data = await request.json()
    messages = data.get("messages", [])

    if ingredient_name == "flour": # 밀가루 -> Few-Shot
        response_text = await few_shot.generate_response(messages)
    elif ingredient_name == "tomato": # 토마토 -> 역할 지정
        response_text = await role_prompting.generate_response(messages)
    elif ingredient_name == "cheese": # 치즈 -> 마크다운 템플릿
        response_text = await markdown_template.generate_response(messages)
    elif ingredient_name == "pepperoni": # 페퍼로니 -> 할루시네이션 유도
        response_text = await hallucination.generate_response(messages)
    elif ingredient_name == "olive": # 올리브 -> RAG
        response_text = await rag.generate_response(messages)
    elif ingredient_name == "basil": # 바질 -> Reflexion
        response_text = await reflexion.generate_response(messages)
    
    else:
        raise HTTPException(status_code=404, detail="재료를 찾을 수 없습니다.")

    return {
        "success": True,
        "data": {
            "text": response_text
        }
    }