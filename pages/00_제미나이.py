import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(page_title="Global Stock Analyzer", layout="wide")

st.title("📈 한/미 주요 주식 수익률 비교")
st.markdown("---")

# 1. 사이드바 설정
st.sidebar.header("⚙️ 분석 설정")

stock_dict = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "현대차": "005380.KS",
    "NAVER": "035420.KS",
    "Apple": "AAPL",
    "Tesla": "TSLA",
    "NVIDIA": "NVDA",
    "Microsoft": "MSFT",
    "S&P 500 (VOO)": "VOO",
    "Nasdaq 100 (QQQ)": "QQQ"
}

selected_names = st.sidebar.multiselect(
    "종목을 선택하세요",
    list(stock_dict.keys()),
    default=["삼성전자", "NVIDIA", "S&P 500 (VOO)"]
)

period = st.sidebar.selectbox("조회 기간", ["1개월", "3개월", "6개월", "1년", "2년", "5년"], index=3)
period_map = {"1개월": 30, "3개월": 90, "6개월": 180, "1년": 365, "2년": 730, "5년": 1825}

# 2. 데이터 다운로드 및 정제
@st.cache_data(show_spinner="데이터 동기화 중...")
def load_and_sync_data(names, days):
    if not names:
        return None
    
    tickers = [stock_dict[name] for name in names]
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 데이터 다운로드
    raw = yf.download(tickers, start=start_date, end=end_date)['Close']
    
    # 1개 종목일 경우 처리
    if len(names) == 1:
        df = raw.to_frame()
        df.columns = names
    else:
        # 티커 -> 한글명 변환
        inv_dict = {v: k for k, v in stock_dict.items()}
        df = raw.rename(columns=inv_dict)
    
    # 전처리: 휴장일 공백을 이전 날짜 데이터로 채움 (앞뒤 결측치 완벽 제거)
    df = df.ffill().bfill()
    return df

if selected_names:
    df = load_and_sync_data(selected_names, period_map[period])
    
    # 3. 수익률 계산 (시작일 = 0%)
    df_returns = (df / df.iloc[0] - 1) * 100

    # 상단 요약 카드
    st.subheader("📌 종목별 성과 요약")
    metrics = st.columns(len(selected_names))
    for i, name in enumerate(selected_names):
        current_val = df[name].iloc[-1]
        total_ret = df_returns[name].iloc[-1]
        metrics[i].metric(label=name, value=f"{current_val:,.0f}", delta=f"{total_ret:.2f}%")

    # 4. 수익률 비교 차트 (Plotly)
    st.markdown("### 📊 누적 수익률 추이")
    fig = go.Figure()
    for col in df_returns.columns:
        fig.add_trace(go.Scatter(x=df_returns.index, y=df_returns[col], name=col, mode='lines'))
    
    fig.update_layout(
        hovermode="x unified",
        template="plotly_dark", # 가독성 좋은 다크 테마
        yaxis_title="수익률 (%)",
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    # 5. 상세 통계 데이터
    st.markdown("### 📉 리스크 및 상관관계")
    col1, col2 = st.columns(2)

    with col1:
        st.write("**최대 낙폭 (MDD)**")
        # MDD 계산
        mdd = ((df / df.cummax() - 1) * 100).min()
        mdd_df = pd.DataFrame(mdd, columns=["Max Drawdown (%)"])
        st.table(mdd_df.style.format("{:.2f}%"))

    with col2:
        st.write("**종목 간 상관계수**")
        # 변동률 기준 상관계수 계산
        corr = df.pct_change().corr()
        # 스타일링에서 background_gradient를 제거하여 matplotlib 에러 방지
        st.dataframe(corr.style.format("{:.2f}"))

else:
    st.info("사이드바에서 비교할 종목을 선택해 주세요.")

st.caption("Data provided by Yahoo Finance. 일일 종가 기준이며 환율 변동은 고려되지 않았습니다.")
