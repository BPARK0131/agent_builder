import time


def number_game_with_process():
    """이진 탐색으로 최소 시도에 숫자를 찾는 과정을 보여줍니다."""
    print("=" * 50)
    print("  최소 시도로 숫자 찾기 (이진 탐색)")
    print("=" * 50)

    while True:
        try:
            answer = int(input("\n정답 숫자를 입력하세요 (1 ~ 100): "))
            if 1 <= answer <= 100:
                break
            print("1부터 100 사이의 숫자를 입력해주세요.")
        except ValueError:
            print("올바른 숫자를 입력해주세요.")

    low, high = 1, 100
    attempts = 0
    print("\n" + "-" * 50)

    while low <= high:
        attempts += 1
        guess = (low + high) // 2  # 중간값 선택

        print(f"\n[시도 {attempts}]")
        print(f"  탐색 범위: {low} ~ {high}")
        print(f"  추측: {guess} (중간값)")

        if guess < answer:
            print(f"  결과: {guess} < 정답 → 더 큰 숫자!")
            low = guess + 1
        elif guess > answer:
            print(f"  결과: {guess} > 정답 → 더 작은 숫자!")
            high = guess - 1
        else:
            print(f"  결과: 정답!")
            break

        time.sleep(0.5)  # 과정을 보기 쉽게 잠시 대기

    print("\n" + "=" * 50)
    print(f"  총 {attempts}번 만에 정답 {answer}을(를) 찾았습니다!")
    print("  (이진 탐색: 최대 7번이면 1~100 범위에서 찾을 수 있음)")
    print("=" * 50)


if __name__ == "__main__":
    number_game_with_process()
