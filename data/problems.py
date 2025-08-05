import json

problems = {
    "story_001": {
        "title": "우정과 이별을 주제로 단편소설 생성",
        "description": "AI에게 단편소설을 작성하라고 요청하세요. 주제는 '우정과 이별'입니다.",
        "expected_output_type": "text",
        "skills_required": ["few_shot", "role", "markdown_format"],
        "reference_prompt": (
            "당신은 섬세한 감성의 소설 작가입니다. 우정과 이별을 주제로 단편소설을 써주세요.\n"
            "이야기의 전개가 자연스럽고, 감정의 흐름이 드러나야 합니다.\n\n"
            "- 제목:\n- 등장인물:\n- 줄거리:"
        ),
        "reference_result": "한때 가장 친했던 두 친구, 지민과 태현은...",
        "tags": ["감성", "창작", "문체", "story"]
    },
    "image_002": {
        "title": "요리 이미지 생성",
        "description": "식욕을 자극하는 파스타 요리를 AI 이미지로 생성하세요.",
        "expected_output_type": "image",
        "skills_required": ["few_shot", "hallucination", "clarity"],
        "reference_prompt": (
            "High-resolution image of creamy truffle pasta on a dark wooden table, "
            "steam rising, soft natural lighting, garnished with parsley --v 5 --ar 3:2"
        ),
        "reference_result": "https://example.com/image_reference/pasta.png",
        "tags": ["음식", "시각", "이미지 생성", "midjourney"]
    },
    "explanation_003": {
        "title": "수험생을 위한 상대성이론 개념 설명",
        "description": "고등학생 수험생이 이해할 수 있도록 상대성이론 개념을 설명하도록 AI에 요청하세요.",
        "expected_output_type": "text",
        "skills_required": ["role", "chain_of_thought", "clarity"],
        "reference_prompt": (
            "당신은 고등학생 과외 선생님입니다. 수험생이 이해할 수 있도록 상대성이론을 비유와 예시를 통해 설명해주세요.\n"
            "복잡한 개념은 쉽게 나누어 설명해주세요."
        ),
        "reference_result": "상대성이론은 크게 두 가지로 나뉩니다. 첫 번째는 특수상대성이론...",
        "tags": ["교육", "물리학", "설명", "학생"]
    },
    "analysis_004": {
        "title": "AI가 작성한 자기소개서 분석",
        "description": "AI가 작성한 자기소개서에 대해 AI가 스스로 피드백을 주도록 요청하세요.",
        "expected_output_type": "text",
        "skills_required": ["markdown_format", "role", "clarity"],
        "reference_prompt": (
            "당신은 경력 10년 이상의 커리어 컨설턴트입니다. 아래 자기소개서를 평가하고, 장점과 단점, 개선 포인트를 알려주세요.\n\n"
            "[자기소개서]\n고등학교 시절부터 로봇에 흥미를 느껴..."
        ),
        "reference_result": "장점: 주제 의식이 뚜렷하고 목표가 명확함...",
        "tags": ["리뷰", "자소서", "분석", "role"]
    },
    "search_005": {
        "title": "여행 추천 검색 시뮬레이션",
        "description": "봄에 부모님과 함께 떠나기 좋은 여행지를 AI가 추천하게 하세요.",
        "expected_output_type": "text",
        "skills_required": ["react", "role", "chain_of_thought"],
        "reference_prompt": (
            "당신은 여행 플래너입니다. 부모님과 함께 봄에 떠나기 좋은 국내 여행지를 추천해주세요. "
            "지역별 장점과 교통, 예상 경비도 포함해 주세요."
        ),
        "reference_result": "전주 한옥마을은 봄철에 특히 어르신들이 좋아하는 장소입니다...",
        "tags": ["여행", "추천", "검색", "리액트"]
    }
}

with open("data/problems.json", "w", encoding="utf-8") as f:
    json.dump(problems, f, ensure_ascii=False, indent=2)
