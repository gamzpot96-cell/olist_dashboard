"""📊 데이터 분석 페이지"""
import streamlit as st
from utils.data import (load_data, filter_data, kpis, insights,
                        chart_monthly, chart_time, chart_category, chart_delivery, chart_region)

st.title("📊 데이터 분석")
orders, items = load_data()

# ① 필터 (왼쪽 사이드바)
months = sorted(orders["월"].unique())
state = st.sidebar.selectbox("고객 지역", ["전체"] + sorted(orders["customer_state"].unique()))
period = st.sidebar.select_slider("기간", options=months, value=(months[0], months[-1]))
od, it = filter_data(orders, items, state, period)
st.caption(f"배송 완료 주문 · {period[0]} ~ {period[1]} · {state}")

if od.empty:                                                   # 고른 조건에 주문이 없으면 그래프를 그릴 수 없음
    st.warning("선택한 지역 · 기간에 주문이 없습니다. 왼쪽에서 조건을 바꿔 보세요.")
    st.stop()                                                  # 아래 코드는 실행하지 않고 여기서 멈춤

# ② 핵심 지표 (3개씩 2줄)
for col, (name, value) in zip(st.columns(3) + st.columns(3), kpis(od).items()):
    col.metric(name, value)

# ③ 인사이트
st.subheader("💡 핵심 인사이트")
for sentence in insights(od):
    st.markdown(f"- {sentence}")

# ④ 그래프 (탭)
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📈 매출 추이", "🕒 주문 시간", "🛍️ 카테고리",
                                              "🚚 배송·리뷰", "🗺️ 지역", "📄 데이터"])
with tab1:
    metric = st.radio("지표", ["매출", "주문 수", "객단가"], horizontal=True)
    fig, msg = chart_monthly(od, metric)
    st.plotly_chart(fig)
    st.info(msg)
with tab2:
    fig, msg = chart_time(od)
    st.plotly_chart(fig)
    st.info(msg)
with tab3:
    fig, msg = chart_category(it)
    st.plotly_chart(fig)
    st.info(msg)
with tab4:
    fig, msg = chart_delivery(od)
    st.plotly_chart(fig)
    st.info(msg)
with tab5:
    fig, msg = chart_region(od)
    st.plotly_chart(fig)
    st.info(msg)
with tab6:
    st.dataframe(od.head(100))
    st.download_button("CSV 내려받기", od.to_csv(index=False).encode("utf-8-sig"), "olist_orders.csv")
