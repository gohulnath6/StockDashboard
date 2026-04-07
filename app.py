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
  .fin-card {
    background: #0f172a;
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 4px 0;
  }
  .fin-label { color: #94a3b8; font-size: 12px; margin-bottom: 2px; }
  .fin-value { color: #e2e8f0; font-size: 20px; font-weight: 700; }
  .svg-banner { border-radius: 14px; overflow: hidden; margin-bottom: 24px; }
</style>
""", unsafe_allow_html=True)

# ─── SVG Backgrounds ─────────────────────────────────────────────────────────

STOCK_BG = """
<div class="svg-banner">
<svg width="100%" viewBox="0 0 1200 220" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e3a5f" stroke-width="0.5"/>
    </pattern>
  </defs>
  <rect width="1200" height="220" fill="#050e1f"/>
  <rect width="1200" height="220" fill="url(#grid)" opacity="0.6"/>
  <polyline points="60,170 160,148 260,155 360,120 460,105 560,88 660,72 760,58 860,44 960,35 1060,24 1140,16"
    fill="none" stroke="#1d9e75" stroke-width="2" opacity="0.55"/>
  <polyline points="60,110 160,125 260,118 360,142 460,150 560,162 660,150 760,170 860,178 960,185 1060,190 1140,196"
    fill="none" stroke="#e24b4a" stroke-width="2" opacity="0.4"/>
  <rect x="130" y="134" width="14" height="22" rx="1" fill="#1d9e75" opacity="0.8"/>
  <line x1="137" y1="128" x2="137" y2="160" stroke="#1d9e75" stroke-width="1.2" opacity="0.8"/>
  <rect x="210" y="142" width="14" height="18" rx="1" fill="#e24b4a" opacity="0.8"/>
  <line x1="217" y1="136" x2="217" y2="163" stroke="#e24b4a" stroke-width="1.2" opacity="0.8"/>
  <rect x="290" y="112" width="14" height="24" rx="1" fill="#1d9e75" opacity="0.8"/>
  <line x1="297" y1="106" x2="297" y2="140" stroke="#1d9e75" stroke-width="1.2" opacity="0.8"/>
  <rect x="370" y="96"  width="14" height="28" rx="1" fill="#1d9e75" opacity="0.8"/>
  <line x1="377" y1="90"  x2="377" y2="128" stroke="#1d9e75" stroke-width="1.2" opacity="0.8"/>
  <rect x="450" y="103" width="14" height="20" rx="1" fill="#e24b4a" opacity="0.8"/>
  <line x1="457" y1="97"  x2="457" y2="126" stroke="#e24b4a" stroke-width="1.2" opacity="0.8"/>
  <rect x="530" y="80"  width="14" height="22" rx="1" fill="#1d9e75" opacity="0.8"/>
  <line x1="537" y1="74"  x2="537" y2="106" stroke="#1d9e75" stroke-width="1.2" opacity="0.8"/>
  <rect x="610" y="64"  width="14" height="20" rx="1" fill="#1d9e75" opacity="0.8"/>
  <line x1="617" y1="58"  x2="617" y2="88"  stroke="#1d9e75" stroke-width="1.2" opacity="0.8"/>
  <rect x="690" y="70"  width="14" height="22" rx="1" fill="#e24b4a" opacity="0.8"/>
  <line x1="697" y1="64"  x2="697" y2="95"  stroke="#e24b4a" stroke-width="1.2" opacity="0.8"/>
  <rect x="770" y="50"  width="14" height="18" rx="1" fill="#1d9e75" opacity="0.8"/>
  <line x1="777" y1="44"  x2="777" y2="72"  stroke="#1d9e75" stroke-width="1.2" opacity="0.8"/>
  <rect x="850" y="36"  width="14" height="20" rx="1" fill="#1d9e75" opacity="0.8"/>
  <line x1="857" y1="30"  x2="857" y2="60"  stroke="#1d9e75" stroke-width="1.2" opacity="0.8"/>
  <rect x="930" y="24"  width="14" height="18" rx="1" fill="#e24b4a" opacity="0.8"/>
  <line x1="937" y1="18"  x2="937" y2="46"  stroke="#e24b4a" stroke-width="1.2" opacity="0.8"/>
  <rect x="1010" y="16" width="14" height="16" rx="1" fill="#1d9e75" opacity="0.8"/>
  <line x1="1017" y1="10" x2="1017" y2="36" stroke="#1d9e75" stroke-width="1.2" opacity="0.8"/>
  <rect x="130"  y="186" width="14" height="18" fill="#1d9e75" opacity="0.3"/>
  <rect x="210"  y="190" width="14" height="14" fill="#e24b4a" opacity="0.3"/>
  <rect x="290"  y="182" width="14" height="22" fill="#1d9e75" opacity="0.3"/>
  <rect x="370"  y="185" width="14" height="19" fill="#1d9e75" opacity="0.3"/>
  <rect x="450"  y="192" width="14" height="12" fill="#e24b4a" opacity="0.3"/>
  <rect x="530"  y="180" width="14" height="24" fill="#1d9e75" opacity="0.3"/>
  <rect x="610"  y="186" width="14" height="18" fill="#1d9e75" opacity="0.3"/>
  <rect x="690"  y="189" width="14" height="15" fill="#e24b4a" opacity="0.3"/>
  <rect x="770"  y="178" width="14" height="26" fill="#1d9e75" opacity="0.3"/>
  <rect x="850"  y="183" width="14" height="21" fill="#1d9e75" opacity="0.3"/>
  <rect x="0" y="198" width="1200" height="22" fill="#0a1628" opacity="0.95"/>
  <line x1="0" y1="198" x2="1200" y2="198" stroke="#1e3a5f" stroke-width="0.5"/>
  <text x="20"   y="214" font-family="monospace" font-size="11" fill="#1d9e75">AAPL +1.24%</text>
  <text x="140"  y="214" font-family="monospace" font-size="11" fill="#1d9e75">MSFT +0.87%</text>
  <text x="260"  y="214" font-family="monospace" font-size="11" fill="#e24b4a">TSLA -2.11%</text>
  <text x="380"  y="214" font-family="monospace" font-size="11" fill="#1d9e75">GOOGL +0.43%</text>
  <text x="510"  y="214" font-family="monospace" font-size="11" fill="#e24b4a">NVDA -0.95%</text>
  <text x="630"  y="214" font-family="monospace" font-size="11" fill="#1d9e75">SPY +0.31%</text>
  <text x="740"  y="214" font-family="monospace" font-size="11" fill="#1d9e75">AMZN +1.55%</text>
  <text x="870"  y="214" font-family="monospace" font-size="11" fill="#e24b4a">META -0.62%</text>
  <text x="990"  y="214" font-family="monospace" font-size="11" fill="#1d9e75">BRK +0.18%</text>
  <text x="1090" y="214" font-family="monospace" font-size="11" fill="#1d9e75">JPM +0.74%</text>
  <text x="50"  y="52" font-family="monospace" font-size="28" font-weight="700" fill="#e2e8f0" opacity="0.95">&#x1F4C8; Stock Market Dashboard</text>
  <text x="52"  y="76" font-family="monospace" font-size="13" fill="#475569">Live Prices · Candlestick · Revenue · Net Income · Market Cap · Volatility</text>
  <text x="1150" y="30" font-family="monospace" font-size="10" fill="#1e3a5f" text-anchor="end">LIVE MKT DATA</text>
</svg>
</div>
"""

WEATHER_BG = """
<div class="svg-banner">
<svg width="100%" viewBox="0 0 1200 220" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="sunGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#fef3c7"/>
      <stop offset="100%" stop-color="#fbbf24" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="1200" height="160" fill="#38bdf8"/>
  <rect y="155" width="1200" height="65" fill="#bae6fd"/>
  <rect y="145" width="1200" height="25" fill="#fed7aa" opacity="0.28"/>
  <circle cx="1080" cy="62" r="52" fill="url(#sunGlow)" opacity="0.85"/>
  <circle cx="1080" cy="62" r="28" fill="#fef3c7" opacity="0.95"/>
  <line x1="1080" y1="18"  x2="1080" y2="6"   stroke="#fef3c7" stroke-width="2" opacity="0.65"/>
  <line x1="1080" y1="106" x2="1080" y2="118"  stroke="#fef3c7" stroke-width="2" opacity="0.65"/>
  <line x1="1036" y1="62"  x2="1024" y2="62"   stroke="#fef3c7" stroke-width="2" opacity="0.65"/>
  <line x1="1124" y1="62"  x2="1136" y2="62"   stroke="#fef3c7" stroke-width="2" opacity="0.65"/>
  <line x1="1049" y1="31"  x2="1040" y2="22"   stroke="#fef3c7" stroke-width="2" opacity="0.65"/>
  <line x1="1111" y1="93"  x2="1120" y2="102"  stroke="#fef3c7" stroke-width="2" opacity="0.65"/>
  <line x1="1111" y1="31"  x2="1120" y2="22"   stroke="#fef3c7" stroke-width="2" opacity="0.65"/>
  <line x1="1049" y1="93"  x2="1040" y2="102"  stroke="#fef3c7" stroke-width="2" opacity="0.65"/>
  <ellipse cx="160"  cy="68"  rx="80"  ry="34" fill="white" opacity="0.94"/>
  <ellipse cx="110"  cy="78"  rx="55"  ry="28" fill="white" opacity="0.94"/>
  <ellipse cx="220"  cy="76"  rx="48"  ry="26" fill="white" opacity="0.94"/>
  <ellipse cx="160"  cy="88"  rx="74"  ry="22" fill="white" opacity="0.88"/>
  <ellipse cx="460"  cy="50"  rx="65"  ry="26" fill="white" opacity="0.88"/>
  <ellipse cx="410"  cy="60"  rx="42"  ry="22" fill="white" opacity="0.88"/>
  <ellipse cx="515"  cy="58"  rx="38"  ry="20" fill="white" opacity="0.88"/>
  <ellipse cx="460"  cy="68"  rx="58"  ry="18" fill="white" opacity="0.82"/>
  <ellipse cx="760"  cy="42"  rx="48"  ry="20" fill="white" opacity="0.80"/>
  <ellipse cx="724"  cy="50"  rx="30"  ry="16" fill="white" opacity="0.80"/>
  <ellipse cx="798"  cy="50"  rx="28"  ry="15" fill="white" opacity="0.80"/>
  <ellipse cx="320"  cy="90"  rx="42"  ry="18" fill="#94a3b8" opacity="0.75"/>
  <ellipse cx="290"  cy="97"  rx="28"  ry="15" fill="#94a3b8" opacity="0.75"/>
  <ellipse cx="352"  cy="97"  rx="25"  ry="14" fill="#94a3b8" opacity="0.75"/>
  <line x1="296" y1="114" x2="292" y2="136" stroke="#60a5fa" stroke-width="1.5" opacity="0.55"/>
  <line x1="314" y1="118" x2="310" y2="140" stroke="#60a5fa" stroke-width="1.5" opacity="0.55"/>
  <line x1="332" y1="112" x2="328" y2="134" stroke="#60a5fa" stroke-width="1.5" opacity="0.55"/>
  <line x1="350" y1="116" x2="346" y2="138" stroke="#60a5fa" stroke-width="1.5" opacity="0.55"/>
  <path d="M 60 128 Q 130 122 200 130 Q 270 138 340 130" fill="none" stroke="#bfdbfe" stroke-width="1.5" opacity="0.5"/>
  <path d="M 75 142 Q 145 136 215 144"                   fill="none" stroke="#bfdbfe" stroke-width="1.2" opacity="0.4"/>
  <ellipse cx="0"    cy="188" rx="250" ry="70" fill="#4ade80" opacity="0.65"/>
  <ellipse cx="320"  cy="198" rx="300" ry="62" fill="#22c55e" opacity="0.55"/>
  <ellipse cx="750"  cy="192" rx="340" ry="58" fill="#4ade80" opacity="0.60"/>
  <ellipse cx="1200" cy="188" rx="220" ry="65" fill="#16a34a" opacity="0.55"/>
  <rect y="210" width="1200" height="10" fill="#15803d"/>
  <rect x="920" y="96"  width="10" height="48" rx="5" fill="white" opacity="0.65"/>
  <circle cx="925" cy="148" r="9" fill="#f97316" opacity="0.85"/>
  <rect x="924" y="108" width="2" height="38" rx="1" fill="#f97316" opacity="0.85"/>
  <text x="937" y="152" font-family="monospace" font-size="12" fill="white" opacity="0.9">28C</text>
  <path d="M 925 72 Q 917 84 917 92 Q 917 102 925 102 Q 933 102 933 92 Q 933 84 925 72Z" fill="#60a5fa" opacity="0.8"/>
  <text x="937" y="96" font-family="monospace" font-size="12" fill="white" opacity="0.9">72%</text>
  <rect x="0" y="0" width="1200" height="46" fill="#0c4a6e" opacity="0.50"/>
  <text x="50"  y="32" font-family="sans-serif" font-size="26" font-weight="700" fill="white" opacity="0.97">&#x1F324; Weather Dashboard</text>
  <text x="280" y="32" font-family="sans-serif" font-size="13" fill="#bae6fd" opacity="0.88">  Today · Yesterday · Forecast · Calendar Filter · Multi-city</text>
</svg>
</div>
"""

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
    return df.reset_index()

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
        return latest, change, (change / prev) * 100
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    latest = float(df["Close"].iloc[-1])
    prev   = float(df["Close"].iloc[-2])
    change = latest - prev
    return latest, change, (change / prev) * 100

def fmt_large(val):
    if val is None:
        return "N/A"
    try:
        val = float(val)
    except (TypeError, ValueError):
        return "N/A"
    if val >= 1e12:  return f"${val/1e12:.2f}T"
    if val >= 1e9:   return f"${val/1e9:.2f}B"
    if val >= 1e6:   return f"${val/1e6:.2f}M"
    return f"${val:,.0f}"

@st.cache_data(ttl=3600)
def get_financials(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info   = ticker.info
        market_cap = info.get("marketCap")
        fin = ticker.financials
        revenue = net_income = None
        if fin is not None and not fin.empty:
            if "Total Revenue" in fin.index:
                revenue = float(fin.loc["Total Revenue"].iloc[0])
            if "Net Income" in fin.index:
                net_income = float(fin.loc["Net Income"].iloc[0])
        margin = (net_income / revenue * 100) if revenue and net_income else None
        return {
            "market_cap": market_cap, "revenue": revenue,
            "net_income": net_income, "margin":  margin,
            "pe_ratio":   info.get("trailingPE"),
            "eps":        info.get("trailingEps"),
        }
    except Exception:
        return {"market_cap": None, "revenue": None, "net_income": None,
                "margin": None, "pe_ratio": None, "eps": None}

# ════════════════════════════════════════════════════════════════
# WEATHER FUNCTIONS
# ════════════════════════════════════════════════════════════════

def get_weather(city):
    url = (f"https://api.openweathermap.org/data/2.5/weather"
           f"?q={city}&units=metric&appid={OWM_KEY}")
    try:
        d = requests.get(url, timeout=10).json()
        return {
            "city":       city,
            "temp":       round(d["main"]["temp"], 1),
            "feels":      round(d["main"]["feels_like"], 1),
            "humidity":   d["main"]["humidity"],
            "wind":       round(d["wind"]["speed"] * 3.6, 1),
            "cond":       d["weather"][0]["description"].title(),
            "pressure":   d["main"].get("pressure", 0),
            "visibility": round(d.get("visibility", 0) / 1000, 1),
            "sunrise":    datetime.fromtimestamp(d["sys"]["sunrise"]).strftime("%H:%M"),
            "sunset":     datetime.fromtimestamp(d["sys"]["sunset"]).strftime("%H:%M"),
            "icon":       d["weather"][0]["icon"],
        }
    except Exception:
        return {"city": city, "temp": 0, "feels": 0, "humidity": 0,
                "wind": 0, "cond": "Unavailable", "pressure": 0,
                "visibility": 0, "sunrise": "--", "sunset": "--", "icon": "01d"}

def get_forecast(city):
    url = (f"https://api.openweathermap.org/data/2.5/forecast"
           f"?q={city}&units=metric&appid={OWM_KEY}")
    try:
        items = requests.get(url, timeout=10).json().get("list", [])
        rows  = []
        for i in items:
            dt = datetime.strptime(i["dt_txt"], "%Y-%m-%d %H:%M:%S")
            rows.append({
                "datetime": dt, "date": dt.date(), "time": i["dt_txt"],
                "temp":     i["main"]["temp"], "feels": i["main"]["feels_like"],
                "humidity": i["main"]["humidity"],
                "wind":     round(i["wind"]["speed"] * 3.6, 1),
                "pressure": i["main"]["pressure"],
                "cond":     i["weather"][0]["description"].title(),
                "rain":     i.get("rain", {}).get("3h", 0),
                "pop":      round(i.get("pop", 0) * 100),
            })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

def get_historical_weather(city, days_back=1):
    geo_url = (f"https://api.openweathermap.org/geo/1.0/direct"
               f"?q={city}&limit=1&appid={OWM_KEY}")
    try:
        geo = requests.get(geo_url, timeout=10).json()
        if not geo:
            return pd.DataFrame()
        lat, lon  = geo[0]["lat"], geo[0]["lon"]
        end_dt    = date.today() - timedelta(days=1)
        start_dt  = end_dt - timedelta(days=days_back - 1)
        url = (f"https://api.open-meteo.com/v1/forecast"
               f"?latitude={lat}&longitude={lon}"
               f"&hourly=temperature_2m,relativehumidity_2m,windspeed_10m,precipitation"
               f"&start_date={start_dt}&end_date={end_dt}&timezone=auto")
        hourly = requests.get(url, timeout=15).json().get("hourly", {})
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

st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S  %d %b %Y')}  |  Auto-refresh every 5 min")

tab1, tab2 = st.tabs(["📈  Stocks", "🌦  Weather"])

# ════════════════════════════════════════════════════════════════
# TAB 1 – STOCKS
# ════════════════════════════════════════════════════════════════
with tab1:

    st.markdown(STOCK_BG, unsafe_allow_html=True)

    cols = st.columns(len(STOCKS))
    histories = {}
    for i, sym in enumerate(STOCKS):
        price, change, pct = get_latest(sym)
        cols[i].metric(label=sym, value=f"${price:.2f}", delta=f"{pct:.2f}%")
        histories[sym] = get_stock_data(sym)

    # 7-day line chart
    fig = go.Figure()
    for sym, hist in histories.items():
        fig.add_trace(go.Scatter(x=hist["Date"], y=hist["Close"],
                                 mode="lines+markers", name=sym))
    fig.update_layout(title="7-Day Closing Prices",
                      xaxis_title="Date", yaxis_title="Price (USD)",
                      hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True, key="stock_line")

    # ── Financials ─────────────────────────────────────────────
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

    # Comparison bar charts
    fin_rows = []
    for sym in STOCKS:
        f = get_financials(sym)
        fin_rows.append({"Symbol": sym,
                          "Revenue":    f["revenue"]    or 0,
                          "Net Income": f["net_income"] or 0,
                          "Market Cap": f["market_cap"] or 0})
    df_fin = pd.DataFrame(fin_rows)

    c1, c2 = st.columns(2)
    with c1:
        fig_rev = px.bar(df_fin, x="Symbol", y="Revenue",
                         title="Annual Revenue Comparison",
                         color="Revenue", color_continuous_scale="Teal")
        fig_rev.update_traces(hovertemplate="%{x}: %{customdata}",
                              customdata=[fmt_large(v) for v in df_fin["Revenue"]])
        st.plotly_chart(fig_rev, use_container_width=True, key="fin_rev")
    with c2:
        fig_ni = px.bar(df_fin, x="Symbol", y="Net Income",
                        title="Net Income Comparison",
                        color="Net Income", color_continuous_scale="Greens")
        fig_ni.update_traces(hovertemplate="%{x}: %{customdata}",
                             customdata=[fmt_large(v) for v in df_fin["Net Income"]])
        st.plotly_chart(fig_ni, use_container_width=True, key="fin_ni")

    fig_mc = px.bar(df_fin, x="Symbol", y="Market Cap",
                    title="Market Capitalisation (Net Worth) Comparison",
                    color="Market Cap", color_continuous_scale="Purples")
    fig_mc.update_traces(hovertemplate="%{x}: %{customdata}",
                         customdata=[fmt_large(v) for v in df_fin["Market Cap"]])
    st.plotly_chart(fig_mc, use_container_width=True, key="fin_mc")

    st.divider()

    # Volatility
    vol_data = []
    for sym, hist in histories.items():
        daily_range = ((hist["High"] - hist["Low"]) / hist["Close"] * 100).mean()
        vol_data.append({"symbol": sym, "avg_range_%": round(float(daily_range), 2)})
    df_vol = pd.DataFrame(vol_data)
    fig_vol = px.bar(df_vol, x="symbol", y="avg_range_%",
                     title="Average Daily Volatility – High/Low Spread (%)",
                     color="avg_range_%", color_continuous_scale="Reds")
    st.plotly_chart(fig_vol, use_container_width=True, key="stock_vol")

    st.subheader("Volatility Alerts")
    any_alert = False
    for sym, hist in histories.items():
        if len(hist) >= 2:
            close_data = hist["Close"]
            if hasattr(close_data, "columns"):
                close_data = close_data.iloc[:, 0]
            chg = float(close_data.pct_change().iloc[-1]) * 100
            if abs(chg) > 2:
                st.warning(f"{sym}: {chg:.2f}% move – above 2% threshold")
                any_alert = True
    if not any_alert:
        st.success("All stocks within normal range.")

# ════════════════════════════════════════════════════════════════
# TAB 2 – WEATHER
# ════════════════════════════════════════════════════════════════
with tab2:

    st.markdown(WEATHER_BG, unsafe_allow_html=True)

    weather_all = [get_weather(c) for c in CITIES]

    selected_city = st.selectbox("Select city for detailed view", CITIES, index=0)

    w_cols = st.columns(len(CITIES))
    for i, w in enumerate(weather_all):
        w_cols[i].metric(w["city"], f"{w['temp']}°C", w["cond"])
        w_cols[i].caption(
            f"Feels {w['feels']}°C  |  Humidity {w['humidity']}%  |  Wind {w['wind']} km/h"
        )

    st.divider()

    sel = next(w for w in weather_all if w["city"] == selected_city)
    st.subheader(f"{selected_city} – Detailed Conditions")

    d1, d2, d3, d4, d5, d6 = st.columns(6)
    d1.metric("Temperature",  f"{sel['temp']}°C")
    d2.metric("Feels Like",   f"{sel['feels']}°C")
    d3.metric("Humidity",     f"{sel['humidity']}%")
    d4.metric("Wind Speed",   f"{sel['wind']} km/h")
    d5.metric("Visibility",   f"{sel['visibility']} km")
    d6.metric("Pressure",     f"{sel['pressure']} hPa")

    s1, s2 = st.columns(2)
    s1.metric("Sunrise", sel["sunrise"])
    s2.metric("Sunset",  sel["sunset"])

    st.divider()

    # ── Calendar date filter ─────────────────────────────────────
    st.subheader("Date Range – Forecast & History")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        today    = date.today()
        min_date = today - timedelta(days=6)
        max_date = today + timedelta(days=4)
        date_range = st.date_input(
            "Select date range",
            value=(today - timedelta(days=1), today + timedelta(days=2)),
            min_value=min_date, max_value=max_date,
            help="Past dates: historical (Open-Meteo). Future dates: OWM forecast."
        )
    with col_f2:
        hourly_granularity = st.selectbox("Chart granularity",
                                          ["3-hourly", "Daily average"], index=1)

    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range if isinstance(date_range, date) else today

    forecast_df = historical_df = pd.DataFrame()
    if end_date >= today:
        forecast_df = get_forecast(selected_city)
    if start_date < today:
        days_back = (today - start_date).days
        with st.spinner("Fetching historical weather…"):
            historical_df = get_historical_weather(selected_city, days_back=days_back)

    combined_rows = []

    if not historical_df.empty:
        hf = historical_df[
            (historical_df["date"] >= start_date) &
            (historical_df["date"] < today)
        ].copy()
        if not hf.empty:
            if hourly_granularity == "Daily average":
                ha = hf.groupby("date").agg(temp=("temp","mean"), humidity=("humidity","mean"),
                                             wind=("wind","mean"), rain=("rain","sum")).reset_index()
                ha["datetime"] = pd.to_datetime(ha["date"])
                ha["source"] = "Historical"; ha["pop"] = 0
                combined_rows.append(ha)
            else:
                hf["source"] = "Historical"; hf["pop"] = 0
                combined_rows.append(hf[["datetime","date","temp","humidity","wind","rain","pop","source"]])

    if not forecast_df.empty:
        ff = forecast_df[
            (forecast_df["date"] >= max(start_date, today)) &
            (forecast_df["date"] <= end_date)
        ].copy()
        if not ff.empty:
            if hourly_granularity == "Daily average":
                fa = ff.groupby("date").agg(temp=("temp","mean"), humidity=("humidity","mean"),
                                             wind=("wind","mean"), rain=("rain","sum"),
                                             pop=("pop","max")).reset_index()
                fa["datetime"] = pd.to_datetime(fa["date"])
                fa["source"] = "Forecast"
                combined_rows.append(fa)
            else:
                ff["source"] = "Forecast"
                combined_rows.append(ff[["datetime","date","temp","humidity","wind","rain","pop","source"]])

    if combined_rows:
        df_all = pd.concat(combined_rows, ignore_index=True).sort_values("datetime")

        fig_t = go.Figure()
        for src, grp in df_all.groupby("source"):
            fig_t.add_trace(go.Scatter(
                x=grp["datetime"], y=grp["temp"],
                mode="lines+markers", name=f"Temp ({src})",
                line=dict(color="tomato" if src=="Forecast" else "#f97316",
                          dash="dash"    if src=="Forecast" else "solid")))
        fig_t.update_layout(title=f"Temperature Timeline – {selected_city}",
                            yaxis_title="°C", hovermode="x unified")
        st.plotly_chart(fig_t, use_container_width=True, key="temp_timeline")

        fig_h = go.Figure()
        for src, grp in df_all.groupby("source"):
            fig_h.add_trace(go.Scatter(
                x=grp["datetime"], y=grp["humidity"],
                mode="lines+markers", name=f"Humidity ({src})",
                line=dict(color="steelblue" if src=="Forecast" else "#0284c7",
                          dash="dash"       if src=="Forecast" else "solid")))
        if "pop" in df_all.columns and df_all["pop"].max() > 0:
            fig_h.add_trace(go.Bar(x=df_all["datetime"], y=df_all["pop"],
                                   name="Rain Probability (%)",
                                   marker_color="rgba(56,189,248,0.3)", yaxis="y2"))
        fig_h.update_layout(title=f"Humidity & Rain Probability – {selected_city}",
                            yaxis=dict(title="Humidity (%)"),
                            yaxis2=dict(title="Rain Prob. (%)", overlaying="y", side="right"),
                            hovermode="x unified")
        st.plotly_chart(fig_h, use_container_width=True, key="humidity_timeline")

        fig_w = go.Figure()
        for src, grp in df_all.groupby("source"):
            fig_w.add_trace(go.Scatter(
                x=grp["datetime"], y=grp["wind"],
                mode="lines+markers", name=f"Wind ({src})", fill="tozeroy",
                line=dict(color="#a3e635" if src=="Forecast" else "#65a30d",
                          dash="dash"     if src=="Forecast" else "solid")))
        fig_w.update_layout(title=f"Wind Speed – {selected_city}",
                            yaxis_title="km/h", hovermode="x unified")
        st.plotly_chart(fig_w, use_container_width=True, key="wind_timeline")

        with st.expander("Raw data table"):
            disp = ["datetime","source","temp","humidity","wind","rain","pop"]
            disp = [c for c in disp if c in df_all.columns]
            st.dataframe(df_all[disp].rename(columns={
                "datetime":"Date/Time","source":"Source","temp":"Temp (°C)",
                "humidity":"Humidity (%)","wind":"Wind (km/h)","rain":"Rain (mm)",
                "pop":"Rain Prob. (%)"}),
                use_container_width=True, hide_index=True)
    else:
        st.info("No data available for the selected date range.")

    st.divider()

    col_left, col_right = st.columns(2)
    df_w = pd.DataFrame(weather_all)
    with col_left:
        fig_hum = px.bar(df_w, x="city", y="humidity", title="Humidity by City (%)",
                         color="humidity", color_continuous_scale="Blues")
        st.plotly_chart(fig_hum, use_container_width=True, key="weather_hum")
    with col_right:
        fig_temp = px.bar(df_w, x="city", y="temp", title="Temperature by City (°C)",
                          color="temp", color_continuous_scale="Oranges")
        st.plotly_chart(fig_temp, use_container_width=True, key="weather_temp")

    fig_wind = px.bar(df_w, x="city", y="wind", title="Wind Speed by City (km/h)",
                      color="wind", color_continuous_scale="Greens")
    st.plotly_chart(fig_wind, use_container_width=True, key="weather_wind")

    st.subheader("Weather Alerts")
    any_w = False
    for w in weather_all:
        if w["temp"] > 30:
            st.error(f"{w['city']}: {w['temp']}°C – extreme heat")
            any_w = True
        if w["humidity"] > 80:
            st.warning(f"{w['city']}: {w['humidity']}% humidity – high moisture")
            any_w = True
        if w["wind"] > 50:
            st.warning(f"{w['city']}: {w['wind']} km/h – strong winds")
            any_w = True
    if not any_w:
        st.success("No weather alerts.")

# ════════════════════════════════════════════════════════════════
# AUTO REFRESH
# ════════════════════════════════════════════════════════════════
time.sleep(REFRESH)
st.rerun()
