from fastapi import APIRouter

router = APIRouter()

@router.post("/evaluate_prompt")
def evaluate_prompt(user_prompt: str, problem_id: str) -> dict:
    # Placeholder logic for demonstration
    return {
        "techniques": {"few_shot": True, "role": False},
        "quality": {"clarity": 7, "specificity": 6},
        "best_practices": {"natural_korean": 4, "hallucination_safety": 2},
        "feedback": "역할 지정 기법이 빠졌습니다. 문체 지시를 추가해보세요.",
        "outputs": {
            "user": "사용자 프롬프트 결과 텍스트",
            "reference": "정석 프롬프트 결과 텍스트"
        }
    }
