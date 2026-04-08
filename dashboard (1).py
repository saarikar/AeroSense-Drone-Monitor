import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import socket
import json
import requests
from datetime import datetime
import random
import math

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AeroSense | Drone Sensor Dashboard",
    page_icon="🛸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Share+Tech+Mono&family=Exo+2:wght@300;400;600&display=swap');

  :root {
    --bg-dark: #080d14;
    --bg-card: #0d1520;
    --accent-cyan: #00f5d4;
    --accent-blue: #0466c8;
    --accent-orange: #f77f00;
    --accent-red: #e63946;
    --accent-green: #57cc99;
    --accent-yellow: #ffd60a;
    --text-primary: #e8f4f8;
    --text-muted: #7a9bb5;
    --border: #1a3a5c;
  }

  html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-dark) !important;
    font-family: 'Exo 2', sans-serif;
    color: var(--text-primary);
  }
  [data-testid="stSidebar"] {
    background: #09121d !important;
    border-right: 1px solid var(--border);
  }
  [data-testid="stSidebar"] * { color: var(--text-primary) !important; }

  h1, h2, h3 { font-family: 'Rajdhani', sans-serif !important; letter-spacing: 0.08em; }

  .drone-header {
    background: linear-gradient(135deg, #080d14 0%, #0d1e35 50%, #080d14 100%);
    border: 1px solid var(--accent-cyan);
    border-radius: 8px;
    padding: 18px 28px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
  }
  .drone-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
  }
  .drone-header h1 {
    color: var(--accent-cyan) !important;
    font-size: 2.2rem; margin: 0;
    text-shadow: 0 0 20px rgba(0,245,212,0.4);
  }
  .drone-header p {
    color: var(--text-muted);
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.8rem; margin: 4px 0 0 0;
    letter-spacing: 0.12em;
  }

  .metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 14px;
    text-align: center;
    position: relative;
    overflow: hidden;
  }
  .metric-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    background: var(--indicator-color, #0466c8);
  }
  .metric-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.68rem;
    color: var(--text-muted);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 6px;
  }
  .metric-value {
    font-family: 'Rajdhani', sans-serif;
    font-size: 2.2rem;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 4px;
  }
  .metric-unit {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.72rem;
    color: var(--text-muted);
  }
  .badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.66rem;
    font-family: 'Share Tech Mono', monospace;
    letter-spacing: 0.08em;
    font-weight: 600;
    margin-top: 4px;
  }
  .badge-ok   { background: rgba(87,204,153,0.15); color: #57cc99; border: 1px solid rgba(87,204,153,0.4); }
  .badge-warn { background: rgba(255,214,10,0.15);  color: #ffd60a; border: 1px solid rgba(255,214,10,0.4); }
  .badge-crit { background: rgba(230,57,70,0.15);   color: #e63946; border: 1px solid rgba(230,57,70,0.4); }

  .derived-card {
    background: linear-gradient(135deg, #0d1520, #0a1828);
    border: 1px solid #1a3a5c;
    border-left: 3px solid var(--accent-cyan);
    border-radius: 8px;
    padding: 12px 16px;
  }
  .derived-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }
  .derived-value {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--accent-cyan);
    line-height: 1.1;
  }
  .derived-unit {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    color: #4a7a9b;
  }
  .derived-desc {
    font-size: 0.7rem;
    color: #4a7a9b;
    margin-top: 2px;
    font-style: italic;
  }

  .section-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.1rem;
    color: var(--accent-cyan);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    border-bottom: 1px solid var(--border);
    padding-bottom: 6px;
    margin-bottom: 14px;
    margin-top: 6px;
  }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  THRESHOLDS
# ─────────────────────────────────────────────
THRESHOLDS = {
    "temperature": {"warn_low": 5,   "warn_high": 45, "crit_low": -10, "crit_high": 60,  "unit": "°C"},
    "humidity":    {"warn_low": 20,  "warn_high": 80, "crit_low": 5,   "crit_high": 95,  "unit": "%"},
    "pressure":    {"warn_low": 950, "warn_high": 1020,"crit_low": 900,"crit_high": 1060,"unit": "hPa"},
    "gas_res":     {"warn_low": 50,  "warn_high": 200, "crit_low": 20, "crit_high": 400, "unit": "kO"},
    "ch4":         {"warn_low": 0,   "warn_high": 500, "crit_low": 0,  "crit_high": 2000,"unit": "ppm"},
}

def get_status(value, key):
    t = THRESHOLDS[key]
    if value <= t["crit_low"] or value >= t["crit_high"]:
        return "crit", "CRITICAL"
    elif value <= t["warn_low"] or value >= t["warn_high"]:
        return "warn", "WARNING"
    else:
        return "ok",   "NORMAL"

# ─────────────────────────────────────────────
#  DERIVED VALUE CALCULATIONS
# ─────────────────────────────────────────────
def calc_dew_point(T, RH):
    if RH <= 0: return 0.0
    a, b = 17.625, 243.04
    gamma = math.log(max(RH, 0.01) / 100.0) + (a * T) / (b + T)
    return round((b * gamma) / (a - gamma), 2)

def calc_heat_index(T, RH):
    if T < 27 or RH < 40:
        es = 6.105 * math.exp(17.27 * T / (237.7 + T))
        return round(T + 0.33 * (RH / 100 * es) - 4.0, 2)
    c = [-8.78469475556, 1.61139411, 2.33854883889, -0.14611605,
         -0.012308094, -0.0164248277778, 0.002211732, 0.00072546, -0.000003582]
    HI = (c[0] + c[1]*T + c[2]*RH + c[3]*T*RH + c[4]*T**2 + c[5]*RH**2
          + c[6]*T**2*RH + c[7]*T*RH**2 + c[8]*T**2*RH**2)
    return round(HI, 2)

def calc_absolute_humidity(T, RH):
    es = 6.112 * math.exp((17.67 * T) / (T + 243.5))
    return round((RH / 100.0) * es * 2.1674 / (T + 273.15), 3)

def calc_air_density(T, P):
    R_dry = 287.058
    return round((P * 100) / (R_dry * (T + 273.15)), 4)

def calc_lel_percent(ch4_ppm):
    return round((ch4_ppm / 50000.0) * 100, 3)

def calc_voc_index(gas_res_kohm):
    return round(max(0, min(500, 500 * (1 - min(gas_res_kohm, 500) / 500))), 1)

# ─────────────────────────────────────────────
#  DATA SIMULATOR
# ─────────────────────────────────────────────
def simulate_esp32_data(t, scenario="normal"):
    noise = lambda s: random.gauss(0, s)
    if scenario == "methane_leak":
        ch4 = max(0, 3200 + noise(350) + 700 * np.sin(t * 0.3))
    elif scenario == "humid_cloud":
        ch4 = max(0, 180 + noise(20))
    else:
        ch4 = max(0, 320 + noise(35) + 50 * np.sin(t * 0.1))

    temp = round(22 + 7 * np.sin(t * 0.08) + noise(0.3), 2)
    rh   = round(max(5, min(99, 58 + 18 * np.cos(t * 0.06) + noise(0.8))), 2)
    pres = round(1005 + 8 * np.sin(t * 0.04) + noise(0.3), 2)
    gres = round(max(1, 130 + 55 * np.sin(t * 0.11) + noise(4)), 2)
    return {
        "timestamp":   datetime.now().isoformat(),
        "temperature": temp,
        "humidity":    rh,
        "pressure":    pres,
        "gas_res":     gres,
        "ch4":         round(ch4, 1),
    }

def mq4_adc_to_ppm(raw_adc):
    """Convert MQ4 raw ADC (0-4095, 3.3V ref) to approximate CH4 ppm.
    Resistive divider: RL = 10 kOhm, R0 = 9.83 kOhm (clean-air calibration).
    Curve: ppm = 1000 * (Rs/R0)^-2.13
    """
    if raw_adc <= 0:
        return 0.0
    volt = raw_adc * (3.3 / 4095.0)
    if volt >= 3.29:
        return 0.0
    rs    = ((3.3 - volt) / volt) * 10.0
    ratio = rs / 9.83
    return round(max(0.0, 1000.0 * (ratio ** -2.13)), 1)


def fetch_esp32_data(ip, port=80):
    """
    Use a raw TCP socket instead of requests.

    Why: The ESP32 raw WiFiServer never reads the incoming HTTP request —
    it sends JSON the moment a client connects. requests (HTTP/1.1,
    keep-alive) deadlocks waiting for the server to consume its headers.
    A browser works because it reads eagerly. A raw socket with HTTP/1.0
    forces immediate connection-close and avoids the deadlock entirely.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((ip, port))
        # HTTP/1.0 + Connection: close  →  server must close after response
        request = (
            f"GET / HTTP/1.0\r\n"
            f"Host: {ip}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        )
        sock.sendall(request.encode())

        raw = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            raw += chunk
        sock.close()

        # Strip HTTP headers — body starts after the blank line
        response = raw.decode("utf-8", errors="ignore")
        body = response.split("\r\n\r\n", 1)[-1].strip()
        if not body:
            body = response.split("\n\n", 1)[-1].strip()

        data = json.loads(body)

        # Support both key formats:
        #   Short (your ESP32): temp / hum / pres / gas1 / gas2(raw ADC)
        #   Long  (WebServer):  temperature / humidity / pressure / gas_res / ch4(ppm)
        temperature = data.get("temp",  data.get("temperature", 0))
        humidity    = data.get("hum",   data.get("humidity",    0))
        pressure    = data.get("pres",  data.get("pressure",    0))
        gas_res     = data.get("gas1",  data.get("gas_res",     0))

        if "gas2" in data:
            ch4 = mq4_adc_to_ppm(int(data["gas2"]))
        else:
            ch4 = float(data.get("ch4", 0))

        return {
            "temperature": round(float(temperature), 2),
            "humidity":    round(float(humidity),    2),
            "pressure":    round(float(pressure),    2),
            "gas_res":     round(float(gas_res),     2),
            "ch4":         ch4,
        }, None

    except Exception as e:
        return None, str(e)

# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
if "history"   not in st.session_state: st.session_state.history   = []
if "t_offset"  not in st.session_state: st.session_state.t_offset  = 0
if "alert_log" not in st.session_state: st.session_state.alert_log = []
if "running"   not in st.session_state: st.session_state.running   = True

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛸 AeroSense Control")
    st.markdown("---")
    data_source = st.radio("📡 Data Source", ["Simulated (Demo)", "Live ESP32"])
    esp32_ip = ""
    if data_source == "Live ESP32":
        esp32_ip = st.text_input("ESP32 IP Address", "192.168.4.1")
        st.caption("Enter the IP printed on ESP32 Serial Monitor")

    st.markdown("---")
    st.markdown("#### 🎛 Simulation Settings")
    scenario = st.selectbox("Scenario", ["normal", "methane_leak", "humid_cloud"],
        format_func=lambda x: {"normal":"🟢 Normal Flight",
                                "methane_leak":"🔴 Methane Leak",
                                "humid_cloud":"🔵 Humid / Cloud Layer"}[x])
    refresh_rate = st.slider("Refresh Rate (s)", 1, 10, 2)
    history_len  = st.slider("History Length",   30, 300, 120)

    st.markdown("---")
    st.markdown("#### ⚠️ CH4 Thresholds")
    THRESHOLDS["ch4"]["warn_high"] = st.number_input("Warning (ppm)", value=500,  step=100)
    THRESHOLDS["ch4"]["crit_high"] = st.number_input("Critical (ppm)",value=2000, step=100)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("▶ Start" if not st.session_state.running else "⏸ Pause"):
            st.session_state.running = not st.session_state.running
    with c2:
        if st.button("🗑 Clear"):
            st.session_state.history   = []
            st.session_state.alert_log = []
            st.session_state.t_offset  = 0

    st.markdown("---")
    if data_source == "Simulated (Demo)":
        st.success("✅ Simulator Active")
    else:
        d, err = fetch_esp32_data(esp32_ip)
        if d:   st.success("✅ ESP32 Connected")
        else:   st.error(f"❌ {err}")
    st.caption("AeroSense v2.0 | ESP32 · BME680 · MQ4")

# ─────────────────────────────────────────────
#  DATA FETCH / GENERATE
# ─────────────────────────────────────────────
if st.session_state.running:
    
    if data_source == "Live ESP32":
        raw, err = fetch_esp32_data(esp32_ip)

        if raw is not None:
            current = raw
        else:
            st.warning(f"ESP32 unreachable ({err}) — using last reading")

            if st.session_state.history:
                current = st.session_state.history[-1]
            else:
                current = {
                    "temperature": 0,
                    "humidity": 0,
                    "pressure": 0,
                    "gas_res": 0,
                    "ch4": 0,
                    "timestamp": datetime.now().isoformat()
                }
    
    else:
        current = simulate_esp32_data(st.session_state.t_offset, scenario)
        st.session_state.t_offset += 1

    current["timestamp"] = datetime.now().isoformat()
    st.session_state.history.append(current)
    if len(st.session_state.history) > history_len:
        st.session_state.history = st.session_state.history[-history_len:]

    for key in ["temperature", "humidity", "pressure", "gas_res", "ch4"]:
        s, label = get_status(current[key], key)
        if s in ("warn", "crit"):
            entry = {"time": datetime.now().strftime("%H:%M:%S"),
                     "sensor": key.upper(),
                     "value": f"{current[key]} {THRESHOLDS[key]['unit']}",
                     "level": ("⛔ CRITICAL" if s == "crit" else "⚠ WARNING")}
            if not st.session_state.alert_log or st.session_state.alert_log[-1]["sensor"] != key:
                st.session_state.alert_log.append(entry)
                st.session_state.alert_log = st.session_state.alert_log[-50:]
else:
    current = st.session_state.history[-1] if st.session_state.history else simulate_esp32_data(0)

df = pd.DataFrame(st.session_state.history) if st.session_state.history else pd.DataFrame()

# ─────────────────────────────────────────────
#  DERIVED VALUES (current reading)
# ─────────────────────────────────────────────
T   = current.get("temperature", 25)
RH  = current.get("humidity", 50)
P   = current.get("pressure", 1013)
GR  = current.get("gas_res", 100)
CH4 = current.get("ch4", 300)

dew_point   = calc_dew_point(T, RH)
heat_index  = calc_heat_index(T, RH)
abs_hum     = calc_absolute_humidity(T, RH)
air_density = calc_air_density(T, P)
lel_pct     = calc_lel_percent(CH4)
voc_idx     = calc_voc_index(GR)

# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="drone-header">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <div>
      <h1>🛸 AEROSENSE MISSION MONITOR</h1>
      <p>ESP32 · BME680 ENVIRONMENTAL SENSOR · MQ4 METHANE DETECTOR · REAL-TIME AERIAL DATA</p>
    </div>
    <div style="text-align:right; font-family:'Share Tech Mono',monospace; font-size:0.8rem; color:#7a9bb5;">
      <div style="font-size:1.4rem; color:#00f5d4;">{'🟢 LIVE' if st.session_state.running else '⏸ PAUSED'}</div>
      <div>{datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}</div>
      <div style="margin-top:4px;">SAMPLES: {len(df)} &nbsp;|&nbsp; {scenario.upper()}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  METRIC CARD HELPER
# ─────────────────────────────────────────────
def metric_card(label, value, unit, key, icon=""):
    s, badge_label = get_status(value, key)
    color_map = {"ok": "#57cc99", "warn": "#ffd60a", "crit": "#e63946"}
    color = color_map[s]
    icon_map = {"ok": "✔", "warn": "⚠", "crit": "⛔"}
    st.markdown(f"""
    <div class="metric-card" style="--indicator-color:{color};">
      <div class="metric-label">{icon} {label}</div>
      <div class="metric-value" style="color:{color};">{value}</div>
      <div class="metric-unit">{unit}</div>
      <div><span class="badge badge-{s}">{icon_map[s]} {badge_label}</span></div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  SENSOR METRICS
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">📊 LIVE SENSOR READINGS — BME680 + MQ4</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)
for col, label, val, unit, key, icon in [
    (c1, "TEMPERATURE", T,   "°C",  "temperature", "🌡️"),
    (c2, "HUMIDITY",    RH,  "%RH", "humidity",    "💧"),
    (c3, "PRESSURE",    P,   "hPa", "pressure",    "📊"),
    (c4, "GAS RESIST.", GR,  "kΩ",  "gas_res",     "🔬"),
    (c5, "METHANE",     CH4, "ppm", "ch4",         "⚗️"),
]:
    with col:
        metric_card(label, val, unit, key, icon)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  DERIVED VALUES
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">🧮 DERIVED & CALCULATED VALUES</div>', unsafe_allow_html=True)

lel_color = "#57cc99" if lel_pct < 1 else "#ffd60a" if lel_pct < 4 else "#e63946"
voc_color = "#57cc99" if voc_idx < 100 else "#ffd60a" if voc_idx < 250 else "#e63946"
hi_color  = "#57cc99" if heat_index < 32 else "#ffd60a" if heat_index < 41 else "#e63946"

d1, d2, d3, d4, d5, d6 = st.columns(6)
for col, label, val, unit, color, desc in [
    (d1, "DEW POINT",     dew_point,   "°C",    "#4cc9f0", "Air saturation temperature"),
    (d2, "HEAT INDEX",    heat_index,  "°C",    hi_color,  "Apparent / feels-like temp"),
    (d3, "ABS. HUMIDITY", abs_hum,     "g/m³",  "#a855f7", "Actual water vapour mass"),
    (d4, "AIR DENSITY",   air_density, "kg/m³", "#06d6a0", "ρ = P/(R·T), ideal gas law"),
    (d5, "CH4 % LEL",     lel_pct,     "% LEL", lel_color, "LEL = 50,000 ppm"),
    (d6, "VOC INDEX",     voc_idx,     "/ 500", voc_color, "Derived from BME680 gas res."),
]:
    with col:
        st.markdown(f"""
        <div class="derived-card">
          <div class="derived-label">{label}</div>
          <div class="derived-value" style="color:{color};">{val}</div>
          <div class="derived-unit">{unit}</div>
          <div class="derived-desc">{desc}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  CHART HELPERS
# ─────────────────────────────────────────────
CT = {"paper": "#0d1520", "plot": "#080d14", "grid": "#1a3a5c", "font": "#7a9bb5"}

def base_layout(title, color, unit, height=280):
    return dict(
        title=dict(text=f"<b>{title}</b>",
                   font=dict(color=color, size=13, family="Rajdhani"), x=0.01),
        height=height, margin=dict(l=10, r=80, t=36, b=20),
        showlegend=False,
        xaxis=dict(showgrid=True, gridcolor=CT["grid"], showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor=CT["grid"], title=unit,
                   title_font=dict(size=9), zeroline=False, tickfont=dict(size=9)),
        paper_bgcolor=CT["paper"], plot_bgcolor=CT["plot"],
        font=dict(color=CT["font"]),
    )

def add_thresholds(fig, key):
    t = THRESHOLDS[key]
    for val, clr, lbl in [
        (t["warn_high"], "#ffd60a", f"WARN {t['warn_high']}"),
        (t["crit_high"], "#e63946", f"CRIT {t['crit_high']}"),
    ]:
        fig.add_hline(y=val, line_dash="dot", line_color=clr, line_width=1.2, opacity=0.85,
                      annotation_text=f" {lbl}", annotation_position="right",
                      annotation_font_color=clr, annotation_font_size=9)
    for val, clr, lbl in [
        (t["warn_low"], "#ffd60a", f"WARN {t['warn_low']}"),
        (t["crit_low"], "#e63946", f"CRIT {t['crit_low']}"),
    ]:
        if val > 0:
            fig.add_hline(y=val, line_dash="dot", line_color=clr, line_width=1.2, opacity=0.85,
                          annotation_text=f" {lbl}", annotation_position="right",
                          annotation_font_color=clr, annotation_font_size=9)

def line_chart(df, col, title, unit, color, key, height=280):
    fig = go.Figure()
    r, g, b = int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)
    x = list(range(len(df)))
    fig.add_trace(go.Scatter(
        x=x, y=df[col].tolist(),
        fill='tozeroy', fillcolor=f"rgba({r},{g},{b},0.07)",
        line=dict(color=color, width=2), mode='lines',
        hovertemplate=f"<b>{title}</b>: %{{y:.2f}} {unit}<extra></extra>",
    ))
    if len(df):
        fig.add_trace(go.Scatter(x=[x[-1]], y=[df[col].iloc[-1]],
            mode='markers', marker=dict(color=color, size=8), showlegend=False))
    add_thresholds(fig, key)
    fig.update_layout(**base_layout(title, color, unit, height))
    return fig

# ─────────────────────────────────────────────
#  SENSOR CHARTS
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">📈 SENSOR TELEMETRY — HISTORICAL GRAPHS</div>', unsafe_allow_html=True)

if not df.empty:
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.plotly_chart(line_chart(df,"temperature","Temperature","°C","#ff6b6b","temperature"),
                        use_container_width=True, config={"displayModeBar":False})
    with r1c2:
        st.plotly_chart(line_chart(df,"humidity","Relative Humidity","%","#4cc9f0","humidity"),
                        use_container_width=True, config={"displayModeBar":False})

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.plotly_chart(line_chart(df,"pressure","Barometric Pressure","hPa","#a855f7","pressure"),
                        use_container_width=True, config={"displayModeBar":False})
    with r2c2:
        st.plotly_chart(line_chart(df,"gas_res","Gas Resistance (BME680)","kΩ","#06d6a0","gas_res"),
                        use_container_width=True, config={"displayModeBar":False})

    # ── METHANE FULL WIDTH ──
    st.markdown('<div class="section-title">⚗️ METHANE CONCENTRATION (MQ4)</div>', unsafe_allow_html=True)

    fig_ch4 = go.Figure()
    x = list(range(len(df)))
    ch4v = df["ch4"].tolist()
    wh  = THRESHOLDS["ch4"]["warn_high"]
    crh = THRESHOLDS["ch4"]["crit_high"]

    fig_ch4.add_trace(go.Scatter(
        x=x + x[::-1], y=[wh]*len(x) + [0]*len(x),
        fill='toself', fillcolor='rgba(87,204,153,0.05)',
        line=dict(width=0), showlegend=True, name="Safe Zone", hoverinfo='skip'))

    pt_colors = ["#e63946" if v >= crh else "#f77f00" if v >= wh else "#ffd60a" for v in ch4v]
    fig_ch4.add_trace(go.Scatter(
        x=x, y=ch4v, mode='lines+markers',
        line=dict(color="#ffd60a", width=2.5),
        marker=dict(color=pt_colors, size=5),
        name="CH4 (ppm)",
        hovertemplate="<b>CH4</b>: %{y:.1f} ppm<extra></extra>",
    ))
    fig_ch4.add_hline(y=wh,  line_dash="dot", line_color="#f77f00", line_width=1.5, opacity=0.9,
                      annotation_text=f" WARNING {wh} ppm", annotation_position="right",
                      annotation_font_color="#f77f00", annotation_font_size=10)
    fig_ch4.add_hline(y=crh, line_dash="dot", line_color="#e63946", line_width=1.5, opacity=0.9,
                      annotation_text=f" CRITICAL {crh} ppm", annotation_position="right",
                      annotation_font_color="#e63946", annotation_font_size=10)

    ch4_layout = base_layout("Methane Concentration — MQ4 Sensor", "#ffd60a", "ppm", 300)
    ch4_layout["showlegend"] = True
    ch4_layout["legend"] = dict(font=dict(size=9), bgcolor="rgba(0,0,0,0)")
    ch4_layout["margin"] = dict(l=10, r=110, t=36, b=20)
    fig_ch4.update_layout(**ch4_layout)
    st.plotly_chart(fig_ch4, use_container_width=True, config={"displayModeBar":False})

    # ── DERIVED TRENDS ──
    st.markdown('<div class="section-title">🧮 DERIVED VALUE TRENDS</div>', unsafe_allow_html=True)

    df["dew_point"]   = df.apply(lambda r: calc_dew_point(r.temperature, r.humidity),   axis=1)
    df["heat_index"]  = df.apply(lambda r: calc_heat_index(r.temperature, r.humidity),  axis=1)
    df["abs_hum"]     = df.apply(lambda r: calc_absolute_humidity(r.temperature, r.humidity), axis=1)
    df["air_density"] = df.apply(lambda r: calc_air_density(r.temperature, r.pressure), axis=1)
    df["lel_pct"]     = df["ch4"].apply(calc_lel_percent)
    df["voc_idx"]     = df["gas_res"].apply(calc_voc_index)

    dc1, dc2, dc3 = st.columns(3)

    with dc1:
        fig_dp = go.Figure()
        xr = list(range(len(df)))
        fig_dp.add_trace(go.Scatter(x=xr, y=df["dew_point"].tolist(),
            line=dict(color="#4cc9f0", width=2), mode='lines', name="Dew Point",
            hovertemplate="Dew Point: %{y:.2f} °C<extra></extra>"))
        fig_dp.add_trace(go.Scatter(x=xr, y=df["heat_index"].tolist(),
            line=dict(color="#ff6b6b", width=2, dash="dash"), mode='lines', name="Heat Index",
            hovertemplate="Heat Index: %{y:.2f} °C<extra></extra>"))
        fig_dp.add_trace(go.Scatter(x=xr, y=df["temperature"].tolist(),
            line=dict(color="#ffffff", width=1, dash="dot"), mode='lines', name="Actual Temp",
            opacity=0.35, hovertemplate="Temp: %{y:.2f} °C<extra></extra>"))
        fig_dp.update_layout(
            title=dict(text="<b>Dew Point / Heat Index / Temp</b>",
                       font=dict(color="#4cc9f0", size=12, family="Rajdhani"), x=0.01),
            height=265, margin=dict(l=10, r=10, t=36, b=20),
            showlegend=True,
            legend=dict(font=dict(size=8), bgcolor="rgba(0,0,0,0)", x=0, y=1.1, orientation="h"),
            xaxis=dict(showgrid=True, gridcolor=CT["grid"], showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=True, gridcolor=CT["grid"], title="°C",
                       title_font=dict(size=9), zeroline=False),
            paper_bgcolor=CT["paper"], plot_bgcolor=CT["plot"], font=dict(color=CT["font"]),
        )
        st.plotly_chart(fig_dp, use_container_width=True, config={"displayModeBar":False})

    with dc2:
        fig_dens = go.Figure()
        fig_dens.add_trace(go.Scatter(x=list(range(len(df))), y=df["air_density"].tolist(),
            fill='tozeroy', fillcolor='rgba(6,214,160,0.07)',
            line=dict(color="#06d6a0", width=2), mode='lines', name="Air Density",
            hovertemplate="Density: %{y:.4f} kg/m³<extra></extra>"))
        fig_dens.add_trace(go.Scatter(x=list(range(len(df))), y=df["abs_hum"].tolist(),
            line=dict(color="#a855f7", width=2, dash="dash"), mode='lines',
            yaxis="y2", name="Abs. Humidity",
            hovertemplate="Abs. Hum: %{y:.3f} g/m³<extra></extra>"))
        fig_dens.update_layout(
            title=dict(text="<b>Air Density & Absolute Humidity</b>",
                       font=dict(color="#06d6a0", size=12, family="Rajdhani"), x=0.01),
            height=265, margin=dict(l=10, r=55, t=36, b=20),
            showlegend=True,
            legend=dict(font=dict(size=8), bgcolor="rgba(0,0,0,0)", x=0, y=1.1, orientation="h"),
            xaxis=dict(showgrid=True, gridcolor=CT["grid"], showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=True, gridcolor=CT["grid"], title="kg/m³",
                       title_font=dict(size=9), zeroline=False),
            yaxis2=dict(overlaying="y", side="right", title="g/m³",
                        title_font=dict(size=9), showgrid=False,
                        tickfont=dict(size=8), zeroline=False),
            paper_bgcolor=CT["paper"], plot_bgcolor=CT["plot"], font=dict(color=CT["font"]),
        )
        st.plotly_chart(fig_dens, use_container_width=True, config={"displayModeBar":False})

    with dc3:
        lel_vals = df["lel_pct"].tolist()
        lel_colors = ["#e63946" if v >= 4 else "#f77f00" if v >= 1 else "#57cc99" for v in lel_vals]
        fig_lel = go.Figure()
        fig_lel.add_trace(go.Bar(x=list(range(len(df))), y=lel_vals,
            marker_color=lel_colors, name="CH4 % LEL",
            hovertemplate="CH4 LEL: %{y:.3f}%<extra></extra>"))
        fig_lel.add_hline(y=1, line_dash="dot", line_color="#f77f00", line_width=1.2,
                          annotation_text=" 1% LEL", annotation_position="right",
                          annotation_font_color="#f77f00", annotation_font_size=9)
        fig_lel.add_hline(y=4, line_dash="dot", line_color="#e63946", line_width=1.2,
                          annotation_text=" 4% LEL", annotation_position="right",
                          annotation_font_color="#e63946", annotation_font_size=9)
        fig_lel.update_layout(
            title=dict(text="<b>Methane % of LEL</b>",
                       font=dict(color="#ffd60a", size=12, family="Rajdhani"), x=0.01),
            height=265, margin=dict(l=10, r=70, t=36, b=20),
            showlegend=False, bargap=0.1,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=True, gridcolor=CT["grid"], title="% of LEL",
                       title_font=dict(size=9), zeroline=True, zerolinecolor=CT["grid"]),
            paper_bgcolor=CT["paper"], plot_bgcolor=CT["plot"], font=dict(color=CT["font"]),
        )
        st.plotly_chart(fig_lel, use_container_width=True, config={"displayModeBar":False})

    # ── CORRELATIONS ──
    st.markdown('<div class="section-title">🔗 SENSOR CORRELATIONS</div>', unsafe_allow_html=True)
    sc1, sc2 = st.columns(2)

    with sc1:
        # Humidity vs Pressure coloured by Temperature
        # FIX: colorbar title uses dict format (not deprecated titlefont)
        fig_sc1 = go.Figure()
        fig_sc1.add_trace(go.Scatter(
            x=df["humidity"].tolist(),
            y=df["pressure"].tolist(),
            mode='markers',
            marker=dict(
                color=df["temperature"].tolist(),
                colorscale="Plasma",
                size=6, opacity=0.8,
                colorbar=dict(
                    title=dict(text="Temp °C", font=dict(size=9)),
                    thickness=10,
                    tickfont=dict(size=8),
                ),
                showscale=True,
            ),
            hovertemplate="Humidity: %{x:.1f}%<br>Pressure: %{y:.1f} hPa<extra></extra>",
        ))
        fig_sc1.update_layout(
            title=dict(text="<b>Humidity vs Pressure (colour = Temp)</b>",
                       font=dict(color="#a855f7", size=12, family="Rajdhani"), x=0.01),
            height=280, margin=dict(l=10, r=20, t=36, b=20),
            xaxis=dict(showgrid=True, gridcolor=CT["grid"], title="Humidity %",
                       title_font=dict(size=9), zeroline=False),
            yaxis=dict(showgrid=True, gridcolor=CT["grid"], title="Pressure hPa",
                       title_font=dict(size=9), zeroline=False),
            paper_bgcolor=CT["paper"], plot_bgcolor=CT["plot"], font=dict(color=CT["font"]),
        )
        st.plotly_chart(fig_sc1, use_container_width=True, config={"displayModeBar":False})

    with sc2:
        # Gas Resistance vs CH4 coloured by Humidity
        fig_sc2 = go.Figure()
        fig_sc2.add_trace(go.Scatter(
            x=df["gas_res"].tolist(),
            y=df["ch4"].tolist(),
            mode='markers',
            marker=dict(
                color=df["humidity"].tolist(),
                colorscale="Viridis",
                size=6, opacity=0.8,
                colorbar=dict(
                    title=dict(text="RH %", font=dict(size=9)),
                    thickness=10,
                    tickfont=dict(size=8),
                ),
                showscale=True,
            ),
            hovertemplate="Gas Res: %{x:.1f} kΩ<br>CH4: %{y:.1f} ppm<extra></extra>",
        ))
        fig_sc2.update_layout(
            title=dict(text="<b>Gas Resistance vs CH4 (colour = Humidity)</b>",
                       font=dict(color="#06d6a0", size=12, family="Rajdhani"), x=0.01),
            height=280, margin=dict(l=10, r=20, t=36, b=20),
            xaxis=dict(showgrid=True, gridcolor=CT["grid"], title="Gas Resistance kΩ",
                       title_font=dict(size=9), zeroline=False),
            yaxis=dict(showgrid=True, gridcolor=CT["grid"], title="CH4 ppm",
                       title_font=dict(size=9), zeroline=False),
            paper_bgcolor=CT["paper"], plot_bgcolor=CT["plot"], font=dict(color=CT["font"]),
        )
        st.plotly_chart(fig_sc2, use_container_width=True, config={"displayModeBar":False})

# ─────────────────────────────────────────────
#  ALERT LOG + RAW TABLE
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">🚨 ALERT LOG & RAW DATA</div>', unsafe_allow_html=True)
al_col, tbl_col = st.columns([1, 2])

with al_col:
    if st.session_state.alert_log:
        adf = pd.DataFrame(st.session_state.alert_log[-10:][::-1])
        st.dataframe(adf, use_container_width=True, height=220)
    else:
        st.markdown("""
        <div style="background:#0d1520;border:1px solid #1a3a5c;border-radius:8px;padding:20px;
                    text-align:center;color:#57cc99;font-family:'Share Tech Mono',monospace;
                    height:220px;display:flex;align-items:center;justify-content:center;flex-direction:column;">
          <div style="font-size:2rem;">✔</div>
          <div>ALL SENSORS NOMINAL</div>
          <div style="font-size:0.7rem;color:#7a9bb5;margin-top:6px;">No alerts detected</div>
        </div>""", unsafe_allow_html=True)

with tbl_col:
    if not df.empty:
        disp = df[["temperature","humidity","pressure","gas_res","ch4"]].tail(10).copy()
        disp.columns = ["Temp (°C)","Humidity (%)","Pressure (hPa)","Gas Res (kΩ)","CH4 (ppm)"]
        disp.index = [f"T-{len(disp)-i}" for i in range(len(disp))]
        st.dataframe(disp.style.format("{:.2f}"), use_container_width=True, height=220)

# ─────────────────────────────────────────────
#  ESP32 SETUP GUIDE
# ─────────────────────────────────────────────
with st.expander("📟 ESP32 Setup — How to connect your hardware to this dashboard"):
    st.markdown("""
    <div style="font-family:'Share Tech Mono',monospace;font-size:0.8rem;color:#7a9bb5;line-height:2;">
    <b style="color:#00f5d4; font-size:0.9rem;">STEP 1 — Wire your sensors</b><br>
    BME680 → ESP32 &nbsp;: &nbsp; VCC → 3.3V &nbsp;|&nbsp; GND → GND &nbsp;|&nbsp; SDA → GPIO 21 &nbsp;|&nbsp; SCL → GPIO 22<br>
    MQ4 &nbsp;&nbsp;&nbsp;&nbsp; → ESP32 &nbsp;: &nbsp; VCC → 5V (VBUS) &nbsp;|&nbsp; GND → GND &nbsp;|&nbsp; AOUT → GPIO 34<br><br>
    <b style="color:#00f5d4; font-size:0.9rem;">STEP 2 — Flash the sketch (Arduino IDE)</b><br>
    Install: <code>Adafruit BME680</code> library + <code>ArduinoJson</code> via Library Manager<br>
    Board: <code>ESP32 Dev Module</code> &nbsp;|&nbsp; Port: your COM port &nbsp;|&nbsp; Baud: 115200<br><br>
    <b style="color:#00f5d4; font-size:0.9rem;">STEP 3 — Get the IP address</b><br>
    Open Serial Monitor at 115200. After Wi-Fi connects, the ESP32 prints: <code>IP: 192.168.x.x</code><br><br>
    <b style="color:#00f5d4; font-size:0.9rem;">STEP 4 — Connect the dashboard</b><br>
    In the sidebar → Data Source → <b>Live ESP32</b> → paste IP address.<br>
    The dashboard calls <code>GET http://&lt;IP&gt;/data</code> and expects JSON with these keys:<br>
    <code>temperature, humidity, pressure, gas_res, ch4</code>
    </div>
    """, unsafe_allow_html=True)

    st.code("""
#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include <Adafruit_BME680.h>
#include <ArduinoJson.h>

const char* ssid     = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASS";

Adafruit_BME680 bme;   // I2C address 0x77 (SDO to 3.3V) or 0x76 (SDO to GND)
WebServer server(80);
const int MQ4_PIN = 34;   // ADC1 channel 6

// MQ4 approximate CH4 curve: ppm = 1000 * (Rs/R0)^-2.13
// R0 calibrated in clean air ≈ 9.83 kΩ (adjust per your sensor)
float mq4_ppm(int raw) {
  float volt  = raw * (3.3f / 4095.0f);
  if (volt < 0.01f) return 0.0f;
  float rs    = ((3.3f - volt) / volt) * 10.0f;   // RL = 10 kΩ load resistor
  float ratio = rs / 9.83f;                        // Rs/R0
  return 1000.0f * pow(ratio, -2.13f);
}

void handleData() {
  if (!bme.performReading()) {
    server.send(503, "application/json", "{\\"error\\":\\"BME680 read failed\\"}");
    return;
  }
  StaticJsonDocument<256> doc;
  doc["temperature"] = round(bme.temperature * 100.0f) / 100.0f;
  doc["humidity"]    = round(bme.humidity    * 100.0f) / 100.0f;
  doc["pressure"]    = round((bme.pressure / 100.0f) * 100.0f) / 100.0f;
  doc["gas_res"]     = round((bme.gas_resistance / 1000.0f) * 100.0f) / 100.0f;
  doc["ch4"]         = round(mq4_ppm(analogRead(MQ4_PIN)) * 10.0f) / 10.0f;

  String out;
  serializeJson(doc, out);
  server.send(200, "application/json", out);
}

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);    // SDA=21, SCL=22

  if (!bme.begin(0x77)) {
    Serial.println("BME680 not found! Check wiring / I2C address.");
    while (1) delay(100);
  }
  bme.setTemperatureOversampling(BME680_OS_8X);
  bme.setHumidityOversampling(BME680_OS_2X);
  bme.setPressureOversampling(BME680_OS_4X);
  bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
  bme.setGasHeater(320, 150);   // 320°C for 150ms

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println();
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());   // <-- copy this into the dashboard sidebar

  server.on("/data", HTTP_GET, handleData);
  server.begin();
  Serial.println("HTTP server started — dashboard ready");
}

void loop() {
  server.handleClient();
}
""", language="cpp")

# ─────────────────────────────────────────────
#  FOOTER + AUTO REFRESH
# ─────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;margin-top:28px;padding:14px;
            font-family:'Share Tech Mono',monospace;font-size:0.7rem;color:#3a5a7a;
            border-top:1px solid #1a3a5c;">
  AeroSense Mission Monitor v2.0 &nbsp;·&nbsp; ESP32 + BME680 + MQ4 &nbsp;·&nbsp;
  Aerial Environmental Analytics &nbsp;·&nbsp; {len(df)} samples &nbsp;·&nbsp;
  {datetime.now().strftime('%H:%M:%S')}
</div>
""", unsafe_allow_html=True)

if st.session_state.running:
    time.sleep(refresh_rate)
    st.rerun()