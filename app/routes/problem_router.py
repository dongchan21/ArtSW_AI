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