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

# --- 사이드바 설정 ---
st.sidebar.header("설정")
# 시트 템플릿 선택
sheet_template = st.sidebar.selectbox(
    "시트 템플릿",
    ["시트1: 모두 X", "시트2: 모두 예정", "시트3: 모두 O"]
)
# 템플릿에 따른 기본값 매핑
default_map = {
    "시트1: 모두 X": "X",
    "시트2: 모두 예정": "예정",
    "시트3: 모두 O": "O"
}
def_state = default_map[sheet_template]

# 시트 이름 설정
sheet_name = st.sidebar.text_input("시트 이름", value=sheet_template)

# --- Page 설정 ---
st.set_page_config(page_title=f"메이플스토리 2025 흔적 계산기 - {sheet_name}", layout="wide")
st.title(f"메이플스토리 2025 주차별 흔적 계산기 - {sheet_name}")

# --- 사용자 입력 ---
col1, col2 = st.columns(2)
with col1:
    nickname = st.text_input("닉네임")
with col2:
    init_trace = st.number_input("기록시점-현재흔적", min_value=0, value=0)
# 제네시스 패스 구매일자 입력
purchase_date = st.date_input("제네시스 패스 구매일자", value=date(2025, 6, 17))

# --- Summary ---
summary1 = st.empty()
summary2 = st.empty()
summary3 = st.empty()

# 계산 버튼
calc_button = st.button("계산하기")

# --- 스타일: 주차별 컨테이너 테두리 ---
st.markdown(
    "<style>.week-box {border: 1px solid #ccc; padding: 8px; margin-bottom: 6px; border-radius: 4px;}<\/style>",
    unsafe_allow_html=True
)

# --- 주차별 입력 ---
st.subheader("주차별 보스 클리어 상태 입력 (O=클리어, X=미클리어, 예정=예정)")
weeks = list(range(0, 14))
data = []
base_date = date(2025, 6, 17)
for w in weeks:
    # 기간 계산
    start = base_date + timedelta(days=(0 if w == 0 else 2 + 7*(w-1)))
    end = start + timedelta(days=(1 if w == 0 else 6))
    st.markdown(f"<div class='week-box'><strong>{w}주차 {start.strftime('%m.%d')}~{end.strftime('%m.%d')}</strong></div>", unsafe_allow_html=True)
    cols = st.columns(len(BOSS_TABLE))
    row = {"week": w, "start": start}
    for idx, boss in enumerate(BOSS_TABLE):
        choice = cols[idx].selectbox(
            label=boss,
            options=["X", "예정", "O"],
            index=["X", "예정", "O"].index(def_state),
            key=f"{sheet_name}_{boss}_{w}"
        )
        row[boss] = choice
    data.append(row)

df = pd.DataFrame(data)

# --- 계산 및 표시 ---
if calc_button:
    results = []
    acc_trace = init_trace
    total_aug = 0
    for _, row in df.iterrows():
        w = row.week
        kill_date = row.start
        boss_sum = 0
        for boss, base in BOSS_TABLE.items():
            state = row[boss]
            if state == "O":
                mult = 3 if kill_date >= purchase_date else 1
                boss_sum += base * mult
            # 예정 상태는 계산에서 제외하거나 별도로 처리 가능
        drain = QUEST_DRAIN.get(w, 0)
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
    # Summary 출력
    current_acc = init_trace + total_aug
    summary1.metric("흔적증강", int(total_aug))
    summary2.metric("현재흔적", int(current_acc))
    summary3.metric("누적흔적", int(current_acc))
    # 테이블
    st.subheader("계산 결과")
    res_df = pd.DataFrame(results).set_index('주차')
    st.dataframe(res_df)
    # 부족 & 진힐라
    TARGET = 6600
    lack = max(0, TARGET - current_acc)
    need_jin = math.ceil(lack / BOSS_TABLE["노말-진힐라"]) if lack > 0 else 0
    colx, coly = st.columns(2)
    colx.metric("부족 흔적량", int(lack))
    coly.metric("추가 진힐라 필요 횟수", int(need_jin))
