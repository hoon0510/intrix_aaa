# analyzer/copywriter_gpt.py

import os
import json
import hashlib
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # 이 줄이 있어야 .env 로딩됨


CACHE_DIR = "cache"
COPY_PROMPT_PATH = "prompts/copy_prompt.txt"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_cache_key(data):
    key = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(key.encode("utf-8")).hexdigest()

def load_cache(hash_key):
    path = os.path.join(CACHE_DIR, f"copy_{hash_key}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_cache(hash_key, result):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"copy_{hash_key}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

def load_prompt():
    with open(COPY_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()

def extract_key_desires(strategy_json):
    try:
        return strategy_json["Strategic Messaging Framework"]["Emotional Leverage Points"]
    except:
        return {
            "지배형": ["카피1", "카피2"],
            "도발형": ["카피1", "카피2"],
        }


def generate_copies_from_strategy(strategy_result):
    prompt_template = load_prompt()
    key_desires = extract_key_desires(strategy_result)

    hash_key = get_cache_key(key_desires + json.dumps(strategy_result))
    cached = load_cache(hash_key)
    if cached:
        return cached

    prompt_text = prompt_template + f"\n\n# 입력된 전략 정보:\n{json.dumps(strategy_result, ensure_ascii=False, indent=2)}"

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 본능을 자극하는 카피 전문가입니다."},
                {"role": "user", "content": prompt_text}
            ]
        )
        content = response.choices[0].message.content.strip()
        save_cache(hash_key, content)
        return content

    except Exception as e:
        return {"오류": str(e)}
