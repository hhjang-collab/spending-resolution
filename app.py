import streamlit as st
import pandas as pd
import base64
import os
import io
from datetime import datetime
from pypdf import PdfReader, PdfWriter
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

# --- 💡 핵심: 글자 넘침 방지 (Auto-fit) 함수 ---
def draw_text_autofit(can, text, x, y, max_width, default_size=10, align="left"):
    """
    글자가 max_width를 넘어가면 칸에 맞게 폰트 크기를 자동으로 줄여서 그리는 함수.
    """
    text = str(text)
    current_size = default_size
    font_name = "Nanum"
    
    can.setFont(font_name, current_size)
    text_width = pdfmetrics.stringWidth(text, font_name, current_size)

    # 글자가 칸보다 넓으면 폰트 크기를 0.5씩 줄임 (최소 5pt까지만)
    while text_width > max_width and current_size > 5.0:
        current_size -= 0.5
        can.setFont(font_name, current_size)
        text_width = pdfmetrics.stringWidth(text, font_name, current_size)

    # 정렬 방식에 따라 그리기
    if align == "center":
        can.drawCentredString(x + (max_width / 2), y, text)
    elif align == "right":
        can.drawRightString(x + max_width, y, text)
    else: # 기본 왼쪽 정렬
        can.drawString(x, y, text)
        
    # 사용 후 캔버스 폰트 크기 초기화
    can.setFont(font_name, default_size)

# --- PDF 오버레이 로직 ---
def generate_overlay_pdf():
    font_path = "NanumGothic.ttf"
    if not os.path.exists(font_path):
        st.error("⚠️ 'NanumGothic.ttf' 파일이 없습니다. 깃허브에 업로드해주세요.")
        return None
    pdfmetrics.registerFont(TTFont("Nanum", font_path))

    bg_path = "blank_template.pdf"
    if not os.path.exists(bg_path):
        st.error("⚠️ 'blank_template.pdf' (빈 양식 PDF) 파일이 없습니다. 깃허브에 업로드해주세요.")
        return None

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)

    # [나중에 직접 채워 넣어야 하는 부분]
    # draw_text_autofit(캔버스객체, 텍스트, X좌표, Y좌표, 최대허용너비(max_width), 기본폰트크기, 정렬)
    # 아래 max_width(예: 150)는 실제 빈칸의 픽셀 너비에 맞게 조절하세요.
    
    draw_text_autofit(can, project, 150, 700, max_width=180, default_size=10)
    draw_text_autofit(can, purpose, 150, 680, max_width=180, default_size=10)
    draw_text_autofit(can, department, 150, 660, max_width=80, default_size=10)
    draw_text_autofit(can, title, 350, 660, max_width=80, default_size=10)
    draw_text_autofit(can, author, 150, 640, max_width=80, default_size=10)
    draw_text_autofit(can, date.strftime('%Y년 %m월 %d일'), 350, 640, max_width=80, default_size=10)
    draw_text_autofit(can, f"{amount_korean} (\\{total_amount:,})", 150, 620, max_width=180, default_size=10)
    draw_text_autofit(can, account, 350, 620, max_width=80, default_size=10)

    # 지출 내역 리스트업
    start_y = 550
    line_height = 20
    for i, row in edited_df.iterrows():
        current_y = start_y - (i * line_height)
        # 좁은 칸들(지급처, 비고 등)에 오토핏 적용
        draw_text_autofit(can, row['지출일'].strftime('%m/%d'), 70, current_y, max_width=40, align="center")
        draw_text_autofit(can, row['적요'], 130, current_y, max_width=50, align="center")
        draw_text_autofit(can, row['지급처'], 220, current_y, max_width=80) 
        draw_text_autofit(can, f"{row['금액']:,}", 300, current_y, max_width=50, align="right") 
        draw_text_autofit(can, row['비고'], 380, current_y, max_width=100)

    # 합계 및 결제구분
    draw_text_autofit(can, f"\\{total_amount:,}", 300, start_y - (10 * line_height), max_width=50, align="right")
    pay_methods = ", ".join(edited_df["결제구분"].unique())
    attach_methods = ", ".join(edited_df["첨부"].unique())
    draw_text_autofit(can, f"{pay_methods} / {attach_methods}", 220, start_y - (11 * line_height), max_width=150)

    # 서명란
    draw_text_autofit(can, date.strftime('%Y년 %m월 %d일'), 240, 200, max_width=100, default_size=12)
    draw_text_autofit(can, f"{department}      {author}  (인)", 300, 160, max_width=150, default_size=12, align="right")

    can.save()
    packet.seek(0)
    new_pdf = PdfReader(packet)

    existing_pdf = PdfReader(open(bg_path, "rb"))
    output = PdfWriter()

    page = existing_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])
    output.add_page(page)

    output_stream = io.BytesIO()
    output.write(output_stream)
    return output_stream.getvalue()

st.subheader("📥 최종 보고서 출력")

if st.button("📑 완벽한 지출결의서 (PDF) 생성 및 다운로드", type="primary", use_container_width=True):
    if project == "선택" or not author:
        st.error("프로젝트와 출장자(작성자)를 올바르게 입력해주세요.")
    else:
        st.toast("원본 양식 위에 데이터를 덧입히는 중입니다...", icon="⚙️")
        pdf_data = generate_overlay_pdf()
        
        if pdf_data:
            file_name = f"지출결의서_{author if author else '미상'}_{datetime.today().strftime('%Y%m%d')}.pdf"
            
            st.success("🎉 원본 양식과 100% 동일한 완벽한 PDF가 생성되었습니다!")
            st.download_button(
                label="📥 완료된 최종 PDF 다운로드",
                data=pdf_data,
                file_name=file_name,
                mime="application/pdf",
                use_container_width=True
            )
