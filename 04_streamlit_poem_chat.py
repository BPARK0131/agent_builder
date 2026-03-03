"""
AI 시인 Streamlit 챗 앱
- 사용자의 입력(주제/상황/감정 등)을 받아 시를 생성
- temperature 를 슬라이더로 조절 (기본 0.7)

실행 예시:
    streamlit run 04_streamlit_poem_chat.py
"""

import os
import random

import streamlit as st
from openai import AzureOpenAI

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    # python-dotenv 미설치 시에도 앱은 동작하도록 무시
    pass


ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://skt-agent-hol.openai.azure.com")
API_KEY = os.getenv("AZURE_OPENAI_KEY", "")
API_VERSION = "2024-12-01-preview"
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")


st.set_page_config(page_title="AI 시인 챗봇", page_icon="📜", layout="centered")

st.title("📜 AI 시인 챗봇")
st.caption("절제된 서정과 일상어로 시를 지어주는 작은 시인입니다.")
st.markdown("---")

if not API_KEY:
    st.error("API 키가 설정되지 않았습니다. `.env` 파일에 `AZURE_OPENAI_KEY`를 설정해 주세요.")
    st.stop()


client = AzureOpenAI(
    azure_endpoint=ENDPOINT,
    api_key=API_KEY,
    api_version=API_VERSION,
)


POEM_THEMES = [
    "봄날의 추억",
    "가을 단풍",
    "겨울 첫눈",
    "여름 밤의 별",
    "바다와 그리움",
    "어머니의 손",
    "고향의 풍경",
    "이별",
    "재회",
    "사랑의 시작",
    "빗속을 걸으며",
    "창밖의 풍경",
    "잊혀진 편지",
    "새벽의 고요함",
    "꽃잎이 흩날리는 날",
    "기다림",
    "희망",
    "그리움",
    "시간의 흐름",
]


POET_SYSTEM_PROMPT = """
당신은 절제된 서정과 일상적 언어로 시를 쓰는 젊은 현대 시인입니다.
과한 수사 없이, 구체적인 사물과 장면을 통해 감정을 드러냅니다.

[역할]
- 일상의 말로 시를 쓰는 시인
- 감정을 직접 설명하지 않고 장면으로 보여주는 화자
- 무거운 주제를 담담하게 풀어내는 작가

[시 창작 지침]

1. 제목
- 일상에서 나올 법한 구체적인 제목
- 문장형 제목 가능
- 과한 수식어 사용 금지

2. 언어
- 평범한 일상어 사용
- 감정을 직접 설명하는 단어(슬프다, 외롭다 등) 최소화
- 대신 사물, 행동, 상황으로 감정을 드러낼 것
- 난해한 상징이나 과한 은유 금지
- 누군가에게 말하듯 자연스럽게

3. 형식
- 짧은 시
- 한 호흡에 읽히는 분량
- 행갈이를 통해 자연스러운 호흡 형성
- 기계적인 형식 반복 금지

4. 어조
- 담담하고 신중한 말투
- 조용히 건네는 문장
- 결말은 설명하지 않고 여운을 남길 것

5. 필수 요소
- 구체적인 사물 1~2개 등장
- 시간, 계절, 혹은 하루의 흐름 암시 1회 이상

[출력 형식]

제목: [시의 제목]

[시 본문 - 자유 형식]

설명이나 해설은 절대 포함하지 말 것.
"""


def generate_poem(prompt: str, temperature: float = 0.7) -> str:
    """사용자 입력을 주제로 새로운 시를 생성."""
    result = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": POET_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "아래 사용자의 입력을 시의 주제나 장면, 상황으로 삼고 "
                    "지침에 맞는 하나의 시를 새로 작성해 주세요.\n\n"
                    "반드시 지정된 출력 형식만 사용하고, 설명이나 해설은 쓰지 마세요.\n\n"
                    f"사용자 입력:\n{prompt}"
                ),
            },
        ],
        temperature=temperature,
    )
    return result.choices[0].message.content or ""


# ===== 사이드바: 설정 =====
with st.sidebar:
    st.subheader("⚙️ 시 생성 설정")
    temperature = st.slider(
        "temperature (창의성)",
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.1,
        help="값이 높을수록 더 자유롭고 예측하기 어려운 시가 생성됩니다.",
    )

    if st.button("대화 초기화"):
        st.session_state.pop("messages", None)
        st.rerun()

    with st.expander("시 스타일 안내", expanded=False):
        st.markdown(
            "- **일상어**로, 담담하게\n"
            "- **구체적인 사물/장면** 위주\n"
            "- 감정 단어 대신 **상황**으로 드러내기\n"
            "- 결말은 설명하지 않고 **여운** 남기기"
        )


# ===== 세션 상태: 대화 이력 및 랜덤 주제 =====
if "messages" not in st.session_state:
    st.session_state.messages = []
if "random_theme" not in st.session_state:
    st.session_state.random_theme = None

# 랜덤 주제 뽑기 UI
with st.container():
    cols = st.columns([1, 2])
    with cols[0]:
        if st.button("🎲 랜덤 주제 뽑기"):
            st.session_state.random_theme = random.choice(POEM_THEMES)
    with cols[1]:
        if st.session_state.random_theme:
            st.info(f"랜덤 주제: **{st.session_state.random_theme}**")

# 기존 대화 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ===== 입력 & 응답 생성 =====
user_input = st.chat_input(
    "시의 주제나 상황을 자유롭게 적어 주세요 (랜덤 주제를 사용해도 좋습니다)..."
)

if user_input or st.session_state.random_theme:
    # 입력이 비어 있고 랜덤 주제가 있으면 랜덤 주제를 사용
    effective_prompt = user_input.strip() if user_input else st.session_state.random_theme

    # 사용자 메시지 표시
    st.session_state.messages.append({"role": "user", "content": effective_prompt})
    with st.chat_message("user"):
        st.markdown(effective_prompt)

    # 시 생성
    with st.chat_message("assistant"):
        with st.spinner("시를 쓰는 중입니다..."):
            poem = generate_poem(effective_prompt, temperature=temperature)
            st.markdown(poem)

    st.session_state.messages.append({"role": "assistant", "content": poem})
