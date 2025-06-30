import streamlit as st
import pandas as pd
import math
from datetime import date, timedelta, datetime

# --- 기준 테이블 ---
QUEST_DRAIN = {5:1500, 9:1700, 13:2886}
BOSS_TABLE = {
    "하드-스우": 50,
    "하드-데미안": 50,
    "노말-루시드": 20,
    "노말-윌": 25,
    "노말-더스크": 20,
    "노말-듄켈": 25,
    "노말-진힐라": 135,
    "검은 마법사": 600
}

# --- 사이드바 설정 ---
st.sidebar.header("설정")
sheet_template = st.sidebar.selectbox(
    "시트 템플릿",
    ["시트1: 모두 X", "시트2: 모두 예정", "시트3: 모두 O"]
)

# 템플릿별 기본 상태 리턴 함수
def default_state(template):
    if template == "시트1: 모두 X":
        return "X"
    if template == "시트2: 모두 예정":
        return "예정 (솔격)"
    if template == "시트3: 모두 O":
        return "솔격"
    return "X"

sheet_name = st.sidebar.text_input("시트 이름", value=sheet_template)

# --- 페이지 설정 ---
st.set_page_config(page_title=f"{sheet_name}", layout="wide")
st.title(f"메이플스토리 2025 주차별 흔적 계산기 — {sheet_name}")

# --- 사용자 입력 ---
nickname = st.text_input("닉네임")
init_trace = st.number_input("기록시점-현재흔적", min_value=0, value=0)
purchase_date = st.date_input("제네시스 패스 구매일자", value=date(2025,6,17))

# --- 현재 주차 계산 ---
today = datetime.now().date()
base = date(2025,6,17)
delta_days = (today - base).days
if delta_days < 2:
    curr_week = 0
else:
    curr_week = min(13, (delta_days-2)//7 + 1)
st.markdown(f"**현재 주차: {curr_week}주차**")

# --- 다음 해방예정 표시 ---
next_weeks = [w for w in QUEST_DRAIN if w > curr_week]
if next_weeks:
    nw = min(next_weeks)
    if nw == 0:
        ns, ne = base, base + timedelta(days=1)
    else:
        ns = base + timedelta(days=2 + 7*(nw-1))
        ne = ns + timedelta(days=6)
    st.markdown(
        f"**다음 해방퀘 예정: {nw}주차 ({ns:%m.%d}~{ne:%m.%d}) — -{QUEST_DRAIN[nw]}**"
    )

# --- Summary 영역 준비 ---
ph1 = st.empty()
ph2 = st.empty()
ph3 = st.empty()
ph4 = st.empty()

# --- 계산 버튼 ---
calc = st.button("계산하기")

# --- CSS 스타일 ---
st.markdown(
    "<style>.week-box{border:1px solid #ccc;padding:8px;margin:6px 0;border-radius:4px;}</style>",
    unsafe_allow_html=True
)

# --- 주차별 입력 ---
st.subheader("주차별 보스 클리어 상태 입력")
state_options = [
    "X","솔격","2인격","3인격","4인격","5인격",
    "예정 (솔격)","예정 (2인격)","예정 (3인격)",
    "예정 (4인격)","예정 (5인격)","예정 (6인격)"
]
weeks = list(range(14))
data = []
for w in weeks:
    if w == 0:
        s = base; e = base + timedelta(days=1)
    else:
        s = base + timedelta(days=2 + 7*(w-1))
        e = s + timedelta(days=6)
    drain = QUEST_DRAIN.get(w,0)
    st.markdown(
        f"<div class='week-box'><strong>{w}주차 {s:%m.%d}~{e:%m.%d} (해방퀘 -{drain})</strong></div>",
        unsafe_allow_html=True
    )
    cols = st.columns(len(BOSS_TABLE))
    row = {"week": w, "date": s}
    for idx, boss in enumerate(BOSS_TABLE):
        choice = cols[idx].selectbox(
            boss,
            options=state_options,
            index=state_options.index(default_state(sheet_template)),
            key=f"{sheet_name}_{boss}_{w}"
        )
        row[boss] = choice
    data.append(row)

df = pd.DataFrame(data)

# --- 계산 및 결과 표시 ---
if calc:
    acc = init_trace
    total_aug = 0
    rows = []
    for _, r in df.iterrows():
        w, rdate = r.week, r.date
        week_sum = 0
        for boss, base_val in BOSS_TABLE.items():
            stt = r[boss]
            if stt.startswith("예정") or stt == "X":
                continue
            cnt = 1 if stt == "솔격" else int(stt.replace("인격",""))
            week_sum += base_val * cnt
        drain = QUEST_DRAIN.get(w,0)
        delta = week_sum - drain
        total_aug += delta
        acc += delta
        rows.append({
            "주차": f"{w}주차",
            "보스합계": week_sum,
            "소모량": drain,
            "증가량": delta,
            "누적흔적": acc
        })

    final = init_trace + total_aug
    lack = max(0, 6600 - final)
    need_jin = math.ceil(lack / BOSS_TABLE["노말-진힐라"]) if lack > 0 else 0

    # Summary 업데이트
    ph1.metric("흔적증강", total_aug)
    ph2.metric("현재흔적", final)
    ph3.metric("누적흔적", final)
    ph4.metric("부족 흔적량", lack)
    st.write(f"**추가 진힐라 필요 횟수: {need_jin}**")

    # 계산 결과 테이블
    st.subheader("계산 결과")
    st.dataframe(pd.DataFrame(rows).set_index("주차"))
