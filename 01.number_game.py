import random

def number_game():
    answer = random.randint(1, 100)
    attempts = 0

    print("=" * 40)
    print("  1부터 100 사이의 숫자 맞추기 게임")
    print("=" * 40)
    print()

    while True:
        try:
            guess = int(input("숫자를 입력하세요: "))
        except ValueError:
            print("올바른 숫자를 입력해주세요.\n")
            continue

        attempts += 1

        if guess < 1 or guess > 100:
            print("1부터 100 사이의 숫자를 입력해주세요.\n")
            continue

        if guess < answer:
            print("더 큰 숫자입니다!\n")
        elif guess > answer:
            print("더 작은 숫자입니다!\n")
        else:
            print(f"\n정답입니다! 🎉 {attempts}번 만에 맞추셨네요.")
            break


if __name__ == "__main__":
    number_game()
