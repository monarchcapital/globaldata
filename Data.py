import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

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
        '^STOXX50E': 'Euro Stoxx 50',
        '^SETI': 'SET Index (Thailand)',
        '^ATH': 'Athex Composite (Greece)',
        'FTSEMIB.MI': 'FTSE MIB (Italy)',
        '^WIG20': 'WIG20 (Poland)',
        '^FCHI': 'CAC 40 (France)',
        '^KS11': 'KOSPI (South Korea)',
        'IMOEX.ME': 'MOEX (Russia)',
        '^GSPTSE': 'S&P/TSX (Canada)',
        '^AXJO': 'S&P/ASX 200 (Australia)',
        '^PSi': 'PSEi (Philippines)',
        '^AEX': 'AEX (Netherlands)',
        '^TWII': 'TAIEX (Taiwan)',
        '^STI': 'Straits Times (Singapore)',
        '^BUX': 'BUX (Hungary)',
        'XU100.IS': 'BIST 100 (Turkey)',
        '^OMX': 'OMX Stockholm 30 (Sweden)',
    },
    'Currencies': {
        'EURUSD=X': 'Euro/USD',
        'JPY=X': 'USD/JPY',
        'GBPUSD=X': 'British Pound/USD',
        'INR=X': 'USD/INR',
        'CNY=X': 'USD/CNY',
        'AUDUSD=X': 'Australian Dollar/USD',
        'BRL=X': 'USD/BRL',
        'MXN=X': 'USD/MXN',
        'CAD=X': 'USD/CAD',
        'NZD=X': 'USD/NZD',
        'ZAR=X': 'USD/ZAR',
        'CHF=X': 'USD/CHF',
        'PHP=X': 'USD/PHP'
    },
    'Commodities': {
        'CL=F': 'Crude Oil (WTI)',
        'BZ=F': 'Brent Crude Oil',
        'NG=F': 'Natural Gas',
        'HO=F': 'Heating Oil',
        'GC=F': 'Gold',
        'SI=F': 'Silver',
        'PL=F': 'Platinum',
        'HG=F': 'Copper',
        'ZS=F': 'Soybeans',
        'ZL=F': 'Soybean Oil',
        'LE=F': 'Cattle',
        'ZC=F': 'Corn',
        'ZW=F': 'Wheat',
        'KC=F': 'Coffee',
        'CC=F': 'Cocoa',
        'OJ=F': 'Orange Juice',
    },
    'Government Yields': {
        '^TNX': 'US 10-Year Yield',
        '^FVX': 'US 5-Year Yield',
        '^TYX': 'US 30-Year Yield',
        '^GILT10Y': 'UK 10-Year Yield',
        '^IN10Y': 'India 10-Year Yield',
        '^AU10Y': 'Australia 10-Year Yield',
        '^CGB10Y': 'Canada 10-Year Yield',
        '^JGB10Y': 'Japan 10-Year Yield',
        '^FR10Y': 'France 10-Year Yield',
        '^GDBR10Y': 'Germany 10-Year Yield',
        '^BRB10Y': 'Brazil 10-Year Yield'
    }
}

# Mapping for shorter, more concise names for the treemap display
SHORT_NAMES_MAP = {
    'S&P 500': 'S&P 500',
    'NASDAQ Composite': 'NASDAQ',
    'FTSE 100 (UK)': 'UK',
    'Nikkei 225 (Japan)': 'Japan',
    'DAX 30 (Germany)': 'Germany',
    'Nifty 50 (India)': 'India',
    'Bovespa (Brazil)': 'Brazil',
    'IPC Mexico': 'Mexico',
    'Hang Seng (Hong Kong)': 'Hong Kong',
    'Euro Stoxx 50': 'Euro Stoxx 50',
    'SET Index (Thailand)': 'Thailand',
    'Athex Composite (Greece)': 'Greece',
    'FTSE MIB (Italy)': 'Italy',
    'WIG20 (Poland)': 'Poland',
    'CAC 40 (France)': 'France',
    'KOSPI (South Korea)': 'S. Korea',
    'MOEX (Russia)': 'Russia',
    'S&P/TSX (Canada)': 'Canada',
    'S&P/ASX 200 (Australia)': 'Australia',
    'PSEi (Philippines)': 'Philippines',
    'AEX (Netherlands)': 'Netherlands',
    'TAIEX (Taiwan)': 'Taiwan',
    'Straits Times (Singapore)': 'Singapore',
    'BUX (Hungary)': 'Hungary',
    'BIST 100 (Turkey)': 'Turkey',
    'OMX Stockholm 30 (Sweden)': 'Sweden',
    'Euro/USD': 'EUR/USD',
    'USD/JPY': 'USD/JPY',
    'British Pound/USD': 'GBP/USD',
    'USD/INR': 'USD/INR',
    'USD/CNY': 'USD/CNY',
    'Australian Dollar/USD': 'AUD/USD',
    'USD/BRL': 'USD/BRL',
    'USD/MXN': 'USD/MXN',
    'USD/CAD': 'USD/CAD',
    'NZD=X': 'NZD/USD',
    'USD/ZAR': 'USD/ZAR',
    'USD/CHF': 'USD/CHF',
    'USD/PHP': 'USD/PHP',
    'Crude Oil (WTI)': 'Crude Oil',
    'Brent Crude Oil': 'Brent Crude',
    'Natural Gas': 'Nat Gas',
    'Heating Oil': 'Heating Oil',
    'Gold': 'Gold',
    'Silver': 'Silver',
    'Platinum': 'Platinum',
    'Copper': 'Copper',
    'Soybeans': 'Soybeans',
    'Soybean Oil': 'Soy Oil',
    'Cattle': 'Cattle',
    'Corn': 'Corn',
    'Wheat': 'Wheat',
    'Coffee': 'Coffee',
    'Cocoa': 'Cocoa',
    'Orange Juice': 'Orange Juice',
    'US 10-Year Yield': 'US 10Y',
    'US 5-Year Yield': 'US 5Y',
    'US 30-Year Yield': 'US 30Y',
    'UK 10-Year Yield': 'UK 10Y',
    'India 10-Year Yield': 'India 10Y',
    'Australia 10-Year Yield': 'Australia 10Y',
    'Canada 10-Year Yield': 'Canada 10Y',
    'Japan 10-Year Yield': 'Japan 10Y',
    'France 10-Year Yield': 'France 10Y',
    'Germany 10-Year Yield': 'Germany 10Y',
    'Brazil 10-Year Yield': 'Brazil 10Y',
}

# Main Streamlit App Layout and Logic
st.set_page_config(layout="wide", page_title="Global Market Dashboard")

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
    .stButton>button {
        background-color: #4a69bd;
        color: white;
        font-weight: bold;
        border-radius: 8px;
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
    </style>
    <div class="main-header">Global Market Dashboard</div>
    <div class="subheader">Daily changes for key stocks, commodities, currencies, and yields</div>
""", unsafe_allow_html=True)


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
                    
                    change = last_close - previous_close
                    percent_change = (change / previous_close) * 100
                    
                    dates = {
                        'previous_close_date': close_prices.index[-2].strftime('%Y-%m-%d'),
                        'last_close_date': close_prices.index[-1].strftime('%Y-%m-%d')
                    }
                    
                    data_list.append({
                        'Indicator': name,
                        'Category': category_name,
                        'Previous Close': previous_close,
                        'Last Close': last_close,
                        'Change ($)': change,
                        'Change (%)': percent_change,
                        **dates
                    })
                else:
                    data_list.append({
                        'Indicator': name,
                        'Category': category_name,
                        'Previous Close': np.nan,
                        'Last Close': np.nan,
                        'Change ($)': np.nan,
                        'Change (%)': np.nan,
                        'previous_close_date': 'N/A',
                        'last_close_date': 'N/A'
                    })
            except Exception as e:
                data_list.append({
                    'Indicator': name,
                    'Category': category_name,
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

# Function to apply a color to a value based on if it is positive or negative.
def color_change(val):
    """Applies a color to a value based on if it is positive or negative."""
    if isinstance(val, (int, float)):
        if val > 0:
            return 'color: green;'
        elif val < 0:
            return 'color: red;'
    return 'color: black;'

# Function to generate a heatmap-like grid for a given DataFrame and title
def generate_heatmap_grid(df, title):
    """
    Generates a color-coded grid of market indicators for a given category.
    The blocks are colored based on the daily percentage change.
    """
    st.markdown(f"<h4 style='text-align: center; color: #4a69bd;'>{title}</h4>", unsafe_allow_html=True)
    
    # Filter out rows with NaN values in the change column
    df = df.dropna(subset=["Change (%)"])
    
    # Sort the dataframe by percentage change in descending order
    df = df.sort_values("Change (%)", ascending=False)

    # Create a grid with 4 columns
    cols = st.columns(4)
    for i, (_, row) in enumerate(df.iterrows()):
        col = cols[i % 4]
        pct = row["Change (%)"]
        
        # Determine the background color based on the percentage change
        # The alpha channel is adjusted to create a heat-map effect
        color = (
            f"rgba(0, 200, 0, {min(1, abs(pct)/3)})" if pct > 0 else
            f"rgba(200, 0, 0, {min(1, abs(pct)/3)})"
        )
        
        # Determine the font color for readability
        font_color = "black" if abs(pct) < 2 else "white"
        
        # Use Markdown with inline CSS to create the colored block
        col.markdown(
            f"""
            <div style='
                background-color: {color};
                color: {font_color};
                padding: 10px;
                border-radius: 10px;
                margin: 5px 0;
                text-align: center;
                font-size: 0.9rem;
                font-weight: bold;
            '>
                {row["Indicator"]}<br>{pct:+.2f}%
            </div>
            """,
            unsafe_allow_html=True
        )


# Initialize session state for treemap/heatmap view
if 'show_treemap' not in st.session_state:
    st.session_state.show_treemap = True # Set to True by default to show the treemap on load

# Set default dates to today and yesterday
today = datetime.now().date()
yesterday = today - timedelta(days=1)
two_days_ago = today - timedelta(days=2)

# Display the date pickers
col1, col2 = st.columns(2)
with col1:
    date_1 = st.date_input("Select Start Date", two_days_ago)
with col2:
    date_2 = st.date_input("Select End Date", yesterday)

# Fetch and display data for both dates
with st.spinner(f'Fetching market data for {date_1.strftime("%Y-%m-%d")} and {date_2.strftime("%Y-%m-%d")}...'):
    market_data_dfs_1 = fetch_all_data(date_1)
    market_data_dfs_2 = fetch_all_data(date_2)

# Control button layout
col_buttons = st.columns([1,1,1])
with col_buttons[0]:
    if st.button('Refresh Data', help="Click to fetch the latest data"):
        st.cache_data.clear()
        st.rerun()
with col_buttons[2]:
    if not st.session_state.show_treemap:
        if st.button("Show Treemap", help="Display a treemap of daily percentage changes"):
            st.session_state.show_treemap = True
            st.rerun()
    else:
        if st.button("Back to Dashboard", help="Display a grid of daily percentage changes"):
            st.session_state.show_treemap = False
            st.rerun()

# Conditional rendering based on session state
if st.session_state.show_treemap:
    # Combine all data into a single DataFrame for the treemap
    all_data_for_treemap = pd.concat(market_data_dfs_2.values(), ignore_index=True)
    
    # Filter out rows with NaN values
    treemap_data = all_data_for_treemap.dropna(subset=['Change (%)']).copy()
    
    # Create the treemap
    fig = go.Figure(go.Treemap(
        labels=treemap_data['Indicator'],
        parents=treemap_data['Category'],
        values=np.abs(treemap_data['Change (%)']),
        marker_colors=treemap_data['Change (%)'],
        marker_colorscale='RdYlGn',
        marker_cmin=-5,  # Set min value for color scale
        marker_cmax=5,   # Set max value for color scale
        hovertemplate='<b>%{label}</b><br>Change: %{color:.2f}%<extra></extra>',
        textinfo="label+value",
        texttemplate="%{label}<br>%{value:.2f}%",
        textfont={"color": ["#f0f2f6"]}, # Set text color to white for contrast
        textposition="middle center",
        name="",
    ))

    # Update the layout and traces to match the user's requested style
    fig.update_layout(
        margin = dict(t=50, l=25, r=25, b=25),
        paper_bgcolor="#0e1117",
        title={
            'text': f"Daily Percentage Change Treemap for {date_2.strftime('%Y-%m-%d')}",
            'y':0.95, 'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24, 'color': '#f0f2f6'}
        },
        font=dict(color='#f0f2f6'),
        title_font_color="#f0f2f6"
    )
    
    # The image also had category labels. To add these, you can use annotation
    fig.add_annotation(
        text="Commodities",
        xref="paper", yref="paper",
        x=0.08, y=1.02,
        showarrow=False,
        font=dict(color="#f0f2f6", size=14)
    )
    fig.add_annotation(
        text="Stock Indices",
        xref="paper", yref="paper",
        x=0.45, y=1.02,
        showarrow=False,
        font=dict(color="#f0f2f6", size=14)
    )
    fig.add_annotation(
        text="Currencies",
        xref="paper", yref="paper",
        x=0.8, y=1.02,
        showarrow=False,
        font=dict(color="#f0f2f6", size=14)
    )
    fig.add_annotation(
        text="Government Yields",
        xref="paper", yref="paper",
        x=0.9, y=0.1,
        showarrow=False,
        font=dict(color="#f0f2f6", size=14)
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
else:
    # Display the new heatmap grid
    st.header(f"Market Performance Heatmap")
    
    for category in SYMBOLS.keys():
        df2 = market_data_dfs_2.get(category)
        if df2 is not None:
            generate_heatmap_grid(df2, category)
