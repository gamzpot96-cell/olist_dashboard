"""모델 불러오기 + 예측 함수
각 함수는 STEP1 노트북 마지막의 '저장한 파일로 예측해 보기' 셀과 같은 순서로 처리합니다.

| 화면 | pkl 파일 | 노트북 |
|---|---|---|
| 리뷰 감성 분석 | part7_1_sentiment_ml.pkl | 07_1 |
| 상품 추천 | part6_recommend.pkl | 06 |
| 판매자 유형 | part8_seller_segment.pkl | 08 |
| 판매자 이탈 위험 | part9_seller_churn.pkl + data/seller_table.csv | 09 · 10 |
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st

BASE = Path(__file__).parent.parent        # olist_dashboard 폴더
MODEL_DIR = BASE / "model"
DATA_DIR = BASE / "data"


# ───────── 불러오기 ─────────
@st.cache_resource          # 모델은 처음 한 번만 불러오고, 그다음부터는 저장해 둔 것을 씁니다.
def load_model(name):
    return joblib.load(MODEL_DIR / name)


@st.cache_data              # 표도 처음 한 번만 읽습니다.
def load_seller_table():
    return pd.read_csv(DATA_DIR / "seller_table.csv")


# ───────── 07_1 리뷰 감성 분석 ─────────
def predict_sentiment(text):
    ml = load_model("part7_1_sentiment_ml.pkl")
    X = ml["tfidf"].transform([text])                  # ① 문장 → 단어 점수표
    return float(ml["model"].predict_proba(X)[0, 1])   # ② 긍정 확률 (0~1)


def count_known_words(text):
    """모델이 아는 단어 수 (0이면 결과를 믿으면 안 됨)"""
    ml = load_model("part7_1_sentiment_ml.pkl")
    return int(ml["tfidf"].transform([text]).nnz)


# ───────── 06 상품 추천 ─────────
def recommend(product_id):
    """상품 ID → 비슷한 상품 표 (06 노트북 셀 16과 같은 순서)"""
    art = load_model("part6_recommend.pkl")
    prods = art["products"]
    hit = prods.index[prods["product_id"] == product_id]
    if len(hit) == 0:
        return prods.iloc[0:0]                                                  # 목록에 없는 상품
    i = hit[0]
    x = art["scaler"].transform(np.log1p(prods.loc[[i], art["features"]]))     # ① 로그 + 단위 맞추기
    nn, cat_idx = art["knn_by_category"][prods.at[i, "category"]]              # ② 같은 카테고리 KNN
    _, pos = nn.kneighbors(x, n_neighbors=art["k"] + 1)                        # ③ 가까운 상품 찾기
    rec = cat_idx[pos[0]]
    return prods.loc[rec[rec != i][:art["k"]]]                                 # ④ 자기 자신 빼고 k개


# ───────── 08 판매자 유형 ─────────
SEGMENT_GUIDE = {
    "핵심 우량": "주문·판매액이 크고 최근에도 활발 → 우수 판매자 혜택, 이탈 방지",
    "신규 성장": "시작한 지 얼마 안 됐고 최근 판매 있음 → 온보딩 지원, 첫 판매 경험 관리",
    "휴면": "오랫동안 판매가 없음 → 재활성화 캠페인 또는 정리",
    "저평점 위험": "평점이 매우 낮음 → 출고 마감 준수 관리, 품질·배송 점검",
}


def make_segment_input(df, review_fill):
    """판매자 숫자 → 모델 입력 (08 노트북과 같은 처리 : 로그 변환 + 빈 리뷰 채우기)"""
    return pd.DataFrame({
        "log_frequency":    np.log1p(df["frequency"]),
        "log_monetary":     np.log1p(df["monetary"]),
        "recency_days":     df["recency_days"],
        "tenure_days":      df["tenure_days"],
        "avg_review_score": df["avg_review_score"].fillna(review_fill),
    })


def predict_segment(df):
    """판매자 표(한 줄 이상) → 유형 이름 목록"""
    art = load_model("part8_seller_segment.pkl")
    X = make_segment_input(df, art["review_fill"])[art["features"]]
    seg_id = art["kmeans"].predict(art["scaler"].transform(X))
    return [art["names"][s] for s in seg_id]


# ───────── 09 판매자 이탈 위험 ─────────
def risk_label(p):
    """확률 → 위험 등급 (10 노트북과 같은 구간)"""
    return "낮음" if p < 0.3 else "보통" if p < 0.5 else "높음" if p < 0.7 else "매우 높음"


@st.cache_data
def score_sellers():
    """판매자 표 전체에 08 · 09 모델을 적용 (10 노트북 셀 8 · 9와 같은 계산)"""
    table = load_seller_table().copy()
    churn = load_model("part9_seller_churn.pkl")
    table["churn_prob"] = churn["model"].predict_proba(table[churn["features"]])[:, 1]
    table["risk"] = table["churn_prob"].map(risk_label)
    table["segment"] = predict_segment(table)
    table["expected_loss"] = table["churn_prob"] * table["sales_last_3m"]   # 예상 손실 = 확률 × 최근 3개월 판매액
    return table.sort_values("expected_loss", ascending=False).reset_index(drop=True)
