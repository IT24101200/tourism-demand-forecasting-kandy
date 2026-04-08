"""
pages/3_🎛️_What_If_Simulator.py  —  What-If Scenario Simulator
"""
import sys
import pickle
import math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from utils.sidebar import render_sidebar
from utils.auth import require_auth
from utils.theme import get_theme, apply_plotly_theme, apply_custom_theme, render_page_banner

require_auth()
theme = get_theme()

BASE_DIR = Path(__file__).parent.parent
RF_PATH = BASE_DIR / "models" / "rf_model.pkl"
SCALER_PATH = BASE_DIR / "models" / "feature_scaler.pkl"

st.set_page_config(
    page_title="What-If Simulator | Tourist DSS",
    page_icon="🎛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_theme()

# ── Page-level styles ────────────────────────────────────────────
st.markdown(f"""
<style>
    /* ── Result card ── */
    .result-card {{
        background: {theme['surface']};
        backdrop-filter: blur(24px);
        border: 1px solid {theme['border']};
        border-radius: 20px;
        padding: 36px 40px;
        text-align: center;
        box-shadow: 0 8px 30px rgba(0,0,0,0.08);
    }}
    .result-label {{
        color: {theme['text_muted']};
        font-size: 1rem;
        font-weight: 700;
        font-family: 'Inter', sans-serif;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }}
    .result-value {{
        font-size: 3.6rem;
        font-weight: 800;
        margin: 8px 0;
        font-family: 'Manrope', sans-serif;
        color: {theme['text_main']};
    }}

    /* ── Info cards (scenario breakdown) ── */
    .info-card {{
        background: {theme['surface_low']};
        border: 1px solid {theme['border']};
        border-radius: 10px;
        padding: 12px 16px;
        margin: 5px 0;
        font-family: 'Inter', sans-serif;
    }}

    /* ── Guide box ── */
    .guide-box {{
        background: transparent;
        border: 1px solid {theme['border']};
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 28px;
    }}
    .guide-title {{
        color: {theme['accent_dim']};
        font-family: 'Manrope', sans-serif;
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .guide-step {{
        display: flex;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 10px;
    }}
    .guide-step-num {{
        background: {theme['surface_low']};
        color: {theme['accent']};
        font-family: 'Manrope', sans-serif;
        font-weight: 800;
        font-size: 0.75rem;
        min-width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        margin-top: 1px;
    }}
    .guide-step-text {{
        color: {theme['text_muted']};
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        line-height: 1.6;
    }}
    .guide-step-text strong {{
        color: {theme['text_main']};
    }}

    /* ── Section panel headers ── */
    .panel-header {{
        color: {theme['text_main']};
        font-family: 'Manrope', sans-serif;
        font-size: 1.15rem;
        font-weight: 700;
        margin: 0 0 6px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .panel-desc {{
        color: {theme['text_muted']};
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        margin: 0 0 16px 0;
        line-height: 1.5;
    }}

    /* ── Step badge ── */
    .step-badge {{
        color: #fff;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 0.75rem;
        padding: 5px 14px;
        border-radius: 20px;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }}
    .step-badge.step-1 {{ background: linear-gradient(135deg, {theme['accent_dim']}, {theme['accent']}); }}
    .step-badge.step-2 {{ background: linear-gradient(135deg, {theme['accent2_dim']}, {theme['accent2']}); }}
    .step-badge.step-3 {{ background: linear-gradient(135deg, {theme['warning']}, {theme['danger']}); }}

    /* ── Recommendation cards ── */
    .rec-card {{
        background: {theme['surface_low']};
        border: 1px solid {theme['border']};
        border-radius: 16px;
        padding: 22px;
        height: 100%;
        transition: all 0.3s ease;
    }}
    .rec-card:hover {{
        border-color: {theme['accent_dim']};
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }}
    .rec-icon {{ font-size: 2rem; margin-bottom: 6px; }}
    .rec-title {{
        color: {theme['text_main']};
        font-family: 'Manrope', sans-serif;
        font-weight: 700;
        font-size: 1.08rem;
        margin: 8px 0;
    }}
    .rec-body {{
        color: {theme['text_muted']};
        font-family: 'Inter', sans-serif;
        font-size: 0.92rem;
        line-height: 1.6;
    }}

    /* ── Run Simulation button override ── */
    div[data-testid="stButton"] > button[kind="primary"] {{
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
        color: #ffffff !important;
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        font-family: 'Manrope', sans-serif !important;
        padding: 16px 32px !important;
        border-radius: 14px !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(239, 68, 68, 0.3) !important;
        letter-spacing: 0.03em !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }}
    div[data-testid="stButton"] > button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(239, 68, 68, 0.4) !important;
    }}
    div[data-testid="stButton"] > button[kind="primary"]:active {{
        transform: translateY(0px) !important;
    }}
</style>
""", unsafe_allow_html=True)

render_sidebar(active_page="What-If Simulator")

# ── Load model ────────────────────────────────────────────────────
@st.cache_resource
def load_model():
    rf_model, scaler_obj, feat_cols, lstm_model, y_scaler = None, None, [], None, None
    if not RF_PATH.exists() or not SCALER_PATH.exists():
        return None, None, None, None, None
    with open(RF_PATH, "rb") as f:
        rf_model = pickle.load(f)
        
    lstm_path = BASE_DIR / "models" / "lstm_model.keras"
    if lstm_path.exists():
        try:
            import tensorflow as tf
            lstm_model = tf.keras.models.load_model(lstm_path)
        except Exception as e:
            print("Failed to load LSTM:", e)
    with open(SCALER_PATH, "rb") as f:
        scaler_obj = pickle.load(f)

    feat_cols = rf_model.feature_names_in_ if hasattr(rf_model, "feature_names_in_") else []

    if isinstance(scaler_obj, tuple):
        scaler = scaler_obj[0]
        if not len(feat_cols) and len(scaler_obj) > 1:
            feat_cols = scaler_obj[1]
        if len(scaler_obj) > 2:
            y_scaler = scaler_obj[2]
    else:
        scaler = scaler_obj
    return rf_model, scaler, feat_cols, lstm_model, y_scaler

@st.cache_data
def get_baseline():
    csv_path = BASE_DIR / "kandy_festival_demand_NOMISSING.csv"
    if not csv_path.exists():
        return None
    df = pd.read_csv(csv_path, on_bad_lines="skip")
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df["estimated_weekly_kandy_arrivals"] = pd.to_numeric(df["estimated_weekly_kandy_arrivals"], errors="coerce")
    return {
        "mean": df["estimated_weekly_kandy_arrivals"].mean(),
        "median": df["estimated_weekly_kandy_arrivals"].median(),
        "max": df["estimated_weekly_kandy_arrivals"].max(),
        "min": df["estimated_weekly_kandy_arrivals"].min()
    }

rf_model, scaler, feat_cols, lstm_model, y_scaler = load_model()
baseline = get_baseline()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
render_page_banner(
    title="What-If Scenario Simulator",
    subtitle="Model hypothetical scenarios and see AI-driven predictions for weekly tourist arrivals in Kandy.",
    icon="🎛️",
)

if rf_model is None:
    st.warning("""
    ⚠️ **Model not found.**
    Please run the training pipeline first:
    ```
    python train_models.py
    ```
    Then refresh this page.
    """)
    st.stop()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HOW TO USE — User Instructions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.expander("📖  **How to Use This Simulator**  —  Click to expand", expanded=False):
    st.markdown("""
<div class="guide-box">
        <div class="guide-title">🎯 Quick Start Guide</div>
        <div class="guide-step">
            <div class="guide-step-num">1</div>
            <div class="guide-step-text"><strong>Choose a Preset</strong> — Start with a Quick Preset (e.g. "Peak Esala Perahera") to auto-fill realistic values, or select "Custom Scenario" to build from scratch.</div>
        </div>
        <div class="guide-step">
            <div class="guide-step-num">2</div>
            <div class="guide-step-text"><strong>Navigate the Tabs</strong> — The simulator utilizes three distinct tabs: 🕒 Timeline, 📍 Geopolitics, and 🌦️ Weather. Set your experimental parameters inside each tab.</div>
        </div>
        <div class="guide-step">
            <div class="guide-step-num">3</div>
            <div class="guide-step-text"><strong>Real-Time Predictions</strong> — There is no run button! The AI prediction engine instantly processes any changes you make and dynamically updates the visual insights below.</div>
        </div>
        <div class="guide-step">
            <div class="guide-step-num">4</div>
            <div class="guide-step-text"><strong>Analyze Market Impact</strong> — Use the Waterfall bridge chart at the bottom to visualize exactly how your configured scenario shifts the baseline tourism demand.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.info("💡 **Tip:** Compare different scenarios by tweaking individual tabs (e.g. toggle a festival or severe monsoon) to immediately see the impact of that specific factor.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 1: PRESET SELECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(f"""
<div style="display:flex; align-items:center; gap:12px; margin: 28px 0 10px 0;">
    <span class="step-badge step-1">Step 1</span>
    <span style="color:{theme['accent']}; font-family:'Manrope',sans-serif; font-size:1.35rem; font-weight:800;">Choose a Scenario Preset</span>
</div>
<p style="color:{theme['text_muted']}; font-family:'Inter',sans-serif; font-size:0.95rem; margin:0 0 14px 0;">
    Select a pre-configured scenario to auto-fill parameters, or choose "Custom Scenario" to set everything manually.
</p>
""", unsafe_allow_html=True)

preset = st.selectbox("⚡ Quick Presets", [
    "Custom Scenario",
    "Peak Esala Perahera (Ideal Weather)",
    "Severe Monsoon Season",
    "Economic Crisis Impact"
], label_visibility="collapsed",
   help="Select a preset to instantly load realistic scenario parameters.")

# Define defaults based on preset
def_esala = preset == "Peak Esala Perahera (Ideal Weather)"
def_rain = 250.0 if preset == "Severe Monsoon Season" else (30.0 if def_esala else 50.0)
def_temp = 24.0 if preset == "Severe Monsoon Season" else (26.0 if def_esala else 25.0)
def_hum = 85.0 if preset == "Severe Monsoon Season" else (65.0 if def_esala else 75.0)
def_econ = preset == "Economic Crisis Impact"
def_week = 33 if def_esala else (22 if preset == "Severe Monsoon Season" else 33)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 2: CONTROL PANELS (2-column layout)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(f"""
<div style="display:flex; align-items:center; gap:12px; margin: 20px 0 14px 0;">
    <span class="step-badge step-2">Step 2</span>
    <span style="color:{theme['accent2']}; font-family:'Manrope',sans-serif; font-size:1.35rem; font-weight:800;">Configure Scenario Parameters</span>
</div>
<p style="color:{theme['text_muted']}; font-family:'Inter',sans-serif; font-size:0.95rem; margin:0 0 14px 0;">
    Fine-tune the temporal, environmental, and economic conditions below. All fields have sensible defaults.
</p>
""", unsafe_allow_html=True)

tab_time, tab_geom, tab_weather = st.tabs(["🕒 Timeline & Market", "📍 Geopolitics & Events", "🌦️ Weather & Environment"])

# ── TAB 1 ──
with tab_time:
    # -- Temporal Context --
    with st.container(border=True):
        st.markdown("""
        <div class="panel-header">🗓️ Temporal Context</div>
        <div class="panel-desc">Set the target week, month, and year for your simulation scenario.</div>
        """, unsafe_allow_html=True)

        import datetime
        if def_esala: default_date = datetime.date(2026, 8, 15)
        elif preset == "Severe Monsoon Season": default_date = datetime.date(2026, 5, 25)
        else: default_date = datetime.date(2026, 8, 15)

        target_date = st.date_input("Target Scenario Date", value=default_date, help="Select the exact target date.")
        year = target_date.year
        month = target_date.month
        week_of_year = target_date.isocalendar()[1]
        quarter = (month - 1) // 3 + 1

    # -- Market Momentum --
    with st.container(border=True):
        st.markdown("""
        <div class="panel-header">📈 Market Momentum</div>
        <div class="panel-desc">How many tourists visited in the previous week? This is the AI model's primary momentum anchor.</div>
        """, unsafe_allow_html=True)

        avg_arr = int(baseline["mean"]) if baseline else 15000
        def_lag = avg_arr * 1.5 if def_esala else (avg_arr * 0.5 if def_econ else (avg_arr * 0.7 if preset == "Severe Monsoon Season" else avg_arr))

        def_idx = 0
        if preset == "Peak Esala Perahera (Ideal Weather)": def_idx = 4
        elif preset == "Economic Crisis Impact": def_idx = 1
        elif preset == "Severe Monsoon Season": def_idx = 1

        momentum_preset = st.selectbox(
            "Market State (Quick Select)",
            ["Custom (Manual Override)", "Quiet / Low Season (~5k)", "Average Run-Rate (~15k)", "High Season Surge (~30k)", "Peak Festival Surge (~55k)"],
            index=def_idx,
            help="Choose a market state to auto-set recent arrivals, or select Custom to enter your own value."
        )

        if "Quiet" in momentum_preset: target_val = 5000
        elif "Average" in momentum_preset: target_val = 15000
        elif "High Season" in momentum_preset: target_val = 30000
        elif "Peak Festival" in momentum_preset: target_val = 55000
        else: target_val = int(def_lag)

        lag_val = st.number_input("Exact Arrivals (Last 7 Days)", min_value=0, max_value=200000, step=1000, value=target_val,
            help="The exact number of arrivals in the most recent 7-day window. This strongly influences the prediction.")

# ── TAB 2 ──
with tab_geom:
    # -- Geopolitical & Cultural --
    with st.container(border=True):
        st.markdown("""
        <div class="panel-header">📍 Geopolitical & Cultural Climate</div>
        <div class="panel-desc">Select active festivals and any crisis conditions. These are major demand drivers.</div>
        """, unsafe_allow_html=True)

        festival_choice = st.selectbox(
            "Primary Cultural Event",
            ["None / Normal Week", "Esala Perahera (Aug)", "Esala Preparation Week (Jul)",
             "Poson Perahera (Jun)", "Vesak Week (May)", "Sinhala/Tamil New Year (Apr)", "Christmas / New Year (Dec–Jan)"],
            index=1 if def_esala else 0,
            help="Cultural events significantly boost tourist demand, especially Esala Perahera."
        )
        is_esala = festival_choice == "Esala Perahera (Aug)"
        is_esala_prep = festival_choice == "Esala Preparation Week (Jul)"
        is_poson = festival_choice == "Poson Perahera (Jun)"
        is_vesak = festival_choice == "Vesak Week (May)"
        is_stny = festival_choice == "Sinhala/Tamil New Year (Apr)"
        is_xmas = festival_choice == "Christmas / New Year (Dec–Jan)"

        crisis_choice = st.selectbox(
            "Operational Environment",
            ["Normal Operations", "Economic Crisis (Fuel/Inflation)", "COVID-19 Lockdown", "Easter Attacks / Security"],
            index=1 if def_econ else 0,
            help="Crisis conditions severely suppress tourism demand."
        )
        is_normal = crisis_choice == "Normal Operations"
        is_econ = "Economic Crisis" in crisis_choice
        is_covid = "COVID-19" in crisis_choice
        is_easter = "Easter Attacks" in crisis_choice

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            is_poya = st.toggle("Includes Poya Day", help="Poya full-moon days are public holidays in Sri Lanka.")
        with col_t2:
            is_school_hol = st.toggle("School Holiday", help="School holidays increase domestic travel.")
        is_any_fest = int(any([is_esala, is_esala_prep, is_poson, is_vesak, is_stny, is_xmas, is_poya]))

with tab_weather:
    # -- Weather Conditions --
    with st.container(border=True):
        st.markdown("""
        <div class="panel-header">🌦️ Meteorological Conditions</div>
        <div class="panel-desc">Set weather parameters. Rainfall above 150mm will automatically trigger monsoon mode.</div>
        """, unsafe_allow_html=True)

        w_col1, w_col2, w_col3 = st.columns(3)
        with w_col1:
            rainfall_str = st.number_input("🌧️ Rainfall (mm)", min_value=0.0, max_value=1500.0, value=float(def_rain), step=10.0, help="Above 150mm is heavy monsoon.")
        with w_col2:
            temp_str = st.number_input("🌡️ Temp (°C)", min_value=15.0, max_value=40.0, value=float(def_temp), step=0.5)
        with w_col3:
            humidity_str = st.number_input("💧 Humidity (%)", min_value=0.0, max_value=100.0, value=float(def_hum), step=1.0)
        
        is_monsoon = st.toggle("Severe Monsoon Active", value=bool(rainfall_str > 150),
            help="Automatically enabled when rainfall exceeds 150mm. Can be manually toggled.")


# ── Compute festival scores ──
festival_scores = {
    "Esala": (is_esala, 10, 4.0),
    "Esala Prep": (is_esala_prep, 8, 2.5),
    "Xmas": (is_xmas, 8, 3.0),
    "Vesak": (is_vesak, 6, 1.8),
    "Stny": (is_stny, 5, 1.5),
    "Poson": (is_poson, 5, 1.4),
    "Poya": (is_poya, 3, 1.2),
}

active_scores = [s for (b, s, m) in festival_scores.values() if b]
intensity = max(active_scores) if active_scores else 0
multiplier = max([m for (b, s, m) in festival_scores.values() if b] + [1.0])

if is_esala: days_to_esala = 0
elif is_esala_prep: days_to_esala = 7
else:
    target_date = pd.Timestamp(f"{year}-08-10")
    sim_date = pd.Timestamp(f"{year}-01-01") + pd.Timedelta(days=(week_of_year-1)*7)
    days_to_esala = (target_date - sim_date).days
    if days_to_esala < -15:
        target_date = pd.Timestamp(f"{year+1}-08-10")
        days_to_esala = (target_date - sim_date).days


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PREDICTION ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rainfall_mm = float(rainfall_str)
temp_c = float(temp_str)
humidity_pct = float(humidity_str)
feature_dict = {
    "week_of_year": week_of_year,
    "month": month,
    "quarter": quarter,
    "year": year,
    "festival_intensity_score": intensity,
    "festival_demand_multiplier": multiplier,
    "is_esala_perahera": int(is_esala),
    "is_esala_preparation": int(is_esala_prep),
    "is_esala_post_festival": 0,
    "is_august_buildup": int(month == 8 and not is_esala),
    "is_poson_perahera": int(is_poson),
    "is_vesak": int(is_vesak),
    "is_sinhala_tamil_new_year": int(is_stny),
    "is_christmas_new_year": int(is_xmas),
    "is_deepavali": 0,
    "is_thai_pongal": 0,
    "is_monthly_poya_week": int(is_poya),
    "poya_days_away": 15 if not is_poya else 0,
    "is_school_holiday": int(is_school_hol),
    "is_any_festival": is_any_fest,
    "days_until_next_esala": days_to_esala,
    "avg_weekly_rainfall_mm": rainfall_mm,
    "avg_temp_celsius": temp_c,
    "avg_humidity_pct": humidity_pct,
    "is_monsoon_week": int(is_monsoon),
    "is_covid_period": int(is_covid),
    "is_easter_attack_period": int(is_easter),
    "is_economic_crisis": int(is_econ),
    "is_normal_operation": is_normal,
    "arrivals_lag_1": lag_val,
    "arrivals_lag_2": lag_val,
    "arrivals_lag_4": lag_val,
    "arrivals_lag_8": lag_val,
    "arrivals_lag_13": lag_val
}

try:
    input_vec = np.array([feature_dict.get(c, 0.0) for c in feat_cols]).reshape(1, -1)
    
    if lstm_model is None:
        st.error("Deep Learning engine not loaded. Please train the model.")
        st.stop()
        
    scaled_in = scaler.transform(input_vec) if scaler else input_vec
    seq_in = np.tile(scaled_in, (1, 12, 1)) # Duplicate scenario for 12-week sequential lookback
    pred_scaled = float(lstm_model.predict(seq_in, verbose=0)[0][0])
    if y_scaler is not None:
        raw_pred = float(y_scaler.inverse_transform([[pred_scaled]])[0][0])
    else:
        raw_pred = pred_scaled

    # Safety bounding
    min_possible = lag_val * 0.2
    max_possible = lag_val * 4.0
    predicted = max(min_possible, min(raw_pred, max_possible))
    predicted = max(0.0, round(predicted))

except Exception as e:
    st.error("❌ Prediction failed. Please check your inputs and try again.")
    st.stop()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESULTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

st.markdown(f"""
<div style="display:flex; align-items:center; gap:12px; margin: 8px 0 10px 0;">
    <span style="background:linear-gradient(135deg,{theme['accent2_dim']},{theme['accent2']}); color:#ffffff; font-family:'Inter',sans-serif;
                 font-weight:800; font-size:0.75rem; padding:5px 14px; border-radius:20px; letter-spacing:0.06em;
                 text-transform:uppercase;">Result</span>
    <span style="color:{theme['accent2']}; font-family:'Manrope',sans-serif; font-size:1.4rem; font-weight:800;">🔮 AI Prediction Result</span>
</div>
<p style="color:{theme['text_muted']}; font-family:'Inter',sans-serif; font-size:0.95rem; margin:0 0 14px 0;">
    The AI model has analyzed your scenario parameters and generated the following prediction.
</p>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background:{theme['surface_low']}; border:1px solid {theme['border']}; border-radius:12px;
            padding:12px 18px; margin:4px 0 20px 0; display:flex; align-items:center; gap:10px;">
    <span style="font-size:1.15rem">⚠️</span>
    <span style="color:{theme['warning']}; font-family:'Inter',sans-serif; font-size:0.92rem; font-weight:600; line-height:1.4;">
        Disclaimer: These numbers are simulated "What-If" projections for strategic planning. They do not represent guaranteed future outcomes.
    </span>
</div>
""", unsafe_allow_html=True)

delta_vs_mean = predicted - lag_val
delta_pct = (delta_vs_mean / lag_val) * 100 if lag_val > 0 else 0
risk_color = "#4edea3" if delta_vs_mean >= 0 else "#ffb4ab"
delta_sign = "+" if delta_vs_mean >= 0 else ""
daily_avg = predicted / 7
est_revenue = predicted * 1036  # $1,036 avg national spend per tourist (from historical data)
est_revenue_lkr = est_revenue * 300  # ~300 LKR per USD


# Demand level classification
peak_val = baseline["max"] if baseline else 55000
if predicted >= peak_val * 0.8:
    demand_level, demand_color, demand_desc = "VERY HIGH", "{theme['danger']}", "Demand is near or above historical peak levels. Maximum resource allocation recommended."
    demand_pct = min(100, int((predicted / peak_val) * 100))
elif predicted >= lag_val * 1.2:
    demand_level, demand_color, demand_desc = "HIGH", "{theme['warning']}", "Demand is significantly above the baseline. Consider surge pricing and extra staffing."
    demand_pct = min(85, int((predicted / peak_val) * 100))
elif predicted >= lag_val * 0.8:
    demand_level, demand_color, demand_desc = "MODERATE", "{theme['accent_dim']}", "Demand is within typical range. Standard operations should be sufficient."
    demand_pct = min(60, int((predicted / peak_val) * 100))
elif predicted >= lag_val * 0.4:
    demand_level, demand_color, demand_desc = "LOW", "{theme['text_dim']}", "Demand is below average. Consider promotional campaigns to attract visitors."
    demand_pct = min(35, int((predicted / peak_val) * 100))
else:
    demand_level, demand_color, demand_desc = "VERY LOW", "{theme['text_dim']}", "Demand is critically low. Aggressive discounting and cost-cutting measures may be needed."
    demand_pct = max(5, int((predicted / peak_val) * 100))

res_col, gauge_col = st.columns([1.1, 1])

with res_col:
    # Determine status badge
    if not is_normal:
        status_emoji, status_text, status_bg = "⚠️", "Crisis Active", "{theme['surface_low']}"
    elif intensity > 0:
        status_emoji, status_text, status_bg = "🎭", "High Demand Event", "{theme['surface_low']}"
    else:
        status_emoji, status_text, status_bg = "✅", "Normal Operations", "{theme['surface_low']}"

    # ── Main prediction card ──
    st.markdown(f"""
    <div class="result-card">
        <div class="result-label">Predicted Weekly Arrivals</div>
        <div class="result-value">{predicted:,.0f}</div>
        <div style="color:{risk_color}; font-size:1.25rem; font-weight:800; margin-bottom:10px; font-family:'Inter',sans-serif; letter-spacing:0.02em;">
            {delta_sign}{delta_pct:.1f}% vs baseline momentum
        </div>
        <!-- Demand Level Bar -->
        <div style="margin:16px auto; max-width:320px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <span style="color:{theme['text_dim']}; font-family:'Inter',sans-serif; font-size:0.78rem; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;">Demand Level</span>
                <span style="color:{demand_color}; font-family:'Manrope',sans-serif; font-size:0.85rem; font-weight:800;">{demand_level}</span>
            </div>
            <div style="background:rgba(255,255,255,0.06); border-radius:8px; height:10px; overflow:hidden;">
                <div style="width:{demand_pct}%; height:100%; background:linear-gradient(90deg, {demand_color}88, {demand_color}); border-radius:8px; transition:width 0.5s ease;"></div>
            </div>
            <div style="color:{theme['text_dim']}; font-family:'Inter',sans-serif; font-size:0.72rem; margin-top:4px; text-align:center;">
                {demand_desc}
            </div>
        </div>
        <div style="background:{status_bg}; color:{theme['text_main']}; border:1px solid {theme['border']};
                    border-radius:999px; padding:8px 24px; font-size:0.95rem; font-weight:700;
                    display:inline-flex; align-items:center; gap:8px; font-family:'Inter',sans-serif; margin-top:6px;">
            {status_emoji} {status_text}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Quick Stats Row ──
    st.markdown(f"""
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; margin-bottom:18px;">
        <div style="background:{theme['surface_low']}; border:1px solid {theme['surface_low']}; border-radius:12px;
                    padding:16px; text-align:center;">
            <div style="color:{theme['text_dim']}; font-family:'Inter',sans-serif; font-size:0.72rem; font-weight:600;
                        text-transform:uppercase; letter-spacing:0.06em; margin-bottom:4px;">Daily Average</div>
            <div style="color:{theme['text_main']}; font-family:'Manrope',sans-serif; font-size:1.4rem; font-weight:800;">{daily_avg:,.0f}</div>
            <div style="color:{theme['text_dim']}; font-family:'Inter',sans-serif; font-size:0.72rem;">tourists/day</div>
        </div>
        <div style="background:{theme['surface_low']}; border:1px solid {theme['surface_low']}; border-radius:12px;
                    padding:16px; text-align:center;">
            <div style="color:{theme['text_dim']}; font-family:'Inter',sans-serif; font-size:0.72rem; font-weight:600;
                        text-transform:uppercase; letter-spacing:0.06em; margin-bottom:4px;">Est. Revenue</div>
            <div style="color:{theme['accent2']}; font-family:'Manrope',sans-serif; font-size:1.4rem; font-weight:800;">${est_revenue:,.0f}</div>
            <div style="color:{theme['text_dim']}; font-family:'Inter',sans-serif; font-size:0.72rem;">≈ LKR {est_revenue_lkr/1000000:.1f}M</div>
        </div>
        <div style="background:{theme['surface_low']}; border:1px solid {theme['surface_low']}; border-radius:12px;
                    padding:16px; text-align:center;">
            <div style="color:{theme['text_dim']}; font-family:'Inter',sans-serif; font-size:0.72rem; font-weight:600;
                        text-transform:uppercase; letter-spacing:0.06em; margin-bottom:4px;">vs Last Week</div>
            <div style="color:{risk_color}; font-family:'Manrope',sans-serif; font-size:1.4rem; font-weight:800;">{delta_sign}{delta_vs_mean:,.0f}</div>
            <div style="color:{theme['text_dim']}; font-family:'Inter',sans-serif; font-size:0.72rem;">arrivals difference</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Contextual notes for each breakdown item
    rain_note = "⚡ Heavy monsoon — expect disruptions" if rainfall_mm > 150 else ("☀️ Good weather for tourism" if rainfall_mm < 50 else "🌤️ Moderate rainfall")
    temp_note = "🥵 Very hot — indoor activities preferred" if temp_c > 32 else ("❄️ Cool & comfortable" if temp_c < 22 else "👍 Pleasant temperature")
    hum_note = "💦 High humidity — tropical feel" if humidity_pct > 80 else ("🌬️ Dry & comfortable" if humidity_pct < 50 else "👍 Normal humidity")
    fest_note = f"🎉 Active festival boosting demand ×{multiplier:.1f}" if intensity > 0 else "📅 No festivals — normal demand"
    crisis_note = "🚨 Crisis suppressing demand" if not is_normal else "🟢 All systems normal"

    breakdown_items = [
        ("🌧️", "Rainfall", f"{rainfall_mm} mm", rain_note),
        ("🌡️", "Temperature", f"{temp_c}°C", temp_note),
        ("💧", "Humidity", f"{humidity_pct}%", hum_note),
        ("🎭", "Festivals", f"{intensity}/10", fest_note),
        ("🏢", "Operations", crisis_choice.split("(")[0].strip(), crisis_note),
    ]
    
    breakdown_html = """
<div style="color:{theme['accent_dim']}; font-family:'Manrope',sans-serif; font-size:1.2rem; font-weight:800; margin-bottom:12px; display:flex; align-items:center; gap:8px;">
    📊 Scenario Input Summary
</div>
<div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
"""
    for icon, label, val, note in breakdown_items:
        breakdown_html += f"""
<div class="info-card" style="padding:10px 14px; margin:0;">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="color:{theme['text_muted']}; font-size:0.9rem; font-weight:600;">{icon} {label}</span>
        <span style="color:{theme['text_main']}; font-weight:800; font-size:0.95rem;">{val}</span>
    </div>
    <div style="color:{theme['text_dim']}; font-size:0.75rem; margin-top:2px; font-family:'Inter',sans-serif; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="{note}">{note}</div>
</div>
"""
    breakdown_html += "</div>"
    st.markdown(breakdown_html, unsafe_allow_html=True)

with gauge_col:
    max_gauge = baseline["max"] * 1.5 if baseline else 60000
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=predicted,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"Weekly Arrivals<br><sub style='color:{theme['text_muted']}'>Yellow line = baseline momentum</sub>", 'font': {'color': theme['text_main'], 'size': 14}},
        delta={'reference': lag_val, 'increasing': {'color': theme['accent2']}, 'decreasing': {'color': theme['danger']}},
        number={'font': {'color': theme['text_main'], 'size': 36}},
        gauge={
            'axis': {'range': [0, max_gauge], 'tickwidth': 1, 'tickcolor': theme['border'], 'tickfont': {'color': theme['text_dim']}},
            'bar': {'color': "rgba(56, 189, 248, 0.45)"},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 0,
            'bordercolor': theme['border'],
            'steps': [
                {'range': [0, lag_val], 'color': "rgba(255,255,255,0.05)"},
                {'range': [lag_val, max_gauge], 'color': "rgba(255,255,255,0.02)"}
            ],
            'threshold': {
                'line': {'color': "#fde047", 'width': 3},
                'thickness': 0.75,
                'value': lag_val
            }
        }
    ))
    fig_gauge.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=theme['text_main'], family="Inter"),
        height=320, margin=dict(l=20, r=20, t=50, b=20)
    )
    st.plotly_chart(apply_plotly_theme(fig_gauge), use_container_width=True)

    # Comparison bar chart
    comp_labels = ["Your Scenario", "Baseline", "Peak (Esala)"]
    peak_esala = baseline["max"] if baseline else 55000
    comp_values = [predicted, lag_val, peak_esala]
    comp_colors = [theme['accent_dim'], theme['text_dim'], "#fde047"]

    fig_bar = go.Figure(go.Bar(
        x=comp_labels, y=comp_values,
        marker_color=comp_colors,
        text=[f"{v:,.0f}" for v in comp_values],
        textposition="outside",
        textfont=dict(color=theme['text_muted'], size=12, family="Inter"),
        hovertemplate="%{x}: %{y:,.0f} arrivals<extra></extra>"
    ))
    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=220, margin=dict(l=0, r=0, t=20, b=0),
        xaxis=dict(gridcolor=theme['border'], tickfont=dict(color=theme['text_muted'], size=12)),
        yaxis=dict(gridcolor=theme['border'], tickfont=dict(color=theme['text_dim'], size=11))
    )
    st.plotly_chart(apply_plotly_theme(fig_bar), use_container_width=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
st.markdown(f"""
<div style="color:{theme['accent2']}; font-family:'Manrope',sans-serif; font-size:1.3rem; font-weight:800; margin-bottom:12px; display:flex; align-items:center; gap:8px;">
    🌊 Market Impact Bridge (Waterfall)
</div>
<p style="color:{theme['text_muted']}; font-family:'Inter',sans-serif; font-size:0.95rem; margin:0 0 16px 0;">
    Visualizes the exact delta shift separating your recent baseline momentum from the AI's final scenario prediction.
</p>
""", unsafe_allow_html=True)

delta_vs_lag = predicted - lag_val
fig_waterfall = go.Figure(go.Waterfall(
    name="Impact", orientation="v",
    measure=["absolute", "relative", "total"],
    x=["Current Market", "AI Scenario Impact", "Predicted Potential"],
    y=[lag_val, delta_vs_lag, predicted],
    connector={"line":{"color":"rgba(255,255,255,0.1)", "width":1}},
    decreasing={"marker":{"color": theme['danger']}},
    increasing={"marker":{"color": theme['accent2']}},
    totals={"marker":{"color": theme['accent_dim']}}
))
fig_waterfall.update_layout(
    showlegend=False,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=20, b=20, l=20, r=20),
    font=dict(color=theme['text_muted'])
)
st.plotly_chart(apply_plotly_theme(fig_waterfall), use_container_width=True)

# ── Understanding This Result ──
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

mean_val = baseline["mean"] if baseline else 15000
pct_of_peak = (predicted / peak_val * 100) if peak_val > 0 else 0

st.markdown(f"""
<div style="background:linear-gradient(135deg, rgba(56,189,248,0.06), rgba(78,222,163,0.04));
            border:1px solid rgba(56,189,248,0.15); border-radius:14px; padding:20px 22px;">
    <div style="color:{theme['accent_dim']}; font-family:'Manrope',sans-serif; font-size:1.05rem; font-weight:700;
                margin-bottom:12px; display:flex; align-items:center; gap:8px;">
        📖 How to Read This Result
    </div>
    <div style="color:{theme['text_muted']}; font-family:'Inter',sans-serif; font-size:0.88rem; line-height:1.7;">
        <div style="margin-bottom:8px;">
            <strong style="color:{theme['text_main']};">What does {predicted:,.0f} mean?</strong><br>
            The AI model predicts approximately <strong style="color:{theme['accent_dim']};">{predicted:,.0f} tourists</strong> will visit Kandy
            during this simulated week — that's about <strong style="color:{theme['accent2']};">{daily_avg:,.0f} visitors per day</strong>.
        </div>
        <div style="margin-bottom:8px;">
            <strong style="color:{theme['text_main']};">How does this compare?</strong><br>
            This is <strong style="color:{risk_color};">{delta_sign}{delta_pct:.1f}%</strong> compared to your baseline of {lag_val:,} arrivals,
            and represents <strong style="color:{theme['warning']};">{pct_of_peak:.0f}%</strong> of the historical peak ({peak_val:,.0f}).
        </div>
        <div>
            <strong style="color:{theme['text_main']};">Model confidence:</strong>
            The Random Forest model was trained on <strong style="color:#a78bfa;">574 weeks</strong> of real data.
            Predictions are most reliable when inputs are within historical norms.
            {f'<span style="color:{theme["danger"]};">⚠️ Extreme values detected — prediction may be less reliable.</span>' if (rainfall_mm > 200 or temp_c > 35 or temp_c < 18) else f'<span style="color:{theme["accent2"]};">✅ Input values are within trained data range.</span>'}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI RECOMMENDATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

st.markdown(f"""
<div style="display:flex; align-items:center; gap:12px; margin: 8px 0 10px 0;">
    <span style="background:linear-gradient(135deg,#a78bfa,#8b5cf6); color:#fff; font-family:'Inter',sans-serif;
                 font-weight:800; font-size:0.75rem; padding:5px 14px; border-radius:20px; letter-spacing:0.06em;
                 text-transform:uppercase;">Insights</span>
    <span style="color:#a78bfa; font-family:'Manrope',sans-serif; font-size:1.4rem; font-weight:800;">💡 AI-Powered Recommendations</span>
</div>
<p style="color:{theme['text_muted']}; font-family:'Inter',sans-serif; font-size:0.95rem; margin:0 0 16px 0;">
    Based on your scenario parameters, here are actionable strategies tailored to the predicted conditions.
</p>
""", unsafe_allow_html=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

recs = []

if is_econ or is_covid or is_easter:
    recs.append(("⚠️", "Crisis Management Strategy", f"The active crisis is heavily suppressing arrivals (Predicted: {predicted:,.0f}). Focus on deep discounting for domestic travelers, cut non-essential operational costs, and offer highly flexible cancellation policies to secure existing bookings."))
elif is_esala or is_esala_prep:
    if rainfall_mm > 150:
         recs.append(("🌧️", "Wet Perahera Contingency", f"Esala demand is high ({predicted:,.0f} arrivals), but monsoon rains threaten outdoor logistics. Urgently secure covered transport for guests, stock up on umbrellas, and prepare indoor dining alternatives."))
    else:
         recs.append(("🐘", "Peak Festival Optimization", f"Esala Perahera under ideal weather is driving massive volume ({predicted:,.0f} arrivals). Maximize yield by enforcing strict minimum-stay policies, optimizing dynamic pricing, and fully staffing all F&B outlets."))
elif rainfall_mm > 200:
    recs.append(("☔", "Severe Weather Protocol", f"Heavy rainfall ({rainfall_mm}mm) is deterring casual visits. Pivot marketing to emphasize cozy indoor luxury, spa experiences, and culinary events to capture the limited tourist pool ({predicted:,.0f} arrivals)."))
elif temp_c > 32 and humidity_pct > 80:
    recs.append(("🥵", "Heat & Humidity Advisory", f"Extreme heat index detected. Promote early morning or late evening excursions. Ensure AC units are serviced and offer complimentary hydration stations in the lobby."))
elif predicted > lag_val * 1.15:
    recs.append(("📈", "Sustained High Demand", f"Demand is firmly above average (+{delta_pct:.1f}%). A great opportunity to upsell premium suites and capture additional revenue through guided tours to Peradeniya or Hanthana."))
else:
    recs.append(("✅", "Standard Operations", f"Conditions indicate a stable, typical week ({predicted:,.0f} arrivals). Maintain standard staffing levels and focus on baseline customer satisfaction and preventative maintenance."))

# Revenue tip
recs.append(("💰", "Revenue Projection", f"At an estimated baseline spend of $1,036/tourist (national avg), this scenario generates roughly <b>${est_revenue:,.0f}</b> (≈ LKR {est_revenue_lkr/1000000:.1f}M) in national yield. Adjust pricing parity across OTAs to defend margins."))


if recs:
    # Use Streamlit Tabs for interactive recommendations layout
    tab_titles = [f"{icon} {title}" for icon, title, _ in recs]
    tabs = st.tabs(tab_titles)
    
    for i, (icon, title, body) in enumerate(recs):
        with tabs[i]:
            st.markdown(f"""
            <div style="padding:24px; background:linear-gradient(135deg, rgba(30,41,59,0.5), rgba(19,27,46,0.6)); 
                        border-radius:12px; border:1px solid {theme['surface_low']}; margin-top:8px;">
                <div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
                    <span style="font-size:2rem;">{icon}</span>
                    <span style="color:{theme['text_main']}; font-family:'Manrope',sans-serif; font-size:1.25rem; font-weight:800;">{title}</span>
                </div>
                <div style="color:{theme['text_muted']}; font-family:'Inter',sans-serif; font-size:1rem; line-height:1.7;">
                    {body}
                </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; color:{theme['text_dim']}; font-family:'Inter',sans-serif; font-size:0.85rem; padding:16px 0; margin-top:8px; border-top:1px solid rgba(62,72,79,0.15);">
    🤖 Predictions use the Random Forest model trained on 574 weeks of historical data · DSS v1.0.0
</div>
""", unsafe_allow_html=True)
