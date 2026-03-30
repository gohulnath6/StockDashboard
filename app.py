import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import requests
import time
from datetime import datetime

st.set_page_config(page_title="Live Dashboard", page_icon="📊", layout="wide")

OWM_KEY = "ee79b0a9758088ad65ac95d966a2ea42"

STOCKS  = ["AAPL", "MSFT", "GOOGL", "TSLA"]
CITIES  = ["London", "Mumbai", "Tokyo", "New York"]
REFRESH = 300  # 5 minutes

# ════════════════════════════════════════════════════════════════
# STOCK FUNCTIONS
# ════════════════════════════════════════════════════════════════

def get_stock_data(symbol):
    df = yf.download(symbol, period="7d", interval="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.reset_index()
    return df

def get_latest(symbol):
    df = yf.download(symbol, period="5d", interval="1m", progress=False)
    if df.empty or len(df) < 2:
        df2 = yf.download(symbol, period="5d", interval="1d", progress=False)
        if isinstance(df2.columns, pd.MultiIndex):
            df2.columns = df2.columns.get_level_values(0)
        if df2.empty or len(df2) < 2:
            return 0.0, 0.0, 0.0
        latest = float(df2["Close"].iloc[-1])
        prev   = float(df2["Close"].iloc[-2])
        change = latest - prev
        pct    = (change / prev) * 100
        return latest, change, pct
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    latest = float(df["Close"].iloc[-1])
    prev   = float(df["Close"].iloc[-2])
    change = latest - prev
    pct    = (change / prev) * 100
    return latest, change, pct

# ════════════════════════════════════════════════════════════════
# WEATHER FUNCTIONS
# ════════════════════════════════════════════════════════════════

def get_weather(city):
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&units=metric&appid={OWM_KEY}"
    )
    try:
        d = requests.get(url, timeout=10).json()
        return {
            "city":     city,
            "temp":     round(d["main"]["temp"], 1),
            "feels":    round(d["main"]["feels_like"], 1),
            "humidity": d["main"]["humidity"],
            "wind":     round(d["wind"]["speed"] * 3.6, 1),
            "cond":     d["weather"][0]["description"].title(),
        }
    except Exception:
        return {"city": city, "temp": 0, "feels": 0,
                "humidity": 0, "wind": 0, "cond": "Unavailable"}

def get_forecast(city):
    url = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?q={city}&units=metric&cnt=7&appid={OWM_KEY}"
    )
    try:
        items = requests.get(url, timeout=10).json().get("list", [])
        return pd.DataFrame([{
            "time":     i["dt_txt"],
            "temp":     i["main"]["temp"],
            "humidity": i["main"]["humidity"],
        } for i in items])
    except Exception:
        return pd.DataFrame()

# ════════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════════

placeholder = st.empty()

while True:
    with placeholder.container():

        st.title("📊 Live Data Dashboard")
        st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S  %d %b %Y')}  |  Next refresh in 5 min")

        tab1, tab2 = st.tabs(["📈  Stocks", "🌦  Weather"])

        # ════════════════════════════════════════════════════════
        # TAB 1 - STOCKS
        # ════════════════════════════════════════════════════════
        with tab1:

            cols = st.columns(len(STOCKS))
            histories = {}
            for i, sym in enumerate(STOCKS):
                price, change, pct = get_latest(sym)
                cols[i].metric(
                    label=sym,
                    value=f"${price:.2f}",
                    delta=f"{pct:.2f}%"
                )
                histories[sym] = get_stock_data(sym)

            # 7-day line chart
            fig = go.Figure()
            for sym, hist in histories.items():
                fig.add_trace(go.Scatter(
                    x=hist["Date"],
                    y=hist["Close"],
                    mode="lines+markers",
                    name=sym
                ))
            fig.update_layout(
                title="7-Day Closing Prices",
                xaxis_title="Date",
                yaxis_title="Price (USD)",
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Volatility bar chart
            vol_data = []
            for sym, hist in histories.items():
                close_data = hist["Close"]
                if hasattr(close_data, "columns"):
                    close_data = close_data.iloc[:, 0]
                daily_range = ((hist["High"] - hist["Low"]) / hist["Close"] * 100).mean()
                vol_data.append({"symbol": sym, "avg_range_%": round(float(daily_range), 2)})

            df_vol = pd.DataFrame(vol_data)
            fig_vol = px.bar(
                df_vol, x="symbol", y="avg_range_%",
                title="Average Daily Volatility - High/Low Spread (%)",
                color="avg_range_%",
                color_continuous_scale="Reds"
            )
            st.plotly_chart(fig_vol, use_container_width=True)

            # Volatility alerts
            st.subheader("Volatility Alerts")
            any_alert = False
            for sym, hist in histories.items():
                if len(hist) >= 2:
                    close_data = hist["Close"]
                    if hasattr(close_data, "columns"):
                        close_data = close_data.iloc[:, 0]
                    pct_series = close_data.pct_change()
                    chg = float(pct_series.iloc[-1]) * 100
                    if chg > 2:
                        st.warning(f"{sym}: {chg:.2f}% move - above 2% threshold")
                        any_alert = True
            if not any_alert:
                st.success("All stocks within normal range.")

        # ════════════════════════════════════════════════════════
        # TAB 2 - WEATHER
        # ════════════════════════════════════════════════════════
        with tab2:

            weather_all = [get_weather(c) for c in CITIES]

            # Metric cards
            w_cols = st.columns(len(CITIES))
            for i, w in enumerate(weather_all):
                w_cols[i].metric(w["city"], f"{w['temp']}C", w["cond"])
                w_cols[i].caption(
                    f"Feels {w['feels']}C  |  Humidity {w['humidity']}%  |  Wind {w['wind']} km/h"
                )

            col_left, col_right = st.columns(2)

            # Humidity chart
            with col_left:
                df_w = pd.DataFrame(weather_all)
                fig_hum = px.bar(
                    df_w, x="city", y="humidity",
                    title="Humidity by City (%)",
                    color="humidity",
                    color_continuous_scale="Blues"
                )
                st.plotly_chart(fig_hum, use_container_width=True)

            # Temperature chart
            with col_right:
                fig_temp = px.bar(
                    df_w, x="city", y="temp",
                    title="Temperature by City (C)",
                    color="temp",
                    color_continuous_scale="Oranges"
                )
                st.plotly_chart(fig_temp, use_container_width=True)

            # Forecast chart
            st.subheader(f"Short-term Forecast - {CITIES[0]}")
            fc = get_forecast(CITIES[0])
            if not fc.empty:
                fig_fc = go.Figure()
                fig_fc.add_trace(go.Scatter(
                    x=fc["time"], y=fc["temp"],
                    mode="lines+markers", name="Temp C",
                    line=dict(color="tomato")
                ))
                fig_fc.add_trace(go.Scatter(
                    x=fc["time"], y=fc["humidity"],
                    mode="lines+markers", name="Humidity %",
                    line=dict(color="steelblue"), yaxis="y2"
                ))
                fig_fc.update_layout(
                    title=f"Temperature & Humidity Forecast - {CITIES[0]}",
                    yaxis=dict(title="Temp (C)"),
                    yaxis2=dict(title="Humidity (%)", overlaying="y", side="right"),
                    hovermode="x unified"
                )
                st.plotly_chart(fig_fc, use_container_width=True)

            # Weather alerts
            st.subheader("Weather Alerts")
            any_w = False
            for w in weather_all:
                if w["temp"] > 30:
                    st.error(f"{w['city']}: {w['temp']}C - extreme heat")
                    any_w = True
                if w["humidity"] > 80:
                    st.warning(f"{w['city']}: {w['humidity']}% humidity - high moisture")
                    any_w = True
            if not any_w:
                st.success("No weather alerts.")

    time.sleep(REFRESH)