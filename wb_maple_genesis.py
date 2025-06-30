import streamlit as st
import pandas as pd
import math
from datetime import date, timedelta, datetime

# ----------------------------
# 0) 사용자 리스트 (비번==아이디)
# ----------------------------
VALID_USERS = {
    "admin": "admin",
    "플라잉리슝쫙": "플라잉리슝쫙",
    "모든세상의악": "모든세상의악",
    "자하레노":     "자하레노",
    "정실렌엔젤":   "정실렌엔젤",
    "큐레어루제네": "큐레어루제네",
}

# 로그인 상태 초기화
if "user" not in st.session_state:
    st.session_state.user = None

# ----------------------------
# 1) 사이드바: 로그인
# ----------------------------
st.sidebar.header("로그인")
username_input = st.sidebar.text_input("아이디")
password_input = st.sidebar.text_input("비밀번호", type="password")
if st.sidebar.button("로그인"):
    if VALID_USERS.get(username_input) == password_input:
        st.session_state.user = username_input
        st.sidebar.success(f"환영합니다, {username_input}님!")
    else:
        st.sidebar.error("로그인 실패")

# ----------------------------
# 2) 사이드바: 시트 템플릿 & (admin만) 시트 이름
# ----------------------------
st.sidebar.header("설정")
sheet_template = st.sidebar.selectbox(
    "시트 템플릿",
    ["시트1: 모두 X", "시트2: 12주 해방", "시트3: 모두 O"]
)
if st.session_state.user == "admin":
    sheet_name = st.sidebar.text_input("시트 이름", value=sheet_template)
else:
    st.sidebar.write("시트 이름:")
    st.sidebar.markdown(f"**{sheet_template}**")
    sheet_name = sheet_template

# ----------------------------
# 3) 기준 데이터 정의
# ----------------------------
QUEST_DRAIN = {5:1500, 9:1700, 13:2886}
BOSS_TABLE = {
    "하드-스우":50, "하드-데미안":50, "노말-루시드":20,
    "노말-윌":25, "노말-더스크":20, "노말-듄켈":25,
    "노말-진힐라":135, "검은 마법사":600
}
DEFAULT_SHEET2 = [{b:"솔격" for b in BOSS_TABLE} for _ in range(14)]

def default_state(template):
    if template=="시트1: 모두 X": return "X"
    if template=="시트2: 12주 해방": return "솔격"
    if template=="시트3: 모두 O": return "솔격"
    return "X"

# ----------------------------
# 4) 페이지 헤더
# ----------------------------
st.set_page_config(page_title=sheet_name, layout="wide")
st.title(f"메이플스토리 2025 주차별 흔적 계산기 — {sheet_name}")

# ----------------------------
# 5) 사용자 입력
# ----------------------------
col1, col2 = st.columns(2)
with col1:
    init_trace = st.number_input("기록시점-현재흔적", min_value=0, value=0)
with col2:
    purchase_date = st.date_input("제네시스 패스 구매일자", value=date(2025,6,17))

# ----------------------------
# 6) 메트릭 자리 확보
# ----------------------------
m1, m2 = st.columns(2)
actual_ph = m1.empty()
expected_ph = m2.empty()

# ----------------------------
# 7) 현재 주차 / 다음 해방 예정
# ----------------------------
today = datetime.now().date()
base = date(2025,6,17)
d_days = (today - base).days
curr_week = 0 if d_days<2 else min(13, (d_days-2)//7+1)
st.markdown(f"**현재 주차: {curr_week}주차**")
next_ws = [w for w in QUEST_DRAIN if w>curr_week]
if next_ws:
    nw = min(next_ws)
    ns = base if nw==0 else base+timedelta(days=2+7*(nw-1))
    ne = ns+timedelta(days=1 if nw==0 else 6)
    st.markdown(f"**다음 해방퀘: {nw}주차 ({ns:%m.%d}~{ne:%m.%d}) — -{QUEST_DRAIN[nw]}**")

# ----------------------------
# 8) 계산 버튼
# ----------------------------
calc = st.button("계산하기")

# ----------------------------
# 9) CSS 스타일
# ----------------------------
st.markdown(
    "<style>.week-box{border:1px solid #ccc;padding:8px;margin:6px 0;border-radius:4px;}</style>",
    unsafe_allow_html=True
)

# ----------------------------
# 10) 주차별 입력
# ----------------------------
st.subheader("주차별 보스 클리어 상태 입력")
state_options = [
    "X","솔격","2인격","3인격","4인격","5인격",
    "예정 (솔격)","예정 (2인격)","예정 (3인격)",
    "예정 (4인격)","예정 (5인격)","예정 (6인격)"
]
weeks = range(14)
data = []
for w in weeks:
    s = base if w==0 else base+timedelta(days=2+7*(w-1))
    e = s+timedelta(days=1 if w==0 else 6)
    drain = QUEST_DRAIN.get(w,0)
    st.markdown(f"<div class='week-box'><strong>{w}주차 {s:%m.%d}~{e:%m.%d} (해방퀘 -{drain})</strong></div>", unsafe_allow_html=True)
    cols = st.columns(len(BOSS_TABLE))
    row = {"week":w}
    defaults = DEFAULT_SHEET2[w] if sheet_template=="시트2: 12주 해방" else {}
    for i,boss in enumerate(BOSS_TABLE):
        init_st = defaults.get(boss, default_state(sheet_template))
        choice = cols[i].selectbox(
            boss,
            options=state_options,
            index=state_options.index(init_st),
            key=f"{sheet_name}_{boss}_{w}"
        )
        row[boss] = choice
    data.append(row)
df = pd.DataFrame(data)

# ----------------------------
# 11) 계산 및 표시
# ----------------------------
if calc:
    acc = init_trace
    tot_act = 0; tot_exp = 0
    rows = []
    for _,r in df.iterrows():
        w = r.week
        act = exp = 0
        for b,base_v in BOSS_TABLE.items():
            stt = r[b]
            if stt!="X" and not stt.startswith("예정"):
                cnt = 1 if stt=="솔격" else int(stt.replace("인격",""))
                act += base_v*cnt
            if stt!="X":
                cnt = 1 if "솔격" in stt else int(stt.replace("인격","").replace("예정 (",""))
                exp += base_v*cnt
        d = QUEST_DRAIN.get(w,0)
        da = act-d; de = exp-d
        tot_act += da; tot_exp += de
        acc += da
        rows.append({"주차":f"{w}주차","실제증가":da,"예상증가":de,"누적":acc})
    final_act = init_trace+tot_act
    final_exp = init_trace+tot_exp
    lack = max(0,6600-final_exp)
    need = math.ceil(lack/BOSS_TABLE["노말-진힐라"]) if lack>0 else 0

    actual_ph.metric("실제 해방흔적 증가", tot_act)
    expected_ph.metric("예상 해방흔적 증가", tot_exp)
    st.markdown(f"**현재 누적(실제):{final_act} | 예상 누적:{final_exp} | 부족량:{lack} | 추가진힐라:{need}**")
    st.subheader("계산 결과 상세")
    st.dataframe(pd.DataFrame(rows).set_index("주차"))
