import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import requests
import time
from datetime import datetime, timedelta, date

st.set_page_config(page_title="Live Dashboard", page_icon="📊", layout="wide")

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .metric-card {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 8px;
  }
  .fin-card {
    background: #0f172a;
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 4px 0;
  }
  .fin-label { color: #94a3b8; font-size: 12px; margin-bottom: 2px; }
  .fin-value { color: #e2e8f0; font-size: 20px; font-weight: 700; }
  .fin-sub   { color: #64748b; font-size: 11px; }
</style>
""", unsafe_allow_html=True)

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

def fmt_large(val):
    """Format large numbers: B for billions, M for millions, T for trillions."""
    if val is None:
        return "N/A"
    try:
        val = float(val)
    except (TypeError, ValueError):
        return "N/A"
    if val >= 1e12:
        return f"${val/1e12:.2f}T"
    elif val >= 1e9:
        return f"${val/1e9:.2f}B"
    elif val >= 1e6:
        return f"${val/1e6:.2f}M"
    else:
        return f"${val:,.0f}"

@st.cache_data(ttl=3600)
def get_financials(symbol):
    """Fetch revenue, net income, and market cap for a stock."""
    try:
        ticker = yf.Ticker(symbol)
        info   = ticker.info

        # Market cap / net worth
        market_cap  = info.get("marketCap")
        # Try annual income statement
        fin = ticker.financials  # columns = fiscal year ends
        revenue    = None
        net_income = None
        if fin is not None and not fin.empty:
            if "Total Revenue" in fin.index:
                revenue = float(fin.loc["Total Revenue"].iloc[0])
            if "Net Income" in fin.index:
                net_income = float(fin.loc["Net Income"].iloc[0])

        # Profit margin
        margin = None
        if revenue and net_income:
            margin = (net_income / revenue) * 100

        return {
            "market_cap": market_cap,
            "revenue":    revenue,
            "net_income": net_income,
            "margin":     margin,
            "pe_ratio":   info.get("trailingPE"),
            "eps":        info.get("trailingEps"),
        }
    except Exception:
        return {
            "market_cap": None, "revenue": None,
            "net_income": None, "margin": None,
            "pe_ratio": None,   "eps": None,
        }

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
            "pressure": d["main"].get("pressure", 0),
            "visibility": round(d.get("visibility", 0) / 1000, 1),
            "sunrise":  datetime.fromtimestamp(d["sys"]["sunrise"]).strftime("%H:%M"),
            "sunset":   datetime.fromtimestamp(d["sys"]["sunset"]).strftime("%H:%M"),
            "uv":       d.get("uvi", "N/A"),
            "icon":     d["weather"][0]["icon"],
        }
    except Exception:
        return {
            "city": city, "temp": 0, "feels": 0, "humidity": 0,
            "wind": 0, "cond": "Unavailable", "pressure": 0,
            "visibility": 0, "sunrise": "--", "sunset": "--",
            "uv": "N/A", "icon": "01d",
        }

def get_forecast(city, days=7):
    """Returns ~3hr forecast data from OWM free tier (up to 5 days / 40 entries)."""
    url = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?q={city}&units=metric&appid={OWM_KEY}"
    )
    try:
        items = requests.get(url, timeout=10).json().get("list", [])
        rows  = []
        for i in items:
            dt = datetime.strptime(i["dt_txt"], "%Y-%m-%d %H:%M:%S")
            rows.append({
                "datetime":   dt,
                "date":       dt.date(),
                "time":       i["dt_txt"],
                "temp":       i["main"]["temp"],
                "feels":      i["main"]["feels_like"],
                "humidity":   i["main"]["humidity"],
                "wind":       round(i["wind"]["speed"] * 3.6, 1),
                "pressure":   i["main"]["pressure"],
                "cond":       i["weather"][0]["description"].title(),
                "rain":       i.get("rain", {}).get("3h", 0),
                "pop":        round(i.get("pop", 0) * 100),  # probability of precipitation %
            })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

def get_historical_weather(city, days_back=1):
    """
    OWM free tier doesn't support historical API.
    We simulate yesterday's data by slightly adjusting current data.
    For production, use a paid OWM plan or Open-Meteo (free historical).
    Uses Open-Meteo which is completely free.
    """
    # Geocode city → lat/lon using OWM
    geo_url = (
        f"https://api.openweathermap.org/geo/1.0/direct"
        f"?q={city}&limit=1&appid={OWM_KEY}"
    )
    try:
        geo = requests.get(geo_url, timeout=10).json()
        if not geo:
            return pd.DataFrame()
        lat, lon = geo[0]["lat"], geo[0]["lon"]

        # Open-Meteo historical (free, no key needed)
        end_dt   = date.today() - timedelta(days=1)
        start_dt = end_dt - timedelta(days=days_back - 1)
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&hourly=temperature_2m,relativehumidity_2m,windspeed_10m,precipitation"
            f"&start_date={start_dt}&end_date={end_dt}"
            f"&timezone=auto"
        )
        resp = requests.get(url, timeout=15).json()
        hourly = resp.get("hourly", {})
        if not hourly:
            return pd.DataFrame()
        df = pd.DataFrame({
            "datetime": pd.to_datetime(hourly["time"]),
            "temp":     hourly["temperature_2m"],
            "humidity": hourly["relativehumidity_2m"],
            "wind":     hourly["windspeed_10m"],
            "rain":     hourly["precipitation"],
        })
        df["date"] = df["datetime"].dt.date
        return df
    except Exception:
        return pd.DataFrame()

# ════════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════════

st.title("📊 Live Data Dashboard")
st.caption(
    f"Last updated: {datetime.now().strftime('%H:%M:%S  %d %b %Y')}  "
    f"|  Next refresh in 5 min"
)

tab1, tab2 = st.tabs(["📈  Stocks", "🌦  Weather"])

# ════════════════════════════════════════════════════════════════
# TAB 1 – STOCKS
# ════════════════════════════════════════════════════════════════
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
            x=hist["Date"], y=hist["Close"],
            mode="lines+markers", name=sym
        ))
    fig.update_layout(
        title="7-Day Closing Prices",
        xaxis_title="Date", yaxis_title="Price (USD)",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True, key="stock_line")

    # ── NEW: Revenue / Net Income / Market Cap / Margin ──────────────
    st.subheader("💼 Company Financials  (Latest Annual)")
    fin_cols = st.columns(len(STOCKS))
    for i, sym in enumerate(STOCKS):
        fin = get_financials(sym)
        with fin_cols[i]:
            st.markdown(f"### {sym}")
            st.markdown(f"""
            <div class='fin-card'>
              <div class='fin-label'>Market Cap (Net Worth)</div>
              <div class='fin-value'>{fmt_large(fin['market_cap'])}</div>
            </div>
            <div class='fin-card'>
              <div class='fin-label'>Annual Revenue</div>
              <div class='fin-value'>{fmt_large(fin['revenue'])}</div>
            </div>
            <div class='fin-card'>
              <div class='fin-label'>Net Income (Profit)</div>
              <div class='fin-value'>{fmt_large(fin['net_income'])}</div>
            </div>
            <div class='fin-card'>
              <div class='fin-label'>Profit Margin</div>
              <div class='fin-value'>{f"{fin['margin']:.1f}%" if fin['margin'] else "N/A"}</div>
            </div>
            <div class='fin-card'>
              <div class='fin-label'>P/E Ratio</div>
              <div class='fin-value'>{f"{fin['pe_ratio']:.1f}x" if fin['pe_ratio'] else "N/A"}</div>
            </div>
            <div class='fin-card'>
              <div class='fin-label'>EPS (Trailing)</div>
              <div class='fin-value'>{f"${fin['eps']:.2f}" if fin['eps'] else "N/A"}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Comparison bar charts – Revenue & Net Income
    fin_rows = []
    for sym in STOCKS:
        f = get_financials(sym)
        fin_rows.append({
            "Symbol":     sym,
            "Revenue":    f["revenue"] or 0,
            "Net Income": f["net_income"] or 0,
            "Market Cap": f["market_cap"] or 0,
        })
    df_fin = pd.DataFrame(fin_rows)

    c1, c2 = st.columns(2)
    with c1:
        fig_rev = px.bar(
            df_fin, x="Symbol", y="Revenue",
            title="Annual Revenue Comparison",
            color="Revenue", color_continuous_scale="Teal",
            labels={"Revenue": "Revenue (USD)"}
        )
        fig_rev.update_traces(
            hovertemplate="%{x}: %{customdata}",
            customdata=[fmt_large(v) for v in df_fin["Revenue"]]
        )
        st.plotly_chart(fig_rev, use_container_width=True, key="fin_rev")

    with c2:
        fig_ni = px.bar(
            df_fin, x="Symbol", y="Net Income",
            title="Net Income Comparison",
            color="Net Income", color_continuous_scale="Greens",
            labels={"Net Income": "Net Income (USD)"}
        )
        fig_ni.update_traces(
            hovertemplate="%{x}: %{customdata}",
            customdata=[fmt_large(v) for v in df_fin["Net Income"]]
        )
        st.plotly_chart(fig_ni, use_container_width=True, key="fin_ni")

    # Market cap
    fig_mc = px.bar(
        df_fin, x="Symbol", y="Market Cap",
        title="Market Capitalisation (Net Worth) Comparison",
        color="Market Cap", color_continuous_scale="Purples",
        labels={"Market Cap": "Market Cap (USD)"}
    )
    fig_mc.update_traces(
        hovertemplate="%{x}: %{customdata}",
        customdata=[fmt_large(v) for v in df_fin["Market Cap"]]
    )
    st.plotly_chart(fig_mc, use_container_width=True, key="fin_mc")

    st.divider()

    # Volatility bar chart
    vol_data = []
    for sym, hist in histories.items():
        daily_range = ((hist["High"] - hist["Low"]) / hist["Close"] * 100).mean()
        vol_data.append({"symbol": sym, "avg_range_%": round(float(daily_range), 2)})

    df_vol = pd.DataFrame(vol_data)
    fig_vol = px.bar(
        df_vol, x="symbol", y="avg_range_%",
        title="Average Daily Volatility – High/Low Spread (%)",
        color="avg_range_%", color_continuous_scale="Reds"
    )
    st.plotly_chart(fig_vol, use_container_width=True, key="stock_vol")

    # Volatility alerts
    st.subheader("Volatility Alerts")
    any_alert = False
    for sym, hist in histories.items():
        if len(hist) >= 2:
            close_data = hist["Close"]
            if hasattr(close_data, "columns"):
                close_data = close_data.iloc[:, 0]
            chg = float(close_data.pct_change().iloc[-1]) * 100
            if chg > 2:
                st.warning(f"{sym}: {chg:.2f}% move – above 2% threshold")
                any_alert = True
    if not any_alert:
        st.success("All stocks within normal range.")

# ════════════════════════════════════════════════════════════════
# TAB 2 – WEATHER
# ════════════════════════════════════════════════════════════════
with tab2:

    weather_all = [get_weather(c) for c in CITIES]

    # ── City selector ──────────────────────────────────────────
    selected_city = st.selectbox("🏙️ Select city for detailed view", CITIES, index=0)

    # ── Metric cards ───────────────────────────────────────────
    w_cols = st.columns(len(CITIES))
    for i, w in enumerate(weather_all):
        w_cols[i].metric(w["city"], f"{w['temp']}°C", w["cond"])
        w_cols[i].caption(
            f"Feels {w['feels']}°C  |  Humidity {w['humidity']}%  |  Wind {w['wind']} km/h"
        )

    st.divider()

    # ── Detailed cards for selected city ──────────────────────
    sel = next(w for w in weather_all if w["city"] == selected_city)
    st.subheader(f"📍 {selected_city} – Detailed Conditions")

    d1, d2, d3, d4, d5, d6 = st.columns(6)
    d1.metric("🌡 Temperature",   f"{sel['temp']}°C")
    d2.metric("🤔 Feels Like",    f"{sel['feels']}°C")
    d3.metric("💧 Humidity",      f"{sel['humidity']}%")
    d4.metric("💨 Wind Speed",    f"{sel['wind']} km/h")
    d5.metric("🔭 Visibility",    f"{sel['visibility']} km")
    d6.metric("🌀 Pressure",      f"{sel['pressure']} hPa")

    s1, s2 = st.columns(2)
    s1.metric("🌅 Sunrise", sel["sunrise"])
    s2.metric("🌇 Sunset",  sel["sunset"])

    st.divider()

    # ── Calendar date filter ──────────────────────────────────
    st.subheader("📅 Date Range – Forecast & History")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        today    = date.today()
        min_date = today - timedelta(days=6)   # OWM gives ~5d history via open-meteo
        max_date = today + timedelta(days=4)   # OWM free gives ~5d future
        date_range = st.date_input(
            "Select date range",
            value=(today - timedelta(days=1), today + timedelta(days=2)),
            min_value=min_date,
            max_value=max_date,
            help="Past dates: historical data (Open-Meteo). Future dates: OWM forecast."
        )
    with col_f2:
        hourly_granularity = st.selectbox(
            "Chart granularity",
            ["3-hourly", "Daily average"],
            index=1
        )

    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range if isinstance(date_range, date) else today

    # ── Gather data based on date range ───────────────────────
    forecast_df  = pd.DataFrame()
    historical_df = pd.DataFrame()

    if end_date >= today:
        forecast_df = get_forecast(selected_city)

    if start_date < today:
        days_back = (today - start_date).days
        with st.spinner("Fetching historical weather…"):
            historical_df = get_historical_weather(selected_city, days_back=days_back)

    # Combine
    combined_rows = []

    # Historical
    if not historical_df.empty:
        hist_filtered = historical_df[
            (historical_df["date"] >= start_date) &
            (historical_df["date"] < today)
        ].copy()
        if not hist_filtered.empty:
            if hourly_granularity == "Daily average":
                hist_agg = hist_filtered.groupby("date").agg(
                    temp=("temp", "mean"),
                    humidity=("humidity", "mean"),
                    wind=("wind", "mean"),
                    rain=("rain", "sum"),
                ).reset_index()
                hist_agg["datetime"] = pd.to_datetime(hist_agg["date"])
                hist_agg["source"]   = "Historical"
                hist_agg["pop"]      = 0
                combined_rows.append(hist_agg)
            else:
                hist_filtered["source"] = "Historical"
                hist_filtered["pop"]    = 0
                combined_rows.append(
                    hist_filtered[["datetime","date","temp","humidity","wind","rain","pop","source"]]
                )

    # Forecast
    if not forecast_df.empty:
        fc_filtered = forecast_df[
            (forecast_df["date"] >= max(start_date, today)) &
            (forecast_df["date"] <= end_date)
        ].copy()
        if not fc_filtered.empty:
            if hourly_granularity == "Daily average":
                fc_agg = fc_filtered.groupby("date").agg(
                    temp=("temp", "mean"),
                    humidity=("humidity", "mean"),
                    wind=("wind", "mean"),
                    rain=("rain", "sum"),
                    pop=("pop", "max"),
                ).reset_index()
                fc_agg["datetime"] = pd.to_datetime(fc_agg["date"])
                fc_agg["source"]   = "Forecast"
                combined_rows.append(fc_agg)
            else:
                fc_filtered["source"] = "Forecast"
                combined_rows.append(
                    fc_filtered[["datetime","date","temp","humidity","wind","rain","pop","source"]]
                )

    if combined_rows:
        df_all = pd.concat(combined_rows, ignore_index=True).sort_values("datetime")

        # Temperature timeline
        fig_t = go.Figure()
        for src, grp in df_all.groupby("source"):
            fig_t.add_trace(go.Scatter(
                x=grp["datetime"], y=grp["temp"],
                mode="lines+markers", name=f"Temp ({src})",
                line=dict(
                    color="tomato" if src == "Forecast" else "#f97316",
                    dash="dash" if src == "Forecast" else "solid"
                )
            ))
        fig_t.update_layout(
            title=f"Temperature Timeline – {selected_city}",
            yaxis_title="°C", hovermode="x unified"
        )
        st.plotly_chart(fig_t, use_container_width=True, key="temp_timeline")

        # Humidity + Precipitation
        fig_h = go.Figure()
        for src, grp in df_all.groupby("source"):
            fig_h.add_trace(go.Scatter(
                x=grp["datetime"], y=grp["humidity"],
                mode="lines+markers",
                name=f"Humidity ({src})",
                line=dict(
                    color="steelblue" if src == "Forecast" else "#0284c7",
                    dash="dash" if src == "Forecast" else "solid"
                )
            ))
        if "pop" in df_all.columns and df_all["pop"].max() > 0:
            fig_h.add_trace(go.Bar(
                x=df_all["datetime"],
                y=df_all["pop"],
                name="Rain Probability (%)",
                marker_color="rgba(56,189,248,0.3)",
                yaxis="y2"
            ))
        fig_h.update_layout(
            title=f"Humidity & Rain Probability – {selected_city}",
            yaxis=dict(title="Humidity (%)"),
            yaxis2=dict(title="Rain Prob. (%)", overlaying="y", side="right"),
            hovermode="x unified"
        )
        st.plotly_chart(fig_h, use_container_width=True, key="humidity_timeline")

        # Wind speed
        fig_w = go.Figure()
        for src, grp in df_all.groupby("source"):
            fig_w.add_trace(go.Scatter(
                x=grp["datetime"], y=grp["wind"],
                mode="lines+markers",
                name=f"Wind ({src})",
                fill="tozeroy",
                line=dict(
                    color="#a3e635" if src == "Forecast" else "#65a30d",
                    dash="dash" if src == "Forecast" else "solid"
                )
            ))
        fig_w.update_layout(
            title=f"Wind Speed – {selected_city}",
            yaxis_title="km/h", hovermode="x unified"
        )
        st.plotly_chart(fig_w, use_container_width=True, key="wind_timeline")

        # Data table
        with st.expander("📋 Raw data table"):
            display_cols = ["datetime","source","temp","humidity","wind","rain","pop"]
            display_cols = [c for c in display_cols if c in df_all.columns]
            st.dataframe(
                df_all[display_cols].rename(columns={
                    "datetime": "Date/Time", "source": "Source",
                    "temp": "Temp (°C)", "humidity": "Humidity (%)",
                    "wind": "Wind (km/h)", "rain": "Rain (mm)",
                    "pop": "Rain Prob. (%)"
                }),
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("No data available for the selected date range.")

    st.divider()

    # ── Summary charts (all cities) ───────────────────────────
    col_left, col_right = st.columns(2)
    df_w = pd.DataFrame(weather_all)

    with col_left:
        fig_hum = px.bar(
            df_w, x="city", y="humidity",
            title="Humidity by City (%)",
            color="humidity", color_continuous_scale="Blues"
        )
        st.plotly_chart(fig_hum, use_container_width=True, key="weather_hum")

    with col_right:
        fig_temp = px.bar(
            df_w, x="city", y="temp",
            title="Temperature by City (°C)",
            color="temp", color_continuous_scale="Oranges"
        )
        st.plotly_chart(fig_temp, use_container_width=True, key="weather_temp")

    # Wind speed all cities
    fig_wind = px.bar(
        df_w, x="city", y="wind",
        title="Wind Speed by City (km/h)",
        color="wind", color_continuous_scale="Greens"
    )
    st.plotly_chart(fig_wind, use_container_width=True, key="weather_wind")

    # ── Weather alerts ─────────────────────────────────────────
    st.subheader("⚠️ Weather Alerts")
    any_w = False
    for w in weather_all:
        if w["temp"] > 30:
            st.error(f"🔥 {w['city']}: {w['temp']}°C – extreme heat")
            any_w = True
        if w["humidity"] > 80:
            st.warning(f"💧 {w['city']}: {w['humidity']}% humidity – high moisture")
            any_w = True
        if w["wind"] > 50:
            st.warning(f"💨 {w['city']}: {w['wind']} km/h wind – strong winds")
            any_w = True
    if not any_w:
        st.success("✅ No weather alerts.")

# ════════════════════════════════════════════════════════════════
# AUTO REFRESH
# ════════════════════════════════════════════════════════════════
time.sleep(REFRESH)
st.rerun()
