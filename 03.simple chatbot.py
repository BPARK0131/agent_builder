import os
import sys
import requests
from openai import AzureOpenAI

# .env 파일 로드 (스크립트와 같은 폴더의 .env)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass  # pip install python-dotenv

ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://skt-agent-hol.openai.azure.com")
API_KEY = os.getenv("AZURE_OPENAI_KEY", "")
API_VERSION = "2024-12-01-preview"

if not API_KEY:
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    print("오류: API 키가 설정되지 않았습니다.")
    print(f"  .env 경로: {_env_path}")
    print("  .env 내용 예시: AZURE_OPENAI_KEY=실제키값 (등호 주변 공백 없이)")
    print("  또는: $env:AZURE_OPENAI_KEY=\"키값\" (PowerShell)")
    sys.exit(1)

# 배포 목록 조회: python "03.simple chatbot.py" --list
if len(sys.argv) > 1 and sys.argv[1] == "--list":
    url = f"{ENDPOINT.rstrip('/')}/openai/models?api-version=2024-10-21"
    resp = requests.get(url, headers={"api-key": API_KEY})
    if resp.status_code != 200:
        print(f"조회 실패 ({resp.status_code}): {resp.text[:200]}")
        sys.exit(1)
    data = resp.json()
    print("=== 사용 가능한 배포(모델) 목록 ===\n")
    for m in data.get("data", []):
        print(f"  - {m.get('id', '?')}")
    print("\n.env 또는 AZURE_OPENAI_DEPLOYMENT에 위 이름 중 하나를 설정하세요.")
    sys.exit(0)

DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")

client = AzureOpenAI(
    azure_endpoint=ENDPOINT,
    api_key=API_KEY,
    api_version=API_VERSION,
)

def chat(question: str) -> str:
    result = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=[{"role": "user", "content": question}],
    )
    return result.choices[0].message.content


# 질문 입력: 인자로 전달 또는 대화형 입력
if len(sys.argv) > 1 and sys.argv[1] != "--list":
    question = " ".join(sys.argv[1:])
    try:
        print(chat(question))
    except Exception as e:
        if "DeploymentNotFound" in str(e) or "404" in str(e):
            print("오류: 배포를 찾을 수 없습니다.")
            print(f"  현재 설정: {DEPLOYMENT_NAME}")
            print("\n사용 가능한 배포 확인: python \"03.simple chatbot.py\" --list")
        else:
            raise
else:
    print("챗봇 (종료: quit, exit, 빈 입력)")
    print("-" * 40)
    while True:
        try:
            question = input("\n질문: ").strip()
            if not question:
                continue
            if question.lower() in ("quit", "exit", "q"):
                print("종료합니다.")
                break
            print("\n답변:", chat(question))
        except Exception as e:
            if "DeploymentNotFound" in str(e) or "404" in str(e):
                print("오류: 배포를 찾을 수 없습니다. .env의 AZURE_OPENAI_DEPLOYMENT를 확인하세요.")
                break
            raise