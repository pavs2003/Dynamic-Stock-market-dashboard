import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
import time
import numpy as np

st.set_page_config(page_title="📈 Stock Market Dashboard", layout="wide")
st.title("📊 Real-Time Stock Market Dashboard")

# Session State Defaults
if "symbols" not in st.session_state:
    st.session_state.symbols = "AAPL, MSFT, TSLA"
if "start_date" not in st.session_state:
    st.session_state.start_date = date.today() - timedelta(days=180)
if "end_date" not in st.session_state:
    st.session_state.end_date = date.today()
if "currency" not in st.session_state:
    st.session_state.currency = "USD"

# Sidebar Inputs
st.sidebar.header("⚙️ Options")
symbol_input = st.sidebar.text_input("Enter stock symbols (comma-separated)", st.session_state.symbols)
st.session_state.symbols = symbol_input
symbols = [s.strip().upper() for s in symbol_input.split(",") if s.strip()]

refresh = st.sidebar.slider("Auto-refresh (seconds)", 10, 300, 60, step=10)

start_date = st.sidebar.date_input("Start Date", st.session_state.start_date)
end_date = st.sidebar.date_input("End Date", st.session_state.end_date)
st.session_state.start_date = start_date
st.session_state.end_date = end_date

chart_type = st.sidebar.selectbox("Chart Type", ["Candlestick"])
show_ma = st.sidebar.checkbox("Show Moving Averages")
show_rsi = st.sidebar.checkbox("Overlay RSI")
show_bollinger = st.sidebar.checkbox("Overlay Bollinger Bands")

currency = st.sidebar.radio("Currency", ["USD", "INR"])
st.session_state.currency = currency

# Currency Conversion Placeholder
conversion_rate = 83.0 if currency == "INR" else 1.0
currency_symbol = "₹" if currency == "INR" else "$"

# Theme
theme = st.sidebar.radio("Choose Theme", ["Light", "Dark"])
template = "plotly_white" if theme == "Light" else "plotly_dark"

# Portfolio Tracker
st.sidebar.header("💼 Portfolio Tracker")
portfolio = {}
for symbol in symbols:
    shares = st.sidebar.number_input(f"Shares of {symbol}", min_value=0, value=0)
    if shares > 0:
        portfolio[symbol] = shares

st.markdown(f"🔄 Auto-refresh every **{refresh} seconds**.")
time.sleep(refresh)
st.experimental_rerun()

# Main loop
for symbol in symbols:
    st.markdown(f"### 📌 {symbol}")
    with st.spinner(f"Fetching data for {symbol}..."):
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)

            if data.empty:
                st.warning(f"No data found for {symbol}")
                continue

            if show_ma:
                data['MA20'] = data['Close'].rolling(window=20).mean()
                data['MA50'] = data['Close'].rolling(window=50).mean()

            if show_rsi:
                delta = data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                data['RSI'] = 100 - (100 / (1 + rs))

            if show_bollinger:
                data['BB_MID'] = data['Close'].rolling(window=20).mean()
                data['BB_STD'] = data['Close'].rolling(window=20).std()
                data['BB_UPPER'] = data['BB_MID'] + (2 * data['BB_STD'])
                data['BB_LOWER'] = data['BB_MID'] - (2 * data['BB_STD'])

            # Chart
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=data.index, open=data['Open'] * conversion_rate, high=data['High'] * conversion_rate,
                low=data['Low'] * conversion_rate, close=data['Close'] * conversion_rate, name="Candlestick"))

            if show_ma:
                fig.add_trace(go.Scatter(x=data.index, y=data['MA20'] * conversion_rate, name="MA 20", line=dict(dash='dash')))
                fig.add_trace(go.Scatter(x=data.index, y=data['MA50'] * conversion_rate, name="MA 50", line=dict(dash='dot')))

            if show_bollinger:
                fig.add_trace(go.Scatter(x=data.index, y=data['BB_UPPER'] * conversion_rate, name="Bollinger Upper", line=dict(color='lightgray')))
                fig.add_trace(go.Scatter(x=data.index, y=data['BB_LOWER'] * conversion_rate, name="Bollinger Lower", line=dict(color='lightgray')))

            fig.update_layout(title=f"{symbol} Stock Price", xaxis_title="Date", yaxis_title=f"Price ({currency})", template=template)
            st.plotly_chart(fig, use_container_width=True)

            if show_rsi:
                st.subheader("RSI Indicator")
                rsi_fig = go.Figure()
                rsi_fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name="RSI", line=dict(color='orange')))
                rsi_fig.update_layout(yaxis_range=[0, 100], template=template)
                st.plotly_chart(rsi_fig, use_container_width=True)

            # Metrics
            cols = st.columns(4)
            current_price = data['Close'].iloc[-1] * conversion_rate if not data.empty else 0
            cols[0].metric("Current", f"{currency_symbol}{current_price:.2f}")
            cols[1].metric("High", f"{currency_symbol}{ticker.info.get('dayHigh', 'N/A')}")
            cols[2].metric("Low", f"{currency_symbol}{ticker.info.get('dayLow', 'N/A')}")
            cols[3].metric("Dividend", ticker.info.get("dividendYield", "N/A"))

            # Portfolio value display
            if symbol in portfolio:
                shares = portfolio[symbol]
                purchase_price = st.sidebar.number_input(f"Purchase price of {symbol} ({currency})", min_value=0.0, value=0.0)
                value = shares * current_price
                profit_loss = (current_price - purchase_price) * shares if purchase_price > 0 else 0
                st.success(f"📈 Holding {shares} shares = **{currency_symbol}{value:,.2f}**")
                st.info(f"💰 P/L = **{currency_symbol}{profit_loss:,.2f}**")

            st.download_button("📥 Download CSV", data.to_csv(), file_name=f"{symbol}_data.csv")

            # Earnings Calendar
            earnings = ticker.calendar
            if not earnings.empty:
                st.subheader("📅 Earnings Calendar")
                st.dataframe(earnings.transpose())

        except Exception as e:
            st.error(f"Error for {symbol}: {e}")

# Toast notification (after data load)
st.toast("✅ Data updated successfully!", icon="✅")
