import streamlit as st
import pandas as pd
import base64
import os
import io
from datetime import datetime
from xhtml2pdf import pisa

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

# 숫자를 한글 금액으로 변환
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
        [{"지출일": datetime.today().date(), "적요": "교통비(KTX)", "지급처": "", "금액": 0, "결제구분": "법인 카드", "첨부": "영수증", "비고": ""}]
    )

st.title("📄 지출결의서 작성")
st.caption("기존 엑셀 양식과 100% 동일한 구조의 HTML 템플릿을 사용하여 PDF를 생성합니다.")

# 과거 엑셀 업로드 자동완성 (업로드해주신 파일 구조에 맞춰 인덱스 최적화)
with st.expander("📂 과거 작성했던 엑셀 파일로 내용 자동 입력 (선택사항)", expanded=False):
    uploaded_file = st.file_uploader("", type=['xlsx'])
    if uploaded_file is not None:
        try:
            df_up = pd.read_excel(uploaded_file, header=None)
            st.session_state["form_data"]["project"] = str(df_up.iloc[5, 1]) if pd.notna(df_up.iloc[5, 1]) else "선택"
            st.session_state["form_data"]["purpose"] = str(df_up.iloc[5, 3]) if pd.notna(df_up.iloc[5, 3]) else ""
            st.session_state["form_data"]["department"] = str(df_up.iloc[6, 1]) if pd.notna(df_up.iloc[6, 1]) else ""
            st.session_state["form_data"]["title"] = str(df_up.iloc[6, 3]) if pd.notna(df_up.iloc[6, 3]) else ""
            st.session_state["form_data"]["author"] = str(df_up.iloc[7, 1]) if pd.notna(df_up.iloc[7, 1]) else ""
            st.session_state["form_data"]["account"] = str(df_up.iloc[8, 4]) if pd.notna(df_up.iloc[8, 4]) else "선택"
            st.toast("✅ 과거 데이터 불러오기 성공!", icon="✨")
        except Exception as e:
            st.error("데이터를 불러오지 못했습니다. 파일 형식을 확인해주세요.")

thin_divider()

# 첨부 데이터 기반 선택지
PROJECT_LIST = ["선택", "전북 군산산단 AX마스터플랜 수립 연구", "상주시-글로컬", "KEITI-중소환경", "대한의협-정보화", "NIPA-SW인재"]
ACCOUNT_LIST = ["선택", "출장비", "회의비", "복리후생비"]
SUMMARY_LIST = ["식대", "다과비", "간식비", "교통비(KTX)", "교통비(카셰어링)", "주유비", "숙박비"]
PAYMENT_METHODS = ["법인 카드", "개인 카드", "현금", "계좌이체"]
ATTACHMENTS = ["영수증", "세금계산서", "매출전표"]

def get_idx(lst, item): return lst.index(item) if item in lst else 0

st.subheader("📝 기본 정보")
col1, col2 = st.columns(2)
with col1:
    project = st.selectbox("프로젝트", PROJECT_LIST, index=get_idx(PROJECT_LIST, st.session_state["form_data"]["project"]))
    department = st.text_input("소속", value=st.session_state["form_data"]["department"])
    author = st.text_input("출장자", value=st.session_state["form_data"]["author"])
    account = st.selectbox("계정과목", ACCOUNT_LIST, index=get_idx(ACCOUNT_LIST, st.session_state["form_data"]["account"]))
with col2:
    purpose = st.text_input("목적", value=st.session_state["form_data"]["purpose"])
    title = st.text_input("직위", value=st.session_state["form_data"]["title"])
    date = st.date_input("지출일자", st.session_state["form_data"]["date"])
    
thin_divider()

st.subheader("💳 지출 내역 상세")
st.caption("※ 결제구분과 첨부 항목은 작성 완료 후 하단에 일괄 요약되어 표기됩니다.")
edited_df = st.data_editor(
    st.session_state["expense_data"],
    column_config={
        "지출일": st.column_config.DateColumn("지출일자", required=True),
        "적요": st.column_config.SelectboxColumn("적요", options=SUMMARY_LIST, required=True),
        "지급처": st.column_config.TextColumn("지급처", required=True),
        "금액": st.column_config.NumberColumn("금액", min_value=0, step=10, required=True, format="%d 원"),
        "비고": st.column_config.TextColumn("비고"),
        "결제구분": st.column_config.SelectboxColumn("결제구분", options=PAYMENT_METHODS, required=True),
        "첨부": st.column_config.SelectboxColumn("첨부", options=ATTACHMENTS, required=True),
    },
    num_rows="dynamic", use_container_width=True, hide_index=True
)

total_amount = edited_df["금액"].sum()
amount_korean = number_to_korean(total_amount)
st.markdown(f"**총 지출 금액: <span style='color:#e74c3c;'>{total_amount:,} 원</span> ({amount_korean})**", unsafe_allow_html=True)

thin_divider()

# --- 💡 원본 양식을 100% 구현한 HTML ➔ PDF 변환 로직 ---
def generate_html_pdf():
    # 폰트 경로 (서버에 NanumGothic.ttf 필수)
    font_path = os.path.abspath("NanumGothic.ttf")
    if not os.path.exists(font_path):
        st.error("⚠️ 'NanumGothic.ttf' 파일이 깃허브에 없습니다. 한글 출력을 위해 꼭 업로드해주세요.")
        return None

    # 1. 지출 내역 HTML 테이블 행 동적 생성 (올려주신 양식의 5칸 구조)
    rows_html = ""
    for _, row in edited_df.iterrows():
        rows_html += f"""
        <tr>
            <td class="text-center">{row['지출일'].strftime('%m월 %d일')}</td>
            <td class="text-center">{row['적요']}</td>
            <td class="text-left">{row['지급처']}</td>
            <td class="text-right">{row['금액']:,}</td>
            <td class="text-left">{row['비고']}</td>
        </tr>
        """

    # 2. 하단 결제구분 및 첨부 요약
    pay_methods = ", ".join(edited_df["결제구분"].unique())
    attach_methods = ", ".join(edited_df["첨부"].unique())

    # 3. HTML 템플릿 (xhtml2pdf 전용으로 레이아웃이 깨지지 않게 무적의 Table Layout 적용)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        @page {{
            size: a4 portrait;
            margin: 1.5cm;
        }}
        @font-face {{
            font-family: 'NanumGothic';
            src: url('{font_path}');
        }}
        body {{
            font-family: 'NanumGothic', sans-serif;
            font-size: 10pt;
            color: #000;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            border: 1px solid #000;
            padding: 6px;
            vertical-align: middle;
        }}
        .bg-gray {{
            background-color: #f2f2f2;
            text-align: center;
            font-weight: bold;
        }}
        .text-center {{ text-align: center; }}
        .text-left {{ text-align: left; padding-left: 5px; }}
        .text-right {{ text-align: right; padding-right: 5px; }}
        .no-border {{ border: none; }}
    </style>
    </head>
    <body>
        
        <table class="no-border" style="margin-bottom: 20px;">
            <tr>
                <td class="no-border" style="width: 60%; vertical-align: bottom; text-align: center;">
                    <h1 style="font-size: 26pt; letter-spacing: 15px; margin: 0;">지 출 결 의 서</h1>
                </td>
                <td class="no-border" style="width: 40%; text-align: right;">
                    <table style="width: 100%; text-align: center;">
                        <tr>
                            <td class="bg-gray" style="width: 33%;">담당</td>
                            <td class="bg-gray" style="width: 33%;">전결</td>
                            <td class="bg-gray" style="width: 34%;">대표</td>
                        </tr>
                        <tr>
                            <td style="height: 50px;"></td>
                            <td></td>
                            <td></td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>

        <table style="margin-bottom: 20px;">
            <tr>
                <td class="bg-gray" style="width: 15%;">프로젝트</td>
                <td style="width: 35%;">{project}</td>
                <td class="bg-gray" style="width: 15%;">목적</td>
                <td style="width: 35%;">{purpose}</td>
            </tr>
            <tr>
                <td class="bg-gray">소속</td>
                <td>{department}</td>
                <td class="bg-gray">직위</td>
                <td>{title}</td>
            </tr>
            <tr>
                <td class="bg-gray">출장자</td>
                <td>{author}</td>
                <td class="bg-gray">지출일자</td>
                <td>{date.strftime('%Y년 %m월 %d일')}</td>
            </tr>
            <tr>
                <td class="bg-gray">일금</td>
                <td>{amount_korean} (&#8361;{total_amount:,})</td>
                <td class="bg-gray">계정과목</td>
                <td>{account}</td>
            </tr>
        </table>

        <div style="font-weight: bold; font-size: 11pt; margin-bottom: 5px;">■ 지출내역</div>
        <table>
            <tr>
                <td class="bg-gray" style="width: 15%;">지출일자</td>
                <td class="bg-gray" style="width: 20%;">적요</td>
                <td class="bg-gray" style="width: 25%;">지급처</td>
                <td class="bg-gray" style="width: 15%;">금액</td>
                <td class="bg-gray" style="width: 25%;">비고</td>
            </tr>
            {rows_html}
            <tr>
                <td class="bg-gray" colspan="3">합 계</td>
                <td class="text-right" style="font-weight: bold;">&#8361;{total_amount:,}</td>
                <td class="text-left">VAT 포함</td>
            </tr>
            <tr>
                <td class="bg-gray" colspan="2">결제 구분</td>
                <td class="text-center">{pay_methods}</td>
                <td class="bg-gray">첨부</td>
                <td class="text-center">{attach_methods}</td>
            </tr>
        </table>

        <div style="margin-top: 50px; text-align: center; font-size: 14pt;">위 금액을 결의 합니다.</div>
        <div style="margin-top: 20px; text-align: center; font-size: 12pt;">{date.strftime('%Y년 %m월 %d일')}</div>
        <div style="margin-top: 40px; text-align: right; font-size: 13pt; padding-right: 20px;">
            {department} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {author} &nbsp;&nbsp;&nbsp;(인)
        </div>

    </body>
    </html>
    """

    # HTML 문자열을 PDF로 구워냄
    pdf_buf = io.BytesIO()
    pisa_status = pisa.CreatePDF(
        src=html_content, 
        dest=pdf_buf, 
        encoding='utf-8'
    )

    if pisa_status.err:
        st.error("PDF 생성 중 오류가 발생했습니다.")
        return None

    return pdf_buf.getvalue()

st.subheader("📥 최종 보고서 출력")

if st.button("📑 완벽한 지출결의서 (PDF) 생성 및 다운로드", type="primary", use_container_width=True):
    if project == "선택" or not author:
        st.error("프로젝트와 출장자를 올바르게 입력해주세요.")
    else:
        st.toast("HTML 템플릿을 분석하여 PDF를 렌더링 중입니다...", icon="⚙️")
        pdf_data = generate_html_pdf()
        
        if pdf_data:
            file_name = f"지출결의서_{author if author else '미상'}_{datetime.today().strftime('%Y%m%d')}.pdf"
            
            st.success("🎉 원본 엑셀 양식과 완벽하게 동일한 구조의 PDF가 생성되었습니다!")
            st.download_button(
                label="📥 완료된 최종 PDF 다운로드",
                data=pdf_data,
                file_name=file_name,
                mime="application/pdf",
                use_container_width=True
            )
