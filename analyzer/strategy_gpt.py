import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from analyzer.copywriter_gpt import generate_copies_from_strategy

load_dotenv()

PROMPT_DIR = "prompts"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_strategy_gpt(claude_result):
    try:
        if not isinstance(claude_result, dict):
            return {"오류": "Claude 결과가 dict 형식이 아님", "원문": str(claude_result)}

        prompt_old = open(os.path.join(PROMPT_DIR, "strategy_existing.txt"), "r", encoding="utf-8").read()
        prompt_new = open(os.path.join(PROMPT_DIR, "strategy_new.txt"), "r", encoding="utf-8").read()

        merged_prompt = prompt_old + "\n\n" + prompt_new
        user_prompt = json.dumps(claude_result, ensure_ascii=False)

        # 첫 번째 시도: 일반적인 전략 분석 요청
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 세계 최고의 마케팅 전략 기획자입니다."},
                {"role": "user", "content": merged_prompt + "\n\n" + user_prompt}
            ]
        )

        if not hasattr(response, "choices") or not response.choices:
            return {"오류": "GPT 응답에 choices 필드가 없음", "원문": str(response)}

        result_text = response.choices[0].message.content.strip()

        if not result_text:
            return {"오류": "GPT 응답이 비어 있음", "원문": "(응답 없음)"}

        # JSON 형식인지 확인
        if not (result_text.startswith('{') and result_text.endswith('}')):
            # 두 번째 시도: JSON 형식으로 응답하도록 명시적 요청
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "당신은 세계 최고의 마케팅 전략 기획자입니다. 반드시 JSON 형식으로 응답해야 합니다."},
                    {"role": "user", "content": "다음 템플릿을 사용해 JSON 형식으로 응답해주세요:\n" + merged_prompt + "\n\n" + user_prompt}
                ]
            )

            if not hasattr(response, "choices") or not response.choices:
                return {"오류": "GPT 두 번째 응답에 choices 필드가 없음", "원문": str(response)}

            result_text = response.choices[0].message.content.strip()

        if not hasattr(response, "choices") or not response.choices:
            return {"오류": "GPT 응답에 choices 필드가 없음", "원문": str(response)}

        result_text = response.choices[0].message.content.strip()

        if not result_text:
            return {"오류": "GPT 응답이 비어 있음", "원문": "(응답 없음)"}

        if isinstance(result_text, str):
            try:
                # 템플릿 변수 대체
                replacements = {
                    '"{product_name}"': '"제품명 미정"',
                    '"{category}"': '"카테고리 미정"',
                    '"{features}"': '"특징 미정"',
                    '"{competitors}"': '"경쟁사 미정"',
                    '"{target_customers}"': '"타겟 고객 미정"',
                    '"{purpose}"': '"목적 미정"',
                    '{emotion_analysis_json}': json.dumps(claude_result, ensure_ascii=False)
                }
                
                # JSON 시작과 끝 위치 찾기
                json_start = result_text.find('{')
                json_end = result_text.rfind('}')
                if json_start == -1 or json_end == -1:
                    return {"오류": "GPT 응답에서 JSON 형식을 찾을 수 없음", "원문": result_text}
                
                # JSON 부분만 추출하고 템플릿 변수 대체
                json_text = result_text[json_start:json_end + 1]
                for template, value in replacements.items():
                    json_text = json_text.replace(template, value)
                
                result_json = json.loads(json_text)
            except Exception as e:
                return {
                    "오류": f"GPT 응답 파싱 오류: {str(e)}",
                    "원문": result_text,
                    "디버그": f"JSON 시작: {json_start}, JSON 끝: {json_end}, 처리된 JSON: {json_text}"
                }
        elif isinstance(result_text, dict):
            result_json = result_text
        else:
            return {"오류": "GPT 응답이 문자열도 딕셔너리도 아님", "원문": str(result_text)}

        # 카피 생성
        copy_output = generate_copies_from_strategy(result_json)
        if isinstance(copy_output, dict):
            result_json["Generated Copies"] = copy_output
        else:
            result_json["Generated Copies"] = {"오류": "카피 생성 실패", "결과": copy_output}

        # 슬로건 생성
        try:
            slogan_prompt = open(os.path.join(PROMPT_DIR, "copy_prompt.txt"), "r", encoding="utf-8").read()
            slogan_input = f"포지셔닝 슬로건 생성용 전략 요약:\n{json.dumps(result_json, ensure_ascii=False, indent=2)}"

            slogan_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "당신은 본능을 자극하는 슬로건 카피 전문가입니다."},
                    {"role": "user", "content": slogan_prompt + "\n\n" + slogan_input}
                ]
            )
            result_json["Positioning Slogan"] = slogan_response.choices[0].message.content.strip()
        except Exception as e:
            result_json["Positioning Slogan"] = f"슬로건 생성 실패: {str(e)}"

        return result_json

    except Exception as e:
        return {"오류": f"전략 분석 중 내부 오류: {str(e)}"}
