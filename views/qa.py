"""🤖 분석 Q&A (RAG 챗봇 · STEP4 11_olist_rag_chatbot)"""
import os

import streamlit as st
from utils.rag import CHANNELS, ask


def get_api_key():
    """① .streamlit/secrets.toml → ② 환경변수 → ③ 왼쪽 입력 칸 순서로 찾기"""
    try:
        return st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass
    return os.environ.get("OPENAI_API_KEY") or st.sidebar.text_input("OpenAI API 키", type="password")


st.title("🤖 분석 Q&A")
st.caption("Olist 분석 결과를 찾아보고, 근거 ID와 함께 답하는 챗봇입니다. 자료에 없는 내용은 확인할 수 없다고 답합니다.")

api_key = get_api_key()
channel = st.radio("책장 고르기", list(CHANNELS), format_func=CHANNELS.get, horizontal=True)

EXAMPLES = ["늦게 도착한 주문의 리뷰 점수는?", "재구매 고객은 몇 %야?",
            "이탈 모델은 어떤 숫자를 보고 판단해?", "배송이 3일 늦으면 고객은 무엇을 받을 수 있어?",
            "저평점 위험 판매자는 어떤 조치를 받아?", "2019년 매출은 얼마야?"]
with st.expander("예시 질문"):
    st.markdown("\n".join(f"- {q}" for q in EXAMPLES))

if not api_key:
    st.info("왼쪽에 OpenAI API 키를 넣으면 질문할 수 있습니다.")
    st.stop()

# 채널마다 대화 기록을 따로 저장 (화면이 다시 그려져도 남아 있게)
history = st.session_state.setdefault(f"chat_{channel}", [])
for msg in history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

question = st.chat_input("질문을 입력하세요")
if question:
    history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("근거를 찾는 중…"):
            result = ask(question, channel, api_key)
        st.markdown(result["answer"])
        if result["fake"]:                                   # 찾지 않은 ID를 답에 썼다면 경고
            st.warning(f"검색되지 않은 근거 ID가 답에 있습니다: {', '.join(result['fake'])}")
        with st.expander("찾아온 근거 보기"):
            for d in result["found"]:
                st.markdown(f"**[{d.metadata['id']}]** {d.page_content}  \n_출처: {d.metadata['출처']}_")
    history.append({"role": "assistant", "content": result["answer"]})
