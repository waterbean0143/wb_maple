import streamlit as st
import pandas as pd
import math
from datetime import date, timedelta, datetime

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
    "검은 마법사": 600,  # 추가 월간 보스
}

# --- 사이드바 설정 ---
st.sidebar.header("설정")
sheet_template = st.sidebar.selectbox(
    "시트 템플릿",
    ["시트1: 모두 X", "시트2: 모두 예정", "시트3: 모두 O"]
)
sheet_name = st.sidebar.text_input("시트 이름", value=sheet_template)

# --- Page 설정 ---
st.set_page_config(page_title=f"메이플스토리 2025 흔적 계산기 - {sheet_name}", layout="wide")
st.title(f"메이플스토리 2025 주차별 흔적 계산기 - {sheet_name}")

# --- 사용자 입력 ---
nickname = st.text_input("닉네임")
init_trace = st.number_input("기록시점-현재흔적", min_value=0, value=0)
purchase_date = st.date_input("제네시스 패스 구매일자", value=date(2025, 6, 17))

# --- Summary 초기 숨김 ---
summary1 = st.empty()
summary2 = st.empty()
summary3 = st.empty()

# --- 계산 버튼 ---
calc_button = st.button("계산하기")

# --- 스타일 (주차박스 테두리) ---
st.markdown(
    "<style>.week-box {border: 1px solid #ccc; padding: 8px; margin-bottom: 6px; border-radius: 4px;}<\/style>",
    unsafe_allow_html=True
)

# --- 주차별 입력 ---
st.subheader("주차별 보스 클리어 상태 입력")
state_options = ["X","솔격","2인격","3인격","4인격","5인격","예정 (솔격)","예정 (2인격)","예정 (3인격)","예정 (4인격)","예정 (5인격)","예정 (6인격)"]
weeks = list(range(0,14))
data = []
base_date = date(2025,6,17)

# 현재 주차 계산 (매주 목요일 0시 초기화 기준)
today = datetime.now().date()
# 월요일 기준 예시: find week number from base_date
delta_days = (today - base_date).days
curr_week = max(0, min(13, (delta_days - 2)//7 + 1 if delta_days>=2 else 0))

for w in weeks:
    start = base_date + timedelta(days=(0 if w==0 else 2+7*(w-1)))
    end   = start + timedelta(days=(1 if w==0 else 6))
    # 여기에 해방퀘 소모 표시
    drain = QUEST_DRAIN.get(w,0)
    st.markdown(
      f"<div class='week-box'><strong>{w}주차 {start:%m.%d}~{end:%m.%d}  (해방퀘 -{drain})</strong></div>",
      unsafe_allow_html=True
    )
    cols = st.columns(len(BOSS_TABLE))
    row = {"week":w,"start":start}
    for idx,boss in enumerate(BOSS_TABLE):
        choice = cols[idx].selectbox(
            boss,
            options=state_options,
            index=0,
            key=f"{sheet_name}_{boss}_{w}"
        )
        row[boss]=choice
    data.append(row)
df=pd.DataFrame(data)

# --- 계산 및 표시 (버튼 클릭 시) ---
if calc_button:
    results=[]
    acc=init_trace; total_aug=0
    for _,r in df.iterrows():
        w,rdate=r.week,r.start
        boss_sum=0
        for b,base in BOSS_TABLE.items():
            stt=r[b]
            if stt.startswith("예정") or stt=="X": continue
            cnt = 1 if stt=="솔격" else int(stt.replace("인격",""))
            boss_sum += base*cnt
        drain=QUEST_DRAIN.get(w,0)
        delta=boss_sum-drain
        total_aug+=delta; acc+=delta
        results.append({"주차":f"{w}주차","보스합계":boss_sum,"소모량":drain,"순증가량":delta,"누적흔적":acc})
    final_acc = init_trace + total_aug
    lack = max(0,6600-final_acc)
    need_jin = math.ceil(lack/BOSS_TABLE["노말-진힐라"]) if lack>0 else 0

    # 결과 UI를 체크리스트 바로 위에 출력
    summary1.metric("흔적증강", total_aug)
    summary2.metric("현재흔적", final_acc)
    summary3.metric("부족 흔적량", lack)
    st.write(f"**__추가 진힐라 필요 횟수:__ {need_jin}**")

    # 결과 테이블도 아래에
    st.subheader("계산 결과")
    st.dataframe(pd.DataFrame(results).set_index("주차"))
