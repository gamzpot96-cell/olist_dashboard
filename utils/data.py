"""데이터 불러오기 + 분석 함수 (STEP2 05 노트북을 넓힌 것)
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

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
        sentences.append(f"🚚 평균 리뷰 평점은 제때 도착 **{on:.2f}점**, 지연 도착 **{late:.2f}점**입니다.")
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
    return fig, f"선택한 주문의 배송 지연 비율은 **{od['지연'].mean():.1%}**입니다. 막대는 평점이 기록된 주문의 평균입니다."


def chart_review_distribution(orders):
    """배송 상태별 별점 분포와 낮은 평점 집계표를 만든다."""
    scores = [1, 2, 3, 4, 5]
    delivery_labels = {False: "제때 도착", True: "지연 도착"}
    reviewed = orders[orders["review_score"].isin(scores) & orders["지연"].isin(delivery_labels)]
    counts = pd.crosstab(reviewed["지연"], reviewed["review_score"]).reindex(
        index=list(delivery_labels), columns=scores, fill_value=0
    )
    counts.index = counts.index.map(delivery_labels)
    totals = counts.sum(axis=1)
    low_counts = counts[[1, 2]].sum(axis=1)
    denominators = totals.where(totals.gt(0))
    summary = pd.DataFrame({
        "배송 상태": counts.index,
        "평점 기록 주문(건)": totals.to_numpy(),
        "1~2점 주문(건)": low_counts.to_numpy(),
        "1~2점 비율(%)": (low_counts / denominators * 100).round(2).to_numpy(),
    })

    colors = ["#ac2430", "#e27d63", "#b6a770", "#589db3", "#206488"]
    figure = go.Figure()
    for score, color in zip(scores, colors):
        group_counts = counts.loc[totals.gt(0), score]
        figure.add_trace(go.Bar(
            name=f"{score}점",
            y=group_counts.index,
            x=group_counts / totals.loc[group_counts.index] * 100,
            customdata=group_counts,
            orientation="h",
            marker_color=color,
            hovertemplate="%{y} · %{fullData.name}<br>%{customdata:,}건 · %{x:.2f}%<extra></extra>",
        ))
    figure.update_layout(barmode="stack", height=260, legend={"orientation": "h"}, margin={"t": 10, "b": 10})
    figure.update_xaxes(range=[0, 100], title_text="집단 내 비율", ticksuffix="%")
    figure.update_yaxes(autorange="reversed", categoryorder="array", categoryarray=list(delivery_labels.values()))
    return figure, summary


def chart_order_amount(positive_amounts):
    """같은 양수 주문 금액으로 선형·로그 축 누적 분포를 그린다."""
    counts = positive_amounts.value_counts().sort_index()
    cumulative_pct = counts.cumsum() / len(positive_amounts) * 100
    figure = make_subplots(rows=1, cols=2, shared_yaxes=True, subplot_titles=("선형 축", "로그 축"))
    for column, axis_type in [(1, "linear"), (2, "log")]:
        figure.add_trace(go.Scatter(
            x=counts.index,
            y=cumulative_pct,
            mode="lines",
            line={"shape": "hv", "color": "#2869ab"},
            hovertemplate="주문 금액 R$ %{x:,.2f}<br>이하 주문 %{y:.2f}%<extra></extra>",
            showlegend=False,
        ), row=1, col=column)
        figure.update_xaxes(type=axis_type, title_text="주문 금액(R$)", row=1, col=column)
    figure.update_yaxes(range=[0, 100], ticksuffix="%")
    figure.update_yaxes(title_text="이하 주문 비율", row=1, col=1)
    figure.update_layout(height=360)
    return figure


def cohort_reorders(orders, state, months):
    """첫 주문 월과 지역을 기준으로 코호트를 고르고, 월별 재주문 고객을 센다."""
    follow_up_months = list(range(1, 7))
    records = orders[["customer_unique_id", "customer_state", "주문시각", "order_id"]].dropna(
        subset=["customer_unique_id", "주문시각"]
    )
    if records.empty:
        return pd.Series(dtype="int64"), pd.DataFrame(columns=follow_up_months), None, None

    first_date = records["주문시각"].min()
    last_date = records["주문시각"].max()
    first_complete = first_date.to_period("M") + int(first_date.day > 1)
    last_complete = last_date.to_period("M") - int(last_date.day < last_date.days_in_month)

    # 기간 필터를 적용하기 전에 전체 저장 데이터에서 첫 주문을 결정한다.
    first_orders = records.sort_values(["주문시각", "order_id"]).drop_duplicates("customer_unique_id")
    first_orders = first_orders.set_index("customer_unique_id")
    first_orders["첫 주문 월"] = first_orders["주문시각"].dt.to_period("M")
    start, end = (pd.Period(month, freq="M") for month in months)
    first_orders = first_orders[first_orders["첫 주문 월"].between(
        max(start, first_complete), min(end, last_complete)
    )]
    if state != "전체":
        first_orders = first_orders[first_orders["customer_state"].eq(state)]
    cohort_sizes = first_orders.groupby("첫 주문 월", sort=True).size()

    activity = records.join(first_orders["첫 주문 월"], on="customer_unique_id", how="inner")
    activity["주문 월"] = activity["주문시각"].dt.to_period("M")
    activity = activity.drop_duplicates(["customer_unique_id", "주문 월"]).copy()
    activity["경과 월"] = activity["주문 월"].astype("int64") - activity["첫 주문 월"].astype("int64")
    activity = activity[activity["경과 월"].isin(follow_up_months)]
    reorders = (
        activity.groupby(["첫 주문 월", "경과 월"]).size()
        .unstack(fill_value=0)
        .reindex(index=cohort_sizes.index, columns=follow_up_months, fill_value=0)
    )
    observable = pd.DataFrame({
        month: cohort_sizes.index + month <= last_complete
        for month in follow_up_months
    }, index=cohort_sizes.index)
    return cohort_sizes, reorders.where(observable), first_complete, last_complete


def chart_cohort_reorders(cohort_sizes, reorders):
    rates = reorders.div(cohort_sizes, axis=0) * 100
    labels = []
    details = []
    for cohort_month, row in reorders.iterrows():
        size = cohort_sizes.loc[cohort_month]
        labels.append([f"{count / size:.2%}" if pd.notna(count) else "" for count in row])
        details.append([f"{int(count):,}/{size:,}명" if pd.notna(count) else "" for count in row])
    highest_rate = rates.max().max()
    figure = go.Figure(go.Heatmap(
        x=[f"M+{month}" for month in reorders.columns],
        y=cohort_sizes.index.astype(str),
        z=rates.to_numpy(),
        text=labels,
        customdata=details,
        texttemplate="%{text}",
        textfont={"color": "#172d45"},
        hovertemplate="첫 주문 월 %{y} · %{x}<br>재주문 %{customdata} (%{z:.2f}%)<extra></extra>",
        hoverongaps=False,
        zmin=0,
        zmax=highest_rate if pd.notna(highest_rate) and highest_rate > 0 else 1,
        colorscale=[[0, "#eff6ff"], [1, "#7db3f1"]],
        colorbar={"title": "재주문율", "ticksuffix": "%"},
    ))
    figure.update_xaxes(title_text="첫 주문 후 경과 월")
    figure.update_yaxes(title_text="첫 주문 월", autorange="reversed", type="category")
    figure.update_layout(height=max(280, 32 * len(cohort_sizes) + 100), margin={"t": 15})
    return figure


def chart_region(od):
    r = od.groupby("customer_state").agg(주문수=("order_id", "count"), 배송기간=("배송일수", "median"),
                                         평균리뷰=("review_score", "mean")).reset_index()
    fig = px.scatter(r, x="배송기간", y="평균리뷰", size="주문수", text="customer_state",
                     title="주별 배송 기간 vs 평균 리뷰 (원 크기 = 주문 수)")
    fig.update_traces(textposition="top center")                         # 주 이름을 원 위에 표시
    if len(r) < 2:                                                       # 지역을 하나만 고르면 비교할 점이 없음
        return fig, "왼쪽에서 고객 지역을 **전체**로 두면 주별로 비교할 수 있습니다."
    return fig, "오른쪽(배송이 느린 주)으로 갈수록 리뷰 점수가 낮아집니다."
