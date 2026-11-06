"""🏠 홈 페이지"""
import streamlit as st

st.title("📦 Olist 브라질 이커머스 대시보드")
st.write("브라질 온라인 쇼핑몰 Olist의 주문 데이터를 **분석**하고, STEP1에서 학습한 **AI 모델**을 사용해 보는 서비스입니다.")

c1, c2, c3 = st.columns(3)
c1.metric("분석한 주문", "96,203건")
c2.metric("AI 모델", "4개")
c3.metric("모델 파일 합계", "약 340KB")

st.subheader("메뉴 안내")
st.markdown("""
| 메뉴 | 할 수 있는 것 | 사용하는 파일 |
|---|---|---|
| 📊 **데이터 분석** | 지역 · 기간을 골라 핵심 지표, 인사이트, 그래프 보기 | orders · items |
| 💬 **리뷰 감성 분석** | 리뷰 문장 → 긍정/부정 판정 | part7_1_sentiment_ml.pkl |
| 🛍️ **상품 추천** | 상품 선택 → 비슷한 상품 5개 | part6_recommend.pkl |
| 🏪 **판매자 유형** | 판매자 숫자 5개 입력 → 4가지 유형 중 하나 | part8_seller_segment.pkl |
| 🚨 **판매자 이탈 위험** | 판매자 선택 → 이탈 확률 · 먼저 챙길 판매자 순위 | part9_seller_churn.pkl + seller_table.csv |
| 🤖 **분석 Q&A** | 질문 → 분석 결과에서 근거를 찾아 답 (OpenAI API 키 필요) | olist_facts.csv + olist_model_guide.md |
""")
st.caption("왼쪽 메뉴에서 페이지를 선택하세요. 딥러닝 감성 모델(07_2)은 설치가 무거워 웹앱에서는 뺐습니다.")
