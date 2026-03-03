"""
Azure OpenAI 챗봇 웹 앱
- 사용 가능한 배포 목록에서 복수 모델 선택
- 선택한 모델들의 답변을 나란히 비교
"""
import os
import requests
import streamlit as st
from openai import AzureOpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed

# .env 로드
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

st.set_page_config(page_title="모델 비교 챗봇", page_icon="💬", layout="wide")

st.title("💬 Azure OpenAI 모델 비교 챗봇")
st.caption("여러 모델을 선택하면 답변을 나란히 비교할 수 있습니다.")
st.markdown("---")

ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://skt-agent-hol.openai.azure.com")
API_KEY = os.getenv("AZURE_OPENAI_KEY", "")
API_VERSION = "2024-12-01-preview"

if not API_KEY:
    st.error("API 키가 설정되지 않았습니다. .env 파일에 AZURE_OPENAI_KEY를 설정하세요.")
    st.stop()

client = AzureOpenAI(
    azure_endpoint=ENDPOINT,
    api_key=API_KEY,
    api_version=API_VERSION,
)


@st.cache_data(ttl=300)
def fetch_deployments():
    """배포 목록 조회 - deployments API 우선, 없으면 models API (5분 캐시)"""
    headers = {"api-key": API_KEY}

    # 1) deployments API (실제 배포 이름 반환)
    for api_ver in ["2023-05-15", "2023-03-15-preview"]:
        url = f"{ENDPOINT.rstrip('/')}/openai/deployments?api-version={api_ver}"
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            # data 또는 data.data
            items = data.get("data", data) if isinstance(data, dict) else data
            if isinstance(items, list):
                names = []
                for d in items:
                    n = d.get("id") or d.get("name") or d.get("deployment_name")
                    if n:
                        names.append(n)
                if names:
                    return names

    # 2) models API (모델 ID - 배포 이름과 다를 수 있음)
    url = f"{ENDPOINT.rstrip('/')}/openai/models?api-version=2024-10-21"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise Exception(f"배포 목록 조회 실패: {resp.text[:200]}")
    data = resp.json()
    models = [m.get("id", "") for m in data.get("data", []) if m.get("id")]

    # .env의 배포 이름이 목록에 없으면 추가 (사용자가 알고 있는 이름)
    env_deploy = os.getenv("AZURE_OPENAI_DEPLOYMENT", "").strip()
    if env_deploy and env_deploy not in models:
        models = [env_deploy] + models
    return models


def get_response(model: str, question: str) -> tuple[str, str]:
    """단일 모델 응답 (에러 시 에러 메시지 반환)"""
    try:
        result = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": question}],
        )
        return model, result.choices[0].message.content or "(응답 없음)"
    except Exception as e:
        return model, f"오류: {str(e)[:200]}"


# 사이드바: 모델 선택
with st.sidebar:
    st.subheader("⚙️ 설정")
    try:
        deployments = fetch_deployments()
    except Exception as e:
        st.error(f"배포 목록 로드 실패:\n{e}")
        st.stop()

    if not deployments:
        st.warning("사용 가능한 배포가 없습니다.")
        st.stop()

    selected = st.multiselect(
        "비교할 모델 선택 (복수 선택)",
        options=deployments,
        default=deployments[:2] if len(deployments) >= 2 else deployments[:1],
        key="model_select",
    )

    st.markdown("---")
    st.caption("404 오류 시: Azure Portal > Azure OpenAI > 모델 배포에서 배포 이름 확인")
    manual = st.text_input(
        "또는 배포 이름 직접 입력 (쉼표 구분)",
        placeholder="예: gpt-4o-mini, gpt-35-turbo",
        key="manual_deploy",
    )
    if manual:
        manual_list = [x.strip() for x in manual.split(",") if x.strip()]
        selected = list(set(selected) | set(manual_list))

    if not selected:
        st.info("비교할 모델을 1개 이상 선택하세요.")

# 메인 영역
question = st.chat_input("질문을 입력하세요...")

if question and selected:
    with st.spinner("답변 생성 중..."):
        results = {}
        with ThreadPoolExecutor(max_workers=min(5, len(selected))) as executor:
            futures = {executor.submit(get_response, m, question): m for m in selected}
            for future in as_completed(futures):
                model, response = future.result()
                results[model] = response

    st.markdown("---")
    with st.chat_message("user"):
        st.write(question)
    st.subheader("📋 답변 비교")

    cols = st.columns(len(selected))
    for i, model in enumerate(selected):
        with cols[i]:
            st.markdown(f"**{model}**")
            with st.container():
                st.markdown(results.get(model, "—"))

elif question and not selected:
    st.warning("비교할 모델을 사이드바에서 선택하세요.")
