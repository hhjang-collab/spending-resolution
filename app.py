import streamlit as st
import pandas as pd
import base64
import os
from datetime import datetime
from fpdf import FPDF # PDF 생성을 위한 라이브러리

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

# --- 상태 초기화 ---
if "form_data" not in st.session_state:
    st.session_state["form_data"] = {
        "project": "선택", "department": "기술사업화팀", "author": "",
        "account": "선택", "purpose": "", "title": "대리", "date": datetime.today()
    }
if "expense_data" not in st.session_state:
    st.session_state["expense_data"] = pd.DataFrame(
        [{"지출일": datetime.today().date(), "적요": "식대", "지급처": "", "금액": 0, "결제구분": "법인카드", "첨부": "매출전표", "비고": ""}]
    )

# --- 메인 화면 로직 ---
st.title("📄 지출결의서 작성")
st.caption("시스템이 기존 엑셀 양식과 동일한 형태의 완성된 PDF 보고서를 직접 생성합니다.")

# (과거 엑셀 자동완성 기능은 편의성을 위해 그대로 유지)
uploaded_file = st.file_uploader("📂 과거 작성했던 엑셀 파일로 내용 자동 입력 (선택사항)", type=['xlsx'])
if uploaded_file is not None:
    try:
        df_up = pd.read_excel(uploaded_file, header=None)
        st.session_state["form_data"]["project"] = str(df_up.iloc[5, 1]) if pd.notna(df_up.iloc[5, 1]) else "선택"
        st.session_state["form_data"]["purpose"] = str(df_up.iloc[6, 1]) if pd.notna(df_up.iloc[6, 1]) else ""
        st.session_state["form_data"]["department"] = str(df_up.iloc[7, 1]) if pd.notna(df_up.iloc[7, 1]) else ""
        st.session_state["form_data"]["title"] = str(df_up.iloc[7, 3]) if pd.notna(df_up.iloc[7, 3]) else ""
        st.session_state["form_data"]["author"] = str(df_up.iloc[8, 1]) if pd.notna(df_up.iloc[8, 1]) else ""
        st.session_state["form_data"]["account"] = str(df_up.iloc[7, 5]) if pd.notna(df_up.iloc[7, 5]) else "선택"
        
        ex_list = []
        for i in range(11, len(df_up)):
            val = df_up.iloc[i, 0]
            if pd.isna(val): continue
            ex_list.append({
                "지출일": pd.to_datetime(val).date() if isinstance(val, str) else val,
                "적요": str(df_up.iloc[i, 1]) if pd.notna(df_up.iloc[i, 1]) else "식대",
                "지급처": str(df_up.iloc[i, 3]) if pd.notna(df_up.iloc[i, 3]) else "",
                "금액": int(df_up.iloc[i, 5]) if pd.notna(df_up.iloc[i, 5]) else 0,
                "결제구분": "법인카드", "첨부": "매출전표",
                "비고": str(df_up.iloc[i, 7]) if pd.notna(df_up.iloc[i, 7]) else ""
            })
        if ex_list: st.session_state["expense_data"] = pd.DataFrame(ex_list)
        st.toast("✅ 과거 데이터 불러오기 성공!", icon="✨")
    except Exception as e:
        pass

thin_divider()

PROJECT_LIST = ["선택", "전북 군산산단 AX마스터플랜 수립 연구", "상주시-글로컬", "KEITI-중소환경", "대한의협-정보화", "NIPA-SW인재", "호서대-지역청년", "대구TP-과학치안", "KNU-진단 2024"]
ACCOUNT_LIST = ["선택", "출장비", "회의비", "복리후생비"]
SUMMARY_LIST = ["식대", "다과비", "교통비", "교통비(KTX)", "교통비(카셰어링)", "주유비", "숙박비", "간식비"]
PAYMENT_METHODS = ["현금", "계좌이체", "법인카드", "개인카드", "복합결제", "사업비카드"]
ATTACHMENTS = ["매출전표", "세금계산서", "현금영수증"]

def get_idx(lst, item): return lst.index(item) if item in lst else 0

st.subheader("📝 기본 정보")
col1, col2 = st.columns(2)
with col1:
    project = st.selectbox("프로젝트", PROJECT_LIST, index=get_idx(PROJECT_LIST, st.session_state["form_data"]["project"]))
    department = st.text_input("부서", value=st.session_state["form_data"]["department"])
    author = st.text_input("작성자", value=st.session_state["form_data"]["author"])
    account = st.selectbox("계정과목", ACCOUNT_LIST, index=get_idx(ACCOUNT_LIST, st.session_state["form_data"]["account"]))
with col2:
    purpose = st.text_input("목적", value=st.session_state["form_data"]["purpose"])
    title = st.text_input("직위", value=st.session_state["form_data"]["title"])
    date = st.date_input("작성일", st.session_state["form_data"]["date"])
    
thin_divider()

st.subheader("💳 지출 내역 상세")
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
    num_rows="dynamic", use_container_width=True, hide_index=True
)

total_amount = edited_df["금액"].sum()
st.markdown(f"**총 지출 금액: <span style='color:#e74c3c;'>{total_amount:,} 원</span>**", unsafe_allow_html=True)

thin_divider()

# --- 💡 파이썬이 직접 엑셀 모양의 PDF를 그리는 로직 ---
def generate_pdf_report():
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    font_path = "NanumGothic.ttf" # 반드시 깃허브에 업로드 되어있어야 합니다.
    
    if not os.path.exists(font_path):
        st.error("⚠️ 서버에 'NanumGothic.ttf' 폰트가 없습니다. 깃허브에 업로드해주세요!")
        return None

    # 폰트 등록 및 페이지 추가
    pdf.add_font("Nanum", "", font_path, uni=True)
    pdf.add_page()
    
    # 1. 문서 제목
    pdf.set_font("Nanum", "", 20)
    pdf.cell(0, 15, "지 출 결 의 서", align="C", ln=True)
    pdf.ln(5)

    # 2. 기본 정보 표 그리기 (엑셀 양식과 동일한 레이아웃)
    pdf.set_font("Nanum", "", 10)
    w_th = 30 # 항목 너비
    w_td = 65 # 내용 너비
    h = 8     # 높이

    # 첫 번째 줄
    pdf.cell(w_th, h, "프로젝트", border=1, align="C")
    pdf.cell(w_td, h, str(project), border=1)
    pdf.cell(w_th, h, "목적", border=1, align="C")
    pdf.cell(w_td, h, str(purpose), border=1, ln=True)

    # 두 번째 줄
    pdf.cell(w_th, h, "부서", border=1, align="C")
    pdf.cell(w_td, h, str(department), border=1)
    pdf.cell(w_th, h, "직위", border=1, align="C")
    pdf.cell(w_td, h, str(title), border=1, ln=True)

    # 세 번째 줄
    pdf.cell(w_th, h, "작성자", border=1, align="C")
    pdf.cell(w_td, h, str(author), border=1)
    pdf.cell(w_th, h, "작성일", border=1, align="C")
    pdf.cell(w_td, h, date.strftime('%Y-%m-%d'), border=1, ln=True)

    # 네 번째 줄
    pdf.cell(w_th, h, "계정과목", border=1, align="C")
    pdf.cell(w_td, h, str(account), border=1)
    pdf.cell(w_th, h, "총 지출액", border=1, align="C")
    pdf.cell(w_td, h, f"{total_amount:,} 원", border=1, ln=True)

    pdf.ln(10)

    # 3. 지출 내역 상세 표 그리기
    pdf.set_font("Nanum", "", 12)
    pdf.cell(0, 10, "■ 지출 내역 상세", ln=True)
    pdf.set_font("Nanum", "", 9)

    # 테이블 헤더 (총합 너비: 190mm)
    col_widths = [25, 25, 35, 25, 20, 20, 40]
    headers = ["지출일", "적요", "지급처", "금액", "결제구분", "첨부", "비고"]
    for i in range(len(headers)):
        pdf.cell(col_widths[i], 8, headers[i], border=1, align="C")
    pdf.ln()

    # 테이블 내용 반복
    for _, row in edited_df.iterrows():
        pdf.cell(col_widths[0], 8, row['지출일'].strftime('%Y-%m-%d'), border=1, align="C")
        pdf.cell(col_widths[1], 8, str(row['적요']), border=1, align="C")
        pdf.cell(col_widths[2], 8, str(row['지급처']), border=1, align="C")
        pdf.cell(col_widths[3], 8, f"{row['금액']:,}", border=1, align="R")
        pdf.cell(col_widths[4], 8, str(row['결제구분']), border=1, align="C")
        pdf.cell(col_widths[5], 8, str(row['첨부']), border=1, align="C")
        pdf.cell(col_widths[6], 8, str(row['비고']), border=1, align="L")
        pdf.ln()

    # 4. 결재 날인 영역 (추후 도장 이미지를 삽입할 수 있는 여백)
    pdf.ln(20)
    pdf.set_font("Nanum", "", 11)
    pdf.cell(0, 10, "위와 같이 지출결의서를 제출합니다.", align="C", ln=True)
    pdf.ln(10)
    pdf.cell(0, 10, f"작성자 : {str(author)} (인)", align="R", ln=True)
    
    # 💡 도장(서명) 이미지 삽입을 원하시면 추후 여기에 로직을 추가하면 됩니다.
    # if os.path.exists("seal.png"):
    #     pdf.image("seal.png", x=160, y=pdf.get_y()-10, w=15)

    # PDF를 파일 대신 메모리 바이트(Bytes)로 반환하여 즉시 다운로드 지원
    return bytes(pdf.output())

# --- 최종 문서 출력 영역 ---
st.subheader("📥 최종 보고서 출력")

if st.button("📑 시스템 지출결의서 (PDF) 생성 및 다운로드", type="primary", use_container_width=True):
    if project == "선택" or not author:
        st.error("프로젝트와 작성자를 올바르게 입력해주세요.")
    else:
        pdf_data = generate_pdf_report()
        if pdf_data:
            file_name = f"지출결의서_{author if author else '미상'}_{datetime.today().strftime('%Y%m%d')}.pdf"
            
            st.success("🎉 PDF 보고서 생성이 완료되었습니다!")
            st.download_button(
                label="📥 완료된 PDF 다운로드",
                data=pdf_data,
                file_name=file_name,
                mime="application/pdf",
                use_container_width=True
            )
