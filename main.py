# main.py

import os
import json
import streamlit as st
from dotenv import load_dotenv

from analyzer.emotion_claude import analyze_emotion_claude
from analyzer.strategy_gpt import analyze_strategy_gpt
from analyzer.copywriter_gpt import generate_copies_from_strategy
from analyzer.formatter_claude import format_strategy_result

load_dotenv()

st.set_page_config(page_title="Intrix 분석기", page_icon="🧠")
st.title("🎯 전략 설계 결과")

user_input = st.text_area("리뷰 또는 인터뷰 텍스트 입력", height=250)

if st.button("전략 설계 실행"):
    with st.spinner("감정 및 욕구 분석 중..."):
        emotion_result = analyze_emotion_claude(user_input)

    if "오류" in emotion_result:
        st.error("분석 중 오류 발생:")
        st.code(emotion_result)
    else:
        st.success("감정 및 욕구 분석 완료")
        st.markdown("### 1. 감정 및 욕구 요약")
        st.markdown(format_strategy_result(emotion_result), unsafe_allow_html=True)

        with st.spinner("GPT 전략 설계 진행 중..."):
            strategy_result = analyze_strategy_gpt(emotion_result)

        if "오류" in strategy_result:
            st.error("전략 분석 실패")
            st.code(strategy_result)
        else:
            st.success("전략 분석 완료")
            st.markdown("### 2. 전략 기획안 전체")
            st.markdown("#### 📄 전체 구조 (JSON)")
            with st.expander("전략 전체 JSON 보기"):
                st.json(strategy_result)

            if "Formatted Document" in strategy_result:
                st.markdown("#### 📘 실무용 전략 문서")
                st.markdown(strategy_result["Formatted Document"], unsafe_allow_html=True)

            with st.spinner("카피라이팅 자동 생성 중..."):
                copies = generate_copies_from_strategy(strategy_result)

            if isinstance(copies, dict):
                st.success("카피 생성 완료")
                st.markdown("### 3. 스타일별 카피 제안")
                if isinstance(copies, dict):  # 반드시 딕셔너리인지 체크
                    for style, lines in copies.items():
                        st.markdown(f"**{style}**")
                        for line in lines:
                            st.markdown(f"- {line}")
                elif isinstance(copies, str):  # 만약 문자열이라면 단순 출력
                    st.warning("카피 결과가 잘못된 형식입니다. 결과를 직접 확인하세요.")
                    st.code(copies)
                else:  # 예상치 못한 타입 처리
                    st.error(f"예상치 못한 카피 결과 타입: {type(copies)}")
                    st.write(copies)

            else:
                st.error("카피 생성 실패")
                st.code(copies)
