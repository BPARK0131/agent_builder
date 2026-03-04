"""
LangChain 테스트: Azure OpenAI LLM 및 PDF 로더 활용
"""
import os
import time

import numpy as np
import tiktoken
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# -----------------------------------------------------------------------------
# 환경 설정
# -----------------------------------------------------------------------------
load_dotenv()

MODEL_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT")
API_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

# -----------------------------------------------------------------------------
# LLM 초기화
# -----------------------------------------------------------------------------
llm = AzureChatOpenAI(
    azure_deployment=MODEL_DEPLOYMENT_NAME,
    api_key=API_KEY,
    azure_endpoint=AZURE_ENDPOINT,
    api_version=API_VERSION,
    temperature=0,
)

# -----------------------------------------------------------------------------
# 업무 플래너 예시 메시지 (주석 처리된 invoke 예시)
# -----------------------------------------------------------------------------
messages = [
    SystemMessage(
        content="당신은 업무 계획을 세워주는 업무 플래너 머신입니다. "
                "사용자의 업무를 입력 받으면 이를 위한 계획을 작성합니다."
    ),
    HumanMessage(content="신입사원 교육을 해야됩니다."),
]
# response = llm.invoke(messages)
# print(response.content)

# -----------------------------------------------------------------------------
# PDF 로드 및 텍스트 분할
# -----------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(SCRIPT_DIR, "Owners_Manual.pdf")

loader = PyPDFLoader(PDF_PATH)
t0 = time.perf_counter()
pages = loader.load_and_split()
load_sec = time.perf_counter() - t0

tokenizer = tiktoken.get_encoding("cl100k_base")


def tiktoken_len(text: str) -> int:
    """텍스트의 토큰 개수를 반환합니다."""
    return len(tokenizer.encode(text))


# 텍스트 스플리터 설정 (토큰 단위 분할)
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 0

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    length_function=tiktoken_len,
)
t1 = time.perf_counter()
texts = text_splitter.split_documents(pages)
split_sec = time.perf_counter() - t1

# -----------------------------------------------------------------------------
# 임베딩
# -----------------------------------------------------------------------------
EMBEDDING_DEPLOYMENT = "text-embedding-3-large"
EMBEDDING_CHUNK_SIZE = 1000

embedding_model = AzureOpenAIEmbeddings(
    azure_deployment=EMBEDDING_DEPLOYMENT,
    api_key=API_KEY,
    azure_endpoint=AZURE_ENDPOINT,
    api_version=API_VERSION,
    chunk_size=EMBEDDING_CHUNK_SIZE,
)

# 임베딩 테스트용 문장 목록 (n개 자유롭게 추가 가능, 아래 유사도 테이블에 반영됨)
embedding_examples = [
    "안녕하세요,제 이름은 홍길동 입니다.",
    "Hello, my name is Hong Gil Dong.",
    "안녕 나는 홍길동 이야.",
]

t2 = time.perf_counter()
embeddings = embedding_model.embed_documents(embedding_examples)
embed_sec = time.perf_counter() - t2

# -----------------------------------------------------------------------------
# 코사인 유사도
# -----------------------------------------------------------------------------


def cos_sim(a: np.ndarray, b: np.ndarray) -> float:
    """두 벡터의 코사인 유사도를 반환합니다. (-1 ~ 1, 1에 가까울수록 유사)"""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


# n개 문장 간 코사인 유사도 행렬 (n×n)
n_sentences = len(embedding_examples)
similarity_matrix = np.array(
    [[cos_sim(embeddings[i], embeddings[j]) for j in range(n_sentences)] for i in range(n_sentences)]
)

# -----------------------------------------------------------------------------
# Chroma DB (벡터 스토어)
# -----------------------------------------------------------------------------
CHROMA_PERSIST_DIR = os.path.join(SCRIPT_DIR, "chroma_db")

t3 = time.perf_counter()
vectorstore = Chroma.from_documents(
    documents=texts,
    embedding=embedding_model,
    persist_directory=CHROMA_PERSIST_DIR,
)
chroma_sec = time.perf_counter() - t3

# -----------------------------------------------------------------------------
# 실행: PDF 요약, 토큰/청크 수, 임베딩·Chroma 결과 및 코사인 유사도 출력
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    page_index = 1
    print("PDF page count:", len(pages))
    print("  → PDF 로드 소요 시간: {:.1f}초".format(load_sec))
    print("  → 텍스트 분할 소요 시간: {:.1f}초".format(split_sec))
    # print(pages[page_index].page_content)
    print("\nToken count:", tiktoken_len(pages[page_index].page_content))
    print("Split chunks count:", len(texts))

    print("\n--- 임베딩 ---")
    print("문장 개수:", len(embeddings))
    print("벡터 차원 (첫 문장):", len(embeddings[0]))
    print("  → 임베딩 소요 시간: {:.1f}초".format(embed_sec))

    print("\n[샘플 문장 ↔ 임베딩 벡터 앞 5차원]")
    for i, (sentence, vec) in enumerate(zip(embedding_examples, embeddings)):
        preview = vec[:5]
        print("  {} | {!r} → {}".format(i + 1, sentence, [round(x, 4) for x in preview]))

    # n개 문장 간 유사도 테이블
    print("\n[문장 간 코사인 유사도 테이블] (n={})".format(n_sentences))
    col_w = 8
    header = "".join("{:>{w}}".format(j + 1, w=col_w) for j in range(n_sentences))
    print("      {}".format(header))
    print("    " + "-" * (col_w * n_sentences))
    for i in range(n_sentences):
        row_vals = "".join("{:>{w}.3f}".format(similarity_matrix[i, j], w=col_w) for j in range(n_sentences))
        print("  {} |{}".format(i + 1, row_vals))
    print("\n  [문장 목록]")
    for i, s in enumerate(embedding_examples):
        label = (s[:20] + "…") if len(s) > 20 else s
        print("    {} : {}".format(i + 1, label))

    print("\n--- Chroma DB ---")
    print("  저장 경로: {}".format(CHROMA_PERSIST_DIR))
    print("  문서(청크) 수: {}".format(len(texts)))
    print("  → 벡터 스토어 구축 소요 시간: {:.1f}초".format(chroma_sec))
