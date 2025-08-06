
from fastapi import APIRouter, Body
from app.services.evaluator.evaluate import evaluate_prompt

router = APIRouter()

@router.post("/evaluate_prompt")
def evaluate(prompt: str = Body(...), problem_id: str = Body(...)):
    return evaluate_prompt(prompt, problem_id)