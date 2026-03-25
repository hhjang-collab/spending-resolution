import streamlit as st
import pandas as pd
import base64
import os
import io
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

# 1. 페이지 기본 설정 (공통 필수 규칙 2)
st.set_page_config(page_title="지출결의서 작성 앱", layout="centered")

# 2. UI 최적화 CSS (공통 필수 규칙 6)
st.markdown("""
    <style>
        [data-testid="InputInstructions"] {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# 3. 보안 (비밀번호) 로그인 로직 (공통 필수 규칙 3)
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 로그인")
    st.markdown("사내 업무용 시스템입니다. 비밀번호를 입력해주세요.")
    pwd_input = st.text_input("비밀번호", type="password")
    
    if st.button("로그인"):
        correct_password = st.secrets.get("APP_PASSWORD", "1234") 
        if pwd_input == correct_password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("비밀번호가 일치하지 않습니다.")
    st.stop()

# 4. 회사 로고 (우측 상단 고정) (공통 필수 규칙 4)
def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

logo_base64 = get_base64_of_bin_file("company_logo.png")
if logo_base64:
    st.markdown(f"""
        <style>
            .fixed-logo {{
                position: fixed;
                top: 70px;
                right: 30px;
                z-index: 999;
                width: 120px;
            }}
            @media (max-width: 768px) {{
                .fixed-logo {{
                    top: 15px;
                    right: 15px;
                    width: 80px;
                }}
            }}
        </style>
        <img src="data:image/png;base64,{logo_base64}" class="fixed-logo">
    """, unsafe_allow_html=True)

# 5. 홈 버튼 (포털 복귀) 및 얇은 여백 구분선 (공통 필수 규칙 5)
with st.sidebar:
    st.markdown(
        '''
        <div style="margin-top: 5px;">
            <a href="https://ip2b-work-tools.streamlit.app/" target="_blank" style="text-decoration: none; color: #31333F; font-size: 15px; font-weight: 600;">
                🏠 홈으로
            </a>
        </div>
        <hr style="margin-top: 10px; margin-bottom: 15px; border: 0; border-top: 1px solid rgba(49, 51, 63, 0.2);">
        ''', 
        unsafe_allow_html=True
    )
    st.markdown("### 📝 지출결의 메뉴")
    st.button("신규 작성", use_container_width=True)
    st.button("작성 내역 조회", use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### ⚙️ 관리자 메뉴")
    st.button("📊 월별 전체내역 엑셀 다운로드", use_container_width=True)

# 6. 여백이 얇은 구분선 함수화 (공통 필수 규칙 7)
def thin_divider():
    st.markdown('<hr style="margin-top: 15px; margin-bottom: 15px; border: 0; border-top: 1px solid rgba(49, 51, 63, 0.2);">', unsafe_allow_html=True)

def number_to_korean(num):
    if num == 0: return "영"
    units = ["", "십", "백", "천"]
    mans = ["", "만", "억", "조"]
    num_str = str(num)
    length = len(num_str)
    result = ""
    for i in range(length):
        digit = int(num_str[i])
        if digit != 0:
            digit_kor = "일이삼사오육칠팔구"[digit-1]
            unit_kor = units[(length - 1 - i) % 4]
            result += digit_kor + unit_kor
        if (length - 1 - i) % 4 == 0:
            man_idx = (length - 1 - i) // 4
            if man_idx > 0 and result and not result.endswith(mans[man_idx]):
                result += mans[man_idx]
    return f"일금 {result}원정"

if "form_data" not in st.session_state:
    st.session_state["form_data"] = {
        "project": "선택", "department": "기술사업화팀", "author": "",
        "account": "선택", "purpose": "", "title": "대리", "date": datetime.today()
    }
if "expense_data" not in st.session_state:
    st.session_state["expense_data"] = pd.DataFrame(
        [{"지출일": datetime.today().date(), "적요": "식대", "지급처": "", "금액": 0, "결제구분": "법인카드", "첨부": "영수증", "비고": ""}]
    )

st.title("📄 지출결의서 작성")
st.caption("작성된 데이터는 회사의 원본 양식(PDF) 위에 투명하게 덧입혀져 완벽한 결과물로 출력됩니다.")

with st.expander("📂 과거 작성했던 엑셀 파일로 내용 자동 입력 (선택사항)", expanded=False):
    uploaded_file = st.file_uploader("", type=['xlsx'])
    if uploaded_file is not None:
        try:
            df_up = pd.read_excel(uploaded_file, header=None)
            st.session_state["form_data"]["project"] = str(df_up.iloc[5, 1]) if pd.notna(df_up.iloc[5, 1]) else "선택"
            st.session_state["form_data"]["purpose"] = str(df_up.iloc[6, 1]) if pd.notna(df_up.iloc[6, 1]) else ""
            st.session_state["form_data"]["department"] = str(df_up.iloc[7, 1]) if pd.notna(df_up.iloc[7, 1]) else ""
            st.session_state["form_data"]["title"] = str(df_up.iloc[7, 3]) if pd.notna(df_up.iloc[7, 3]) else ""
            st.session_state["form_data"]["author"] = str(df_up.iloc[8, 1]) if pd.notna(df_up.iloc[8, 1]) else ""
            st.session_state["form_data"]["account"] = str(df_up.iloc[7, 5]) if pd.notna(df_up.iloc[7, 5]) else "선택"
            st.toast("✅ 과거 데이터 불러오기 성공!", icon="✨")
        except Exception as e:
            pass

thin_divider()

PROJECT_LIST = ["선택", "전북 군산산단 AX마스터플랜 수립 연구", "상주시-글로컬", "KEITI-중소환경", "대한의협-정보화", "NIPA-SW인재"]
ACCOUNT_LIST = ["선택", "출장비", "회의비", "복리후생비"]
SUMMARY_LIST = ["식대", "다과비", "교통비(KTX)", "교통비(카셰어링)", "주유비", "숙박비", "간식비"]
PAYMENT_METHODS = ["법인카드", "개인카드", "현금", "계좌이체"]
ATTACHMENTS = ["영수증", "세금계산서", "매출전표"]

def get_idx(lst, item): return lst.index(item) if item in lst else 0

st.subheader("📝 기본 정보")
col1, col2 = st.columns(2)
with col1:
    project = st.selectbox("프로젝트", PROJECT_LIST, index=get_idx(PROJECT_LIST, st.session_state["form_data"]["project"]))
    department = st.text_input("소속", value=st.session_state["form_data"]["department"])
    author = st.text_input("출장자(작성자)", value=st.session_state["form_data"]["author"])
    account = st.selectbox("계정과목", ACCOUNT_LIST, index=get_idx(ACCOUNT_LIST, st.session_state["form_data"]["account"]))
with col2:
    purpose = st.text_input("목적", value=st.session_state["form_data"]["purpose"])
    title = st.text_input("직위", value=st.session_state["form_data"]["title"])
    date = st.date_input("지출일자", st.session_state["form_data"]["date"])
    
thin_divider()

st.subheader("💳 지출 내역 상세")
edited_df = st.data_editor(
    st.session_state["expense_data"],
    column_config={
        "지출일": st.column_config.DateColumn("지출일자", required=True),
        "적요": st.column_config.SelectboxColumn("적요", options=SUMMARY_LIST, required=True),
        "지급처": st.column_config.TextColumn("지급처", required=True),
        "금액": st.column_config.NumberColumn("금액", min_value=0, step=10
