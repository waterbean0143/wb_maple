import streamlit as st
import pandas as pd
import math
from datetime import date, timedelta, datetime

# ----------------------------
# 0) 사용자 리스트
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
uid = st.sidebar.text_input("아이디")
pwd = st.sidebar.text_input("비밀번호", type="password")
if st.sidebar.button("로그인"):
    if VALID_USERS.get(uid) == pwd:
        st.session_state.user = uid
        st.sidebar.success(f"{uid}님, 환영합니다!")
    else:
        st.sidebar.error("로그인 실패")

if not st.session_state.user:
    st.stop()
user = st.session_state.user

# ----------------------------
# 2) 시트 목록 구성
# ----------------------------
TEMPLATES = ["시트1: 모두 X", "시트2: 12주 해방", "시트3: 모두 O"]
PERSONAL_SHEETS = list(VALID_USERS.keys())  # 모든 사용자 개인 시트
if user == "admin":
    SHEETS = TEMPLATES + PERSONAL_SHEETS
else:
    SHEETS = TEMPLATES + PERSONAL_SHEETS  # 일반 사용자도 다른 유저 시트 조회 가능

# ----------------------------
# 3) 사이드바: 시트 선택 & 시트 이름 편집
# ----------------------------
st.sidebar.header("설정")
sheet = st.sidebar.selectbox("시트 선택", options=SHEETS, index=SHEETS.index(TEMPLATES[0]))
if user == "admin":
    # admin 은 모든 시트 이름 자유 수정
    sheet_name = st.sidebar.text_input("시트 이름 편집", value=sheet)
else:
    # 일반 유저는 sheet 그대로, 이름 고정
    st.sidebar.markdown(f"**시트 이름:** {sheet}")
    sheet_name = sheet

# ----------------------------
# 4) 기준 데이터
# ----------------------------
QUEST_DRAIN = {5:1500, 9:1700, 13:2886}
BOSS_TABLE = {
    "하드-스우":50, "하드-데미안":50, "노말-루시드":20,
    "노말-윌":25, "노말-더스크":20, "노말-듄켈":25,
    "노말-진힐라":135, "검은 마법사":600
}

# ----------------------------
# 5) 시트2 기본값
# ----------------------------
DEFAULT_SHEET2 = [{b:"솔격" for b in BOSS_TABLE} for _ in range(14)]

def default_state(template):
    if template.startswith("시트1"): return "X"
    if template.startswith("시트2"): return "솔격"
    if template.startswith("시트3"): return "솔격"
    return "X"

# ----------------------------
# 6) 페이지 헤더
# ----------------------------
st.set_page_config(page_title=sheet_name, layout="wide")
st.title(f"{sheet_name} — {user}님")

# ----------------------------
# 7) 사용자 입력
# ----------------------------
editable = (user=="admin" or sheet==user)
col1, col2 = st.columns(2)
with col1:
    init_trace = st.number_input("기록시점-현재흔적", min_value=0, value=0, disabled=not editable)
with col2:
    purchase_date = st.date_input("제네시스 패스 구매일자", value=date(2025,6,17), disabled=not editable)

# ----------------------------
# 8) 현재 주차 & 다음 해방 예정
# ----------------------------
today = datetime.now().date()
base = date(2025,6,17)
delta_days = (today - base).days
if delta_days < 2:
    curr_week = 0
else:
    curr_week = min(13, (delta_days-2)//7 + 1)

# 주차별 title 계산 함수
def week_title(w):
    start = base if w==0 else base+timedelta(days=2+7*(w-1))
    end   = start + timedelta(days=1 if w==0 else 6)
    drain = QUEST_DRAIN.get(w,0)
    return f"{w}주차 {start:%m.%d}~{end:%m.%d} (해방퀘 -{drain})"

# 현재 주차를 동일 포맷으로 표시
st.markdown(f"**현재 주차: {week_title(curr_week)}**")

next_ws = [w for w in QUEST_DRAIN if w>curr_week]
if next_ws:
    nw = min(next_ws)
    st.markdown(f"**다음 해방퀘: {week_title(nw)}**")

# ----------------------------
# 9) 실제/예상 메트릭 자리
# ----------------------------
m1, m2 = st.columns(2)
ph_actual = m1.empty()
ph_expected = m2.empty()

# ----------------------------
# 10) 계산 버튼
# ----------------------------
calc = st.button("계산하기", disabled=not editable)

# ----------------------------
# 11) CSS 스타일
# ----------------------------
st.markdown(
    "<style>.week-box{border:1px solid #ccc;padding:8px;margin:6px 0;border-radius:4px;}</style>",
    unsafe_allow_html=True
)

# ----------------------------
# 12) 주차별 보스 상태 입력
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
    title = week_title(w)
    st.markdown(f"<div class='week-box'><strong>{title}</strong></div>", unsafe_allow_html=True)
    cols = st.columns(len(BOSS_TABLE))
    row = {"week":w}
    defaults = DEFAULT_SHEET2[w] if sheet.startswith("시트2") else {}
    for i,boss in enumerate(BOSS_TABLE):
        init_st = defaults.get(boss, default_state(sheet))
        choice = cols[i].selectbox(
            boss, state_options, index=state_options.index(init_st),
            key=f"{user}_{sheet}_{boss}_{w}",
            disabled=not editable
        )
        row[boss] = choice
    data.append(row)
df = pd.DataFrame(data)

# ----------------------------
# 13) 계산 및 결과
# ----------------------------
if calc:
    total_act = 0
    total_exp = 0
    acc = init_trace
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
        da, de = act-d, exp-d
        total_act += da
        total_exp += de
        acc += da
        rows.append({"주차":f"{w}주차","실제증가":da,"예상증가":de,"누적":acc})

    final_act = init_trace + total_act
    final_exp = init_trace + total_exp
    lack = max(0,6600-final_exp)
    need = math.ceil(lack/BOSS_TABLE["노말-진힐라"]) if lack>0 else 0

    ph_actual.metric("실제 해방흔적 증가", total_act)
    ph_expected.metric("예상 해방흔적 증가", total_exp)
    st.markdown(f"**현재 누적(실제):{final_act} | 예상 누적:{final_exp} | 부족량:{lack} | 추가진힐라:{need}**")

    st.subheader("계산 결과 상세")
    st.dataframe(pd.DataFrame(rows).set_index("주차"))
