"""시작 파일 : streamlit run app.py
페이지를 등록하면 왼쪽에 메뉴가 생깁니다.
"""
import streamlit as st

st.set_page_config(page_title="Olist 대시보드", page_icon="📦", layout="wide")

page = st.navigation({
    "소개": [
        st.Page("views/home.py", title="홈", icon="🏠"),
        st.Page("views/analysis.py", title="데이터 분석", icon="📊"),
    ],
    "AI 모델": [
        st.Page("views/sentiment.py", title="리뷰 감성 분석", icon="💬"),   # 07_1
        st.Page("views/recommend.py", title="상품 추천", icon="🛍️"),       # 06
        st.Page("views/segment.py", title="판매자 유형", icon="🏪"),        # 08
        st.Page("views/churn.py", title="판매자 이탈 위험", icon="🚨"),     # 09
    ],
    "RAG 챗봇": [
        st.Page("views/qa.py", title="분석 Q&A", icon="🤖"),               # STEP4
    ],
})
page.run()
