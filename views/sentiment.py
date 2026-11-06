"""💬 리뷰 감성 분석 (07_1 · part7_1_sentiment_ml.pkl)"""
import streamlit as st
from utils.models import predict_sentiment, count_known_words

st.title("💬 리뷰 감성 분석")
st.caption("리뷰 문장을 넣으면 긍정/부정을 판정합니다. 포르투갈어 리뷰로 학습한 모델입니다.")

EXAMPLES = {
    "produto veio quebrado, péssimo": "상품이 깨져서 왔다, 최악",
    "produto muito bom, chegou antes do prazo": "상품 아주 좋음, 예정보다 일찍 도착",
    "ainda não recebi o produto": "아직 상품을 못 받았다",
}
example = st.selectbox("예시 리뷰", list(EXAMPLES), format_func=lambda s: f"{s}  ({EXAMPLES[s]})")
text = st.text_area("리뷰 (포르투갈어)", example)

if st.button("판정하기", type="primary"):
    if not text.strip():
        st.warning("리뷰 문장을 입력하세요.")
        st.stop()
    if count_known_words(text) == 0:          # 한국어 · 영어처럼 학습하지 않은 단어만 있을 때
        st.warning("모델이 아는 단어가 하나도 없습니다. 포르투갈어로만 학습했으므로 아래 결과는 의미가 없습니다.")
    p = predict_sentiment(text)
    st.metric("판정", "긍정 😊" if p >= 0.5 else "부정 😞")
    st.progress(p, text=f"긍정 확률 {p:.1%}")
