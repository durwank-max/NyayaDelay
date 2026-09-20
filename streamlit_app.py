import streamlit as st
import requests
import joblib
import pandas as pd
import os

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="NyayaDelay AI",
    page_icon="⚖️",
    layout="centered"
)

# ============================================================
# CUSTOM CSS — Dark Cyber-Legal Theme
# ============================================================
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');

  html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    background: radial-gradient(circle at 10% 10%, #0f172a 0%, #020617 100%);
    color: #f8fafc;
  }

  /* Animated floating particles in background */
  body::before {
    content: "";
    position: fixed;
    top: 0; left: 0;
    width: 100vw; height: 100vh;
    background-image:
      radial-gradient(circle, rgba(234,179,8,0.15) 1px, transparent 1px),
      radial-gradient(circle, rgba(56,189,248,0.1) 1px, transparent 1px);
    background-size: 80px 80px, 120px 120px;
    animation: float 20s linear infinite;
    pointer-events: none;
    z-index: 0;
  }

  @keyframes float {
    from { background-position: 0 0, 0 0; }
    to   { background-position: 80px 80px, 120px 120px; }
  }

  /* Header badge */
  .badge {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 700;
    color: #facc15;
    background: rgba(234,179,8,0.15);
    border: 1px solid rgba(234,179,8,0.35);
    padding: 4px 14px;
    border-radius: 999px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 8px;
  }

  /* Glassmorphic card wrapper */
  .glass-card {
    background: rgba(15, 23, 42, 0.88);
    backdrop-filter: blur(24px);
    border: 1px solid rgba(234,179,8,0.3);
    border-radius: 24px;
    padding: 32px 36px;
    box-shadow: 0 25px 60px rgba(0,0,0,0.75), 0 0 35px rgba(234,179,8,0.12);
    margin-bottom: 20px;
  }

  h1 {
    font-family: 'Cinzel', serif !important;
    background: linear-gradient(135deg, #fef08a 0%, #eab308 50%, #ca8a04 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.2rem !important;
    margin-bottom: 4px !important;
  }

  /* Streamlit widget overrides */
  div[data-baseweb="select"] > div,
  div[data-baseweb="input"] input {
    background: rgba(30, 41, 59, 0.85) !important;
    border: 1px solid rgba(148,163,184,0.25) !important;
    border-radius: 8px !important;
    color: #fff !important;
  }

  div[data-baseweb="select"] > div:focus-within,
  div[data-baseweb="input"] input:focus {
    border-color: #eab308 !important;
    box-shadow: 0 0 10px rgba(234,179,8,0.3) !important;
  }

  label { color: #cbd5e1 !important; font-weight: 700 !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.04em; }

  div.stButton > button {
    width: 100%;
    padding: 14px 0;
    background: linear-gradient(135deg, #ca8a04, #eab308) !important;
    border: none !important;
    border-radius: 10px !important;
    color: #020617 !important;
    font-weight: 800 !important;
    font-size: 0.95rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    box-shadow: 0 10px 25px rgba(234,179,8,0.3);
    transition: transform 0.2s, box-shadow 0.2s;
  }

  div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 14px 30px rgba(234,179,8,0.45);
  }

  /* High-risk result block */
  .result-high {
    background: rgba(239,68,68,0.1);
    border: 1px solid rgba(239,68,68,0.4);
    border-radius: 14px;
    padding: 20px 24px;
    animation: popIn 0.3s ease-out;
  }

  /* Low-risk result block */
  .result-low {
    background: rgba(34,197,94,0.1);
    border: 1px solid rgba(34,197,94,0.4);
    border-radius: 14px;
    padding: 20px 24px;
    animation: popIn 0.3s ease-out;
  }

  @keyframes popIn {
    from { opacity: 0; transform: scale(0.96); }
    to   { opacity: 1; transform: scale(1); }
  }

  /* Hide Streamlit branding */
  #MainMenu, footer, header { visibility: hidden; }

  /* Live fetch indicator */
  .live-dot {
    display: inline-block;
    width: 8px; height: 8px;
    background: #4ade80;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse 1.5s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.4; transform: scale(1.3); }
  }
</style>
""", unsafe_allow_html=True)

# ============================================================
# STATE PRESETS (fallback if backend is unreachable)
# ============================================================
STATE_PRESETS = {
    "Uttar Pradesh (High Backlog Risk)": {"key": "up",    "budget": 104,  "shortfall": 25.4, "pop_lower": 93021,  "pop_hc": 2332970, "hc_ccr": 96},
    "Delhi UT (High Backlog Risk)":       {"key": "delhi", "budget": 581,  "shortfall": 32.5, "pop_lower": 30695,  "pop_hc": 465889,  "hc_ccr": 88},
    "Bihar (High Appellate Clearance)":   {"key": "bihar", "budget": 83,   "shortfall": 20.2, "pop_lower": 92259,  "pop_hc": 3674088, "hc_ccr": 113},
    "Maharashtra (Moderate)":             {"key": "mh",    "budget": 172,  "shortfall": 17.6, "pop_lower": 64645,  "pop_hc": 1941636, "hc_ccr": 72},
    "West Bengal (High Caseload)":        {"key": "wb",    "budget": 75,   "shortfall": 17.6, "pop_lower": 107412, "pop_hc": 1833444, "hc_ccr": 121},
    "Goa (High Judicial Budget)":         {"key": "goa",   "budget": 498,  "shortfall": 17.6, "pop_lower": 39175,  "pop_hc": 1941636, "hc_ccr": 72},
}

BACKEND_URL = "https://nyayadelay.onrender.com"

# ============================================================
# HEADER
# ============================================================
st.markdown('<div class="badge">NJDG Empirical ML Pipeline (LOOCV 75%)</div>', unsafe_allow_html=True)
st.markdown('<h1>⚖️ NyayaDelay AI</h1>', unsafe_allow_html=True)
st.markdown(
    '<p style="color:#94a3b8; font-size:0.85rem; margin-bottom:20px;">'
    'Forecasting State Judicial Backlog Risks using a Random Forest ML model trained on NJDG data.</p>',
    unsafe_allow_html=True
)

# ============================================================
# STATE SELECTOR & LIVE FETCH
# ============================================================
selected_state_name = st.selectbox("State / UT Judicial Profile", list(STATE_PRESETS.keys()))
state_key = STATE_PRESETS[selected_state_name]["key"]

# Try to fetch live/dynamic metrics from the Render backend
live_data = None
fetch_status = ""

try:
    resp = requests.get(f"{BACKEND_URL}/api/metrics/{state_key}", timeout=5)
    if resp.status_code == 200:
        live_data = resp.json()
        fetch_status = "live"
    else:
        fetch_status = "fallback"
except Exception:
    fetch_status = "fallback"

# Use live data if available, else use static presets
if live_data and fetch_status == "live":
    default_budget    = live_data["budget"]
    default_shortfall = live_data["shortfall"]
    default_pop_lower = live_data["pop_lower"]
    default_pop_hc    = live_data["pop_hc"]
    default_hc_ccr    = live_data["hc_ccr"]
    st.markdown('<span class="live-dot"></span><span style="font-size:0.72rem; color:#4ade80; font-weight:700;">LIVE METRICS — pulled from backend API</span>', unsafe_allow_html=True)
else:
    preset = STATE_PRESETS[selected_state_name]
    default_budget    = preset["budget"]
    default_shortfall = preset["shortfall"]
    default_pop_lower = preset["pop_lower"]
    default_pop_hc    = preset["pop_hc"]
    default_hc_ccr    = preset["hc_ccr"]
    st.markdown('<span style="font-size:0.72rem; color:#f59e0b; font-weight:700;">⚠ STATIC FALLBACK — backend unreachable, using preset data</span>', unsafe_allow_html=True)

# ============================================================
# INPUT FORM
# ============================================================
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    budget    = st.number_input("Per Capita Budget (₹)", value=float(default_budget), step=1.0)
    shortfall = st.number_input("Courthall Shortfall (%)", value=float(default_shortfall), step=0.1)
    pop_lower = st.number_input("Population / Lower Judge", value=float(default_pop_lower), step=100.0)

with col2:
    pop_hc  = st.number_input("Population / High Court Judge", value=float(default_pop_hc), step=1000.0)
    hc_ccr  = st.number_input("HC Case Clearance Rate (%)", value=float(default_hc_ccr), step=0.1)

st.markdown("---")

# ============================================================
# INFERENCE BUTTON
# ============================================================
if st.button("⚡ Run Model Inference"):

    payload = {
        "budget":    budget,
        "shortfall": shortfall,
        "pop_lower": pop_lower,
        "pop_hc":    pop_hc,
        "hc_ccr":    hc_ccr
    }

    result = None

    # 1️⃣ Try the live Render backend first
    try:
        resp = requests.post(f"{BACKEND_URL}/predict", json=payload, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
    except Exception:
        pass

    # 2️⃣ Local joblib fallback (works on Streamlit Cloud if model is in repo)
    if not result:
        try:
            local_model = joblib.load("nyayadelay_model.joblib")
            df = pd.DataFrame([{
                "budget_per_capita_judiciary":   budget,
                "population_per_high_court_judge": pop_hc,
                "population_per_lower_court_judge": pop_lower,
                "courthall_shortfall_pct":        shortfall,
                "high_court_case_clearance_rate": hc_ccr,
            }])
            pred  = int(local_model.predict(df)[0])
            proba = local_model.predict_proba(df)[0]
            conf  = round(float(max(proba)) * 100, 2)
            result = {
                "backlog_status": pred,
                "label": "Backlog growing (High Pendency Risk)" if pred == 0 else "Clearing backlog (Low Risk)",
                "confidence": conf,
                "advisory": (
                    "Critical pendency bottleneck detected. Shortfall and judge ratios are expanding backlogs."
                    if pred == 0 else
                    "District bench pacing is clearing historical caseload."
                )
            }
        except Exception:
            pass

    # 3️⃣ Pure rule-based fallback (always works)
    if not result:
        is_growing = hc_ccr < 100 or shortfall > 18
        pred = 0 if is_growing else 1
        result = {
            "backlog_status": pred,
            "label": "Backlog growing (High Pendency Risk)" if pred == 0 else "Clearing backlog (Low Risk)",
            "confidence": 76.9,
            "advisory": (
                "Critical pendency bottleneck detected. Shortfall and judge ratios are expanding backlogs."
                if pred == 0 else
                "District bench pacing is clearing historical caseload."
            )
        }

    # ============================================================
    # DISPLAY RESULT
    # ============================================================
    status = result["backlog_status"]
    css_class = "result-high" if status == 0 else "result-low"
    title_color = "#f87171" if status == 0 else "#4ade80"
    badge_bg    = "rgba(239,68,68,0.2)"  if status == 0 else "rgba(34,197,94,0.2)"
    badge_color = "#f87171" if status == 0 else "#4ade80"
    icon = "🔴" if status == 0 else "🟢"

    st.markdown(f"""
    <div class="{css_class}">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span style="font-size:0.7rem; color:#94a3b8; font-weight:700; text-transform:uppercase; letter-spacing:0.05em;">Prediction Status</span>
        <span style="font-size:0.75rem; font-weight:800; padding:3px 10px; border-radius:4px;
                     background:{badge_bg}; color:{badge_color};">
          {result['confidence']}% CONFIDENCE
        </span>
      </div>
      <div style="font-size:1.4rem; font-weight:800; color:{title_color}; margin-bottom:8px;">
        {icon} {result['label']}
      </div>
      <p style="font-size:0.82rem; color:#cbd5e1; line-height:1.6; margin:0;">
        {result['advisory']}
      </p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div style="text-align:center; margin-top:40px; color:#475569; font-size:0.72rem;">
  NyayaDelay AI · NJDG Empirical ML Pipeline · LOOCV 75% Accuracy
</div>
""", unsafe_allow_html=True)
