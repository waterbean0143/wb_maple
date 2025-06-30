import streamlit as st
import pandas as pd
import math
import streamlit_authenticator as stauth
from datetime import date, timedelta, datetime

# ----------------------------
# 1) 사용자 인증 설정
# ----------------------------
credentials = {
    "usernames": {
        "플라잉리슝쫙": {"name": "플라잉리슝쫙", "password": "플라잉리슝쫙"},
        "모든세상의악": {"name": "모든세상의악", "password": "모든세상의악"},
        "자하레노":     {"name": "자하레노",     "password": "자하레노"},
        "정실렌엔젤":   {"name": "정실렌엔젤",   "password": "정실렌엔젤"},
        "큐레어루제네": {"name": "큐레어루제네", "password": "큐레어루제네"},
    }
}

auth = stauth.Authenticate(
    credentials,
    cookie_name="maple_trace_cookie",
    key="some_signature_key",
    cookie_expiry_days=30
)

# --- 사용자 인증 로그인 ---
username, auth_status = auth.login("로그인", location="main")
if not auth_status:
    st.stop()

# ----------------------------
# 2) 기준 데이터 정의
# ----------------------------
QUEST_DRAIN = {5: 1500, 9: 1700, 13: 2886}
BOSS_TABLE = {
    "하드-스우": 50, "하드-데미안": 50, "노말-루시드": 20,
    "노말-윌": 25, "노말-더스크": 20, "노말-듄켈": 25,
    "노말-진힐라": 135, "검은 마법사": 600
}


# ----------------------------
# 3) 시트2 기본값: 12주 해방 루트 모두 '솔격'
# ----------------------------
DEFAULT_SHEET2 = [{b: "솔격" for b in BOSS_TABLE} for _ in range(14)]

# ----------------------------
# 4) 사이드바 설정
# ----------------------------
st.sidebar.header("설정")
sheet_template = st.sidebar.selectbox(
    "시트 템플릿",
    ["시트1: 모두 X", "시트2: 12주 해방", "시트3: 모두 O"]
)
sheet_name = st.sidebar.text_input("시트 이름", value=sheet_template)

def default_state(template):
    if template == "시트1: 모두 X": return "X"
    if template == "시트2: 12주 해방": return "솔격"
    if template == "시트3: 모두 O": return "솔격"
    return "X"

# ----------------------------
# 5) 페이지 헤더
# ----------------------------
st.set_page_config(page_title=sheet_name, layout="wide")
st.title(f"메이플스토리 2025 주차별 흔적 계산기 — {sheet_name}")
st.write(f"안녕하세요, **{username}** 님!")

# ----------------------------
# 6) 사용자 입력
# ----------------------------
col1, col2 = st.columns(2)
with col1:
    init_trace = st.number_input("기록시점-현재흔적", min_value=0, value=0)
with col2:
    purchase_date = st.date_input("제네시스 패스 구매일자", value=date(2025,6,17))

# ----------------------------
# 7) 실제/예상 흔적 메트릭 자리
# ----------------------------
m1, m2 = st.columns(2)
actual_ph = m1.empty()
expected_ph = m2.empty()

# ----------------------------
# 8) 현재 주차 / 다음 해방 예정
# ----------------------------
today = datetime.now().date()
base = date(2025,6,17)
delta_days = (today - base).days
curr_week = 0 if delta_days < 2 else min(13, (delta_days-2)//7 + 1)
st.markdown(f"**현재 주차: {curr_week}주차**")

next_weeks = [w for w in QUEST_DRAIN if w > curr_week]
if next_weeks:
    nw = min(next_weeks)
    ns = base if nw == 0 else base + timedelta(days=2 + 7*(nw-1))
    ne = ns + timedelta(days=1 if nw == 0 else 6)
    st.markdown(f"**다음 해방퀘: {nw}주차 ({ns:%m.%d}~{ne:%m.%d}) — -{QUEST_DRAIN[nw]}**")

# ----------------------------
# 9) 계산 버튼
# ----------------------------
calc = st.button("계산하기")

# ----------------------------
# 10) CSS: 주차별 테두리
# ----------------------------
st.markdown(
    "<style>.week-box{border:1px solid #ccc;padding:8px;margin:6px 0;border-radius:4px;}</style>",
    unsafe_allow_html=True
)

# ----------------------------
# 11) 주차별 보스 상태 입력
# ----------------------------
st.subheader("주차별 보스 클리어 상태 입력")
state_options = [
    "X","솔격","2인격","3인격","4인격","5인격",
    "예정 (솔격)","예정 (2인격)","예정 (3인격)",
    "예정 (4인격)","예정 (5인격)","예정 (6인격)"
]
weeks = list(range(14))
data = []

for w in weeks:
    s = base if w == 0 else base + timedelta(days=2 + 7*(w-1))
    e = s + timedelta(days=1 if w == 0 else 6)
    drain = QUEST_DRAIN.get(w, 0)
    st.markdown(
        f"<div class='week-box'><strong>{w}주차 {s:%m.%d}~{e:%m.%d} (해방퀘 -{drain})</strong></div>",
        unsafe_allow_html=True
    )
    cols = st.columns(len(BOSS_TABLE))
    row = {"week": w}
    defaults = DEFAULT_SHEET2[w] if sheet_template == "시트2: 12주 해방" else {}
    for idx, boss in enumerate(BOSS_TABLE):
        init_st = defaults.get(boss, default_state(sheet_template))
        choice = cols[idx].selectbox(
            boss,
            options=state_options,
            index=state_options.index(init_st),
            key=f"{username}_{sheet_name}_{boss}_{w}"
        )
        row[boss] = choice
    data.append(row)

df = pd.DataFrame(data)

# ----------------------------
# 12) 계산 및 결과 표시
# ----------------------------
if calc:
    total_actual = 0
    total_expected = 0
    acc = init_trace
    rows = []

    for _, r in df.iterrows():
        w = r.week
        week_actual = 0
        week_expected = 0
        for b, base_v in BOSS_TABLE.items():
            stt = r[b]
            if not stt.startswith("예정") and stt != "X":
                cnt = 1 if stt == "솔격" else int(stt.replace("인격",""))
                week_actual += base_v * cnt
            if stt != "X":
                cnt = 1 if "솔격" in stt else int(stt.replace("인격","").replace("예정 (",""))
                week_expected += base_v * cnt
        drain = QUEST_DRAIN.get(w, 0)
        delta_actual = week_actual - drain
        delta_expected = week_expected - drain
        total_actual += delta_actual
        total_expected += delta_expected
        acc += delta_actual
        rows.append({
            "주차": f"{w}주차", "실제합계": week_actual,
            "예상합계": week_expected, "소모량": drain,
            "실제증가": delta_actual, "예상증가": delta_expected,
            "누적흔적": acc
        })

    final_actual = init_trace + total_actual
    final_expected = init_trace + total_expected
    lack = max(0, 6600 - final_expected)
    need = math.ceil(lack / BOSS_TABLE["노말-진힐라"]) if lack > 0 else 0

    actual_ph.metric("실제 해방흔적 증가", total_actual)
    expected_ph.metric("예상 해방흔적 증가", total_expected)

    st.markdown(f"**현재 누적 (실제): {final_actual}  |  예상 누적: {final_expected}**")
    st.markdown(f"**부족 흔적량 (예상 기준): {lack}  |  추가 진힐라 필요 횟수: {need}**")

    res_df = pd.DataFrame(rows).set_index("주차")
    st.subheader("계산 결과 상세")
    st.dataframe(res_df)
