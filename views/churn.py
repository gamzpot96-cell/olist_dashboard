"""🚨 판매자 이탈 위험 (09 · part9_seller_churn.pkl + data/seller_table.csv)
이탈 모델은 숫자 14개가 필요해서 직접 입력하지 않고,
10 노트북에서 만든 판매자 표(seller_table.csv)에서 판매자를 골라 봅니다.
"""
import pandas as pd
import streamlit as st
from utils.models import score_sellers, SEGMENT_GUIDE

st.title("🚨 판매자 이탈 위험")
st.caption("2018-08-23 기준, 최근 3개월 안에 판매가 있었던 판매자가 앞으로 3개월 동안 주문을 못 받을 확률입니다.")

table = score_sellers()          # 표 전체에 08 · 09 모델 적용 (처음 한 번만 계산)

# ① 전체 요약
c1, c2, c3 = st.columns(3)
c1.metric("대상 판매자", f"{len(table):,}명")
c2.metric("이탈 위험 (확률 0.5 이상)", f"{(table['churn_prob'] >= 0.5).sum():,}명")
c3.metric("예상 손실 합계", f"R$ {table['expected_loss'].sum():,.0f}")

# ② 먼저 챙길 판매자 TOP 10 (예상 손실 = 이탈 확률 × 최근 3개월 판매액)
st.subheader("먼저 챙길 판매자 TOP 10")
segments = ["전체"] + list(SEGMENT_GUIDE)
pick = st.radio("유형", segments, horizontal=True)
view = table if pick == "전체" else table[table["segment"] == pick]
top = view.head(10).assign(seller=lambda d: d["seller_id"].str[:8])
st.dataframe(
    top[["seller", "segment", "churn_prob", "risk", "orders_last_3m", "recency_days", "sales_last_3m", "expected_loss"]]
    .rename(columns={"seller": "판매자", "segment": "유형", "churn_prob": "이탈 확률", "risk": "위험 등급",
                     "orders_last_3m": "최근 3개월 주문", "recency_days": "마지막 판매 후 일수",
                     "sales_last_3m": "최근 3개월 판매액(R$)", "expected_loss": "예상 손실(R$)"}),
    hide_index=True,
    column_config={"이탈 확률": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=1),
                   "최근 3개월 판매액(R$)": st.column_config.NumberColumn(format="%.0f"),
                   "예상 손실(R$)": st.column_config.NumberColumn(format="%.0f")},
)

# ③ 판매자 한 명 자세히 보기
st.subheader("판매자 한 명 자세히 보기")
sid = st.selectbox("판매자 선택 (위 표 순서)", view["seller_id"], format_func=lambda s: s[:8])
row = table[table["seller_id"] == sid].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("이탈 확률", f"{row['churn_prob']:.0%}", row["risk"], delta_color="off")
c2.metric("유형", row["segment"])
c3.metric("최근 3개월 주문", f"{row['orders_last_3m']:.0f}건", f"그 전 3개월 {row['orders_prev_3m']:.0f}건", delta_color="off")
c4.metric("예상 손실", f"R$ {row['expected_loss']:,.0f}")
st.progress(float(row["churn_prob"]), text=f"이탈 확률 {row['churn_prob']:.1%}")

def fmt(value, form):
    """빈 값(NaN)이면 '-', 아니면 모양 맞춰 글자로"""
    return "-" if pd.isna(value) else form.format(value)


c1, c2, c3, c4 = st.columns(4)
c1.metric("마지막 판매 후", f"{row['recency_days']:.0f}일")
c2.metric("평균 리뷰", fmt(row["avg_review_score"], "{:.2f}점"))
c3.metric("배송 지연율", fmt(row["late_rate"], "{:.0%}"))
c4.metric("출고 지연율", fmt(row["ship_late_rate"], "{:.0%}"))
st.info(f"**{row['segment']}** 유형 관리 방향 : {SEGMENT_GUIDE[row['segment']]}")
st.caption("이탈 = 실제 폐업이 아니라 '앞으로 3개월 동안 주문 0건'이라는 실습용 정의입니다. '-'는 아직 값이 없는 경우입니다.")
