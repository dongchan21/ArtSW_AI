
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.evaluator.evaluate import evaluate_prompt as eval_service

router = APIRouter()

class EvalReq(BaseModel):
    problem_id: str
    user_prompt: str

@router.post("/evaluate_prompt")
def evaluate_prompt_api(req: EvalReq):
    return eval_service(req.user_prompt, req.problem_id)
