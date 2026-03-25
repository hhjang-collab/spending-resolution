import streamlit as st
import base64
import pandas as pd
from datetime import datetime

# ==========================================
# [공통 필수 규칙] 2. 페이지 기본 설정 (항상 최상단)
# ==========================================
st.set_page_config(page_title="지출결의서 작성", layout="centered")

# ==========================================
# [공통 필수 규칙] 3. 보안 (비밀번호)
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h2 style='text-align: center;'>🔒 시스템 로그인</h2>", unsafe_allow_html=True)
    pwd = st.text_input("비밀번호를 입력하세요.", type="password")
    
    # st.secrets 설정 필요: .streamlit/secrets.toml 파일에 APP_PASSWORD="본인비밀번호" 입력
    if pwd == st.secrets.get("APP_PASSWORD", "1234"): 
        st.session_state.authenticated = True
        st.rerun()
    elif pwd:
        st.error("비밀번호가 일치하지 않습니다.")
    st.stop()

# ==========================================
# [공통 필수 규칙] 4 & 6. 회사 로고 및 UI 최적화 CSS
# ==========================================
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return ""

# 📌 로고 파일명: 회사 로고가 있다면 경로를 맞춰주세요.
logo_base64 = get_base64_of_bin_file("company_logo.png")

custom_css = f"""
<style>
/* Streamlit 불필요한 안내 문구 숨기기 */
[data-testid="InputInstructions"] {{display: none !important;}}

/* 회사 로고 우측 상단 고정 및 모바일 대응 */
.company-logo {{
    position: fixed;
    top: 70px;
    right: 30px;
    width: 120px; /* 필요에 따라 크기 조절 */
    z-index: 1000;
}}
@media (max-width: 768px) {{
    .company-logo {{
        top: 15px;
        right: 15px;
        width: 80px;
    }}
}}
</style>
"""

# 로고가 있을 경우에만 화면에 출력
if logo_base64:
    custom_css += f'<img src="data:image/png;base64,{logo_base64}" class="company-logo">'

st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# [공통 필수 규칙] 7. 얇은 여백 구분선 함수
# ==========================================
def draw_thin_hr():
    st.markdown(
        '<hr style="margin-top: 15px; margin-bottom: 15px; border: 0; border-top: 1px solid rgba(49, 51, 63, 0.2);">',
        unsafe_allow_html=True
    )

# ==========================================
# [공통 필수 규칙] 5. 사이드바 홈 버튼 및 얇은 여백 구분선
# ==========================================
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
    
    st.markdown("### 📝 지출결의서 메뉴")
    st.caption("양식에 맞게 내용을 기입하고 하단의 제출/다운로드 버튼을 이용하세요.")

# ==========================================
# 메인 화면: 지출결의서 본문 UI
# ==========================================
st.markdown("<h2 style='text-align: center;'>지 출 결 의 서</h2>", unsafe_allow_html=True)

draw_thin_hr()

# 1. 헤더 정보 입력란 (엑셀 상단 영역)
col1, col2 = st.columns([1, 5])
with col1: st.write("**프로젝트**")
with col2: st.text_input("프로젝트", label_visibility="collapsed", placeholder="프로젝트명을 입력하세요")

col1, col2 = st.columns([1, 5])
with col1: st.write("**목적**")
with col2: st.text_input("목적", label_visibility="collapsed", placeholder="목적을 입력하세요")

# 3단 분할 영역 (부서, 직위, 계정과목)
c1, c2, c3, c4, c5, c6 = st.columns([1, 2, 1, 2, 1, 2])
with c1: st.write("**부서**")
with c2: st.text_input("부서", label_visibility="collapsed")
with c3: st.write("**직위**")
with c4: st.text_input("직위", label_visibility="collapsed")
with c5: st.write("**계정과목**")
with c6: st.text_input("계정과목", label_visibility="collapsed")

# 3단 분할 영역 (작성자, 작성일, 분류)
c1, c2, c3, c4, c5, c6 = st.columns([1, 2, 1, 2, 1, 2])
with c1: st.write("**작성자**")
with c2: st.text_input("작성자", label_visibility="collapsed")
with c3: st.write("**작성일**")
with c4: st.date_input("작성일", label_visibility="collapsed")
with c5: st.write("**비고(분류)**")
with c6: st.text_input("분류(예: 출장비)", label_visibility="collapsed")

draw_thin_hr()

# 2. 지출내역 입력란 (Data Editor 활용)
st.markdown("#### 💳 지출 내역")

# 초기 데이터프레임 구성 (세션 상태에 저장하여 유지)
if "expense_df" not in st.session_state:
    st.session_state.expense_df = pd.DataFrame(
        [{"지출일": datetime.today(), "적요": "", "지급처": "", "금액": 0, "비고": ""}]
    )

edited_df = st.data_editor(
    st.session_state.expense_df,
    num_rows="dynamic", # 사용자가 행 추가 가능하게 설정
    use_container_width=True,
    hide_index=True,
    column_config={
        "지출일": st.column_config.DateColumn("지출일", format="YYYY-MM-DD", required=True),
        "적요": st.column_config.TextColumn("적요(내역)"),
        "지급처": st.column_config.TextColumn("지급처"),
        "금액": st.column_config.NumberColumn("금액(원)", min_value=0, format="%d", required=True),
        "비고": st.column_config.TextColumn("비고")
    }
)

# 3. 자동 총 합계 계산
# 금액 컬럼에서 숫자가 아닌 빈칸(NaN) 등을 제외하고 합산
total_amount = pd.to_numeric(edited_df["금액"], errors='coerce').fillna(0).sum()

st.markdown(
    f"""
    <div style='text-align: right; background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-top: 10px;'>
        <h4 style='margin: 0; color: #31333F;'>총 청구금액: <span style='color: #e50914;'>{total_amount:,.0f}</span> 원</h4>
    </div>
    """, 
    unsafe_allow_html=True
)

draw_thin_hr()

# 📌 기능 확장부 (사용자가 추후 기능 구현)
cols = st.columns([1, 1, 1])
with cols[2]:
    if st.button("📄 결의서 제출 (저장)", use_container_width=True):
        st.success("제출 로직을 여기에 구현하세요! (DB 저장 또는 파일 생성 등)")
