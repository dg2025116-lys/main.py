import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="주식 비교 대시보드", layout="wide")

st.title("📊 글로벌 주식 비교 대시보드")
st.markdown("한국 🇰🇷 + 미국 🇺🇸 주요 종목 수익률 비교")

# 기본 종목 리스트
DEFAULT_TICKERS = {
    "미국": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
    "한국": ["005930.KS", "000660.KS", "035420.KS", "051910.KS"]
}

# 사이드바 설정
st.sidebar.header("⚙️ 설정")

market = st.sidebar.selectbox("시장 선택", ["전체", "미국", "한국"])

period = st.sidebar.selectbox(
    "기간 선택",
    ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=3
)

custom_tickers = st.sidebar.text_input(
    "추가 티커 입력 (쉼표로 구분)",
    placeholder="예: NVDA, META, 068270.KS"
)

# 티커 구성
tickers = []

if market == "전체":
    tickers = DEFAULT_TICKERS["미국"] + DEFAULT_TICKERS["한국"]
else:
    tickers = DEFAULT_TICKERS[market]

if custom_tickers:
    tickers += [t.strip().upper() for t in custom_tickers.split(",")]

tickers = list(set(tickers))  # 중복 제거

st.write("### 📌 선택된 종목")
st.write(tickers)

# 데이터 가져오기
@st.cache_data
def load_data(tickers, period):
    data = yf.download(tickers, period=period)["Adj Close"]
    return data

data = load_data(tickers, period)

if data.empty:
    st.error("데이터를 불러오지 못했습니다.")
    st.stop()

# 수익률 계산 (정규화)
normalized = data / data.iloc[0] * 100

# 📈 차트
st.subheader("📈 가격 비교 (정규화)")

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

# 📊 수익률 테이블
st.subheader("📊 기간별 수익률")

returns = (data.iloc[-1] / data.iloc[0] - 1) * 100
returns_df = pd.DataFrame(returns, columns=["수익률 (%)"])
returns_df = returns_df.sort_values(by="수익률 (%)", ascending=False)

st.dataframe(returns_df.style.format("{:.2f}"))

# 📌 최고/최저 종목
best = returns_df.idxmax()[0]
worst = returns_df.idxmin()[0]

st.success(f"🏆 최고 수익률: {best}")
st.warning(f"📉 최저 수익률: {worst}")
