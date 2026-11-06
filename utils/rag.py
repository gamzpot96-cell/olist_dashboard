"""RAG 챗봇 함수 (STEP4 11_olist_rag_chatbot 노트북과 같은 순서)

책장(자료)을 세 가지로 나눠 둡니다.
| 채널 | 책장 | 답할 수 있는 것 |
|---|---|---|
| A | 사실표 (data/olist_facts.csv) | 분석 숫자 |
| B | 사실표 + 모델 설명서 (data/olist_model_guide.md) | 분석 숫자 + 모델이 하는 일·한계 |
| C | 사실표 + 모델 설명서 + 규정집 PDF (data/olist_seller_policy.pdf) | 위 내용 + 판매자 규정 |
"""
import re
from pathlib import Path

import pandas as pd
import streamlit as st
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

DATA_DIR = Path(__file__).parent.parent / "data"
CHANNELS = {
    "A": "A. 분석 사실 확인 (사실표)",
    "B": "B. 분석 + 모델 안내 (사실표 + 모델 설명서)",
    "C": "C. 분석 + 모델 + 규정 (사실표 + 설명서 + 규정집 PDF)",
}
NOT_FOUND = "제공된 자료로는 확인할 수 없습니다."


# ───────── ① 자료 → 조각(Document) ─────────
def load_fact_docs():
    """사실표 1행 = 조각 1개"""
    facts = pd.read_csv(DATA_DIR / "olist_facts.csv")
    return [Document(page_content=f"{r['내용']} (기준: {r['기준']})",
                     metadata={"id": r["사실ID"], "출처": r["출처"]})
            for _, r in facts.iterrows()]


def load_guide_docs():
    """모델 설명서의 '## 제목' 하나 = 조각 1개"""
    text = (DATA_DIR / "olist_model_guide.md").read_text(encoding="utf-8")
    docs = []
    for block in text.split("\n## ")[1:]:                     # 맨 앞(# 제목)은 빼고
        title, body = block.split("\n", 1)
        doc_id = title.split()[0]                              # 예: "M09"
        docs.append(Document(page_content=f"{title}\n{body.strip()}",
                             metadata={"id": doc_id, "출처": "모델 설명서"}))
    return docs


def load_policy_docs():
    """규정집 PDF의 '제○조' 하나 = 조각 1개 (쪽 번호를 출처로)"""
    pages = PyPDFLoader(str(DATA_DIR / "olist_seller_policy.pdf")).load()   # 1쪽 = Document 1개
    docs = []
    for page in pages:
        for part in re.split(r"\n(?=제\d+조)", page.page_content):          # '제○조' 앞에서 자르기
            m = re.match(r"제(\d+)조", part)
            if not m:                                                       # 표지 · 머리말은 빼기
                continue
            lines = [l for l in part.splitlines() if not re.match(r"제\d+장|부칙", l)]  # 장 제목 줄 빼기
            docs.append(Document(page_content="\n".join(lines).strip(),
                                 metadata={"id": f"R{int(m.group(1)):02d}",
                                           "출처": f"규정집 {page.metadata['page'] + 1}쪽"}))
    return docs


# ───────── ② 임베딩 → 벡터 저장소 (채널마다 하나) ─────────
@st.cache_resource(show_spinner="자료를 좌표로 바꾸는 중…")
def build_store(channel, api_key):
    docs = load_fact_docs()                                   # A : 사실표
    if channel in ("B", "C"):
        docs += load_guide_docs()                             # B : + 모델 설명서
    if channel == "C":
        docs += load_policy_docs()                            # C : + 규정집 PDF
    emb = OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key)
    return InMemoryVectorStore.from_documents(docs, emb)


# ───────── ③ 지침(프롬프트) ─────────
PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "너는 Olist 분석 결과 안내 챗봇이야.\n"
     "- 아래 [근거]에 있는 내용으로만 답해.\n"
     "- 문장마다 끝에 근거 ID를 [F01]처럼 붙여.\n"
     "- 규정을 인용할 때는 몇 조인지 함께 써.\n"
     "- 숫자는 근거의 숫자를 그대로 써. 직접 계산했다면 '(계산)'이라고 밝혀.\n"
     f"- [근거]로 답할 수 없으면 '{NOT_FOUND}'라고만 답해.\n"
     "- 한국어로 3문장 이내로 답해."),
    ("human", "[근거]\n{context}\n\n[질문]\n{question}"),
])


# ───────── ④ 질문 → 찾기 → 답하기 → 근거 ID 점검 ─────────
def ask(question, channel, api_key, k=4):
    store = build_store(channel, api_key)
    found = store.similarity_search(question, k=k)                         # 비슷한 조각 k개
    context = "\n".join(f"({d.metadata['id']}) {d.page_content}" for d in found)
    llm = ChatOpenAI(model="gpt-5.4-mini", api_key=api_key)
    answer = (PROMPT | llm | StrOutputParser()).invoke({"context": context, "question": question})

    found_ids = {d.metadata["id"] for d in found}
    cited = set(re.findall(r"\[([FMR]\d{2})\]", answer))                     # 답에 쓴 ID
    return {"answer": answer, "found": found, "fake": sorted(cited - found_ids)}  # fake = 찾지 않은 ID
