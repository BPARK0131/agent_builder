"""
숫자 게임 통합 웹 앱 (단일 진입점)
- 게임 1: 1~100 숫자 맞추기 (랜덤 정답, 시도 이력 표시)
- 게임 2: 이진 탐색 과정 보기 (정답 입력, 단계별 진행)

실행: streamlit run 02_streamlit.py
"""
import random
import pandas as pd
import streamlit as st

st.set_page_config(page_title="숫자 게임", page_icon="🎯", layout="centered")

st.title("🎯 숫자 게임")
st.caption("두 가지 게임을 탭에서 선택하세요")
st.markdown("---")

tab1, tab2 = st.tabs(["🎯 숫자 맞추기", "🔍 이진 탐색 과정"])

# ========== 게임 1: 숫자 맞추기 ==========
with tab1:
    st.subheader("1~100 숫자 맞추기 게임")

    # 게임1 전용 세션 상태 (g1_ 접두사)
    if "g1_answer" not in st.session_state:
        st.session_state.g1_answer = random.randint(1, 100)
        st.session_state.g1_attempts = 0
        st.session_state.g1_game_over = False
        st.session_state.g1_history = []  # (시도, 입력값, 결과)
    if "g1_history" not in st.session_state:
        st.session_state.g1_history = []

    if not st.session_state.g1_game_over:
        st.info("컴퓨터가 1~100 사이의 숫자를 정했습니다. 맞춰보세요!")

        # 시도 이력 표시
        if st.session_state.g1_history:
            st.markdown("**📋 시도 이력**")
            rows = []
            for attempt, val, result in st.session_state.g1_history:
                icon = "⬆️ 더 큰" if "큰" in result else "⬇️ 더 작은" if "작은" in result else "🎯 정답!"
                rows.append({"시도": attempt, "입력": val, "결과": icon})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.markdown("---")

        guess = st.number_input(
            "숫자를 입력하세요",
            min_value=1,
            max_value=100,
            value=50,
            step=1,
            key="g1_guess_input",
        )

        if st.button("확인", key="g1_confirm"):
            st.session_state.g1_attempts += 1

            if guess < st.session_state.g1_answer:
                result = "더 큰 숫자입니다!"
                st.session_state.g1_history.append((st.session_state.g1_attempts, guess, result))
                st.warning(f"{result} (시도 {st.session_state.g1_attempts}회)")
            elif guess > st.session_state.g1_answer:
                result = "더 작은 숫자입니다!"
                st.session_state.g1_history.append((st.session_state.g1_attempts, guess, result))
                st.warning(f"{result} (시도 {st.session_state.g1_attempts}회)")
            else:
                st.session_state.g1_history.append((st.session_state.g1_attempts, guess, "정답!"))
                st.session_state.g1_game_over = True
                st.balloons()
                st.success(f"정답입니다! 🎉 {st.session_state.g1_attempts}번 만에 맞추셨네요.")
                st.rerun()

    else:
        st.success(f"정답은 **{st.session_state.g1_answer}** 이었습니다!")
        st.caption(f"총 {st.session_state.g1_attempts}번 만에 맞추셨습니다.")

        # 최종 시도 이력
        st.markdown("**📋 시도 이력**")
        rows = []
        for attempt, val, result in st.session_state.g1_history:
            icon = "⬆️ 더 큰" if "큰" in result else "⬇️ 더 작은" if "작은" in result else "🎯 정답!"
            rows.append({"시도": attempt, "입력": val, "결과": icon})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.markdown("---")

        if st.button("다시 하기", key="g1_restart"):
            st.session_state.g1_answer = random.randint(1, 100)
            st.session_state.g1_attempts = 0
            st.session_state.g1_game_over = False
            st.session_state.g1_history = []
            st.rerun()

# ========== 게임 2: 이진 탐색 과정 ==========
with tab2:
    st.subheader("최소 시도로 숫자 찾기 (이진 탐색)")

    # 게임2 전용 세션 상태 (g2_ 접두사)
    if "g2_answer" not in st.session_state:
        st.session_state.g2_answer = None
        st.session_state.g2_low = 1
        st.session_state.g2_high = 100
        st.session_state.g2_attempts = 0
        st.session_state.g2_history = []
        st.session_state.g2_game_over = False
    if "g2_history" not in st.session_state:
        st.session_state.g2_history = []

    if st.session_state.g2_answer is None:
        st.info("1~100 사이의 정답 숫자를 입력하세요. 이진 탐색으로 찾는 과정을 보여드립니다.")

        answer_input = st.number_input(
            "정답 숫자",
            min_value=1,
            max_value=100,
            value=50,
            step=1,
            key="g2_answer_input",
        )

        if st.button("시작", key="g2_start"):
            st.session_state.g2_answer = answer_input
            st.session_state.g2_low = 1
            st.session_state.g2_high = 100
            st.session_state.g2_attempts = 0
            st.session_state.g2_history = []
            st.session_state.g2_game_over = False
            st.rerun()

    else:
        st.write(f"**정답:** {st.session_state.g2_answer}")

        if not st.session_state.g2_game_over:
            low, high = st.session_state.g2_low, st.session_state.g2_high
            guess = (low + high) // 2

            st.session_state.g2_attempts += 1

            if guess < st.session_state.g2_answer:
                result = f"{guess} < 정답 → 더 큰 숫자!"
                st.session_state.g2_history.append((low, high, guess, result))
                st.session_state.g2_low = guess + 1
            elif guess > st.session_state.g2_answer:
                result = f"{guess} > 정답 → 더 작은 숫자!"
                st.session_state.g2_history.append((low, high, guess, result))
                st.session_state.g2_high = guess - 1
            else:
                st.session_state.g2_history.append((low, high, guess, "정답!"))
                st.session_state.g2_game_over = True

            st.markdown("---")
            for i, (l, h, g, r) in enumerate(st.session_state.g2_history, 1):
                is_last = i == len(st.session_state.g2_history)
                if is_last:
                    st.subheader(f"시도 {i}")
                    st.write(f"**탐색 범위:** {l} ~ {h}")
                    st.write(f"**추측:** {g} (중간값)")
                    if st.session_state.g2_game_over:
                        st.success("정답!")
                    else:
                        st.info(r)
                else:
                    with st.expander(f"시도 {i}"):
                        st.write(f"범위: {l}~{h} | 추측: {g} | {r}")

            if not st.session_state.g2_game_over:
                if st.button("다음 시도", key="g2_next"):
                    st.rerun()
            else:
                st.balloons()
                st.success(f"총 {st.session_state.g2_attempts}번 만에 정답 {st.session_state.g2_answer}을(를) 찾았습니다!")
                st.caption("이진 탐색: 최대 7번이면 1~100 범위에서 찾을 수 있음")

                if st.button("다시 하기", key="g2_restart"):
                    st.session_state.g2_answer = None
                    st.session_state.g2_low = 1
                    st.session_state.g2_high = 100
                    st.session_state.g2_attempts = 0
                    st.session_state.g2_history = []
                    st.session_state.g2_game_over = False
                    st.rerun()
        else:
            for i, (l, h, g, r) in enumerate(st.session_state.g2_history, 1):
                with st.expander(f"시도 {i}", expanded=(i == len(st.session_state.g2_history))):
                    st.write(f"범위: {l}~{h} | 추측: {g} | {r}")

            st.success(f"총 {st.session_state.g2_attempts}번 만에 정답 {st.session_state.g2_answer}을(를) 찾았습니다!")

            if st.button("다시 하기", key="g2_restart2"):
                st.session_state.g2_answer = None
                st.session_state.g2_low = 1
                st.session_state.g2_high = 100
                st.session_state.g2_attempts = 0
                st.session_state.g2_history = []
                st.session_state.g2_game_over = False
                st.rerun()
