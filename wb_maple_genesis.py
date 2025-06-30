import streamlit as st
import pandas as pd
import math
import json
import os
from datetime import date, timedelta, datetime

# ----------------------------
# 페이지 설정 (반드시 이 위치)
# ----------------------------
st.set_page_config(page_title="메이플스토리 흔적 계산기", layout="wide")

# ----------------------------
# 0) 사용자 & 시트 설정
# ----------------------------
VALID_USERS = {
    "admin":"admin",
    "플라잉리슝쫙":"플라잉리슝쫙",
    "모든세상의악":"모든세상의악",
    "자하레노":"자하레노",
    "정실렌엔젤":"정실렌엔젤",
    "큐레어루제네":"큐레어루제네"
}
if "user" not in st.session_state:
    st.session_state.user = None


# ----------------------------
# 1) 사용자 & 시트 설정
# ----------------------------
VALID_USERS = {
    "admin":"admin",
    "플라잉리슝쫙":"플라잉리슝쫙",
    "모든세상의악":"모든세상의악",
    "자하레노":"자하레노",
    "정실렌엔젤":"정실렌엔젤",
    "큐레어루제네":"큐레어루제네"
}
if "user" not in st.session_state:
    st.session_state.user = None

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

TEMPLATES = ["시트1: 모두 X", "시트2: 12주 해방", "시트3: 모두 O"]
PERSONAL_SHEETS = list(VALID_USERS.keys())
SHEETS = TEMPLATES + PERSONAL_SHEETS

st.sidebar.header("설정")
sheet = st.sidebar.selectbox("시트 선택", options=SHEETS, index=0)
if user == "admin":
    sheet_name = st.sidebar.text_input("시트 이름 편집", sheet)
else:
    st.sidebar.markdown(f"**시트 이름:** {sheet}")
    sheet_name = sheet

# ----------------------------
# 2) 기준 데이터
# ----------------------------
QUEST_DRAIN = {5:1500, 9:1700, 13:2886}
BOSS_TABLE = {
    "하드-스우":50, "하드-데미안":50, "노말-루시드":20,
    "노말-윌":25, "노말-더스크":20, "노말-듄켈":25,
    "노말-진힐라":135, "검은 마법사":600
}
DEFAULT_SHEET2 = [{b:"솔격" for b in BOSS_TABLE} for _ in range(14)]
def default_state(tpl):
    if tpl.startswith("시트1"): return "X"
    if tpl.startswith("시트2"): return "솔격"
    if tpl.startswith("시트3"): return "솔격"
    return "X"

# ----------------------------
# 3) 페이지 헤더
# ----------------------------
st.set_page_config(page_title=sheet_name, layout="wide")
st.title(f"{sheet_name} — {user}님")

# ----------------------------
# 4) 사용자 입력
# ----------------------------
editable = (user=="admin" or sheet==user)
col1, col2 = st.columns(2)
with col1:
    init_trace = st.number_input("기록시점-현재흔적", min_value=0, value=0, disabled=not editable)
with col2:
    purchase_date = st.date_input("제네시스 패스 구매일자", value=date(2025,6,17), disabled=not editable)

# ----------------------------
# 5) 현재 주차 계산
# ----------------------------
base = date(2025,6,17)
today = datetime.now().date()
delta_days = (today - base).days
curr_week = 0 if delta_days<2 else min(13, (delta_days-2)//7 + 1)

def week_title(w):
    s = base if w==0 else base + timedelta(days=2 + 7*(w-1))
    e = s + timedelta(days=1 if w==0 else 6)
    d = QUEST_DRAIN.get(w,0)
    return f"{w}주차 {s:%m.%d}~{e:%m.%d} (해방퀘 -{d})"

st.markdown(f"**현재 주차: {week_title(curr_week)}**")
next_ws = [w for w in QUEST_DRAIN if w>curr_week]
if next_ws:
    nw = min(next_ws)
    st.markdown(f"**다음 해방퀘: {week_title(nw)}**")

# ----------------------------
# 6) 메트릭 자리 & 버튼
# ----------------------------
m1, m2 = st.columns(2)
actual_ph = m1.empty()
expected_ph = m2.empty()
c_col, s_col = st.columns(2)
calc = c_col.button("계산하기", disabled=not editable)
save = s_col.button("저장하기", disabled=not editable)

# ----------------------------
# 7) CSS 스타일
# ----------------------------
st.markdown(
    "<style>.week-box{border:1px solid #ccc;padding:8px;margin:6px 0;border-radius:4px;}</style>",
    unsafe_allow_html=True
)

# ----------------------------
# 8) 주차별 입력
# ----------------------------
st.subheader("주차별 보스 클리어 상태 입력")
state_options = ["X","솔격","2인격","3인격","4인격","5인격"] + [f"예정 ({i}인격)" for i in range(1,7)]
weeks = range(14)
data = []

for w in weeks:
    title = week_title(w)
    if w < curr_week:
        bg = "#ffe5e5"
    elif w == curr_week:
        bg = "#e5ffe5"
    elif w <= max(QUEST_DRAIN):
        bg = "#fff0e5"
    else:
        bg = "transparent"
    st.markdown(
        f"""<div style="
            background-color:{bg};
            border:1px solid #ccc;
            padding:8px;margin:6px 0;border-radius:4px;">
            <strong>{title}</strong>
        </div>""",
        unsafe_allow_html=True
    )
    cols = st.columns(len(BOSS_TABLE))
    defaults = DEFAULT_SHEET2[w] if sheet.startswith("시트2") else {}
    row = {"week":w}
    for idx, boss in enumerate(BOSS_TABLE):
        init_st = defaults.get(boss, default_state(sheet))
        choice = cols[idx].selectbox(
            boss, state_options,
            index=state_options.index(init_st),
            key=f"{user}_{sheet}_{boss}_{w}",
            disabled=not editable
        )
        row[boss] = choice
    data.append(row)

df = pd.DataFrame(data)

# ----------------------------
# 9) 저장하기 동작
# ----------------------------
if save:
    save_user_log(user, {
        "init_trace": init_trace,
        "purchase_date": purchase_date.isoformat(),
        "choices": {
            int(r.week): {b: df.at[i, b] for b in BOSS_TABLE}
            for i, r in df.iterrows()
        }
    })
    st.success("현재 상태를 저장했습니다.")

# ----------------------------
# 10) 계산 및 결과 표시
# ----------------------------
if calc:
    total_act = total_exp = 0
    acc = init_trace
    rows = []
    # (계산 로직 생략 없이 이전과 동일)
    for _, r in df.iterrows():
        w = r.week; act = exp = 0
        for b, val in BOSS_TABLE.items():
            stt = r[b]
            if stt!="X" and not stt.startswith("예정"):
                cnt = 1 if stt=="솔격" else int(stt.replace("인격",""))
                act += val*cnt
            if stt!="X":
                cnt = 1 if "솔격" in stt else int(stt.replace("예정 (","").replace("인격",""))
                exp += val*cnt
        d = QUEST_DRAIN.get(w,0)
        da, de = act-d, exp-d
        total_act += da; total_exp += de; acc += da
        rows.append({"주차":f"{w}주차","실제증가":da,"예상증가":de,"누적흔적":acc})
    final_act = init_trace + total_act
    final_exp = init_trace + total_exp
    lack = max(0,6600-final_exp)
    need = math.ceil(lack / BOSS_TABLE["노말-진힐라"]) if lack>0 else 0

    actual_ph.metric("실제 해방흔적 증가", total_act)
    expected_ph.metric("예상 해방흔적 증가", total_exp)
    st.markdown(f"**현재 누적(실제):{final_act} | 예상 누적:{final_exp} | 부족량:{lack} | 추가진힐라:{need}**")
    st.subheader("계산 결과 상세")
    st.dataframe(pd.DataFrame(rows).set_index("주차"))

# ----------------------------
# 11) Admin 전용: 로그 보기
# ----------------------------
if user == "admin":
    st.sidebar.header("사용자 로그 조회")
    target = st.sidebar.selectbox("로그 볼 사용자", options=[u for u in VALID_USERS if u!="admin"])
    if st.sidebar.button("로그 불러오기"):
        logs = load_user_log(target)
        if not logs:
            st.info("로그 없음")
        else:
            df_logs = []
            for entry in logs:
                row = {
                    "timestamp": entry["timestamp"],
                    "init_trace": entry["data"]["init_trace"],
                    "purchase_date": entry["data"]["purchase_date"],
                    "choices": json.dumps(entry["data"]["choices"], ensure_ascii=False)
                }
                df_logs.append(row)
            st.subheader(f"{target}님 로그")
            st.dataframe(pd.DataFrame(df_logs))







