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


# --- Yahoo Finance Data Configuration (from user's data.py file) ---

SYMBOLS = {
    'Stock Indices': {
        '^GSPC': 'S&P 500', '^IXIC': 'NASDAQ Composite', '^FTSE': 'FTSE 100 (UK)',
        '^N225': 'Nikkei 225 (Japan)', '^GDAXI': 'DAX 30 (Germany)', '^NSEI': 'Nifty 50 (India)',
        '^BVSP': 'Bovespa (Brazil)', '^MXX': 'IPC Mexico', '^HSI': 'Hang Seng (Hong Kong)',
        '^STOXX50E': 'Euro Stoxx 50', '^SETI': 'SET Index (Thailand)', '^ATH': 'Athex Composite (Greece)',
        'FTSEMIB.MI': 'FTSE MIB (Italy)', '^WIG20': 'WIG20 (Poland)', '^FCHI': 'CAC 40 (France)',
        '^KS11': 'KOSPI (South Korea)', 'IMOEX.ME': 'MOEX (Russia)', '^GSPTSE': 'S&P/TSX (Canada)',
        '^AXJO': 'S&P/ASX 200 (Australia)', '^PSi': 'PSEi (Philippines)', '^AEX': 'AEX (Netherlands)',
        '^TWII': 'TAIEX (Taiwan)', '^STI': 'Straits Times (Singapore)', '^BUX': 'BUX (Hungary)',
        'XU100.IS': 'BIST 100 (Turkey)', '^OMX': 'OMX Stockholm 30 (Sweden)',
    },
    'Currencies': {
        'DX-Y.NYB': 'US Dollar Index (DXY)', 'EURUSD=X': 'Euro/USD', 'JPY=X': 'USD/JPY',
        'GBPUSD=X': 'British Pound/USD', 'INR=X': 'USD/INR', 'CNY=X': 'USD/CNY',
        'AUDUSD=X': 'Australian Dollar/USD', 'BRL=X': 'USD/BRL', 'MXN=X': 'USD/MXN',
        'CAD=X': 'USD/CAD', 'NZD=X': 'NZD/USD', 'ZAR=X': 'USD/ZAR', 'CHF=X': 'USD/CHF',
        'PHP=X': 'USD/PHP'
    },
    'Commodities': {
        'CL=F': 'Crude Oil (WTI)', 'BZ=F': 'Brent Crude Oil', 'NG=F': 'Natural Gas',
        'HO=F': 'Heating Oil', 'GC=F': 'Gold', 'SI=F': 'Silver', 'PL=F': 'Platinum',
        'HG=F': 'Copper', 'ZS=F': 'Soybeans', 'ZL=F': 'Soybean Oil', 'LE=F': 'Cattle',
        'ZC=F': 'Corn', 'ZW=F': 'Wheat', 'KC=F': 'Coffee', 'CC=F': 'Cocoa',
        'OJ=F': 'Orange Juice',
    },
    'Government Yields': {
        '^TNX': 'US 10-Year Yield', '^FVX': 'US 5-Year Yield', '^TYX': 'US 30-Year Yield',
        '^GILT10Y': 'UK 10-Year Yield', '^IN10Y': 'India 10-Year Yield',
        '^AU10Y': 'Australia 10-Year Yield', '^CGB10Y': 'Canada 10-Year Yield',
        '^JGB10Y': 'Japan 10-Year Yield', '^FR10Y': 'France 10-Year Yield',
        '^GDBR10Y': 'Germany 10-Year Yield', '^BRB10Y': 'Brazil 10-Year Yield'
    }
}
INVERTED_CURRENCIES = ['EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'NZD=X', 'CHF=X']

# --- Common Functions (Updated from data.py) ---

@st.cache_data(ttl=3600)
def fetch_all_data(end_date):
    """Fetches market data for a given end date and returns a dictionary of DataFrames."""
    category_dataframes = {}

    for category_name, category_symbols in SYMBOLS.items():
        data_list = []
        for symbol, name in category_symbols.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=end_date - timedelta(days=10), end=end_date + timedelta(days=1))
                
                if not hist.empty and len(hist['Close'].dropna()) >= 2:
                    close_prices = hist['Close'].dropna()
                    
                    last_close = close_prices.iloc[-1]
                    previous_close = close_prices.iloc[-2]
                    
                    # Invert the values and name for currencies quoted as XXX/USD for correct interpretation
                    if category_name == 'Currencies' and symbol in INVERTED_CURRENCIES:
                        if last_close != 0 and previous_close != 0:
                            last_close = 1 / last_close
                            previous_close = 1 / previous_close
                            name_parts = name.split('/')
                            if len(name_parts) == 2:
                                name = f'USD/{name_parts[0]}'
                            else:
                                name = f'USD/{name}'

                    change = last_close - previous_close
                    percent_change = (change / previous_close) * 100
                    
                    last_day_data = hist.iloc[-1]
                    previous_day_data = hist.iloc[-2]
                    
                    if category_name == 'Currencies' and symbol in INVERTED_CURRENCIES:
                        if last_day_data['Open'] != 0: last_day_data['Open'] = 1 / last_day_data['Open']
                        if last_day_data['High'] != 0: last_day_data['High'] = 1 / last_day_data['High']
                        if last_day_data['Low'] != 0: last_day_data['Low'] = 1 / last_day_data['Low']

                    dates = {
                        'previous_close_date': previous_day_data.name.strftime('%Y-%m-%d'),
                        'last_close_date': last_day_data.name.strftime('%Y-%m-%d')
                    }
                    
                    data_list.append({
                        'Indicator': name,
                        'Category': category_name,
                        'Previous Close': previous_close,
                        'Last Close': last_close,
                        'Open': last_day_data['Open'],
                        'High': last_day_data['High'],
                        'Low': last_day_data['Low'],
                        'Change ($)': change,
                        'Change (%)': percent_change,
                        **dates
                    })
                else:
                    data_list.append({
                        'Indicator': name,
                        'Category': category_name,
                        'Previous Close': np.nan, 'Last Close': np.nan,
                        'Open': np.nan, 'High': np.nan, 'Low': np.nan,
                        'Change ($)': np.nan, 'Change (%)': np.nan,
                        'previous_close_date': 'N/A', 'last_close_date': 'N/A'
                    })
            except Exception as e:
                data_list.append({
                    'Indicator': name,
                    'Category': category_name,
                    'Previous Close': np.nan, 'Last Close': np.nan,
                    'Open': np.nan, 'High': np.nan, 'Low': np.nan,
                    'Change ($)': np.nan, 'Change (%)': np.nan,
                    'previous_close_date': 'N/A', 'last_close_date': 'N/A'
                })

        if data_list:
            df = pd.DataFrame(data_list)
            category_dataframes[category_name] = df

    return category_dataframes

def color_change(val):
    """Applies a color to a value based on if it is positive or negative."""
    if isinstance(val, (int, float)):
        if val > 0:
            return 'color: green;'
        elif val < 0:
            return 'color: red;'
    return 'color: black;'

def generate_styled_table(df, category, date):
    """Generates a styled Streamlit dataframe table for a given category."""
    st.markdown(f"<h4 style='text-align: center; color: #4a69bd;'>{category} as of {date.strftime('%Y-%m-%d')}</h4>", unsafe_allow_html=True)

    if not df.empty and not df.isnull().all().all():
        df_display = df.dropna(subset=['Change (%)']).sort_values("Change (%)", ascending=False)
        
        previous_close_date = df_display['previous_close_date'].iloc[0] if not df_display.empty else 'N/A'
        last_close_date = df_display['last_close_date'].iloc[0] if not df_display.empty else 'N/A'
        
        close_format = "${:,.4f}" if 'Currencies' in category else "${:,.2f}"
        change_format = "{:+.4f}" if 'Currencies' in category else "{:+.2f}"
        
        display_df = df_display.drop(columns=['previous_close_date', 'last_close_date', 'Category']).rename(columns={
            'Previous Close': f'Previous Close ({previous_close_date})',
            'Last Close': f'Last Close ({last_close_date})',
            'Open': f'Open ({last_close_date})',
            'High': f'High ({last_close_date})',
            'Low': f'Low ({last_close_date})'
        })
        
        format_dict = {
            f'Previous Close ({previous_close_date})': close_format,
            f'Last Close ({last_close_date})': close_format,
            f'Open ({last_close_date})': close_format,
            f'High ({last_close_date})': close_format,
            f'Low ({last_close_date})': close_format,
            'Change ($)': change_format,
            'Change (%)': "{:+.2f}%"
        }

        styled_df = display_df.style.applymap(color_change, subset=['Change ($)', 'Change (%)']).format(
            format_dict, na_rep='N/A'
        )
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.warning(f"No data available for {category}.")

def generate_heatmap_grid(df, title):
    """Generates a color-coded grid of market indicators for a given category."""
    st.markdown(f"<h4 style='text-align: center; color: #4a69bd;'>{title} Heatmap</h4>", unsafe_allow_html=True)
    if not df.empty:
        sorted_df = df.dropna(subset=["Change (%)"]).sort_values("Change (%)", ascending=False)
        
        with st.container(border=True):
            cols = st.columns(8)
            for i, (_, row) in enumerate(sorted_df.iterrows()):
                pct = row["Change (%)"]
                color = (
                    f"rgba(0, 200, 0, {min(1, abs(pct)/3)})" if pct > 0 else
                    f"rgba(200, 0, 0, {min(1, abs(pct)/3)})"
                )
                
                cols[i % 8].markdown(
                    f"""
                    <div class='heatmap-item' style='background-color: {color};'>
                        {row["Indicator"]}<br>{pct:+.2f}%
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

# --- Page Functions ---

def yahoo_finance_page():
    st.markdown("""
        <style>
        .stApp {
            background-color: #0e1117;
            color: #f0f2f6;
        }
        .main-header {
            font-size: 2.5em;
            font-weight: bold;
            color: #f0f2f6;
            text-align: center;
            margin-bottom: 0.5em;
        }
        .subheader {
            font-size: 1.2em;
            color: #f0f2f6;
            text-align: center;
            margin-bottom: 1.5em;
        }
        .stDataFrame {
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            background-color: #26292e;
            color: #f0f2f6;
        }
        .stButton > button {
            background-color: #26292e;
            color: #f0f2f6;
            font-weight: bold;
            border-radius: 8px;
            border: 1px solid #4a69bd;
        }
        .stButton > button:hover {
            background-color: #4a69bd;
            color: white;
        }
        h2 {
            color: #f0f2f6;
            border-bottom: 2px solid #4a69bd;
            padding-bottom: 5px;
        }
        .stplotly {
            height: 100% !important;
            width: 100% !important;
        }
        .category-title {
            text-align: center;
            font-weight: bold;
            padding-top: 10px;
            padding-bottom: 5px;
            border-bottom: 2px solid #4a69bd;
        }
        .heatmap-item {
            padding: 8px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 5px;
            font-size: 0.75rem;
            font-weight: bold;
            color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        </style>
        <div class="main-header">Global Market Dashboard</div>
        <div class="subheader">Daily changes for key stocks, commodities, currencies, and yields</div>
    """, unsafe_allow_html=True)
    
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = 'tables'
        st.session_state.start_date = datetime.now().date() - timedelta(days=2)
        st.session_state.end_date = datetime.now().date() - timedelta(days=1)

    col1, col2 = st.columns(2)
    with col1:
        date_1 = st.date_input("Select Start Date", value=st.session_state.start_date)
    with col2:
        date_2 = st.date_input("Select End Date", value=st.session_state.end_date)

    with st.spinner(f'Fetching market data for {date_1.strftime("%Y-%m-%d")} and {date_2.strftime("%Y-%m-%d")}...'):
        market_data_dfs_1 = fetch_all_data(date_1)
        market_data_dfs_2 = fetch_all_data(date_2)

    col_buttons = st.columns([1,1,1,1])
    with col_buttons[0]:
        if st.button('Refresh Data', help="Click to fetch the latest data"):
            st.session_state.end_date = datetime.now().date() - timedelta(days=1)
            st.session_state.start_date = datetime.now().date() - timedelta(days=2)
            st.cache_data.clear()
            st.rerun()
    with col_buttons[2]:
        if st.button("Show Tables", help="Display the detailed tables"):
            st.session_state.view_mode = 'tables'
            st.rerun()
    with col_buttons[3]:
        if st.button("Show Heatmap", help="Display a heatmap grid of daily percentage changes"):
            st.session_state.view_mode = 'heatmap'
            st.rerun()

    if st.session_state.view_mode == 'tables':
        st.header(f"Market Performance: {date_1.strftime('%Y-%m-%d')} vs {date_2.strftime('%Y-%m-%d')}")
        for category in SYMBOLS.keys():
            df2 = market_data_dfs_2.get(category)
            if df2 is not None:
                generate_styled_table(df2, category, date_2)
                
    elif st.session_state.view_mode == 'heatmap':
        st.header(f"Market Performance Heatmap: {date_1.strftime('%Y-%m-%d')} vs {date_2.strftime('%Y-%m-%d')}")
        for category in SYMBOLS.keys():
            df2 = market_data_dfs_2.get(category)
            if df2 is not None:
                generate_heatmap_grid(df2, category)


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
