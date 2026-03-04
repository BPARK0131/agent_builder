"""
여행 에이전트 테스트 스크립트

Azure OpenAI의 Function Calling을 활용하여
날씨 조회, 환율 계산 등 도구를 사용하는 여행사 에이전트를 구현합니다.
"""

import json
import os
import sys

from dotenv import load_dotenv
from openai import AzureOpenAI

# =============================================================================
# 1. 환경 설정 및 클라이언트 초기화
# =============================================================================

load_dotenv()

ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
API_KEY = os.getenv("AZURE_OPENAI_KEY") or os.getenv("API_KEY")
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION") or os.getenv("API_VERSION")
DEPLOYMENT_NAME = "gpt-4.1"  # Azure OpenAI 배포 모델명

client = AzureOpenAI(
    azure_endpoint=ENDPOINT,
    api_key=API_KEY,
    api_version=API_VERSION,
)


# =============================================================================
# 2. 도구(Tools) 함수 정의 - 에이전트가 호출할 실제 로직
# =============================================================================

def get_weather(city: str) -> str:
    """
    특정 도시의 날씨 정보를 반환합니다.

    Args:
        city: 조회할 도시 이름 (예: 도쿄, 파리, 뉴욕)

    Returns:
        해당 도시의 날씨 및 온도 문자열
    """
    weather_map = {
        "도쿄": "흐림, 18도",
        "파리": "맑음, 22도",
        "뉴욕": "눈, -2도",
    }
    result = weather_map.get(city, f"{city}의 날씨 정보를 찾을 수 없습니다.")
    print(f"[시스템 로그] 날씨 조회: {city} → {result}")
    return result


def get_exchange_rate(currency_code: str) -> float:
    """
    원화(KRW) 대비 해당 통화의 환율을 반환합니다.

    Args:
        currency_code: 통화 코드 (예: JPY, USD, EUR)

    Returns:
        원화 대비 환율 (1 외화 = N 원)
    """
    rates = {
        "JPY": 9.2,
        "USD": 1340.5,
        "EUR": 1460.0,
    }
    result = rates.get(currency_code.upper(), 1.0)
    print(f"[시스템 로그] 환율 조회: {currency_code} → {result}")
    return result


# =============================================================================
# 3. 도구 메타데이터 - 모델에게 전달할 Function Calling 스키마
# =============================================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "특정 도시의 현재 날씨와 온도를 가져옵니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "도시 이름 (예: 도쿄, 파리)",
                    }
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": "원화(KRW) 대비 해당 통화의 환율을 가져옵니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "currency_code": {
                        "type": "string",
                        "description": "통화 코드 (예: JPY, USD, EUR)",
                    }
                },
                "required": ["currency_code"],
            },
        },
    },
]

# 에이전트 시스템 프롬프트
SYSTEM_PROMPT = "너는 유능한 여행사 직원이야. 도구를 사용해 정확한 정보를 제공해줘."

# 디버그 출력 여부 (True: 중간 과정 출력, False: 최종 답변만)
DEBUG = True


# =============================================================================
# 4. 에이전트 실행 로직
# =============================================================================

def _debug(msg: str, data: object = None) -> None:
    """디버그 메시지를 포맷팅하여 출력합니다."""
    prefix = "[DEBUG]"
    if data is not None:
        if isinstance(data, str):
            # 문자열은 그대로 출력 (줄바꿈 등 가독성 유지)
            print(f"{prefix} {msg}")
            print("-" * 40)
            print(data)
        else:
            try:
                formatted = json.dumps(data, ensure_ascii=False, indent=2)
            except (TypeError, ValueError):
                formatted = str(data)
            print(f"{prefix} {msg}\n{formatted}")
    else:
        print(f"{prefix} {msg}")
    print()


def _execute_tool_call(tool_call) -> dict:
    """
    모델이 요청한 도구 호출을 실행하고 결과를 메시지 형식으로 반환합니다.

    Args:
        tool_call: OpenAI 응답의 tool_call 객체

    Returns:
        tool 역할의 메시지 딕셔너리
    """
    function_name = tool_call.function.name
    function_args = json.loads(tool_call.function.arguments)

    if function_name == "get_weather":
        result = get_weather(function_args.get("city"))
    elif function_name == "get_exchange_rate":
        result = str(get_exchange_rate(function_args.get("currency_code")))
    else:
        result = f"알 수 없는 도구: {function_name}"

    return {
        "tool_call_id": tool_call.id,
        "role": "tool",
        "name": function_name,
        "content": result,
    }


def run_travel_agent(user_prompt: str, debug: bool = None) -> str:
    """
    사용자 질문에 대해 도구를 활용하여 답변을 생성합니다.

    흐름:
        1) 모델이 도구 사용 필요 여부 판단
        2) 필요 시 도구 호출 실행
        3) 도구 결과를 반영하여 최종 답변 생성

    Args:
        user_prompt: 사용자 질문
        debug: 디버그 출력 여부 (None이면 전역 DEBUG 사용)

    Returns:
        에이전트의 최종 답변 문자열
    """
    show_debug = debug if debug is not None else DEBUG

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    # --- 1단계: 모델 호출 - 도구 사용 여부 자동 판단 ---
    if show_debug:
        _debug("=== 1단계: 모델 호출 (도구 사용 여부 판단) ===")
        _debug("사용자 질문", user_prompt)

    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if show_debug:
        if tool_calls:
            _debug("모델 판단: 도구 사용 필요")
            _debug(
                "※ 혼합 질문 시: 도구가 필요한 부분만 tool_call로 선택됨. "
                "나머지(일반 지식)는 3단계에서 모델이 자체 지식으로 답변"
            )
            _debug("선택된 도구 호출 목록", [
                {"name": tc.function.name, "arguments": tc.function.arguments}
                for tc in tool_calls
            ])
            if response_message.content:
                _debug("1단계 모델 메모(있을 경우)", response_message.content)
        else:
            _debug("모델 판단: 도구 사용 불필요 (직접 답변으로 응답)")
            _debug("판단 근거: 날씨/환율 등 도구 정보가 필요 없다고 판단 → content로 즉시 응답")
            _debug("1단계 모델 응답(직접 답변)", response_message.content)

    # 도구 사용이 필요 없는 경우 → 바로 답변 반환
    if not tool_calls:
        return response_message.content

    # --- 2단계: 도구 호출 실행 ---
    if show_debug:
        _debug("=== 2단계: 도구 실행 ===")

    messages.append(response_message)

    for tool_call in tool_calls:
        if show_debug:
            _debug(
                f"도구 호출: {tool_call.function.name}",
                json.loads(tool_call.function.arguments),
            )
        tool_result = _execute_tool_call(tool_call)
        if show_debug:
            _debug(f"도구 결과: {tool_result['name']}", tool_result["content"])
        messages.append(tool_result)

    # --- 3단계: 도구 결과를 반영하여 최종 답변 생성 ---
    if show_debug:
        _debug("=== 3단계: 최종 답변 생성 ===")
        _debug(
            "모델에 전달되는 정보: [원본 질문] + [도구 실행 결과]. "
            "혼합 질문이었다면, 도구 결과로 답한 부분 + 자체 지식으로 답한 부분을 합쳐 최종 응답 생성"
        )
        msg_roles = [
            m.get("role", "?") if isinstance(m, dict) else getattr(m, "role", "?")
            for m in messages
        ]
        _debug("3단계 전달 메시지 구조 (역할 순서)", msg_roles)

    second_response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=messages,
    )

    return second_response.choices[0].message.content


# =============================================================================
# 5. 메인 실행
# =============================================================================

def _get_user_prompt() -> str | None:
    """
    사용자 질문을 가져옵니다.
    - 명령줄 인자로 전달된 경우: 해당 문자열 사용
    - 인자가 없으면: 터미널에서 입력 대기 (빈 입력 시 None 반환)
    """
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:])
    prompt = input("질문을 입력하세요 (종료: 빈 입력): ").strip()
    return prompt if prompt else None


if __name__ == "__main__":
    if DEBUG:
        print("=" * 60)
        print("  [디버그 모드] 에이전트 중간 과정 출력")
        print("=" * 60)
        print()

    print("여행 에이전트 (종료: 빈 입력 또는 Ctrl+C)")
    print("예시 - 혼합 질문: '3월에 여행가기 좋은 나라 알려주고, 도쿄 날씨도 알려줘'")
    print("-" * 40)

    # 명령줄 인자로 질문 전달 시: 1회 실행 후 종료
    if len(sys.argv) > 1:
        user_prompt = _get_user_prompt()
        answer = run_travel_agent(user_prompt)
        print("-" * 60)
        print(f"최종 답변: {answer}")
    else:
        # 대화형 모드: 반복 질문 가능
        while True:
            user_prompt = _get_user_prompt()
            if user_prompt is None:
                print("종료합니다.")
                break
            answer = run_travel_agent(user_prompt)
            print("-" * 60)
            print(f"최종 답변: {answer}")
            print()
