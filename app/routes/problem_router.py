# app/routes/problem_router.py
from fastapi import APIRouter, HTTPException
from data.problems import problems

router = APIRouter()

@router.get("/api/problems/{problem_id}")
def get_problem(problem_id: str):
    if problem_id not in problems:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")
    return problems[problem_id]
