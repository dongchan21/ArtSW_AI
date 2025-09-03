# app/routes/problem_router.py
from fastapi import APIRouter, HTTPException
from data.problems import problems
from pydantic import BaseModel


router = APIRouter()

@router.get("/problems/{problem_id}")
def get_problem(problem_id: str):
    if problem_id not in problems:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")
    return problems[problem_id]

class PromptSubmission(BaseModel):
    problem_id: str
    user_prompt: str

@router.post("/submit_prompt")
def submit_prompt(data: PromptSubmission):
    print(f"사용자 프롬프트 제출됨: 문제 ID = {data.problem_id}, 프롬프트 = {data.user_prompt}")
    return {"message": "프롬프트가 성공적으로 제출되었습니다."}

@router.get("/problems")
def list_problems():
    print("🔍 [GET] /problems 요청 도착")
    return problems

class PromptEvaluationRequest(BaseModel):
    problem_id: str
    user_prompt: str

@router.post("/api/evaluate_prompt")
def evaluate_prompt(data: PromptEvaluationRequest):
    if data.problem_id not in problems:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")
    
    ref_prompt = problems[data.problem_id]["reference_prompt"]
    skills = problems[data.problem_id]["skills_required"]

    user_prompt = data.user_prompt.strip().lower()

    # 간단한 평가 기준 예시
    score = 0
    feedback = []

    for skill in skills:
        if skill in user_prompt:
            score += 1
            feedback.append(f"✅ '{skill}' 요소가 잘 반영되어 있습니다.")
        else:
            feedback.append(f"⚠️ '{skill}' 요소가 부족하거나 누락되었습니다.")

    return {
        "score": score,
        "total": len(skills),
        "feedback": feedback
    }