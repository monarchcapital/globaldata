import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# Configuration for Indicators
SYMBOLS = {
    'Stock Indices': {
        '^GSPC': 'S&P 500',
        '^IXIC': 'NASDAQ Composite',
        '^FTSE': 'FTSE 100 (UK)',
        '^N225': 'Nikkei 225 (Japan)',
        '^GDAXI': 'DAX 30 (Germany)',
        '^NSEI': 'Nifty 50 (India)',
        '^BVSP': 'Bovespa (Brazil)',
        '^MXX': 'IPC Mexico',
        '^HSI': 'Hang Seng (Hong Kong)',
        '^STOXX50E': 'Euro Stoxx 50'
    },
    'Currencies': {
        'EURUSD=X': 'Euro/USD',
        'JPY=X': 'USD/JPY',
        'GBPUSD=X': 'British Pound/USD',
        'INR=X': 'USD/INR',
        'CNY=X': 'USD/CNY',
        'AUDUSD=X': 'Australian Dollar/USD',
        'BRL=X': 'USD/BRL',
        'MXN=X': 'USD/MXN'
    },
    'Commodities & Yields': {
        'CL=F': 'Crude Oil (WTI)',
        'GC=F': 'Gold',
        'SI=F': 'Silver',
        'HG=F': 'Copper',
        'PL=F': 'Platinum',
        '^TNX': 'US 10-Year Yield',
        '^FVX': 'US 5-Year Yield',
        '^TYX': 'US 30-Year Yield'
    }
}

# Main Streamlit App Layout and Logic
st.set_page_config(layout="wide", page_title="Global Market Dashboard")

st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117; /* Changed to a professional dark blue-gray */
        color: #f0f2f6; /* Changed text color to a lighter tone for contrast */
    }
    .main-header {
        font-size: 2.5em;
        font-weight: bold;
        color: #f0f2f6; /* Header text color changed to white */
        text-align: center;
        margin-bottom: 0.5em;
    }
    .subheader {
        font-size: 1.2em;
        color: #f0f2f6; /* Subheader text color changed to white */
        text-align: center;
        margin-bottom: 1.5em;
    }
    .stDataFrame {
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        background-color: #26292e; /* Changed to a contrasting dark gray */
        color: #f0f2f6;
    }
    .stButton>button {
        background-color: #4a69bd; /* Changed button color to a professional blue */
        color: white;
        font-weight: bold;
        border-radius: 8px;
    }
    h2 {
        color: #f0f2f6; /* Subheader color changed to white for visibility */
        border-bottom: 2px solid #4a69bd; /* Border color changed to match button */
        padding-bottom: 5px;
    }
    </style>
    <div class="main-header">Global Market Dashboard</div>
    <div class="subheader">Daily changes for key stocks, commodities, currencies, and yields</div>
""", unsafe_allow_html=True)

# Date input for the user
selected_date = st.date_input("Select a date", datetime.now().date())

# A button to manually refresh data
if st.button('Refresh Data', help="Click to fetch the latest data"):
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=3600)  # Cache for 1 hour to avoid frequent data fetching
def fetch_all_data(end_date):
    """
    Fetches market data using the yfinance library and returns a dictionary of DataFrames,
    one for each category, with detailed daily change information.
    """
    category_dataframes = {}

    for category_name, category_symbols in SYMBOLS.items():
        data_list = []
        for symbol, name in category_symbols.items():
            try:
                ticker = yf.Ticker(symbol)
                # Fetch a period ending on the selected date to find the last two trading days
                hist = ticker.history(start=end_date - timedelta(days=10), end=end_date + timedelta(days=1))
                
                if not hist.empty and len(hist['Close'].dropna()) >= 2:
                    close_prices = hist['Close'].dropna()
                    
                    last_close = close_prices.iloc[-1]
                    previous_close = close_prices.iloc[-2]
                    
                    change = last_close - previous_close
                    percent_change = (change / previous_close) * 100
                    
                    # Store dates in a temporary dictionary for later use
                    dates = {
                        'previous_close_date': close_prices.index[-2].strftime('%Y-%m-%d'),
                        'last_close_date': close_prices.index[-1].strftime('%Y-%m-%d')
                    }
                    
                    data_list.append({
                        'Indicator': name,
                        'Previous Close': previous_close,
                        'Last Close': last_close,
                        'Change ($)': change,
                        'Change (%)': percent_change,
                        **dates # Add dates to the data for later retrieval
                    })
                else:
                    data_list.append({
                        'Indicator': name,
                        'Previous Close': np.nan,
                        'Last Close': np.nan,
                        'Change ($)': np.nan,
                        'Change (%)': np.nan,
                        'previous_close_date': 'N/A',
                        'last_close_date': 'N/A'
                    })
            except Exception as e:
                st.warning(f"Could not process data for {name} ({symbol}): {e}")
                data_list.append({
                    'Indicator': name,
                    'Previous Close': np.nan,
                    'Last Close': np.nan,
                    'Change ($)': np.nan,
                    'Change (%)': np.nan,
                    'previous_close_date': 'N/A',
                    'last_close_date': 'N/A'
                })

        if data_list:
            df = pd.DataFrame(data_list)
            category_dataframes[category_name] = df

    return category_dataframes

# Use a spinner to show that data is being fetched
with st.spinner('Fetching the latest market data...'):
    market_data_dfs = fetch_all_data(selected_date)

if market_data_dfs:
    # Function to apply color based on value, returning a full CSS string
    def color_change(val):
        """Applies a color to a value based on if it is positive or negative."""
        if isinstance(val, (int, float)):
            if val > 0:
                return 'color: green;'
            elif val < 0:
                return 'color: red;'
        return 'color: black;'

    # Display the separate tables
    for category, df in market_data_dfs.items():
        st.subheader(category)
        
        # Get the dates from the first row to use for column headers
        if not df.empty:
            previous_close_date = df['previous_close_date'].iloc[0]
            last_close_date = df['last_close_date'].iloc[0]
        else:
            previous_close_date = 'N/A'
            last_close_date = 'N/A'
        
        # Determine the format string based on the category
        close_format = "${:,.4f}" if 'Currencies' in category else "${:,.2f}"
        change_format = "{:+.4f}" if 'Currencies' in category else "{:+.2f}"

        # Create a new DataFrame with the desired column headers for display
        display_df = df.drop(columns=['previous_close_date', 'last_close_date']).rename(columns={
            'Previous Close': f'Previous Close ({previous_close_date})',
            'Last Close': f'Last Close ({last_close_date})'
        })

        # Create a single format dictionary
        format_dict = {
            f'Previous Close ({previous_close_date})': close_format,
            f'Last Close ({last_close_date})': close_format,
            'Change ($)': change_format,
            'Change (%)': "{:+.2f}%"
        }
        
        # Apply the styling and formatting, ensuring to handle NaNs gracefully
        styled_df = display_df.style.applymap(color_change, subset=['Change ($)', 'Change (%)']).format(
            format_dict, na_rep='N/A'
        )
        
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

else:
    st.error("Failed to retrieve market data. Please check your internet connection or try again later.")
