import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="주식 비교 대시보드", layout="wide")

st.title("📊 글로벌 주식 비교 대시보드")
st.markdown("한국 🇰🇷 + 미국 🇺🇸 주식 수익률 비교")

# 기본 종목
DEFAULT_TICKERS = {
    "미국": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
    "한국": ["005930.KS", "000660.KS", "035420.KS", "051910.KS"]
}

# ---------------- 사이드바 ----------------
st.sidebar.header("⚙️ 설정")

market = st.sidebar.selectbox("시장 선택", ["전체", "미국", "한국"])

period = st.sidebar.selectbox(
    "기간 선택",
    ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=3
)

custom_input = st.sidebar.text_input(
    "추가 티커 (쉼표 구분)",
    placeholder="예: NVDA, META, 068270.KS"
)

# ---------------- 티커 구성 ----------------
tickers = []

if market == "전체":
    tickers = DEFAULT_TICKERS["미국"] + DEFAULT_TICKERS["한국"]
else:
    tickers = DEFAULT_TICKERS[market]

if custom_input:
    extra = [t.strip().upper() for t in custom_input.split(",") if t.strip()]
    tickers += extra

tickers = list(set(tickers))  # 중복 제거

st.write("### 📌 선택된 종목", tickers)

# ---------------- 데이터 로드 ----------------
@st.cache_data(ttl=3600)
def load_data_safe(tickers, period):
    result = pd.DataFrame()

    for ticker in tickers:
        try:
            df = yf.download(ticker, period=period, progress=False)

            # 데이터 없는 경우 스킵
            if df.empty:
                continue

            # Adj Close 없으면 Close 사용
            if "Adj Close" in df.columns:
                series = df["Adj Close"]
            elif "Close" in df.columns:
                series = df["Close"]
            else:
                continue

            result[ticker] = series

        except Exception:
            continue

    return result

data = load_data_safe(tickers, period)

# ---------------- 데이터 검증 ----------------
if data.empty or len(data.columns) == 0:
    st.error("❌ 데이터를 불러오지 못했습니다. 티커를 확인하세요.")
    st.stop()

# 결측치 제거 (중요!)
data = data.dropna(axis=1, how="all")
data = data.fillna(method="ffill")

if data.shape[0] < 2:
    st.error("❌ 데이터가 충분하지 않습니다.")
    st.stop()

# ---------------- 수익률 계산 ----------------
normalized = data / data.iloc[0] * 100

returns = (data.iloc[-1] / data.iloc[0] - 1) * 100
returns_df = pd.DataFrame(returns, columns=["수익률 (%)"])
returns_df = returns_df.sort_values(by="수익률 (%)", ascending=False)

# ---------------- 차트 ----------------
st.subheader("📈 수익률 비교 차트")

fig = go.Figure()

for col in normalized.columns:
    fig.add_trace(
        go.Scatter(
            x=normalized.index,
            y=normalized[col],
            mode="lines",
            name=col
        )
    )

fig.update_layout(
    height=500,
    xaxis_title="날짜",
    yaxis_title="수익률 (%)",
    legend_title="종목"
)

st.plotly_chart(fig, use_container_width=True)

# ---------------- 테이블 ----------------
st.subheader("📊 종목별 수익률")

st.dataframe(
    returns_df.style.format("{:.2f}"),
    use_container_width=True
)

# ---------------- 베스트/워스트 ----------------
if not returns_df.empty:
    best = returns_df["수익률 (%)"].idxmax()
    worst = returns_df["수익률 (%)"].idxmin()

    st.success(f"🏆 최고 수익률: {best}")
    st.warning(f"📉 최저 수익률: {worst}")

# ---------------- 안내 ----------------
st.caption("💡 한국 주식은 반드시 .KS 또는 .KQ 붙여야 합니다 (예: 005930.KS)")
