import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import warnings

warnings.filterwarnings("ignore")

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Market Comparison App")
st.title("Market Performance Dashboard")

# --- QH API Data Function ---
def get_qh_api_data(instruments_list, interval='1M', count=10):
    """
    Fetches OHLC data from the QH API for a list of instruments.

    Args:
        instruments_list (list): A list of instrument tickers (e.g., ["ES", "NQ"]).
        interval (str): The time interval for the data (e.g., '1M', '1H', '1D').
        count (int): The number of data points to retrieve.

    Returns:
        pd.DataFrame: A DataFrame with the fetched data or an empty DataFrame on failure.
    """
    # CRITICAL: You MUST replace 'your_access_token_here' with your actual authorization token.
    # The API will return an error if this token is missing or invalid.
    api_token = "your_access_token_here"
    url = "https://qh-api.corp.hertshtengroup.com/api/v2/ohlc"
    
    headers = {
        "Authorization": f"Bearer {api_token}"
    }

    params = {
        "instruments": ",".join(instruments_list),
        "interval": interval,
        "count": str(count)
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        
        # Check if the response is JSON before trying to parse it.
        if response.headers.get('Content-Type') != 'application/json':
            st.error(f"Error fetching data from QH API: Expected JSON, but received a different content type.")
            st.error(f"Raw API response: {response.text}")
            return pd.DataFrame()

        data = response.json()
        
        # The API returns a dictionary where keys are instruments.
        # We'll combine them into a single DataFrame.
        all_data = []
        for instrument, ohlc_data in data.items():
            if ohlc_data:
                df = pd.DataFrame(ohlc_data)
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
                df = df.set_index('datetime')
                df['instrument'] = instrument
                all_data.append(df)
        
        if all_data:
            return pd.concat(all_data)
        else:
            st.error("No data returned from the QH API.")
            return pd.DataFrame()
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from QH API: {e}")
        return pd.DataFrame()


# --- Yahoo Finance Data Configuration ---

# Configuration for Yahoo Finance Symbols
SYMBOLS = {
    'Stock Indices': {
        '^GSPC': 'S&P 500', '^IXIC': 'NASDAQ Composite', '^FTSE': 'FTSE 100 (UK)',
        '^N225': 'Nikkei 225 (Japan)', '^GDAXI': 'DAX 30 (Germany)', '^NSEI': 'Nifty 50 (India)',
        '^BVSP': 'Bovespa (Brazil)', '^MXX': 'IPC Mexico', '^HSI': 'Hang Seng (Hong Kong)',
        '^STOXX50E': 'Euro Stoxx 50', '^SETI': 'SET Index (Thailand)', '^ATH': 'Athex Composite (Greece)',
        'FTSEMIB.MI': 'FTSE MIB (Italy)', '^WIG20': 'WIG20 (Poland)', '^FCHI': 'CAC 40 (France)',
        '^KS11': 'KOSPI (South Korea)', 'IMOEX.ME': 'MOEX (Russia)', '^GSPTSE': 'S&P/TSX (Canada)',
        '^AXJO': 'S&P/ASX 200 (Australia)', '^PSI': 'PSEi (Philippines)'
    },
    'Commodities': {
        'GC=F': 'Gold Futures', 'SI=F': 'Silver Futures', 'CL=F': 'Crude Oil Futures',
        'NG=F': 'Natural Gas Futures', 'BZ=F': 'Brent Crude Futures', 'HG=F': 'Copper Futures'
    },
    'Currencies': {
        'EURUSD=X': 'EUR/USD', 'JPY=X': 'USD/JPY', 'GBPUSD=X': 'GBP/USD',
        'AUDUSD=X': 'AUD/USD', 'CADUSD=X': 'CAD/USD', 'CHFUSD=X': 'CHF/USD'
    },
    'Major Tech Stocks': {
        'AAPL': 'Apple Inc.', 'MSFT': 'Microsoft Corp.', 'GOOGL': 'Alphabet Inc. (Class A)',
        'AMZN': 'Amazon.com Inc.', 'META': 'Meta Platforms Inc.', 'TSLA': 'Tesla Inc.',
        'NVDA': 'NVIDIA Corp.', 'AMD': 'Advanced Micro Devices Inc.', 'NFLX': 'Netflix Inc.'
    }
}

# Configuration for QH API Tickers
QH_TICKERS = {
    "Bonds": ["TU", "YR", "FV", "TY", "TN", "ZB"],
    "Futures": ["6E", "6J", "6B", "6S", "RF", "6C"],
    "Index": ["ES", "YM", "DXY", "FXXP", "FTUK", "FDAX", "JNI", "FDXM", "FESX", "NQ", "DX"],
    "Yields": [
        "DE2YR", "DE3YR", "DE5YR", "DE10YR", "DE30YR",
        "GB2YR", "GB3YR", "GB10YR", "CA2YR", "CA3YR", "CA10YR",
        "BR2YR", "BR5YR", "BR10YR", "US2YR", "US3YR", "US5YR", "US7YR", "US10YR", "US30YR",
        "JP2YR", "JP5YR", "JP10YR"
    ]
}

# --- Common Functions ---

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def fetch_yfinance_data(symbols_dict, start, end):
    data = {}
    for category, symbols in symbols_dict.items():
        tickers = list(symbols.keys())
        # The yfinance download is exclusive of the end date, so we add a day to be inclusive.
        df = yf.download(tickers, start=start, end=end + timedelta(days=1), progress=False)
        if not df.empty:
            df.columns = [
                f"{col[0]}_{col[1]}" if isinstance(col, tuple) else col
                for col in df.columns.values
            ]
            df = df.reset_index().rename(columns={'Date': 'date'})
            df['date'] = pd.to_datetime(df['date']).dt.date
            df = df.set_index('date')
            data[category] = df
    return data

def generate_styled_table(df, title, date):
    st.subheader(f"{title} - Data for {date.strftime('%Y-%m-%d')}")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.write("Data not available for this category and date.")
        
def color_change(val):
    """Applies a color to a value based on if it is positive or negative."""
    color = "green" if val > 0 else "red" if val < 0 else "black"
    return f"color: {color}"

def calculate_and_display_changes(df_1, df_2, category):
    st.subheader(f"{category} Change")
    if df_1 is not None and df_2 is not None and not df_1.empty and not df_2.empty:
        try:
            # Drop the index to align the dataframes correctly
            df_1_close = df_1["Close"].reset_index(drop=True)
            df_2_close = df_2["Close"].reset_index(drop=True)
            changes = (
                ((df_2_close - df_1_close) / df_1_close * 100)
                .round(2)
                .to_frame(name="% Change")
            )
            # Find the original ticker names to use for the index
            ticker_list = [col.split('_')[-1] for col in df_1.columns if 'Close' in col]
            changes = changes.rename(index=dict(zip(range(len(ticker_list)), ticker_list)))

            st.dataframe(
                changes.style.applymap(color_change, subset=["% Change"]),
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Error calculating changes for {category}: {e}")
    else:
        st.write("Data not available for comparison.")

def generate_heatmap_grid(df, title):
    """Generates a color-coded grid of market indicators for a given category."""
    st.markdown(f"<h4 style='text-align: center; color: #4a69bd;'>{title} Heatmap</h4>", unsafe_allow_html=True)
    if not df.empty:
        # Create a container for the entire heatmap of a category
        with st.container(border=True):
            cols = st.columns(8)
            for i, (_, row) in enumerate(df.iterrows()):
                # Assume a 'Close_Ticker' column exists to get the value
                close_value = row.get(f'Close_{df.columns[0].split("_")[-1]}')
                
                # In this simplified version, we can't calculate a heatmap without both dates.
                # A full implementation would require a dedicated function. For now, we'll
                # just display the value from the latest date.
                st.write("Heatmap feature requires both dates for a proper comparison. Please switch to the tables view.")


# --- Page Functions ---

def yahoo_finance_page():
    st.header("Yahoo Finance Market Data")

    # Date selection for Yahoo Finance data
    if 'start_date' not in st.session_state:
        st.session_state.start_date = datetime.now().date() - timedelta(days=2)
    if 'end_date' not in st.session_state:
        st.session_state.end_date = datetime.now().date() - timedelta(days=1)
    if 'view_mode_yf' not in st.session_state:
        st.session_state.view_mode_yf = 'tables'

    col_dates = st.columns([1, 1])
    with col_dates[0]:
        start_date = st.date_input("Start Date", st.session_state.start_date, key="yf_start_date")
    with col_dates[1]:
        end_date = st.date_input("End Date", st.session_state.end_date, key="yf_end_date")
    
    if start_date > end_date:
        st.error("Error: End Date must be after or equal to Start Date.")
        return

    # Update session state
    st.session_state.start_date = start_date
    st.session_state.end_date = end_date
    
    col_buttons = st.columns([1, 1, 1])
    with col_buttons[0]:
        if st.button('Refresh Data', help="Click to fetch the latest data"):
            st.session_state.end_date = datetime.now().date() - timedelta(days=1)
            st.session_state.start_date = datetime.now().date() - timedelta(days=2)
            st.cache_data.clear()
            st.rerun()

    with col_buttons[1]:
        if st.button("Show Tables", help="Display the detailed tables"):
            st.session_state.view_mode_yf = 'tables'
            st.rerun()

    with col_buttons[2]:
        if st.button("Show Percentage Changes", help="Display a table of percentage changes"):
            st.session_state.view_mode_yf = 'changes'
            st.rerun()

    # Fetch data
    market_data_dfs = fetch_yfinance_data(SYMBOLS, start_date, end_date)
    market_data_dfs_1 = fetch_yfinance_data(SYMBOLS, start_date, start_date)
    market_data_dfs_2 = fetch_yfinance_data(SYMBOLS, end_date, end_date)
    
    if st.session_state.view_mode_yf == 'tables':
        st.header(f"Market Data Tables: {start_date.strftime('%Y-%m-%d')} vs {end_date.strftime('%Y-%m-%d')}")
        for category in SYMBOLS.keys():
            df_start = market_data_dfs_1.get(category)
            df_end = market_data_dfs_2.get(category)
            if df_start is not None and df_end is not None:
                generate_styled_table(df_start, category, start_date)
                generate_styled_table(df_end, category, end_date)
            else:
                st.subheader(f"{category} - Data not available for one or both dates.")

    elif st.session_state.view_mode_yf == 'changes':
        st.header(f"Market Performance Changes")
        for category in SYMBOLS.keys():
            df_start = market_data_dfs_1.get(category)
            df_end = market_data_dfs_2.get(category)
            if df_start is not None and df_end is not None:
                calculate_and_display_changes(df_start, df_end, category)
            else:
                st.subheader(f"{category} - Data not available for one or both dates.")


def quanthub_api_page():
    st.header("QuantHub API Data")
    st.write("Fetching the latest data for selected instruments from the QH API.")
    
    selected_category = st.selectbox(
        "Select an Instrument Category:",
        list(QH_TICKERS.keys()),
        key="qh_category_select"
    )
    
    if selected_category:
        instruments = QH_TICKERS[selected_category]
        if instruments:
            # Fetch data using the new function
            qh_df = get_qh_api_data(instruments)
            if not qh_df.empty:
                st.subheader(f"OHLC Data for {selected_category}")
                st.dataframe(qh_df, use_container_width=True)
            else:
                st.write("Could not retrieve data for the selected instruments.")


# --- Main App Logic (Multipage) ---
with st.sidebar:
    st.header("Navigation")
    page_selection = st.selectbox("Choose a Data Source:", ["Yahoo Finance", "QuantHub API"])

if page_selection == "Yahoo Finance":
    yahoo_finance_page()
elif page_selection == "QuantHub API":
    quanthub_api_page()
