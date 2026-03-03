import os
import random
import sys
import requests
from openai import AzureOpenAI

# 랜덤 시 주제 목록 (빈 입력 시 사용)
POEM_THEMES = [
    "봄날의 추억", "가을 단풍", "겨울 첫눈", "여름 밤의 별", "바다와 그리움",
    "어머니의 손", "고향의 풍경", "이별", "재회", "사랑의 시작",
    "빗속을 걸으며", "창밖의 풍경", "잊혀진 편지", "새벽의 고요함",
    "꽃잎이 흩날리는 날", "기다림", "희망", "그리움", "시간의 흐름",
]

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

# 배포 목록 조회: python "04.AI_poem.py" --list
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


def write_poem(theme: str, temperature: float = 0.7) -> str:
    result = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": POET_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "다음 주제로 시를 써 주세요. "
                    "제목과 시 본문을 지정된 형식으로 출력해 주세요.\n\n"
                    f"주제: {theme}"
                ),
            },
        ],
        temperature=temperature,
    )
    return result.choices[0].message.content


# 시의 주제 입력: 인자로 전달 또는 대화형 입력
if len(sys.argv) > 1 and sys.argv[1] != "--list":
    theme = " ".join(sys.argv[1:]).strip()
    if not theme:
        theme = random.choice(POEM_THEMES)
        print(f"(랜덤 주제: {theme})\n")
    try:
        # 인자 모드에서는 기본 temperature 0.7 사용
        print(write_poem(theme, temperature=0.7))
    except Exception as e:
        if "DeploymentNotFound" in str(e) or "404" in str(e):
            print("오류: 배포를 찾을 수 없습니다.")
            print(f"  현재 설정: {DEPLOYMENT_NAME}")
            print("\n사용 가능한 배포 확인: python \"04.AI_poem.py\" --list")
        else:
            raise
else:
    print("AI 시인 (종료: quit, exit, q / 빈 입력 시 랜덤 주제)")
    print("-" * 40)
    print("temperature 범위: 0.0 ~ 2.0 (엔터 시 0.7)")
    while True:
        try:
            theme = input("\n시의 주제: ").strip()
            if theme.lower() in ("quit", "exit", "q"):
                print("종료합니다.")
                break
            if not theme:
                theme = random.choice(POEM_THEMES)
                print(f"(랜덤 주제: {theme})\n")

            temp_input = input("temperature (기본 0.7): ").strip()
            if temp_input == "":
                temperature = 0.7
            else:
                try:
                    temperature = float(temp_input)
                except ValueError:
                    print("숫자로 입력해 주세요. 기본값 0.7을 사용합니다.")
                    temperature = 0.7

            print("\n[시]\n", write_poem(theme, temperature=temperature))
        except Exception as e:
            if "DeploymentNotFound" in str(e) or "404" in str(e):
                print("오류: 배포를 찾을 수 없습니다. .env의 AZURE_OPENAI_DEPLOYMENT를 확인하세요.")
                break
            raise