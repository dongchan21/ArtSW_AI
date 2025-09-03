from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json, os, re
from typing import Dict, Any, List

from app.services.utils.model_api import chat_complete

router = APIRouter()

DATA_PATH = os.path.join("data", "problems.json")

def load_problems() -> Dict[str, Any]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

class RunEvalRequest(BaseModel):
    problem_id: str
    user_prompt: str
    mode: str = "evaluation"  # "guided" | "evaluation"

class RunEvalResponse(BaseModel):
    problem_id: str
    used_model: str
    user_prompt: str
    reference_prompt: str
    user_output: str
    reference_output: str
    heuristic: Dict[str, Any]
    llm_eval: Dict[str, Any]

# ---- 간단 heuristic 검사기들 ----
def contains_role(prompt: str) -> bool:
    # "너는 ~한 역할이다" 류 탐지 (국문/영문 일부)
    patts = [
        r"(너는|당신은)\s?.{0,10}\s?(전문가|교사|상담사|작가|가이드|플래너)",
        r"you are (an?|the)\s.+",
    ]
    return any(re.search(p, prompt, re.IGNORECASE) for p in patts)

def contains_few_shot(prompt: str) -> bool:
    # 예시 구간 여부(--- 예시 ---), "예시:" 등 단서
    patts = [r"예시[:：]", r"examples?[:：]", r"k-?shot", r"few[-\s]?shot"]
    return any(re.search(p, prompt, re.IGNORECASE) for p in patts)

def contains_markdown_format(prompt: str) -> bool:
    # 제목, 리스트, 표 등 출력 형식 강제 흔적
    patts = [r"^# ", r"^- ", r"\|.+\|", r"## ", r"출력 형식", r"형식:", r"포맷:"]
    return any(re.search(p, prompt, re.IGNORECASE | re.MULTILINE) for p in patts)

def contains_cot(prompt: str) -> bool:
    # 단계별 사고 유도
    patts = [r"단계별로", r"step[-\s]?by[-\s]?step", r"생각의 과정을", r"chain of thought"]
    return any(re.search(p, prompt, re.IGNORECASE) for p in patts)

def contains_react(prompt: str) -> bool:
    # Thought/Action/Observation 키워드 일부
    patts = [r"Thought:", r"Action:", r"Observation:", r"ReAct"]
    return any(re.search(p, prompt, re.IGNORECASE) for p in patts)

def contains_hallu_induce(prompt: str) -> bool:
    # 상상력/창작 허용 문구
    patts = [r"상상력을 발휘", r"창의적으로", r"지어내도", r"허구적"]
    return any(re.search(p, prompt, re.IGNORECASE) for p in patts)

def heuristic_score(user_prompt: str, expected_skills: List[str]) -> Dict[str, Any]:
    # 6개 기법 기준으로 플래그+스코어링
    detectors = {
        "few_shot": contains_few_shot,
        "role": contains_role,
        "markdown_format": contains_markdown_format,
        "chain_of_thought": contains_cot,
        "react": contains_react,
        "hallucination": contains_hallu_induce,
    }
    flags = {k: (detectors[k](user_prompt) if k in detectors else False) for k in expected_skills}
    score = sum(1 for v in flags.values() if v)
    return {
        "expected_skills": expected_skills,
        "flags": flags,
        "score": score,
        "total": len(expected_skills),
        "ratio": (score / max(1, len(expected_skills))),
    }

# ---- LLM 기반 평가 프롬프트 ----
LLM_EVAL_SYSTEM = "You are a strict prompt-engineering TA. Return JSON only."
LLM_EVAL_USER_TMPL = """다음은 문제와 두 개의 프롬프트 결과입니다.

[문제 설명]
{title}
{description}

[요구 기법]
{skills}

[사용자 프롬프트]
{user_prompt}

[사용자 결과]
{user_output}

[정석 프롬프트]
{ref_prompt}

[정석 결과]
{ref_output}

아래 JSON 스키마로만 평가 결과를 주세요. 근데 점수를 좀 짜게 줬으면 좋겠어요.
 쓸만하고, 잘 작성된 프롬프트 정도면 60점 정도.(설명 없이 JSON만):
{{
  "quality": {{
    "clarity": 0-10,
    "specificity": 0-10,
    "appropriateness": 0-10,
    "creativity": 0-10
  }},
  "techniques_used": ["role", "few_shot", "..."],
  "missing_techniques": ["..."],
  "feedback": "사용자가 작성한 프롬프트를 평가해줘. 정석 프롬프트에 비해 뭐가 부족하고, 뭘 잘했는지.",
  "overall_score": 0-100
}}
"""

@router.post("/run_and_evaluate", response_model=RunEvalResponse)
def run_and_evaluate(body: RunEvalRequest):
    problems = load_problems()
    if body.problem_id not in problems:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")

    prob = problems[body.problem_id]
    expected_type = prob.get("expected_output_type", "text")
    ref_prompt = prob.get("reference_prompt", "")
    title = prob.get("title", "")
    desc = prob.get("description", "")
    skills = prob.get("skills_required", [])

    # 1) 사용자 프롬프트 실행 (텍스트 기준)
    user_output = ""
    reference_output = ""

    # 이미지 타입이면 실제 생성 대신 프롬프트 에코/설명으로 대체(개발 초기)
    if expected_type == "image":
        user_output = "(이미지 생성 문제입니다. 현재는 텍스트로 프롬프트만 평가합니다.)"
        reference_output = "(이미지 생성 문제입니다. 현재는 텍스트로 프롬프트만 평가합니다.)"
    else:
        try:
            user_output = chat_complete(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": body.user_prompt},
                ],
                max_tokens=600,
            )
        except Exception as e:
            user_output = f"(생성 실패: {e})"

        try:
            reference_output = chat_complete(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": ref_prompt},
                ],
                max_tokens=600,
            )
        except Exception as e:
            reference_output = f"(정석 생성 실패: {e})"

    # 2) 휴리스틱 스코어
    h = heuristic_score(body.user_prompt, skills)

    # 3) LLM 평가 (JSON만 받도록 유도)
    llm_eval_raw = "{}"
    try:
        llm_eval_raw = chat_complete(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": LLM_EVAL_SYSTEM},
                {"role": "user", "content": LLM_EVAL_USER_TMPL.format(
                    title=title,
                    description=desc,
                    skills=", ".join(skills),
                    user_prompt=body.user_prompt,
                    user_output=user_output,
                    ref_prompt=ref_prompt,
                    ref_output=reference_output,
                )},
            ],
            temperature=0.2,
            max_tokens=500,
        )
        # JSON 파싱 시도
        import json
        llm_eval = json.loads(llm_eval_raw)
    except Exception:
        llm_eval = {
            "quality": {"clarity": 0, "specificity": 0, "appropriateness": 0, "creativity": 0},
            "techniques_used": [],
            "missing_techniques": [k for k, v in h["flags"].items() if not v],
            "feedback": "LLM 평가에 실패했습니다. 휴리스틱 결과를 참고하세요.",
            "overall_score": int(h["ratio"] * 100),
            "_raw": llm_eval_raw,
        }

    return RunEvalResponse(
        problem_id=body.problem_id,
        used_model="gpt-4o-mini",
        user_prompt=body.user_prompt,
        reference_prompt=ref_prompt,
        user_output=user_output,
        reference_output=reference_output,
        heuristic=h,
        llm_eval=llm_eval,
    )
