import streamlit as st
import pandas as pd
import math
from datetime import date, timedelta, datetime

# --- 기준 테이블 ---
QUEST_DRAIN = {5:1500, 9:1700, 13:2886}
BOSS_TABLE = { "하드-스우":50, "하드-데미안":50, "노말-루시드":20,
               "노말-윌":25, "노말-더스크":20, "노말-듄켈":25,
               "노말-진힐라":135, "검은 마법사":600 }

# --- 사이드바 ---
st.sidebar.header("설정")
sheet_template = st.sidebar.selectbox("시트 템플릿",
    ["시트1: 모두 X","시트2: 12주 해방","시트3: 모두 O"])
sheet_name = st.sidebar.text_input("시트 이름", value=sheet_template)

# --- 페이지 설정 ---
st.set_page_config(page_title=sheet_name, layout="wide")
st.title(f"메이플스토리 2025 주차별 흔적 계산기 — {sheet_name}")

# --- 사용자 입력 ---
nickname = st.text_input("닉네임")
init_trace = st.number_input("기록시점-현재흔적", min_value=0, value=0)
purchase_date = st.date_input("제네시스 패스 구매일자", value=date(2025,6,17))

# --- 현재 주차 계산 (매주 목요일 0시 기준) ---
today = datetime.now().date()
base = date(2025,6,17)
delta_days = (today - base).days
if delta_days < 2:
    curr_week = 0
else:
    curr_week = min(13, (delta_days-2)//7 + 1)
st.markdown(f"**현재 주차: {curr_week}주차**")

# --- 다음 해방 예정일자 표시 ---
next_drain_week = min(w for w,d in QUEST_DRAIN.items() if w>curr_week) if curr_week < 13 else None
if next_drain_week is not None:
    # 주차 시작일 계산
    if next_drain_week==0:
        ns = base; ne = base+timedelta(days=1)
    else:
        ns = base + timedelta(days=2+7*(next_drain_week-1))
        ne = ns + timedelta(days=6)
    st.markdown(f"**다음 해방 퀘스트 소모 예정:** {next_drain_week}주차 ({ns:%m.%d}~{ne:%m.%d}) — `-{QUEST_DRAIN[next_drain_week]}`")

# --- Summary 자리 확보 ---
c1,c2,c3,c4 = st.columns([1,1,1,1])
# placeholder: 나중에 값 세팅
with c1: ph1 = st.empty()
with c2: ph2 = st.empty()
with c3: ph3 = st.empty()
with c4: ph4 = st.empty()

# --- 계산 버튼 ---
calc = st.button("계산하기")

# --- 스타일 ---
st.markdown(
    "<style>.week-box{border:1px solid #ccc;padding:8px;margin:6px 0;border-radius:4px;}</style>",
    unsafe_allow_html=True
)

# --- 주차별 입력 ---
st.subheader("주차별 보스 상태 입력")
states = ["X","솔격","2인격","3인격","4인격","5인격",
          "예정 (솔격)","예정 (2인격)","예정 (3인격)",
          "예정 (4인격)","예정 (5인격)","예정 (6인격)"]
weeks = list(range(14))
data=[]
for w in weeks:
    # 기간
    if w==0:
        s=base; e=base+timedelta(days=1)
    else:
        s=base+timedelta(days=2+7*(w-1)); e=s+timedelta(days=6)
    drain=QUEST_DRAIN.get(w,0)
    st.markdown(f"<div class='week-box'><strong>{w}주차 {s:%m.%d}~{e:%m.%d} (해방퀘 -{drain})</strong></div>", unsafe_allow_html=True)
    cols=st.columns(len(BOSS_TABLE))
    row={"week":w,"date":s}
    for i,b in enumerate(BOSS_TABLE):
        row[b]=cols[i].selectbox(b, states, key=f"{sheet_name}_{b}_{w}")
    data.append(row)
df=pd.DataFrame(data)

# --- 계산 및 결과 ---
if calc:
    acc=init_trace; tot_aug=0; rows=[]
    for _,r in df.iterrows():
        w,rdate = r.week, r.date
        s=0
        for b,base_val in BOSS_TABLE.items():
            stt=r[b]
            if stt.startswith("예정") or stt=="X": continue
            cnt=1 if stt=="솔격" else int(stt.replace("인격",""))
            s+=base_val*cnt
        d=QUEST_DRAIN.get(w,0)
        delta=s-d
        tot_aug+=delta; acc+=delta
        rows.append({"주차":f"{w}주차","보스합계":s,"소모":d,"증가":delta,"누적":acc})
    final=init_trace+tot_aug; lack=max(0,6600-final)
    need=math.ceil(lack/BOSS_TABLE["노말-진힐라"]) if lack>0 else 0

    # summary 세팅
    ph1.metric("흔적증강", tot_aug)
    ph2.metric("현재흔적", final)
    ph3.metric("부족 흔적량", lack)
    ph4.metric("추가 진힐라 필요횟수", need)

    # 차트
    res=pd.DataFrame(rows).set_index("주차")
    st.subheader("주간 누적 증가량 차트")
    st.bar_chart(res["증가"])

    # 결과 테이블
    st.subheader("계산 결과")
    st.dataframe(res)
