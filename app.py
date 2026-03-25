import streamlit as st
import pandas as pd
import base64
import os
from datetime import datetime
from fpdf import FPDF # PDF 생성을 위한 라이브러리 (requirements.txt에 fpdf2 추가 필요)

# 1. 페이지 기본 설정 (공통 필수 규칙 2)
st.set_page_config(page_title="지출결의서 작성 앱", layout="centered")

# 2. UI 최적화 CSS (공통 필수 규칙 6)
st.markdown("""
    <style>
        [data-testid="InputInstructions"] {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# 3. 보안 (비밀번호) 로그인 로직 (공통 필수 규칙 3)
# [나중에 직접 채워 넣어야 하는 부분] Streamlit Cloud 대시보드 Secrets에 APP_PASSWORD 설정
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

# [나중에 직접 채워 넣어야 하는 부분] 깃허브에 company_logo.png 업로드
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

# --- 숫자를 한글 금액으로 변환해주는 함수 ---
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

# --- 상태 초기화 ---
if "form_data" not in st.session_state:
    st.session_state["form_data"] = {
        "project": "선택", "department": "기술사업화팀", "author": "",
        "account": "선택", "purpose": "", "title": "대리", "date": datetime.today()
    }
if "expense_data" not in st.session_state:
    st.session_state["expense_data"] = pd.DataFrame(
        [{"지출일": datetime.today().date(), "적요": "식대", "지급처": "", "금액": 0, "결제구분": "법인카드", "첨부": "영수증", "비고": ""}]
    )

# --- 메인 화면 로직 ---
st.title("📄 지출결의서 작성")
st.caption("입력하신 데이터는 회사의 공식 지출결의서 양식과 동일한 PDF로 즉시 변환됩니다.")

# 과거 엑셀 업로드 자동완성 영역 (숨길 수 있도록 expander 처리)
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
        "금액": st.column_config.NumberColumn("금액", min_value=0, step=10, required=True, format="%d 원"),
        "결제구분": st.column_config.SelectboxColumn("결제구분", options=PAYMENT_METHODS, required=True),
        "첨부": st.column_config.SelectboxColumn("첨부", options=ATTACHMENTS, required=True),
        "비고": st.column_config.TextColumn("비고"),
    },
    num_rows="dynamic", use_container_width=True, hide_index=True
)

total_amount = edited_df["금액"].sum()
amount_korean = number_to_korean(total_amount)
st.markdown(f"**총 지출 금액: <span style='color:#e74c3c;'>{total_amount:,} 원</span> ({amount_korean})**", unsafe_allow_html=True)

thin_divider()

# --- 💡 완벽한 레이아웃을 갖춘 PDF 생성 로직 ---
def generate_pdf_report():
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    # [주의] 깃허브에 NanumGothic.ttf 파일을 반드시 올려주셔야 한글이 출력됩니다!
    font_path = "NanumGothic.ttf" 
    
    if not os.path.exists(font_path):
        st.error("⚠️ 서버에 'NanumGothic.ttf' 폰트가 없어 PDF를 생성할 수 없습니다.")
        return None

    pdf.add_font("Nanum", "", font_path, uni=True)
    pdf.add_page()
    
    # 1. 문서 제목 & 우측 결재란
    pdf.set_font("Nanum", "", 24)
    pdf.cell(0, 15, "지 출 결 의 서", align="C", ln=False)
    
    # 결재란 표 그리기 (우측 상단)
    pdf.set_font("Nanum", "", 10)
    box_x = 135
    box_y = 10
    w_sign = 20
    
    # 결재란 헤더 (담당, 전결, 대표)
    pdf.set_xy(box_x, box_y)
    pdf.cell(w_sign, 6, "담당", border=1, align="C")
    pdf.cell(w_sign, 6, "전결", border=1, align="C")
    pdf.cell(w_sign, 6, "대표", border=1, align="C")
    
    # 결재란 서명공간
    pdf.set_xy(box_x, box_y + 6)
    pdf.cell(w_sign, 15, "", border=1)
    pdf.cell(w_sign, 15, "", border=1)
    pdf.cell(w_sign, 15, "", border=1)
    
    pdf.set_y(40) # 제목 및 결재란 아래로 Y축 이동

    # 2. 기본 정보 영역 (견고한 테이블)
    pdf.set_font("Nanum", "", 10)
    th_w = 25  # 헤더 열 너비
    td_w = 65  # 데이터 열 너비
    h = 8      # 행 높이

    # 행 1: 프로젝트
    pdf.cell(th_w, h, "프로젝트", border=1, align="C", fill=False)
    pdf.cell(td_w*2 + th_w, h, f" {project}", border=1, ln=True)

    # 행 2: 목적
    pdf.cell(th_w, h, "목적", border=1, align="C")
    pdf.cell(td_w*2 + th_w, h, f" {purpose}", border=1, ln=True)

    # 행 3: 소속 / 직위
    pdf.cell(th_w, h, "소속", border=1, align="C")
    pdf.cell(td_w, h, f" {department}", border=1)
    pdf.cell(th_w, h, "직위", border=1, align="C")
    pdf.cell(td_w, h, f" {title}", border=1, ln=True)

    # 행 4: 출장자 / 지출일자
    pdf.cell(th_w, h, "출장자", border=1, align="C")
    pdf.cell(td_w, h, f" {author}", border=1)
    pdf.cell(th_w, h, "지출일자", border=1, align="C")
    pdf.cell(td_w, h, f" {date.strftime('%Y년 %m월 %d일')}", border=1, ln=True)

    # 행 5: 일금 / 계정과목
    pdf.cell(th_w, h, "일금", border=1, align="C")
    pdf.cell(td_w, h, f" {amount_korean} (\\{total_amount:,})", border=1)
    pdf.cell(th_w, h, "계정과목", border=1, align="C")
    pdf.cell(td_w, h, f" {account}", border=1, ln=True)

    pdf.ln(5)

    # 3. 지출 내역 영역
    pdf.cell(0, 8, "▶ 지출내역", ln=True)
    pdf.set_font("Nanum", "", 9)

    cols = [20, 30, 45, 25, 60] # 총 180mm
    headers = ["지출일자", "적요", "지급처", "금액", "비고"]
    
    for i, h_text in enumerate(headers):
        pdf.cell(cols[i], 7, h_text, border=1, align="C")
    pdf.ln()

    # 지출 항목 리스트업
    for _, row in edited_df.iterrows():
        pdf.cell(cols[0], 7, row['지출일'].strftime('%m월 %d일'), border=1, align="C")
        pdf.cell(cols[1], 7, str(row['적요']), border=1, align="C")
        pdf.cell(cols[2], 7, str(row['지급처']), border=1, align="L")
        pdf.cell(cols[3], 7, f"{row['금액']:,}", border=1, align="R")
        pdf.cell(cols[4], 7, f" {row['비고']}", border=1, align="L")
        pdf.ln()

    # 합계 행 및 결제구분
    pdf.set_font("Nanum", "", 10)
    pdf.cell(cols[0] + cols[1] + cols[2], 8, "합  계", border=1, align="C")
    pdf.cell(cols[3], 8, f"\\ {total_amount:,}", border=1, align="R")
    pdf.cell(cols[4], 8, " VAT 포함", border=1, align="L")
    pdf.ln()
    
    # 결제구분 및 첨부
    pdf.cell(cols[0] + cols[1], 8, "결제 구분 / 첨부", border=1, align="C")
    
    # 여러 건일 경우 첫 번째 항목 기준 또는 복합 처리
    pay_methods = ", ".join(edited_df["결제구분"].unique())
    attach_methods = ", ".join(edited_df["첨부"].unique())
    pdf.cell(cols[2] + cols[3] + cols[4], 8, f" {pay_methods} / {attach_methods}", border=1, align="L")
    pdf.ln()

    # 4. 서명(결의) 영역
    pdf.ln(15)
    pdf.set_font("Nanum", "", 12)
    pdf.cell(0, 10, "위 금액을 결의 합니다.", align="C", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Nanum", "", 11)
    pdf.cell(0, 8, f"{date.strftime('%Y년 %m월 %d일')}", align="C", ln=True)
    
    pdf.ln(5)
    # 우측 정렬로 소속 및 이름 배치
    pdf.cell(140, 8, f"{department}", align="R")
    pdf.cell(40, 8, f"{author}  (인)", align="R", ln=True)

    return bytes(pdf.output())

# --- 최종 문서 출력 영역 ---
st.subheader("📥 최종 보고서 출력")

if st.button("📑 완벽한 지출결의서 (PDF) 생성 및 다운로드", type="primary", use_container_width=True):
    if project == "선택" or not author:
        st.error("프로젝트와 출장자(작성자)를 올바르게 입력해주세요.")
    else:
        pdf_data = generate_pdf_report()
        if pdf_data:
            file_name = f"지출결의서_{author if author else '미상'}_{datetime.today().strftime('%Y%m%d')}.pdf"
            
            st.success("🎉 완벽한 양식의 PDF가 생성되었습니다!")
            st.download_button(
                label="📥 완료된 PDF 다운로드",
                data=pdf_data,
                file_name=file_name,
                mime="application/pdf",
                use_container_width=True
            )
