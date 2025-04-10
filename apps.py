import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import date, timedelta

st.set_page_config(page_title="Stock Market Dashboard", layout="wide")
st.title("📈 Dynamic Stock Market Dashboard")

# Sidebar input
st.sidebar.header("Input")
stocks = st.sidebar.text_input("Enter stock symbols separated by commas", "AAPL, MSFT, GOOGL")
start_date = st.sidebar.date_input("Start Date", date.today() - timedelta(days=30))
end_date = st.sidebar.date_input("End Date", date.today())

if start_date > end_date:
    st.sidebar.error("Error: End date must fall after start date.")

stock_list = [stock.strip().upper() for stock in stocks.split(",")]

# Fetching data
def fetch_data(stock):
    try:
        data = yf.download(stock, start=start_date, end=end_date)
        data["Symbol"] = stock
        return data
    except Exception as e:
        st.error(f"Failed to fetch data for {stock}: {e}")
        return None

all_data = []
for stock in stock_list:
    data = fetch_data(stock)
    if data is not None and not data.empty:
        all_data.append(data)

if all_data:
    df = pd.concat(all_data)
    df.reset_index(inplace=True)

    # Line chart of closing prices
    st.subheader("📉 Closing Price Trends")
    for stock in stock_list:
        stock_data = df[df["Symbol"] == stock]
        st.line_chart(stock_data.set_index("Date")["Close"], height=250)

    # Volume chart
    st.subheader("🔊 Trading Volume")
    for stock in stock_list:
        stock_data = df[df["Symbol"] == stock]
        st.bar_chart(stock_data.set_index("Date")["Volume"], height=250)

    # Comparative performance
    st.subheader("📊 Comparative Performance")
    compare_data = {stock: df[df['Symbol'] == stock]['Close'].iloc[-1] for stock in stock_list if not df[df['Symbol'] == stock].empty}
    comp_df = pd.DataFrame(list(compare_data.items()), columns=["Company", "Value"])
    st.write("Compare Data Table:")
    st.dataframe(comp_df)
    st.line_chart(comp_df.set_index("Company"))

else:
    st.warning("Please enter valid stock symbols to fetch data.")
