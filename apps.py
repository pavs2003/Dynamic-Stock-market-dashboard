import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta

st.set_page_config(page_title="📈 Stock Market Dashboard", layout="wide")
st.title("📊 Real-Time Stock Market Dashboard")

# Sidebar Inputs
st.sidebar.header("⚙️ Options")
symbols = st.sidebar.text_input("Enter stock symbols (comma-separated)", "AAPL, MSFT, TSLA")
symbols = [s.strip().upper() for s in symbols.split(",") if s.strip()]

refresh = st.sidebar.slider("Auto-refresh (seconds)", 10, 300, 60, step=10)
start_date = st.sidebar.date_input("Start Date", date.today() - timedelta(days=180))
end_date = st.sidebar.date_input("End Date", date.today())
chart_type = st.sidebar.selectbox("Chart Type", ["Line", "Candlestick"])
show_ma = st.sidebar.checkbox("Show Moving Averages")

st_autorefresh = st.empty()
st_autorefresh.markdown(f"🔄 Auto-refresh every **{refresh} seconds**.")

# Main loop
for symbol in symbols:
    st.markdown(f"### 📌 {symbol}")
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=start_date, end=end_date)

        if data.empty:
            st.warning(f"No data found for {symbol}")
            continue

        if show_ma:
            data['MA20'] = data['Close'].rolling(window=20).mean()
            data['MA50'] = data['Close'].rolling(window=50).mean()

        # Chart
        fig = go.Figure()
        if chart_type == "Candlestick":
            fig.add_trace(go.Candlestick(
                x=data.index, open=data['Open'], high=data['High'],
                low=data['Low'], close=data['Close'], name="Candlestick"))
        else:
            fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name="Close Price"))
            if show_ma:
                fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], name="MA 20", line=dict(dash='dash')))
                fig.add_trace(go.Scatter(x=data.index, y=data['MA50'], name="MA 50", line=dict(dash='dot')))

        fig.update_layout(title=f"{symbol} Stock Price", xaxis_title="Date", yaxis_title="Price", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        # Metrics
        cols = st.columns(3)
        cols[0].metric("Current", ticker.info.get("currentPrice", "N/A"))
        cols[1].metric("High", ticker.info.get("dayHigh", "N/A"))
        cols[2].metric("Low", ticker.info.get("dayLow", "N/A"))

        st.download_button("📥 Download CSV", data.to_csv(), file_name=f"{symbol}_data.csv")

    except Exception as e:
        st.error(f"Error for {symbol}: {e}")

# Auto-refresh the app
st.experimental_rerun()
