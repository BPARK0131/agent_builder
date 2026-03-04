"""
Vector Search 기반 RAG 챗봇 웹앱
- Chroma DB 벡터 검색 + Azure OpenAI LLM
- 일반적인 LLM 채팅 인터페이스

실행: streamlit run 06_streamlit_vector_chat.py
"""
import os

import streamlit as st
from dotenv import load_dotenv
from langchain_classic.chains import RetrievalQA
from langchain_chroma import Chroma
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

load_dotenv()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PERSIST_DIR = os.path.join(SCRIPT_DIR, "chroma_db")

st.set_page_config(page_title="RAG 챗봇", page_icon="🔍", layout="centered")

st.title("🔍 RAG 챗봇")
st.caption("벡터 검색 기반 문서 질의응답 - 저장된 문서에서 관련 내용을 찾아 답변합니다.")
st.markdown("---")

# API 키 확인
if not os.getenv("AZURE_OPENAI_KEY"):
    st.error("API 키가 설정되지 않았습니다. `.env` 파일에 `AZURE_OPENAI_KEY`를 설정해 주세요.")
    st.stop()


@st.cache_resource
def init_qa_chain():
    """임베딩, 벡터스토어, QA 체인 초기화 (앱 실행 중 한 번만)"""
    embedding_model = AzureOpenAIEmbeddings(
        azure_deployment="text-embedding-3-large",
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        chunk_size=1000,
    )

    vectorstore = Chroma(
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=embedding_model,
    )

    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        temperature=0,
    )

    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 3, "fetch_k": 10},
        ),
    )
    return qa


# 사이드바 설정
with st.sidebar:
    st.subheader("⚙️ 설정")
    if st.button("🗑️ 대화 초기화"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.caption("Chroma DB에 저장된 문서를 기반으로 질문에 답변합니다.")
    st.caption("예: 실내 온도 조절, 전기 공급, 작동 방법 등")


# 세션 상태: 채팅 이력
if "messages" not in st.session_state:
    st.session_state.messages = []


# 기존 대화 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# 사용자 입력
user_input = st.chat_input("질문을 입력하세요...")

if user_input:
    # 사용자 메시지 표시 및 저장
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # QA 체인으로 답변 생성
    with st.chat_message("assistant"):
        with st.spinner("검색 및 답변 생성 중..."):
            try:
                qa = init_qa_chain()
                result = qa.invoke(user_input)
                answer = result.get("result", "(답변을 생성하지 못했습니다.)")
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                err_msg = f"오류가 발생했습니다: {str(e)}"
                st.error(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg})
