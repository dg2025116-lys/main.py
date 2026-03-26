import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(page_title="글로벌 주식 분석기", layout="wide")

st.title("🚀 한/미 주요 주식 수익률 비교 대시보드")

# 1. 사이드바: 종목 및 기간 선택
st.sidebar.header("📊 분석 설정")

stock_dict = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "현대차": "005380.KS",
    "에코프로": "086520.KQ",
    "Apple": "AAPL",
    "Tesla": "TSLA",
    "NVIDIA": "NVDA",
    "Microsoft": "MSFT",
    "S&P 500 (VOO)": "VOO",
    "Nasdaq 100 (QQQ)": "QQQ"
}

selected_names = st.sidebar.multiselect(
    "비교할 종목을 선택하세요",
    list(stock_dict.keys()),
    default=["삼성전자", "NVIDIA", "S&P 500 (VOO)"]
)

period = st.sidebar.selectbox("조회 기간", ["1개월", "3개월", "6개월", "1년", "2년", "5년"], index=3)
period_map = {"1개월": 30, "3개월": 90, "6개월": 180, "1년": 365, "2년": 730, "5년": 1825}

# 2. 데이터 불러오기 함수
@st.cache_data(show_spinner="데이터를 불러오는 중입니다...")
def get_cleaned_data(names, days):
    tickers = [stock_dict[name] for name in names]
    end = datetime.now()
    start = end - timedelta(days=days)
    
    # 데이터 다운로드
    data = yf.download(tickers, start=start, end=end)['Close']
    
    # 단일 종목 선택 시 DataFrame 형태 유지
    if len(names) == 1:
        data = data.to_frame()
        data.columns = names
    else:
        # 티커명을 한글 이름으로 변경
        inv_dict = {v: k for k, v in stock_dict.items()}
        data = data.rename(columns=inv_dict)
    
    # 한국/미국 휴장일 차이로 인한 결측치 채우기 (앞의 데이터로 채움)
    data = data.ffill().dropna()
    return data

if selected_names:
    df = get_cleaned_data(selected_names, period_map[period])

    # 3. 수익률 계산 (시작점 0% 기준)
    df_return = (df / df.iloc[0] - 1) * 100

    # 상단 요약 지표 (Metrics)
    cols = st.columns(len(selected_names))
    for i, name in enumerate(selected_names):
        curr_price = df[name].iloc[-1]
        total_ret = df_return[name].iloc[-1]
        cols[i].metric(name, f"{curr_price:,.2f}", f"{total_ret:+.2f}%")

    # 4. 메인 수익률 차트
    st.subheader(f"📈 선택 종목 누적 수익률 ({period})")
    fig = go.Figure()
    for col in df_return.columns:
        fig.add_trace(go.Scatter(
            x=df_return.index, 
            y=df_return[col], 
            name=col, 
            mode='lines',
            hovertemplate='%{x}<br>%{y:.2f}%'
        ))
    
    fig.update_layout(
        hovermode="x unified",
        yaxis_title="수익률 (%)",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    # 5. 상세 분석 (통계)
    st.divider()
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📉 위험도 분석 (MDD)")
        # 최대 낙폭(MDD) 계산
        roll_max = df.cummax()
        drawdown = (df / roll_max - 1.0) * 100
        mdd = drawdown.min()
        
        mdd_df = pd.DataFrame(mdd, columns=["최대 낙폭(%)"])
        st.dataframe(mdd_df.style.format("{:.2f}%"))
        st.caption("MDD(Max Drawdown): 고점 대비 최대 얼마나 하락했는지 나타내는 지표")

    with col_right:
        st.subheader("🤝 종목 간 상관관계")
        # matplotlib 에러 방지를 위해 스타일 없이 기본 출력하거나 Plotly 사용
        corr_matrix = df.pct_change().corr()
        st.dataframe(corr_matrix.style.format("{:.2f}").background_gradient(cmap='Greens'))

else:
    st.warning("왼쪽 사이드바에서 종목을 하나 이상 선택해주세요.")

st.caption("제공되는 데이터는 투자 참고용이며 실제 거래 데이터와 차이가 있을 수 있습니다.")
