import streamlit as st
import base64
import pandas as pd
from datetime import datetime
from io import BytesIO
try:
    from fpdf import FPDF
except ImportError:
    st.error("fpdf2 라이브러리가 필요합니다. 터미널에서 `pip install fpdf2`를 실행하세요.")

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
    
    # 📌 st.secrets 설정 필요: .streamlit/secrets.toml 파일에 APP_PASSWORD="본인비밀번호" 입력
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

# 📌 로고 파일명: 회사 로고가 있다면 동일한 폴더에 "company_logo.png"로 저장해 주세요.
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
    width: 120px;
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
    # 📌 포털 주소: 필요시 href의 주소를 변경하세요.
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
    st.caption("양식에 맞게 내용을 기입하고 하단의 PDF 다운로드 버튼을 이용하세요.")

# ==========================================
# PDF 생성 로직 (FPDF2)
# ==========================================
def generate_pdf(header_data, df, total_amount):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    
    try:
        # 📌 한글 폰트 적용: 루트 폴더에 'NanumGothic.ttf' 폰트 파일을 반드시 넣어주세요!
        pdf.add_font("Nanum", "", "NanumGothic.ttf")
        font_name = "Nanum"
    except RuntimeError:
        # 폰트가 없을 경우 기본 폰트 사용 (한글이 깨질 수 있음)
        font_name = "helvetica"
    
    # 제목
    pdf.set_font(font_name, size=20)
    pdf.cell(0, 15, "지 출 결 의 서", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    # 기본 정보 표
    pdf.set_font(font_name, size=10)
    line_height = 8
    
    # 1행: 프로젝트, 목적
    pdf.cell(30, line_height, "프로젝트", border=1, align="C")
    pdf.cell(160, line_height, header_data['project'], border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(30, line_height, "목 적", border=1, align="C")
    pdf.cell(160, line_height, header_data['purpose'], border=1, new_x="LMARGIN", new_y="NEXT")
    
    # 2행: 부서, 직위, 계정과목
    pdf.cell(30, line_height, "부 서", border=1, align="C")
    pdf.cell(35, line_height, header_data['dept'], border=1)
    pdf.cell(30, line_height, "직 위", border=1, align="C")
    pdf.cell(35, line_height, header_data['position'], border=1)
    pdf.cell(30, line_height, "계정과목", border=1, align="C")
    pdf.cell(30, line_height, header_data['account'], border=1, new_x="LMARGIN", new_y="NEXT")
    
    # 3행: 작성자, 작성일, 분류
    pdf.cell(30, line_height, "작성자", border=1, align="C")
    pdf.cell(35, line_height, header_data['author'], border=1)
    pdf.cell(30, line_height, "작성일", border=1, align="C")
    pdf.cell(35, line_height, str(header_data['date']), border=1)
    pdf.cell(30, line_height, "분 류", border=1, align="C")
    pdf.cell(30, line_height, header_data['category'], border=1, new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(10)
    
    # 지출내역 테이블 헤더
    pdf.set_font(font_name, size=12)
    pdf.cell(0, 10, "[ 지 출 내 역 ]", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font(font_name, size=9)
    col_widths = [30, 60, 40, 30, 30]
    headers = ["지출일", "적요(내역)", "지급처", "금액(원)", "비고"]
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], line_height, h, border=1, align="C")
    pdf.ln(line_height)
    
    # 지출내역 데이터
    for _, row in df.iterrows():
        pdf.cell(col_widths[0], line_height, str(row['지출일'])[:10] if pd.notnull(row['지출일']) else "", border=1, align="C")
        pdf.cell(col_widths[1], line_height, str(row['적요']), border=1)
        pdf.cell(col_widths[2], line_height, str(row['지급처']), border=1)
        pdf.cell(col_widths[3], line_height, f"{pd.to_numeric(row['금액'], errors='coerce'):,.0f}", border=1, align="R")
        pdf.cell(col_widths[4], line_height, str(row['비고']), border=1)
        pdf.ln(line_height)
        
    pdf.ln(10)
    
    # 총 청구금액
    pdf.set_font(font_name, size=14)
    pdf.cell(0, 10, f"총 청구금액 : {total_amount:,.0f} 원", align="R")
    
    return pdf.output()

# ==========================================
# 메인 화면: 지출결의서 본문 UI
# ==========================================
st.markdown("<h2 style='text-align: center;'>지 출 결 의 서</h2>", unsafe_allow_html=True)

draw_thin_hr()

# 1. 헤더 정보 입력란
col1, col2 = st.columns([1, 5])
with col1: st.write("**프로젝트**")
with col2: val_project = st.text_input("프로젝트", label_visibility="collapsed", placeholder="프로젝트명을 입력하세요")

col1, col2 = st.columns([1, 5])
with col1: st.write("**목적**")
with col2: val_purpose = st.text_input("목적", label_visibility="collapsed", placeholder="목적을 입력하세요")

c1, c2, c3, c4, c5, c6 = st.columns([1, 2, 1, 2, 1, 2])
with c1: st.write("**부서**")
with c2: val_dept = st.text_input("부서", label_visibility="collapsed")
with c3: st.write("**직위**")
with c4: val_position = st.text_input("직위", label_visibility="collapsed")
with c5: st.write("**계정과목**")
with c6: val_account = st.text_input("계정과목", label_visibility="collapsed")

c1, c2, c3, c4, c5, c6 = st.columns([1, 2, 1, 2, 1, 2])
with c1: st.write("**작성자**")
with c2: val_author = st.text_input("작성자", label_visibility="collapsed")
with c3: st.write("**작성일**")
with c4: val_date = st.date_input("작성일", label_visibility="collapsed")
with c5: st.write("**비고(분류)**")
with c6: val_category = st.text_input("분류", label_visibility="collapsed")

draw_thin_hr()

# 2. 지출내역 입력란
st.markdown("#### 💳 지출 내역")

if "expense_df" not in st.session_state:
    st.session_state.expense_df = pd.DataFrame(
        [{"지출일": datetime.today(), "적요": "", "지급처": "", "금액": 0, "비고": ""}]
    )

edited_df = st.data_editor(
    st.session_state.expense_df,
    num_rows="dynamic",
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

# 4. PDF 다운로드 영역
header_dict = {
    "project": val_project, "purpose": val_purpose,
    "dept": val_dept, "position": val_position, "account": val_account,
    "author": val_author, "date": val_date, "category": val_category
}

col_empty, col_btn = st.columns([2, 1])
with col_btn:
    # PDF 생성
    pdf_bytes = generate_pdf(header_dict, edited_df, total_amount)
    
    st.download_button(
        label="📄 PDF로 다운로드",
        data=pdf_bytes,
        file_name=f"지출결의서_{val_author if val_author else '작성자'}_{datetime.today().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
