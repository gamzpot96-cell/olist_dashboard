"""데이터 불러오기 + 분석 함수 (STEP2 05 노트북을 넓힌 것)
그래프 함수는 모두 (그래프, 설명 문장) 두 개를 돌려줍니다.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_DIR = Path(__file__).parent.parent / "data"      # 이 파일 기준으로 data 폴더 찾기


@st.cache_data              # 데이터는 처음 한 번만 읽고, 그다음부터는 저장해 둔 것을 씁니다.
def load_data():
    orders = pd.read_parquet(DATA_DIR / "orders.parquet")
    items = pd.read_parquet(DATA_DIR / "items.parquet")
    orders["월"] = orders["주문시각"].dt.strftime("%Y-%m")
    return orders, items


def filter_data(orders, items, state, months):
    """지역 · 기간으로 거르기"""
    od = orders[orders["월"].between(months[0], months[1])]
    if state != "전체":
        od = od[od["customer_state"] == state]
    return od, items[items["order_id"].isin(od["order_id"])]


def kpis(od):
    """핵심 지표 6개"""
    return {
        "주문 수": f"{len(od):,}건",
        "매출": f"R$ {od['매출'].sum() / 1e6:.2f}M",
        "객단가": f"R$ {od['매출'].mean():,.0f}",
        "배송 기간 (중앙값)": f"{od['배송일수'].median():.1f}일",
        "배송 지연율": f"{od['지연'].mean():.1%}",
        "평균 리뷰": f"{od['review_score'].mean():.2f}점",
    }


def insights(od):
    """인사이트 문장 — 숫자를 계산해서 끼워 넣으므로 필터를 바꾸면 문장도 바뀝니다."""
    repeat = (od.groupby("customer_unique_id")["order_id"].count() >= 2).mean()
    review = od.groupby("지연")["review_score"].mean()
    top3 = od["customer_state"].value_counts(normalize=True).head(3)
    sentences = [f"🔁 재구매 고객은 **{repeat:.1%}** → 두 번째 구매를 유도하는 것이 가장 큰 기회"]
    review = review.dropna()                       # 리뷰가 하나도 없는 쪽은 비교에서 뺌
    if len(review) == 2:                           # 제때 · 지연 주문이 모두 있을 때만 비교
        on, late = review[False], review[True]
        verb = "떨어짐" if late < on else "오히려 높음 (주문 수가 적으면 우연일 수 있음)"
        sentences.append(f"🚚 늦게 도착하면 리뷰가 **{on:.2f}점 → {late:.2f}점**으로 {verb}")
    if od["customer_state"].nunique() > 1:         # 지역을 하나만 고르면 '상위 3개 주'는 의미가 없음
        sentences.append(f"🗺️ 주문 상위 3개 주 ({', '.join(top3.index)})가 전체의 **{top3.sum():.1%}**")
    return sentences


def chart_monthly(od, metric):
    if metric == "매출":
        m = od.groupby("월")["매출"].sum()
    elif metric == "주문 수":
        m = od.groupby("월")["order_id"].count()
    else:
        m = od.groupby("월")["매출"].mean()
    fig = px.bar(x=m.index, y=m.values, labels={"x": "월", "y": metric}, title=f"월별 {metric}")
    msg = f"가장 높은 달은 **{m.idxmax()}** 입니다."
    if m.idxmax() == "2017-11":
        msg += " (2017-11-24 블랙프라이데이)"
    return fig, msg


def chart_time(od):
    days = ["월", "화", "수", "목", "금", "토", "일"]
    t = od.groupby([od["주문시각"].dt.day_of_week, od["주문시각"].dt.hour]).size().unstack(fill_value=0)
    fig = px.imshow(t, y=[days[i] for i in t.index], color_continuous_scale="Blues",
                    labels={"x": "시간", "y": "요일", "color": "주문 수"}, title="요일 × 시간대 주문 수")
    day_share = od["주문시각"].dt.hour.between(10, 16).mean()
    return fig, f"낮 10~16시 주문이 **{day_share:.1%}** → 광고는 평일 낮에, 서버 점검은 새벽에"


def chart_category(it):
    c = it.groupby("product_category_name_english")["price"].sum().nlargest(10).sort_values()
    fig = px.bar(x=c.values, y=c.index, orientation="h", labels={"x": "매출 (R$)", "y": ""},
                 title="매출 TOP 10 카테고리")
    return fig, f"매출 1위 카테고리는 **{c.index[-1]}** 입니다."


def chart_delivery(od):
    r = od.groupby("지연")["review_score"].mean().rename({False: "제때 도착", True: "지연 도착"})
    fig = px.bar(x=r.index, y=r.values, text_auto=".2f", labels={"x": "", "y": "평균 리뷰"},
                 title="배송 지연 여부별 평균 리뷰")
    return fig, f"지연 주문은 **{od['지연'].mean():.1%}**뿐이지만, 리뷰 점수를 크게 떨어뜨립니다."


def chart_region(od):
    r = od.groupby("customer_state").agg(주문수=("order_id", "count"), 배송기간=("배송일수", "median"),
                                         평균리뷰=("review_score", "mean")).reset_index()
    fig = px.scatter(r, x="배송기간", y="평균리뷰", size="주문수", text="customer_state",
                     title="주별 배송 기간 vs 평균 리뷰 (원 크기 = 주문 수)")
    fig.update_traces(textposition="top center")                         # 주 이름을 원 위에 표시
    if len(r) < 2:                                                       # 지역을 하나만 고르면 비교할 점이 없음
        return fig, "왼쪽에서 고객 지역을 **전체**로 두면 주별로 비교할 수 있습니다."
    return fig, "오른쪽(배송이 느린 주)으로 갈수록 리뷰 점수가 낮아집니다."
