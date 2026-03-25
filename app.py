import streamlit as st
import pandas as pd
import base64
import os
from datetime import datetime

# 1. 페이지 기본 설정 (공통 필수 규칙 2)
st.set_page_config(page_title="지출결의서 작성 앱", layout="centered")

# 2. UI 최적화 CSS (공통 필수 규칙 6)
st.markdown("""
    <style>
        [data-testid="InputInstructions"] {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# 3. 보안 (비밀번호) 로그인 로직 (공통 필수 규칙 3)
# [나중에 직접 채워 넣어야 하는 부분] .streamlit/secrets.toml 파일에 APP_PASSWORD = "설정한비밀번호" 를 입력해야 합니다.
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

# [나중에 직접 채워 넣어야 하는 부분] 앱과 같은 경로에 "company_logo.png" 파일을 업로드해 두어야 합니다.
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
    
    # 관리자용 엑셀 다운로드는 사이드바로 분리하여 일반 사용자의 혼선을 방지합니다.
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### ⚙️ 관리자 메뉴")
    st.button("📊 월별 전체내역 엑셀 다운로드", use_container_width=True)

# 6. 여백이 얇은 구분선 함수화 (공통 필수 규칙 7)
def thin_divider():
    st.markdown('<hr style="margin-top: 15px; margin-bottom: 15px; border: 0; border-top: 1px solid rgba(49, 51, 63, 0.2);">', unsafe_allow_html=True)

# --- 메인 화면 로직 ---
st.title("📄 지출결의서 작성")
st.caption("내용을 입력하고 하단의 'PDF 다운로드'를 클릭하면 전자날인이 포함된 최종 결의서가 생성됩니다.")
thin_divider()

# 첨부 데이터를 기반으로 한 선택지
PROJECT_LIST = ["선택", "전북 군산산단 AX마스터플랜 수립 연구", "상주시-글로컬", "KEITI-중소환경", "NIPA-SW인재"]
ACCOUNT_LIST = ["선택", "출장비", "회의비", "복리후생비"]
SUMMARY_LIST = ["식대", "다과비", "교통비(KTX)", "교통비(카셰어링)", "주유비", "숙박비"]
PAYMENT_METHODS = ["법인카드", "개인카드", "현금", "계좌이체", "사업비카드", "복합결제"]
ATTACHMENTS = ["매출전표", "세금계산서", "현금영수증"]

# 기본 정보 입력 영역
col1, col2 = st.columns(2)
with col1:
    project = st.selectbox("프로젝트", PROJECT_LIST)
    department = st.text_input("부서", value="기술사업화팀")
    author = st.text_input("작성자")
    account = st.selectbox("계정과목", ACCOUNT_LIST)

with col2:
    purpose = st.text_input("목적", value="용역착수보고회 참석")
    title = st.text_input("직위", value="대리")
    date = st.date_input("작성일", datetime.today())
    
thin_divider()

st.subheader("💳 지출 내역 상세")

if "expense_data" not in st.session_state:
    st.session_state["expense_data"] = pd.DataFrame(
        [
            {"지출일": datetime.today().date(), "적요": "교통비(KTX)", "지급처": "한국철도공사", "금액": 32000, "결제구분": "법인카드", "첨부": "매출전표", "비고": "용산-익산"},
        ]
    )

edited_df = st.data_editor(
    st.session_state["expense_data"],
    column_config={
        "지출일": st.column_config.DateColumn("지출일", required=True),
        "적요": st.column_config.SelectboxColumn("적요", options=SUMMARY_LIST, required=True),
        "지급처": st.column_config.TextColumn("지급처", required=True),
        "금액": st.column_config.NumberColumn("금액", min_value=0, step=1000, required=True, format="%d 원"),
        "결제구분": st.column_config.SelectboxColumn("결제구분", options=PAYMENT_METHODS, required=True),
        "첨부": st.column_config.SelectboxColumn("첨부", options=ATTACHMENTS, required=True),
        "비고": st.column_config.TextColumn("비고"),
    },
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True
)

total_amount = edited_df["금액"].sum()
st.markdown(f"**총 지출 금액: <span style='color:#e74c3c;'>{total_amount:,} 원</span>**", unsafe_allow_html=True)

thin_divider()

# --- 최종 문서 출력 영역 (PDF 단일화) ---
st.subheader("📥 문서 출력")

# 사용자는 이 큰 버튼 하나만 누르게 됩니다.
if st.button("📑 최종 지출결의서 PDF 다운로드 (전자날인 포함)", type="primary", use_container_width=True):
    if project == "선택" or not author:
        st.error("프로젝트와 작성자를 입력해주세요.")
    else:
        # [나중에 직접 채워 넣어야 하는 부분] 
        # 실제로는 이곳에서 1. 빈 엑셀에 데이터 삽입 -> 2. PDF로 변환 -> 3. 도장 이미지 합성 로직이 실행됩니다.
        st.toast(f"✅ {author}님의 지출결의서를 PDF로 생성 중입니다...", icon="⏳")
        st.info("💡 향후 이곳에 백그라운드 PDF 생성 로직(HTML to PDF 또는 Excel to PDF)이 연결됩니다.")
