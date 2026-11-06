"""🛍️ 상품 추천 (06 · part6_recommend.pkl)"""
import streamlit as st
from utils.models import load_model, recommend

st.title("🛍️ 비슷한 상품 추천")
st.caption("상품을 고르면 같은 카테고리에서 가격·무게·크기·사진 수·평점이 가장 비슷한 상품 5개를 보여 줍니다.")

prods = load_model("part6_recommend.pkl")["products"]
COLS = {"product_id": "상품 ID", "category_kr": "카테고리", "price": "가격(R$)", "weight_g": "무게(g)",
        "photos_qty": "사진 수", "avg_review_score": "평균 평점"}

c1, c2 = st.columns(2)
category = c1.selectbox("① 카테고리", sorted(prods["category_kr"].unique()))
price = prods[prods["category_kr"] == category].set_index("product_id")["price"].sort_values()   # 싼 상품부터
pid = c2.selectbox("② 기준 상품", price.index, format_func=lambda p: f"{p[:8]} · R$ {price[p]:,.0f}")

def show(df):
    """보기 좋게 : 필요한 열만, 한글 이름, 상품 ID는 앞 8자리"""
    out = df[list(COLS)].rename(columns=COLS)
    out["상품 ID"] = out["상품 ID"].str[:8]
    return out.round(1)


st.subheader("기준 상품")
st.dataframe(show(prods[prods["product_id"] == pid]), hide_index=True)

st.subheader("추천 상품 5개")
st.dataframe(show(recommend(pid)), hide_index=True)
st.info("표의 숫자가 기준 상품과 비슷한지 비교해 보세요. 이 추천은 '특징이 비슷한 상품'일 뿐, 고객이 실제로 함께 산 상품은 아닙니다.")
