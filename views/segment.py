"""🏪 판매자 유형 (08 · part8_seller_segment.pkl)
판매자 숫자 5개를 직접 넣어 보는 화면입니다.
"""
import pandas as pd
import streamlit as st
from utils.models import predict_segment, SEGMENT_GUIDE

st.title("🏪 판매자 유형 판정")
st.caption("판매자의 숫자 5개를 넣으면 4가지 유형 중 하나로 판정합니다. 예시를 고른 뒤 숫자를 바꿔 보세요.")

# 08 노트북 셀 11의 유형별 대표값(중앙값)
EXAMPLES = {
    "핵심 우량형 판매자":   dict(frequency=38, monetary=4950, recency_days=15,  tenure_days=388, avg_review_score=4.1),
    "신규 성장형 판매자":   dict(frequency=3,  monetary=405,  recency_days=27,  tenure_days=98,  avg_review_score=4.3),
    "휴면형 판매자":        dict(frequency=3,  monetary=309,  recency_days=324, tenure_days=430, avg_review_score=4.3),
    "저평점 위험형 판매자": dict(frequency=1,  monetary=180,  recency_days=205, tenure_days=265, avg_review_score=1.6),
}
ex = EXAMPLES[st.selectbox("예시 판매자", list(EXAMPLES))]

c1, c2, c3 = st.columns(3)
frequency = c1.number_input("① 주문 건수", min_value=1, value=ex["frequency"])
monetary = c2.number_input("② 판매액 (R$)", min_value=0, value=ex["monetary"], step=100)
avg_review = c3.number_input("③ 평균 리뷰 점수 (1~5)", min_value=1.0, max_value=5.0, value=ex["avg_review_score"], step=0.1)
recency = c1.number_input("④ 마지막 판매 후 지난 날 수", min_value=0, value=ex["recency_days"])
tenure = c2.number_input("⑤ 첫 판매 후 지난 날 수", min_value=0, value=ex["tenure_days"])

if tenure < recency:
    st.warning("첫 판매는 마지막 판매보다 먼저입니다. ⑤는 ④보다 크거나 같아야 합니다.")

if st.button("판정하기", type="primary"):
    seller = pd.DataFrame([{"frequency": frequency, "monetary": monetary, "recency_days": recency,
                            "tenure_days": tenure, "avg_review_score": avg_review}])
    name = predict_segment(seller)[0]
    st.success(f"### {name}")
    st.write(f"**관리 방향** : {SEGMENT_GUIDE[name]}")

with st.expander("숫자 5개는 무엇인가요?"):
    st.markdown("""
| 입력 | 뜻 | 모델 안에서 |
|---|---|---|
| 주문 건수 | 지금까지 받은 주문 수 | 로그로 바꿔 사용 |
| 판매액 | 지금까지 판 금액 합계 | 로그로 바꿔 사용 |
| 평균 리뷰 점수 | 고객 별점 평균 | 그대로 |
| 마지막 판매 후 지난 날 수 | 최근에도 팔고 있는가 | 그대로 |
| 첫 판매 후 지난 날 수 | 입점한 지 얼마나 됐는가 | 그대로 |

모델은 2018-06-01 이전 데이터로 판매자를 4묶음으로 나눴고, 넣은 숫자가 **가장 가까운 묶음**의 이름을 돌려줍니다.
""")
