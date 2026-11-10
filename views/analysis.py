"""📊 데이터 분석 페이지"""
import pandas as pd
import streamlit as st
from utils.data import (load_data, filter_data, kpis, insights,
                        chart_monthly, chart_time, chart_category, chart_delivery, chart_region,
                        chart_review_distribution, chart_order_amount,
                        cohort_reorders, chart_cohort_reorders)

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
tab1, tab2, tab3, tab4, tab5, tab6, cohort_tab = st.tabs([
    "📈 매출 추이", "🕒 주문 시간", "🛍️ 카테고리", "🚚 배송·리뷰", "🗺️ 지역", "📄 데이터", "재주문 코호트"
])
with tab1:
    metric = st.radio("지표", ["매출", "주문 수", "객단가"], horizontal=True)
    fig, msg = chart_monthly(od, metric)
    st.plotly_chart(fig)
    st.info(msg)
    st.subheader("주문 금액 분포 · 선형 축과 로그 축")
    amounts = od["매출"]
    positive_amounts = amounts[amounts.gt(0)]
    st.caption(f"선택 범위의 양수 금액 주문 {len(positive_amounts):,}건 · 0·음수·결측 제외 {len(amounts) - len(positive_amounts):,}건")
    if positive_amounts.empty:
        st.info("선택한 범위에는 비교할 양수 주문 금액이 없습니다.")
    else:
        st.caption("두 그래프는 같은 주문을 사용합니다. 세로축은 해당 금액 이하인 주문의 비율입니다.")
        st.plotly_chart(chart_order_amount(positive_amounts))
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
    st.subheader("배송 지연 여부별 별점 분포")
    review_figure, review_summary = chart_review_distribution(od)
    reviewed_count = review_summary["평점 기록 주문(건)"].sum()
    if reviewed_count:
        st.plotly_chart(review_figure)
        st.dataframe(review_summary, hide_index=True)
        st.caption("별점 비율의 분모는 각 배송 집단에서 1~5점의 평점이 기록된 주문 수입니다. 차이는 선택 범위에서 관찰된 결과입니다.")
    else:
        st.info("선택한 범위에는 비교할 평점이 없습니다.")
    st.caption(f"평점·배송 상태 조건으로 제외된 주문 {len(od) - reviewed_count:,}건")
with tab5:
    fig, msg = chart_region(od)
    st.plotly_chart(fig)
    st.info(msg)
with tab6:
    st.dataframe(od.head(100))
    st.download_button("CSV 내려받기", od.to_csv(index=False).encode("utf-8-sig"), "olist_orders.csv")
with cohort_tab:
    st.subheader("첫 주문 월별 재주문율")
    st.caption("첫 주문이 기록된 달에 따라, 다음 달에 다시 주문한 고객 비율은 어떻게 달랐나요?")
    st.caption("기간 필터는 첫 주문 월, 지역 필터는 첫 주문의 고객 지역을 고릅니다. 이후 주문은 전체 저장 데이터에서 확인합니다.")
    sizes, reorders, first_complete, last_complete = cohort_reorders(orders, state, period)
    if sizes.empty:
        st.info("선택 조건에 해당하는 관찰 완료 첫 주문 월이 없습니다.")
    else:
        st.plotly_chart(chart_cohort_reorders(sizes, reorders))
        st.caption(
            f"관찰 완료 월: {first_complete}~{last_complete}. M+1은 첫 주문의 다음 달입니다. "
            "0.00%는 관찰 완료 후 재주문 고객이 0명인 경우이고, 빈칸은 관찰이 끝나지 않은 달입니다."
        )
        next_month = reorders[1]
        st.dataframe(pd.DataFrame({
            "첫 주문 월": sizes.index.astype(str),
            "첫 주문 고객(명)": sizes.to_numpy(),
            "다음 달 재주문 고객(명)": next_month.astype("Int64").array,
            "다음 달 재주문율(%)": (next_month / sizes * 100).round(2).to_numpy(),
        }), hide_index=True)
    st.caption("분모는 첫 주문 월의 고유 고객 수입니다. 배송 완료 주문 기록을 사용하며, 같은 달에 여러 번 주문한 고객은 한 번만 셉니다.")
