import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(page_title="Pro 주식 분석 대시보드", layout="wide")

# 사이드바 설정
st.sidebar.title("🔍 분석 설정")
stock_dict = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "현대차": "005380.KS",
    "Apple": "AAPL",
    "Tesla": "TSLA",
    "NVIDIA": "NVDA",
    "Microsoft": "MSFT",
    "S&P 500 (VOO)": "VOO",
    "Nasdaq 100 (QQQ)": "QQQ"
}

selected_names = st.sidebar.multiselect(
    "종목 선택", 
    list(stock_dict.keys()), 
    default=["삼성전자", "NVIDIA", "S&P 500 (VOO)"]
)

period = st.sidebar.selectbox("기간 설정", ["1개월", "3개월", "6개월", "1년", "2년", "5년"], index=3)
period_map = {"1개월": 30, "3개월": 90, "6개월": 180, "1년": 365, "2년": 730, "5년": 1825}

# 데이터 캐싱 (속도 향상)
@st.cache_data
def load_data(tickers, days):
    end = datetime.now()
    start = end - timedelta(days=days)
    data = yf.download(tickers, start=start, end=end)
    return data['Close']

if selected_names:
    tickers = [stock_dict[name] for name in selected_names]
    raw_data = load_data(tickers, period_map[period])
    
    # 데이터 정리
    if len(selected_names) == 1:
        df = raw_data.to_frame()
        df.columns = selected_names
    else:
        # 티커명을 한글 이름으로 매핑
        inv_dict = {v: k for k, v in stock_dict.items()}
        df = raw_data.rename(columns=inv_dict)

    # 결측치 처리 (휴장일 등)
    df = df.ffill()

    # 1. 누적 수익률 계산 (Normalization)
    df_return = (df / df.iloc[0] - 1) * 100

    # 메인 화면 레이아웃
    st.title("📊 글로벌 주식 성과 분석")
    
    # 지표 요약 (Metrics)
    cols = st.columns(len(selected_names))
    for i, name in enumerate(selected_names):
        current_price = df[name].iloc[-1]
        total_return = df_return[name].iloc[-1]
        cols[i].metric(name, f"{current_price:,.2f}", f"{total_return:.2f}%")

    # --- 차트 1: 수익률 비교 차트 ---
    st.subheader("✅ 종목별 누적 수익률 비교 (%)")
    fig_rel = go.Figure()
    for col in df_return.columns:
        fig_rel.add_trace(go.Scatter(x=df_return.index, y=df_return[col], name=col, mode='lines'))
    
    fig_rel.update_layout(
        hovermode="x unified",
        template="plotly_white",
        margin=dict(l=20, r=20, t=20, b=20),
        height=500
    )
    st.plotly_chart(fig_rel, use_container_width=True)

    # --- 차트 2: 개별 종목 상세 분석 (캔들스틱/이동평균) ---
    st.divider()
    st.subheader("🔍 개별 종목 상세 데이터 (상대적 변동성)")
    
    # MDD (Max Drawdown) 계산 함수
    def get_mdd(series):
        roll_max = series.cummax()
        daily_drawdown = series / roll_max - 1.0
        return daily_drawdown.min() * 100

    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.write("**고점 대비 최대 낙폭 (MDD)**")
        mdd_data = {name: [f"{get_mdd(df[name]):.2f}%"] for name in selected_names}
        st.table(pd.DataFrame(mdd_data, index=["MDD"]))

    with col2:
        st.write("**상관관계 분석**")
        st.dataframe(df.corr().style.background_gradient(cmap='RdYlGn'))

else:
    st.info("왼쪽 사이드바에서 분석할 주식을 선택해 주세요.")

st.caption("Data Source: Yahoo Finance | Built with Streamlit")
