# analyzer/emotion_claude.py

import hashlib
import os
import json
import re
import requests
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("CLAUDE_API_KEY")

CACHE_DIR = "cache"

def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def load_cache(hash_key: str):
    file_path = os.path.join(CACHE_DIR, f"감정분석_{hash_key}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_cache(hash_key: str, data: dict):
    os.makedirs(CACHE_DIR, exist_ok=True)
    file_path = os.path.join(CACHE_DIR, f"감정분석_{hash_key}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def analyze_emotion_claude(text: str) -> dict:
    hash_key = hash_text(text)
    cached = load_cache(hash_key)
    if cached:
        return cached

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"
    }

    data = {
        "model": "claude-3-7-sonnet-20250219",
        "max_tokens": 1000,
        "temperature": 0.2,
        "messages": [
            {
                "role": "user",
                "content": f"""
다음 사용자의 피드백에서 감정의 흐름과 관련된 무의식적 욕구(40가지 체계 기반)를 추출하라.
출력은 반드시 JSON 형식으로 하되, 다음 구조를 따를 것:

{{
  "감정흐름": ["예: 처음엔 만족했으나 후반부 불만이 증가함", ...],
  "주요감정": ["불안", "기대", "혼란"],
  "관련욕구": [
    {{
      "욕구명": "사회적 인정",
      "분류": "상위욕구",
      "근거": "리뷰 중 '남들도 알아줬으면 좋겠다'라는 표현에서 추론됨"
    }},
    ...
  ]
}}

리뷰:
{text}
                """
            }
        ]
    }

    try:
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)

        if response.status_code == 200:
            result = response.json()
            content_list = result.get("content", [])
            if content_list and isinstance(content_list, list):
                content = content_list[0].get("text", "")
            else:
                content = ""

            # 백틱 감싼 JSON 제거
            content_clean = re.sub(r"```json\n(.*?)\n```", r"\1", content, flags=re.DOTALL)

            try:
                parsed = json.loads(content_clean)
                save_cache(hash_key, parsed)
                return parsed
            except Exception:
                return {"오류": "응답 파싱 실패", "원문": content}
        else:
            return {"오류": f"API 호출 실패 ({response.status_code})", "내용": response.text}

    except Exception as e:
        return {"오류": "요청 중 예외 발생", "내용": str(e)}
