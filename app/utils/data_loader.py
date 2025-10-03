# app/utils/data_loader.py

import json
from typing import Dict, Any, Optional
from pathlib import Path

# 프로젝트 루트를 기준으로 데이터 파일 경로를 지정합니다.
DATA_FILE_PATH = Path(__file__).parent.parent.parent / "data" / "tutorial_info.json"

# 데이터를 캐시할 변수
_TUTORIAL_DATA_CACHE: Optional[Dict[str, Any]] = None

def load_tutorial_data_to_cache() -> Dict[str, Any]:
    """
    tutorial_info.json 파일을 읽어와 {key: item} 형태로 메모리에 캐시합니다.
    """
    global _TUTORIAL_DATA_CACHE

    if _TUTORIAL_DATA_CACHE is None:
        if not DATA_FILE_PATH.exists():
            # ⚠️ 실제 서비스 시에는 에러 처리 필요. 임시로 빈 데이터 반환.
            # 하지만 이 파일은 존재해야 합니다!
            print(f"ERROR: 튜토리얼 데이터 파일이 존재하지 않습니다: {DATA_FILE_PATH}")
            return {}
        
        with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
            data_list = json.load(f)
            
        # 데이터를 key (예: 'flour', 'tomato')를 기준으로 빠르게 찾을 수 있도록 딕셔너리로 변환
        _TUTORIAL_DATA_CACHE = {item['key']: item for item in data_list}
    
    return _TUTORIAL_DATA_CACHE

def get_tutorial_full_text(technique_key: str) -> Optional[str]:
    """
    주어진 technique_key에 해당하는 튜토리얼의 전체 텍스트를 반환합니다.
    """
    data_cache = load_tutorial_data_to_cache()
    
    item = data_cache.get(technique_key)
    
    # 해당 키의 'text' 필드를 반환합니다.
    return item.get('text') if item else None