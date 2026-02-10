import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import feedparser

# Page title
st.title("Stock Data Dashboard 📈")

# Sidebar inputs
st.sidebar.header("Stock Analysis By Ajay Sharma")
ticker_name = st.sidebar.text_input("**Enter Stock Ticker** (e.g. AAPL ,MSFT ,GOOGL ,AMZN ,TSLA ,META ,NFLX ,NVDA ,TCS.NS ,INFY.NS ,RELIANCE.NS ,ICICIBANK.NS )", value="TCS.NS")


start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2020-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))
ma_window = st.sidebar.slider("Moving Average Window", min_value=5, max_value=50, value=20)


# Fetching data
st.write(f"Fetching data for **{ticker_name}** from {start_date} to {end_date}...")
data = yf.download(ticker_name, start=start_date, end=end_date , progress=False)

if data.empty:
    st.error("No data found. Please check the ticker symbol or date range.")
    st.stop()

#  FIX 1: multiindex columns ko single level columns me convert karta h agar jarurat ho 
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

#  FIX 2: check karta h kon sa column available h dataset me close ya adjusted
if "Close" in data.columns: 
    price_col = "Close"
elif "Adj Close" in data.columns:
    price_col = "Adj Close"
else:
    st.error("No price column found.")
    st.stop()
volume_col = "Volume" if "Volume" in data.columns else None

# FIX 3:  Data ko safely clean karne ke liye 
data = data.dropna(subset=[price_col])
if volume_col:
    data = data.dropna(subset=[volume_col])

# Moving Average
data["MA"] = data[price_col].rolling(ma_window).mean()

# Tabs
tabs = st.tabs(["📋Raw Data","📈 Price Chart","📊 Volume Chart","📉 Moving Avg", "💵 Payouts", "🧾 Stock Summary", "📰 News"
])

# Tab 1: Raw Data Ki Last 5 Rows 
with tabs[0]:
    st.subheader(f"Raw Data for {ticker_name}")
    st.write(data.tail())
    st.download_button("Download Data as CSV", data.to_csv(), file_name=f"{ticker_name}_data.csv")

# Tab 2: Closing Price Chart Ke Liye 
with tabs[1]:
    if price_col:
        st.subheader("Closing Price Over Time")
        st.line_chart(data[price_col])
    else:
        st.warning("Closing price data is not available for this stock.")

# Tab 3: Volume Chart Ke Liye Or Volume Crores Me Dikhe 
with tabs[2]:
    if volume_col:
        st.subheader("Volume Over Time (in Crores)")

        volume_crore = (data[volume_col] / 1_000_0000)
        volume_crore.name = "Volume (Cr)"   

        st.bar_chart(volume_crore)

    else:
        st.warning("Volume data is not available for this stock.")

        
# Tab 4: Moving Averages Chart Ke Liye 
with tabs[3]:
    st.subheader(f"Closing Price with {ma_window}-Day Moving Average")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(data.index, data[price_col], label="Closing Price", color='blue')
    ax.plot(data.index, data["MA"], label=f"{ma_window}-Day Moving Average", color='orange')
    ax.set_title(f"Closing Price with {ma_window}-Day Moving Average")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.legend()
    st.pyplot(fig)



# Tab 5: Dividends & Splits Ke liye
with tabs[4]:
    st.subheader("Dividends & Splits")
    ticker = yf.Ticker(ticker_name)
    dividends = ticker.dividends
    splits = ticker.splits

    st.write("**Dividends:**")
    st.write(dividends if not dividends.empty else "No dividends found during this period.")
    st.write("**Splits:**")
    st.write(splits if not splits.empty else "No splits found during this period.")

with tabs[5]:
    st.subheader("Stock Analysis Summary")

    max_price = data[price_col].max()
    min_price = data[price_col].min()
    avg_price = data[price_col].mean()

    max_date = data[price_col].idxmax().date()
    min_date = data[price_col].idxmin().date()

    summary = pd.DataFrame({
        "Metric": ["Maximum Price", "Minimum Price", "Average Price"],
        "Value": [
            round(max_price, 2),
            round(min_price, 2),
            round(avg_price, 2)
        ],
        "Date": [max_date, min_date, ""]
    })

    st.dataframe(summary, use_container_width=True, hide_index=True)

# Tab: Stock News
with tabs[6]:
    st.subheader("Latest News")

    try:
        rss_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker_name}&region=US&lang=en-US"
        feed = feedparser.parse(rss_url)

        if feed.entries:
            for i, entry in enumerate(feed.entries[:5], start=1):
                st.markdown(f"**{i}. {entry.title}**")
                st.markdown(f"[Read full news]({entry.link})")
                st.divider()
        else:
            st.info("No news found for this stock.")

    except Exception as e:
        st.warning("Unable to fetch news at the moment.")

