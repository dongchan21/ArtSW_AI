# app/routes/evaluate_only_router.py (새 파일 권장)
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
import json, os, re
from typing import Dict, Any, List

from app.routes.evaluate_router import heuristic_score, LLM_EVAL_SYSTEM, LLM_EVAL_USER_TMPL
from app.services.utils.model_api import chat_complete

router = APIRouter()

DATA_PATH = os.path.join("data", "problems.json")
def load_problems():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

class EvaluateOnlyReq(BaseModel):
    problem_id: str
    user_prompt: str
    user_output: str
    reference_output: str
    mode: str = "evaluation"  # guided|evaluation

@router.post("/run_evaluate_only")
def run_evaluate_only(body: EvaluateOnlyReq):
    problems = load_problems()
    prob = problems.get(body.problem_id)
    if not prob:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")

    title = prob.get("title","")
    desc = prob.get("description","")
    skills = prob.get("skills_required",[])
    ref_prompt = prob.get("reference_prompt","")

    # 휴리스틱
    h = heuristic_score(body.user_prompt, skills)

    # LLM 평가 (출력은 이미 전달받음 → 재생성 없음)
    try:
        llm_eval_raw = chat_complete(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content": LLM_EVAL_SYSTEM},
                {"role":"user","content": LLM_EVAL_USER_TMPL.format(
                    title=title,
                    description=desc,
                    skills=", ".join(skills),
                    user_prompt=body.user_prompt,
                    user_output=body.user_output,
                    ref_prompt=ref_prompt,
                    ref_output=body.reference_output,
                )},
            ],
            temperature=0.2,
            max_tokens=500,
        )
        # 안전 파싱
        import re as _re, json as _json
        m = _re.search(r"\{[\s\S]*\}$", llm_eval_raw.strip())
        llm_eval = _json.loads(m.group(0) if m else "{}")
    except Exception:
        llm_eval = {
            "quality": {"clarity":0,"specificity":0,"appropriateness":0,"creativity":0},
            "techniques_used": [],
            "missing_techniques": [k for k,v in h["flags"].items() if not v],
            "feedback": "LLM 평가에 실패했습니다. 휴리스틱 결과를 참고하세요.",
            "overall_score": int(h["ratio"]*100),
        }

    # 프롬프트/출력은 응답에 넣지 않음
    return {
        "problem_id": body.problem_id,
        "heuristic": h,
        "llm_eval": llm_eval,
    }
