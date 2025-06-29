import streamlit as st
import pandas as pd
import math
from datetime import date

# --- 기준 테이블 ---
QUEST_DRAIN = {5: 1500, 9: 1700, 13: 2886}
BOSS_TABLE = {
    "하드-스우": 50,
    "하드-데미안": 50,
    "노말-루시드": 20,
    "노말-윌": 25,
    "노말-더스크": 20,
    "노말-듄켈": 25,
    "노말-진힐라": 135,
}

st.set_page_config(page_title="메이플 주차별 흔적 계산기", layout="wide")
st.title("메이플스토리 주차별 흔적 계산기")

# --- 사용자 입력 ---
col1, col2, col3 = st.columns(3)
with col1:
    nickname = st.text_input("닉네임")
with col2:
    start_date = st.date_input("시작일자", value=date.today())
with col3:
    init_trace = st.number_input("기록시점-현재흔적", min_value=0, value=0)

# 제네시스 패스 상태 선택
st.subheader("제네시스 패스 활성화 여부")
pass_state = st.radio("패스 상태", options=["X","ㅁ","O"], horizontal=True)
mult = 3 if pass_state == "O" else 1 if pass_state == "ㅁ" else 0

# --- 주차별 입력 그리드 ---
st.subheader("주차별 보스 클리어 상태 입력 (O=패스 활성×3, ㅁ=패스 비활성×1, X=미클리어)")
weeks = list(range(0,14))
data = []
for w in weeks:
    cols = st.columns(len(BOSS_TABLE) + 2)
    cols[0].write(f"{w}주차")
    cols[1].write((start_date + pd.Timedelta(weeks=w)).strftime('%m월 %d일'))
    row = {"week": w}
    for idx, boss in enumerate(BOSS_TABLE, start=2):
        choice = cols[idx].selectbox(
            boss,
            options=["X","ㅁ","O"], key=f"{boss}_{w}"
        )
        row[boss] = choice
    data.append(row)

df = pd.DataFrame(data)

# --- 계산 로직 ---
results = []
acc_trace = init_trace
for _, row in df.iterrows():
    w = row.week
    # 보스 흔적 합계
    boss_sum = 0
    for boss, base in BOSS_TABLE.items():
        state = row[boss]
        if state == "O":
            boss_sum += base * 3
        elif state == "ㅁ":
            boss_sum += base * 1
    # 해방퀘스트 소모량
    drain = QUEST_DRAIN.get(w, 0)
    # 순 증가량
    delta = boss_sum - drain
    acc_trace += delta
    results.append({
        "주차": w,
        "보스합계": boss_sum,
        "소모량": drain,
        "순증가량": delta,
        "누적흔적": acc_trace
    })

res_df = pd.DataFrame(results)

# --- 결과 출력 ---
st.subheader("계산 결과")
st.dataframe(res_df.set_index('주차'))

# --- 부족/추가 진힐라 ---
st.subheader("목표 대비 부족량 및 추가 진힐라 필요 횟수")
TARGET = 6600
final_acc = acc_trace
lack = max(0, TARGET - final_acc)
need_jin = math.ceil(lack / BOSS_TABLE["노말-진힐라"]) if lack > 0 else 0
colx, coly = st.columns(2)
colx.metric("최종 누적 흔적", final_acc)
coly.metric("부족 흔적량", lack)
st.metric("추가 진힐라 필요 횟수", need_jin)
