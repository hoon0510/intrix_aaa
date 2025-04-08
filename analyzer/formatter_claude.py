# analyzer/formatter_claude.py

import os
import json
import hashlib
import requests

CACHE_DIR = "cache"

ANTHROPIC_API_KEY = os.getenv("CLAUDE_API_KEY")
MODEL_NAME = "claude-3-7-sonnet-20250219"
ENDPOINT = "https://api.anthropic.com/v1/messages"

headers = {
    "x-api-key": ANTHROPIC_API_KEY,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json"
}

def get_cache_key(data):
    key = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(key.encode("utf-8")).hexdigest()

def load_cache(hash_key):
    path = os.path.join(CACHE_DIR, f"format_{hash_key}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_cache(hash_key, result):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"format_{hash_key}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

def format_strategy_result(strategy_result):
    hash_key = get_cache_key(strategy_result)
    cached = load_cache(hash_key)
    if cached:
        return cached

    user_prompt = f"""
다음은 마케팅 전략 분석 결과입니다.
카피는 제외하고 전체 내용을 정리된 문서 형태로 포맷팅하세요.
실무자가 마케팅 전략 기획안으로 곧바로 활용할 수 있도록 구조화하십시오.
결과의 본질적 내용과 카피, 슬로건은 절대 수정하지 말고, 나머지 내용 전체를 구조화하고 세계적인 마케팅 전략 전문가가 작성한 기획안으로 만들어주세요.

<입력 원문>
{json.dumps(strategy_result, ensure_ascii=False, indent=2)}
"""

    payload = {
        "model": MODEL_NAME,
        "max_tokens": 4096,
        "temperature": 0.3,
        "messages": [
            {"role": "user", "content": user_prompt}
        ]
    }

    try:
        response = requests.post(ENDPOINT, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            content = result.get("content", [{}])[0].get("text", "")
            save_cache(hash_key, content)
            return content
        else:
            return {"오류": f"API 호출 실패 ({response.status_code})", "내용": response.text}
    except Exception as e:
        return {"오류": str(e)}