import streamlit as st
import pandas as pd
import math
from datetime import date, timedelta

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

st.set_page_config(page_title="메이플스토리 2025 주차별 흔적 계산기", layout="wide")
st.title("메이플스토리 2025 주차별 흔적 계산기")

# --- 사용자 입력 ---
col1, col2 = st.columns(2)
with col1:
    nickname = st.text_input("닉네임")
with col2:
    init_trace = st.number_input("기록시점-현재흔적", min_value=0, value=0)

# 제네시스 패스 구매일자 입력
purchase_date = st.date_input("제네시스 패스 구매일자", value=date(2025, 6, 17))

# --- Summary 영역 (계산 전 자리 확보) ---
summary_col1, summary_col2, summary_col3 = st.columns(3)
summary_col1.metric("흔적증강", "—")
summary_col2.metric("현재흔적", "—")
summary_col3.metric("누적흔적", "—")

# 계산 버튼
calc_button = st.button("계산")

# 스타일: 주차별 컨테이너에 테두리 적용
st.markdown(
    "<style>.week-box {border: 1px solid #ddd; padding: 10px; margin-bottom: 8px; border-radius: 5px;}</style>",
    unsafe_allow_html=True
)

# --- 주차별 입력 그리드 ---
st.subheader("주차별 보스 클리어 상태 입력 (O=클리어, X=미클리어)")
weeks = list(range(0, 14))
data = []
base_date = date(2025, 6, 17)
for w in weeks:
    # 기간 계산
    if w == 0:
        start = base_date
        end = base_date + timedelta(days=1)
    else:
        start = base_date + timedelta(days=2 + 7 * (w - 1))
        end = start + timedelta(days=6)
    # 주차별 컨테이너
    st.markdown(f"<div class='week-box'>{w}주차 {start.strftime('%m.%d')}~{end.strftime('%m.%d')}</div>", unsafe_allow_html=True)
    cols = st.columns(len(BOSS_TABLE))
    row = {"week": w, "start": start}
    for idx, boss in enumerate(BOSS_TABLE):
        choice = cols[idx].selectbox(
            label=boss,
            options=["X", "O"],
            key=f"{boss}_{w}"
        )
        row[boss] = choice
    data.append(row)
df = pd.DataFrame(data)

# 계산 수행
if calc_button:
    results = []
    acc_trace = init_trace
    total_aug = 0
    for _, row in df.iterrows():
        w = row.week
        kill_date = row.start
        # 보스 합계
        boss_sum = sum(
            BOSS_TABLE[b] * (3 if (row[b] == 'O' and kill_date >= purchase_date) else (1 if row[b] == 'O' else 0))
            for b in BOSS_TABLE
        )
        # 소모량
        drain = QUEST_DRAIN.get(w, 0)
        # 순 증가
        delta = boss_sum - drain
        total_aug += delta
        acc_trace += delta
        results.append({
            "주차": f"{w}주차",
            "보스합계": boss_sum,
            "소모량": drain,
            "순증가량": delta,
            "누적흔적": acc_trace
        })
    # 요약 업데이트
    current_acc = init_trace + total_aug
    summary_col1.metric("흔적증강", total_aug)
    summary_col2.metric("현재흔적", current_acc)
    summary_col3.metric("누적흔적", current_acc)
    # 결과 테이블
    res_df = pd.DataFrame(results).set_index('주차')
    st.subheader("계산 결과")
    st.dataframe(res_df)
    # 부족 및 진힐라
    TARGET = 6600
    lack = max(0, TARGET - current_acc)
    need_jin = math.ceil(lack / BOSS_TABLE["노말-진힐라"]) if lack > 0 else 0
    colx, coly = st.columns(2)
    colx.metric("부족 흔적량", lack)
    coly.metric("추가 진힐라 필요 횟수", need_jin)
