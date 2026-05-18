import streamlit as st
import io
from urllib.parse import quote
import pandas as pd
import plotly.graph_objects as go

# ── 설정 ──────────────────────────────────────────────────────
SALES_SHEET_ID   = "1-ATlZN-VmstKUkuee83nJhW-tAaEmojk0uPuC329ELY"
WEATHER_SHEET_ID = "1TfQTCPs8W14Pb5Nn_KG4WtthtTa4k0XrfXSM_jedqIk"
CONFIG_SHEET_ID  = "11g3CLTwzsDObWPNUkpLB3iJ45UbMpGC49G6VICwW12k"
YEARS = [2023, 2024, 2025, 2026]
ADMIN_PASSWORD = "farmers24@#$%"

st.set_page_config(page_title="마르쉐 매출 조회", page_icon="🌿", layout="centered")

# ── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
  .hero {
    background:#EAF3DE;border-radius:16px;padding:20px 24px;
    border:0.5px solid #C0DD97;margin-bottom:20px
  }
  .best-card {
    background:#EAF3DE;border:1px solid #3B6D11;
    border-radius:12px;padding:14px 16px;margin-bottom:8px
  }
  .worst-card {
    background:#FAEEDA;border:1px solid #FAC775;
    border-radius:12px;padding:14px 16px;margin-bottom:8px
  }
  .weather-tag { font-size:12px;color:#5F5E5A;margin-top:6px }
  .rank-card {
    border-radius:12px;padding:12px 14px;margin-bottom:8px;
    display:flex;align-items:center;justify-content:space-between
  }
  .info-box {
    background:#E8F0FB;border:0.5px solid #93B4EE;border-radius:10px;
    padding:10px 14px;font-size:13px;color:#2152A3;margin-bottom:16px
  }
  .stButton > button {
    border-radius:20px !important;
  }
  @media print {
    .stApp header, .stApp footer,
    [data-testid="stSidebar"],
    [data-testid="stToolbar"],
    .stTabs [role="tablist"],
    .stSelectbox, .stButton,
    .stCaption { display: none !important; }
    .stDataFrame { page-break-inside: avoid; }
  }
</style>
""", unsafe_allow_html=True)


# ── PDF 생성 함수 ─────────────────────────────────────────────
def generate_pdf(team, show_df, total_sales, total_fund, yr_f="전체", mo_f="전체", mk_f="전체"):
    """전체 내역을 PDF로 생성"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import urllib.request, os

        # 나눔고딕 폰트 다운로드 (한글 지원)
        font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        font_path = "/tmp/NanumGothic.ttf"
        if not os.path.exists(font_path):
            urllib.request.urlretrieve(font_url, font_path)
        pdfmetrics.registerFont(TTFont("NanumGothic", font_path))

        # A4 용지 실제 사용 가능한 폭 (mm)
        # A4 = 210mm, 좌우 여백 각 15mm → 사용 폭 = 180mm
        PAGE_W = 180 * mm

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                rightMargin=15*mm, leftMargin=15*mm,
                                topMargin=15*mm, bottomMargin=15*mm)

        title_style = ParagraphStyle("title", fontName="NanumGothic", fontSize=15,
                                     spaceAfter=3, textColor=colors.HexColor("#27500A"))
        sub_style   = ParagraphStyle("sub",   fontName="NanumGothic", fontSize=10,
                                     spaceAfter=2, textColor=colors.HexColor("#3B6D11"))
        filter_style = ParagraphStyle("filter", fontName="NanumGothic", fontSize=9,
                                      spaceAfter=8, textColor=colors.HexColor("#5F5E5A"))

        elements = []

        # 제목
        elements.append(Paragraph("마르쉐 출점팀 매출 내역", title_style))
        elements.append(Paragraph(team, sub_style))

        # 필터 조건 표시
        filter_parts = []
        if yr_f != "전체": filter_parts.append(f"연도: {yr_f}")
        if mo_f != "전체": filter_parts.append(f"월: {mo_f}")
        if mk_f != "전체": filter_parts.append(f"시장: {mk_f}")
        filter_str = " | ".join(filter_parts) if filter_parts else "전체 기간"
        elements.append(Paragraph(f"조회 조건: {filter_str}", filter_style))
        elements.append(Spacer(1, 4*mm))

        # 요약 테이블 (3열 가로 배치)
        summary_data = [
            ["총 출점 횟수", "매출 합계", "지속가능기금"],
            [f"{len(show_df)}회", f"{total_sales:,.0f}원", f"{total_fund:,.0f}원"],
        ]
        sw = PAGE_W / 3
        summary_table = Table(summary_data, colWidths=[sw, sw, sw])
        summary_table.setStyle(TableStyle([
            ("FONTNAME",   (0,0),(-1,-1), "NanumGothic"),
            ("FONTSIZE",   (0,0),(-1,-1), 9),
            ("BACKGROUND", (0,0),(-1,0),  colors.HexColor("#EAF3DE")),
            ("TEXTCOLOR",  (0,0),(-1,0),  colors.HexColor("#3B6D11")),
            ("TEXTCOLOR",  (0,1),(-1,-1), colors.HexColor("#27500A")),
            ("FONTSIZE",   (0,1),(-1,-1), 11),
            ("FONTNAME",   (0,1),(-1,-1), "NanumGothic"),
            ("GRID",       (0,0),(-1,-1), 0.5, colors.HexColor("#C0DD97")),
            ("ALIGN",      (0,0),(-1,-1), "CENTER"),
            ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
            ("PADDING",    (0,0),(-1,-1), 7),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 6*mm))

        # 상세 내역 테이블
        # 컬럼 너비: 날짜(30) + 시장명(50) + 날씨(38) + 매출(32) + 지속가능기금(30) = 180mm
        headers = ["날짜", "시장명", "날씨", "매출", "지속가능기금"]
        data = [headers]
        for _, row in show_df.iterrows():
            data.append([
                str(row.get("날짜", "")),
                str(row.get("시장명", "")),
                str(row.get("날씨", "")),
                str(row.get("매출", "")),
                str(row.get("지속가능기금", "")),
            ])

        col_widths = [30*mm, 50*mm, 38*mm, 32*mm, 30*mm]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("FONTNAME",      (0,0),(-1,-1), "NanumGothic"),
            ("FONTSIZE",      (0,0),(-1,-1), 8),
            ("BACKGROUND",    (0,0),(-1,0),  colors.HexColor("#EAF3DE")),
            ("TEXTCOLOR",     (0,0),(-1,0),  colors.HexColor("#27500A")),
            ("FONTSIZE",      (0,0),(-1,0),  9),
            ("TEXTCOLOR",     (0,1),(-1,-1), colors.HexColor("#333")),
            ("GRID",          (0,0),(-1,-1), 0.3, colors.HexColor("#C0DD97")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, colors.HexColor("#F7FBF0")]),
            ("ALIGN",         (3,0),(-1,-1), "RIGHT"),
            ("ALIGN",         (0,0),(1,-1),  "LEFT"),
            ("ALIGN",         (2,0),(2,-1),  "CENTER"),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
            ("PADDING",       (0,0),(-1,-1), 5),
        ]))
        elements.append(table)

        doc.build(elements)
        return buf.getvalue()

    except Exception as e:
        st.error(f"PDF 생성 실패: {e}")
        return b""


# ── 데이터 로드 함수들 ─────────────────────────────────────────
@st.cache_data(ttl=0)
def load_team_list():
    """정규팀 리스트 로드 (C열=팀명, P열=비밀번호, 4행 헤더, 5행~데이터)"""
    url = f"https://docs.google.com/spreadsheets/d/{CONFIG_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=" + quote("정규팀리스트") + ""
    try:
        # 전체를 헤더 없이 읽은 뒤, "팀명" 텍스트가 있는 행을 헤더로 사용
        raw = pd.read_csv(url, header=None, dtype=str)

        # "팀명" 이 들어있는 행 번호 찾기
        header_row_idx = None
        for i, row in raw.iterrows():
            if any(str(v).strip() == "팀명" for v in row.values):
                header_row_idx = i
                break

        if header_row_idx is None:
            st.error("팀명 헤더 행을 찾을 수 없어요.")
            return pd.DataFrame(columns=["팀명","비밀번호"])

        # 헤더 행 이후 데이터만 추출
        df = raw.iloc[header_row_idx+1:].copy()
        df.columns = [str(v).strip() for v in raw.iloc[header_row_idx].values]
        df = df.reset_index(drop=True)

        # 컬럼 이름으로 찾기
        team_col = None
        pw_col   = None
        for c in df.columns:
            cs = str(c).strip()
            if cs == "팀명":
                team_col = c
            if "비밀번호" in cs:
                pw_col = c

        if team_col is None or pw_col is None:
            st.error(f"컬럼을 찾을 수 없어요. 컬럼 목록: {df.columns.tolist()}")
            return pd.DataFrame(columns=["팀명","비밀번호"])

        result = df[[team_col, pw_col]].copy()
        result = result.rename(columns={team_col: "팀명", pw_col: "비밀번호"})
        result["팀명"]     = result["팀명"].astype(str).str.strip()
        result["비밀번호"] = result["비밀번호"].astype(str).str.strip()

        # 빈 행, nan, 헤더 중복 제거
        result = result[~result["팀명"].isin(["", "nan", "팀명", "None"])]
        result = result[~result["비밀번호"].isin(["", "nan", "None"])]

        return result.reset_index(drop=True)
    except Exception as e:
        st.error(f"팀 목록 로드 실패: {e}")
        return pd.DataFrame(columns=["팀명","비밀번호"])


@st.cache_data(ttl=0)
def load_regular_markets():
    """정규시장 목록 로드 (A열=시장명)"""
    url = f"https://docs.google.com/spreadsheets/d/{CONFIG_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=" + quote("정규시장") + ""
    try:
        df = pd.read_csv(url, header=0)
        col = df.columns[0]
        markets = df[col].dropna().astype(str).str.strip().tolist()
        return [m for m in markets if m]
    except Exception as e:
        st.warning(f"정규시장 목록 로드 실패: {e}")
        return ["농부시장@목동", "채소시장@서교", "농부시장@서울숲", "농부시장@국립극장"]


@st.cache_data(ttl=0)
def load_sales():
    """매출 데이터 로드"""
    # 시장일(0)|시장명(1)|팀분류(2)|정규(3)|성격(4)|속성(5)|출점팀명(6)|매출총액(7)|지속가능기금(8)
    COL = {"날짜":0,"시장명":1,"팀분류":2,"출점팀":6,"매출":7,"지속가능기금":8}
    dfs = []
    for year in YEARS:
        url = f"https://docs.google.com/spreadsheets/d/{SALES_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={year}"
        try:
            df = pd.read_csv(url, header=0)
            if df.empty: continue
            cols = df.columns.tolist()
            rename = {cols[idx]: name for name, idx in COL.items() if idx < len(cols)}
            df = df.rename(columns=rename)
            df["연도"] = year
            keep = [c for c in ["날짜","시장명","팀분류","출점팀","매출","지속가능기금","연도"] if c in df.columns]
            dfs.append(df[keep])
        except Exception as e:
            st.warning(f"{year}년 매출 데이터 로드 실패: {e}")
    if not dfs: return pd.DataFrame()
    df = pd.concat(dfs, ignore_index=True)
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    for col in ["매출","지속가능기금"]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",","",regex=False)
                    .str.replace("원","",regex=False).str.strip(),
                errors="coerce"
            )
    df["월"] = df["날짜"].dt.month
    df = df.dropna(subset=["날짜","매출","출점팀"])
    df = df[df["매출"] > 0]
    df = df[~df["출점팀"].astype(str).str.strip().isin(["","출점팀","출점팀명","NA","nan"])]
    return df.reset_index(drop=True)


@st.cache_data(ttl=0)
def load_weather():
    """시장 날씨/유동인구 데이터 로드"""
    dfs = []
    for year in YEARS:
        url = f"https://docs.google.com/spreadsheets/d/{WEATHER_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={year}"
        try:
            df = pd.read_csv(url, header=0)
            if df.empty: continue
            df.columns = [c.strip() for c in df.columns]
            df["연도"] = year
            dfs.append(df)
        except Exception as e:
            st.warning(f"{year}년 시장 데이터 로드 실패: {e}")
    if not dfs: return pd.DataFrame()
    df = pd.concat(dfs, ignore_index=True)
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    return df.dropna(subset=["날짜","시장명"]).reset_index(drop=True)


# ── 유틸 함수 ─────────────────────────────────────────────────
def weather_display(w):
    if w is None: return ""
    icons = {"맑음":"☀️","구름많음":"⛅","흐림":"⛅","비":"🌧️","눈":"❄️","소나기":"🌦️"}
    label = str(w.get("날씨","")).strip()
    icon  = icons.get(label,"🌡️")
    def sf(v):
        try: return float(v) if pd.notna(v) and str(v).strip() != "" else None
        except: return None
    hi  = sf(w.get("최고기온"))
    lo  = sf(w.get("최저기온"))
    avg = sf(w.get("기온"))
    if hi is not None and lo is not None: return f"{icon} {label}  최고 {hi:.0f}° / 최저 {lo:.0f}°"
    elif avg is not None:                 return f"{icon} {label}  11시 기준 {avg:.0f}°C"
    elif label:                           return f"{icon} {label}"
    return ""


def get_weather(w_df, date, market):
    if w_df.empty or date is None: return None
    d = pd.Timestamp(date).date()
    m = w_df[(w_df["날짜"].dt.date == d) & (w_df["시장명"] == market)]
    if m.empty: m = w_df[w_df["날짜"].dt.date == d]
    return m.iloc[0].to_dict() if not m.empty else None


# ════════════════════════════════════════════════════════════════
# 로그인 화면
# ════════════════════════════════════════════════════════════════
def show_login(team_list_df):
    st.markdown("""
    <div class="hero">
      <h2 style="color:#27500A;margin:0;font-size:22px">🌿 마르쉐 매출 조회</h2>
      <p style="color:#3B6D11;margin:4px 0 0;font-size:13px">출점팀 전용 매출 조회 서비스</p>
    </div>
    """, unsafe_allow_html=True)

    # 로그인 탭 2개: 출점팀 / 관리자
    login_tab1, login_tab2 = st.tabs(["🌿 출점팀 로그인", "🔑 관리자 로그인"])

    # ── 출점팀 로그인 ──
    with login_tab1:
        st.caption("팀명과 비밀번호를 입력해주세요. 초기 비밀번호는 팀명+0000 입니다.")

        if team_list_df.empty or "팀명" not in team_list_df.columns:
            st.error("팀 목록을 불러오지 못했어요. 잠시 후 새로고침 해주세요.")
            st.stop()

        team_names = sorted(team_list_df["팀명"].dropna().tolist())
        selected_team = st.selectbox("팀 선택", ["-- 팀을 선택하세요 --"] + team_names, key="team_sel")
        password_input = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요", key="team_pw")

        if st.button("로그인", type="primary", use_container_width=True, key="team_login_btn"):
            if selected_team == "-- 팀을 선택하세요 --":
                st.error("팀을 선택해주세요.")
            else:
                match = team_list_df[team_list_df["팀명"] == selected_team]
                if match.empty:
                    st.error("등록되지 않은 팀입니다.")
                else:
                    correct_pw = str(match.iloc[0]["비밀번호"]).strip()
                    if password_input.strip() == correct_pw:
                        st.session_state["logged_in"] = True
                        st.session_state["is_admin"]  = False
                        st.session_state["team"] = selected_team
                        st.rerun()
                    else:
                        st.error("비밀번호가 올바르지 않습니다.")

    # ── 관리자 로그인 ──
    with login_tab2:
        st.caption("관리자 비밀번호를 입력하세요.")
        admin_pw_input = st.text_input("관리자 비밀번호", type="password",
                                        placeholder="관리자 비밀번호 입력", key="admin_pw")

        if st.button("관리자 로그인", type="primary", use_container_width=True, key="admin_login_btn"):
            if admin_pw_input.strip() == ADMIN_PASSWORD:
                st.session_state["logged_in"] = True
                st.session_state["is_admin"]  = True
                st.session_state["team"] = ""
                st.rerun()
            else:
                st.error("관리자 비밀번호가 올바르지 않습니다.")


# ════════════════════════════════════════════════════════════════
# 메인 앱
# ════════════════════════════════════════════════════════════════
def show_app(team, sales_df, weather_df, regular_markets):
    team_df = sales_df[sales_df["출점팀"] == team].copy()

    # 헤더
    col_h1, col_h2 = st.columns([5, 1])
    with col_h1:
        is_admin = st.session_state.get("is_admin", False)
        admin_badge = ' <span style="background:#3B6D11;color:#EAF3DE;font-size:10px;padding:2px 8px;border-radius:20px;vertical-align:middle">관리자</span>' if is_admin else ""
        st.markdown(f"""
        <div class="hero">
          <h2 style="color:#27500A;margin:0;font-size:20px">🌿 {team}{admin_badge}</h2>
          <p style="color:#3B6D11;margin:4px 0 0;font-size:12px">마르쉐 매출 조회</p>
        </div>
        """, unsafe_allow_html=True)

        # 관리자 전용: 팀 전환 드롭다운
        if is_admin:
            all_teams = sorted(sales_df["출점팀"].dropna().unique().tolist())
            selected = st.selectbox(
                "📋 팀 전환 (관리자)",
                options=all_teams,
                index=all_teams.index(team) if team in all_teams else 0,
                key="admin_team_switch"
            )
            if selected != team:
                st.session_state["team"] = selected
                st.rerun()
    with col_h2:
        st.write("")
        st.write("")
        if st.button("로그아웃", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["team"] = ""
            st.rerun()

    tab1, tab2, tab3 = st.tabs(["🏠 홈", "📊 분석", "📋 전체 내역"])


    # ── 탭1: 홈 ────────────────────────────────────────────────
    with tab1:

        # 연도별 요약
        st.markdown("#### 연도별 요약")
        yr_sum = (
            team_df.groupby("연도")["매출"]
            .agg(총매출="sum", 평균매출="mean", 출점횟수="count")
            .reset_index()
        )
        yr_sum["총매출_표시"]  = yr_sum["총매출"].apply(lambda x: f"{x:,.0f}원")
        yr_sum["평균매출_표시"] = yr_sum["평균매출"].apply(lambda x: f"{x:,.0f}원")
        st.dataframe(
            yr_sum[["연도","총매출_표시","평균매출_표시","출점횟수"]].rename(columns={
                "총매출_표시":"총 매출","평균매출_표시":"평균 매출","출점횟수":"출점 횟수"
            }),
            use_container_width=True, hide_index=True
        )

        # 최고 / 최저 매출 + 날씨
        st.markdown("#### 최고 / 최저 매출")
        best  = team_df.loc[team_df["매출"].idxmax()]
        worst = team_df.loc[team_df["매출"].idxmin()]
        bw = get_weather(weather_df, best["날짜"],  best["시장명"])
        ww = get_weather(weather_df, worst["날짜"], worst["시장명"])

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="best-card">
              <div style="font-size:11px;color:#5F5E5A">최고 매출 🏆</div>
              <div style="font-size:22px;font-weight:600;color:#27500A">{best['매출']:,.0f}원</div>
              <div style="font-size:11px;color:#3B6D11;margin-top:4px">
                {int(best['연도'])}년 {int(best['월'])}월 · {best['시장명']}
              </div>
              <div class="weather-tag">{weather_display(bw)}</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="worst-card">
              <div style="font-size:11px;color:#5F5E5A">최저 매출</div>
              <div style="font-size:22px;font-weight:600;color:#633806">{worst['매출']:,.0f}원</div>
              <div style="font-size:11px;color:#854F0B;margin-top:4px">
                {int(worst['연도'])}년 {int(worst['월'])}월 · {worst['시장명']}
              </div>
              <div class="weather-tag">{weather_display(ww)}</div>
            </div>""", unsafe_allow_html=True)

        # 연도별 매출 추이
        st.markdown("#### 연도별 매출 추이")
        yr_c = team_df.groupby("연도").agg(
            총매출=("매출","sum"), 출점평균=("매출","mean")
        ).reset_index()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=yr_c["연도"], y=yr_c["총매출"], mode="lines+markers", name="총매출",
            line=dict(color="#3B6D11", width=2), marker=dict(size=7, color="#3B6D11"),
            fill="tozeroy", fillcolor="rgba(63,109,17,0.08)"
        ))
        fig.add_trace(go.Scatter(
            x=yr_c["연도"], y=yr_c["출점평균"], mode="lines+markers", name="출점평균",
            line=dict(color="#C0DD97", width=2, dash="dash"), marker=dict(size=5, color="#C0DD97")
        ))
        fig.update_layout(
            yaxis_tickformat=",", plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=0,r=0,t=10,b=0), legend=dict(orientation="h",y=-0.2), height=250
        )
        fig.update_xaxes(showgrid=False, tickmode="linear", dtick=1)
        fig.update_yaxes(gridcolor="#EAF3DE")
        st.plotly_chart(fig, use_container_width=True)


    # ── 탭2: 분석 ──────────────────────────────────────────────
    with tab2:
        st.markdown(f"#### {team} 분석")

        # ① 정규시장 필터 토글
        only_regular = st.toggle("정규시장만 보기", value=False)

        # ② 시기 필터
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            yr_opts = ["전체"] + sorted(team_df["연도"].unique().tolist(), reverse=True)
            a_yr = st.selectbox("연도", yr_opts, key="a_yr")
        with col_f2:
            a_mo = st.selectbox("월", ["전체"] + list(range(1,13)), key="a_mo")

        # 전체 데이터에도 동일 필터 적용
        filtered_all  = sales_df.copy()
        filtered_team = team_df.copy()

        if only_regular:
            filtered_all  = filtered_all[filtered_all["시장명"].isin(regular_markets)]
            filtered_team = filtered_team[filtered_team["시장명"].isin(regular_markets)]
        if a_yr != "전체":
            filtered_all  = filtered_all[filtered_all["연도"] == int(a_yr)]
            filtered_team = filtered_team[filtered_team["연도"] == int(a_yr)]
        if a_mo != "전체":
            filtered_all  = filtered_all[filtered_all["월"] == int(a_mo)]
            filtered_team = filtered_team[filtered_team["월"] == int(a_mo)]

        if filtered_team.empty:
            st.warning("선택한 조건에 해당하는 데이터가 없어요.")
        else:
            # 팀 카테고리
            team_cat = team_df["팀분류"].dropna().mode()
            team_cat = team_cat.iloc[0] if not team_cat.empty else ""

            my_avg  = filtered_team["매출"].mean()
            all_avg = filtered_all["매출"].mean()
            cat_avg = filtered_all[filtered_all["팀분류"]==team_cat]["매출"].mean() if team_cat else all_avg

            pct     = round((my_avg-all_avg)/all_avg*100)   if all_avg  else 0
            pct_cat = round((my_avg-cat_avg)/cat_avg*100)   if cat_avg  else 0
            pc  = "#0F6E56" if pct>=0     else "#D85A30"
            pcc = "#0F6E56" if pct_cat>=0 else "#D85A30"

            filter_label = []
            if only_regular: filter_label.append("정규시장")
            if a_yr != "전체": filter_label.append(f"{a_yr}년")
            if a_mo != "전체": filter_label.append(f"{a_mo}월")
            filter_str = " · ".join(filter_label) if filter_label else "전체"

            st.markdown(f"""
            <div class="info-box">
              [{filter_str}] 출점 평균 매출 <strong>{my_avg:,.0f}원</strong> —
              전체 평균 대비 <strong style="color:{pc}">{'+' if pct>=0 else ''}{pct}%</strong>
              {f', {team_cat} 평균 대비 <strong style="color:{pcc}">{chr(43) if pct_cat>=0 else ""}{pct_cat}%</strong>' if team_cat else ''}
            </div>""", unsafe_allow_html=True)

            # 시장별 평균 대비 비교
            st.markdown("**시장별 평균 대비 내 매출**")
            markets = filtered_team["시장명"].dropna().unique()
            mk_strength = []

            for mk in markets:
                my_mk  = filtered_team[filtered_team["시장명"]==mk]["매출"].mean()
                all_mk = filtered_all[filtered_all["시장명"]==mk]["매출"].mean()
                cat_mk = filtered_all[(filtered_all["시장명"]==mk)&(filtered_all["팀분류"]==team_cat)]["매출"].mean() if team_cat else all_mk
                diff   = round((my_mk-all_mk)/all_mk*100) if all_mk else 0
                mk_strength.append({"시장명":mk,"내평균":my_mk,"전체평균":all_mk,"카테고리평균":cat_mk,"차이":diff})

                color = "#0F6E56" if diff>=0 else "#D85A30"
                col1, col2 = st.columns([4,1])
                with col1:
                    st.markdown(f"**{mk}**")
                    st.caption(f"내 평균 {my_mk:,.0f}원 | 전체 평균 {all_mk:,.0f}원 | {team_cat} 평균 {cat_mk:,.0f}원")
                    st.progress(min(my_mk/max(all_mk,1)/2, 1.0))
                with col2:
                    st.markdown(
                        f"<div style='color:{color};font-weight:600;font-size:14px;"
                        f"text-align:right;padding-top:16px'>{'▲' if diff>=0 else '▼'}{abs(diff)}%</div>",
                        unsafe_allow_html=True
                    )

            # 강세 시장 순위
            st.markdown("**강세 시장 순위**")
            mk_strength = sorted(mk_strength, key=lambda x: x["차이"], reverse=True)
            medals = ["🥇","🥈","🥉"]
            for i, r in enumerate(mk_strength):
                dc = "#0F6E56" if r["차이"]>=0 else "#D85A30"
                db = "#E0F5EE" if r["차이"]>=0 else "#FBE9E2"
                st.markdown(f"""
                <div style="background:{'#EAF3DE' if i==0 else 'white'};
                            border:0.5px solid {'#3B6D11' if i==0 else '#C0DD97'};
                            border-radius:12px;padding:12px 14px;margin-bottom:8px;
                            display:flex;align-items:center;justify-content:space-between">
                  <div>
                    <span style="font-size:16px">{medals[i] if i<3 else '·'}</span>
                    <strong style="margin-left:8px;color:#27500A">{r['시장명']}</strong>
                    <div style="font-size:11px;color:#5F5E5A;margin-top:3px;margin-left:26px">
                      내 평균 {r['내평균']:,.0f}원 · 전체 평균 {r['전체평균']:,.0f}원
                    </div>
                  </div>
                  <span style="background:{db};color:{dc};padding:3px 10px;
                               border-radius:20px;font-size:12px;font-weight:600">
                    {'+' if r['차이']>=0 else ''}{r['차이']}%
                  </span>
                </div>""", unsafe_allow_html=True)

            # 날씨별 평균 매출
            if not weather_df.empty:
                st.markdown("**날씨별 평균 매출**")
                w_cols = [c for c in ["날짜","시장명","날씨","기온","최저기온","최고기온"] if c in weather_df.columns]
                merged = filtered_team.merge(weather_df[w_cols], on=["날짜","시장명"], how="left")
                if "날씨" in merged.columns and merged["날씨"].notna().any():
                    w_avg = (
                        merged[merged["날씨"].notna()]
                        .groupby("날씨")["매출"]
                        .agg(평균="mean", 횟수="count")
                        .reset_index()
                        .sort_values("평균", ascending=False)
                    )
                    icons = {"맑음":"☀️","구름많음":"⛅","흐림":"⛅","비":"🌧️","눈":"❄️"}
                    wcols = st.columns(len(w_avg))
                    for idx, (_, row) in enumerate(w_avg.iterrows()):
                        with wcols[idx]:
                            icon = icons.get(str(row["날씨"]).strip(),"🌡️")
                            st.markdown(f"""
                            <div style="background:{'#EAF3DE' if idx==0 else 'white'};
                                        border:{'1px solid #3B6D11' if idx==0 else '0.5px solid #C0DD97'};
                                        border-radius:12px;padding:12px;text-align:center">
                              <div style="font-size:20px">{icon}</div>
                              <div style="font-size:11px;color:#5F5E5A;margin:4px 0">{row['날씨']}</div>
                              <div style="font-size:15px;font-weight:600;color:#27500A">{row['평균']:,.0f}</div>
                              <div style="font-size:10px;color:#888">{int(row['횟수'])}회 평균</div>
                            </div>""", unsafe_allow_html=True)


    # ── 탭3: 전체 내역 ──────────────────────────────────────────
    with tab3:

        # 다중 선택 필터
        yr_opts = sorted(team_df["연도"].unique().tolist(), reverse=True)
        mo_opts = sorted([int(m) for m in team_df["월"].dropna().unique().tolist()])
        mk_opts = sorted(team_df["시장명"].dropna().unique().tolist())

        col1, col2, col3 = st.columns(3)
        with col1:
            yr_f = st.multiselect(
                "연도 (복수 선택 가능)",
                options=yr_opts,
                default=[],
                key="r_yr",
                placeholder="전체"
            )
        with col2:
            mo_f = st.multiselect(
                "월 (복수 선택 가능)",
                options=mo_opts,
                default=[],
                key="r_mo",
                placeholder="전체",
                format_func=lambda x: f"{x}월"
            )
        with col3:
            mk_f = st.multiselect(
                "시장 (복수 선택 가능)",
                options=mk_opts,
                default=[],
                key="r_mk",
                placeholder="전체"
            )

        filtered = team_df.copy()
        if yr_f: filtered = filtered[filtered["연도"].isin(yr_f)]
        if mo_f: filtered = filtered[filtered["월"].isin(mo_f)]
        if mk_f: filtered = filtered[filtered["시장명"].isin(mk_f)]

        # PDF용 필터 레이블
        yr_label = ", ".join([f"{y}년" for y in yr_f]) if yr_f else "전체"
        mo_label = ", ".join([f"{m}월" for m in mo_f]) if mo_f else "전체"
        mk_label = ", ".join(mk_f) if mk_f else "전체"

        # 날씨 합치기
        if not weather_df.empty:
            w_cols = [c for c in ["날짜","시장명","날씨","기온","최저기온","최고기온","총방문객"] if c in weather_df.columns]
            filtered = filtered.merge(weather_df[w_cols], on=["날짜","시장명"], how="left")
            def fmt_w(row):
                icons = {"맑음":"☀️","구름많음":"⛅","흐림":"⛅","비":"🌧️","눈":"❄️"}
                icon = icons.get(str(row.get("날씨","")).strip(),"")
                def sf(v):
                    try: return float(v) if pd.notna(v) and str(v).strip()!="" else None
                    except: return None
                hi,lo,avg = sf(row.get("최고기온")),sf(row.get("최저기온")),sf(row.get("기온"))
                if hi and lo: return f"{icon} {row.get('날씨','')} {hi:.0f}°/{lo:.0f}°"
                elif avg:     return f"{icon} {row.get('날씨','')} {avg:.0f}°C"
                return str(row.get("날씨",""))
            filtered["날씨_표시"] = filtered.apply(fmt_w, axis=1)
        else:
            filtered["날씨_표시"] = ""

        total_s = filtered["매출"].sum()
        total_f = filtered["지속가능기금"].sum() if "지속가능기금" in filtered.columns else 0
        st.caption(f"총 {len(filtered)}건 · 매출 합계 **{total_s:,.0f}원** · 지속가능기금 **{total_f:,.0f}원**")

        # 테이블
        show = filtered[["날짜","시장명","날씨_표시","매출","지속가능기금"]].sort_values("날짜", ascending=False).copy()
        show["날짜"]       = show["날짜"].dt.strftime("%Y-%m-%d")
        show["매출"]       = show["매출"].apply(lambda x: f"{x:,.0f}")
        show["지속가능기금"] = show["지속가능기금"].apply(lambda x: f"{float(x):,.0f}" if pd.notna(x) else "-")
        show = show.rename(columns={"날씨_표시":"날씨"})
        st.dataframe(show, use_container_width=True, hide_index=True)

        # 버튼 2개
        col_a, col_b = st.columns(2)
        with col_a:
            csv = filtered.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                "⬇️ CSV 다운로드", csv,
                f"마르쉐_{team}_매출내역.csv", "text/csv",
                use_container_width=True
            )
        with col_b:
            # PDF 생성 후 다운로드
            pdf_bytes = generate_pdf(team, show, total_s, total_f, yr_label, mo_label, mk_label)
            st.download_button(
                "🖨️ PDF 다운로드", pdf_bytes,
                f"마르쉐_{team}_매출내역.pdf", "application/pdf",
                use_container_width=True
            )


# ════════════════════════════════════════════════════════════════
# 진입점
# ════════════════════════════════════════════════════════════════
def main():
    # 세션 초기화
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "team" not in st.session_state:
        st.session_state["team"] = ""
    if "is_admin" not in st.session_state:
        st.session_state["is_admin"] = False

    # 데이터 로드
    team_list_df   = load_team_list()
    regular_markets = load_regular_markets()

    if not st.session_state["logged_in"]:
        show_login(team_list_df)
    else:
        with st.spinner("데이터 불러오는 중..."):
            sales_df   = load_sales()
            weather_df = load_weather()

        if sales_df.empty:
            st.error("매출 데이터를 불러올 수 없어요. 잠시 후 다시 시도해주세요.")
            return

        # 관리자로 로그인했는데 팀이 없으면 첫 번째 팀으로 자동 설정
        if not st.session_state["team"] and not sales_df.empty:
            st.session_state["team"] = sorted(sales_df["출점팀"].dropna().unique().tolist())[0]
            st.rerun()

        show_app(
            st.session_state["team"],
            sales_df,
            weather_df,
            regular_markets
        )


if __name__ == "__main__":
    main()
