"""
pages/5_🌦️_Climate_Impact_Forecaster.py  —  Climate Impact Forecaster
"""

# -------------------- IMPORTS --------------------
import sys
from pathlib import Path
import datetime
import json
import pickle
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Custom utility modules (project-specific helpers)
from utils.sidebar import render_sidebar
from utils.auth import require_auth
from utils.theme import apply_plotly_theme, apply_custom_theme, render_page_banner

# Ensure project root is in path (so imports work correctly)
sys.path.insert(0, str(Path(__file__).parent.parent))

# Require user authentication before accessing page
require_auth()

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Climate Impact Forecaster | Kandy Tourism DSS",
    page_icon="🌦️",
    layout="wide"
)

# Apply custom UI theme
apply_custom_theme()

# -------------------- CUSTOM CSS STYLING --------------------
# Styling for alert cards and stat pills
st.markdown("""
<style>
.alert-card {
    background: rgba(19, 27, 46, 0.6);
    backdrop-filter: blur(24px);
    border-radius:14px; padding:16px 20px; margin-bottom:12px;
    border: 1px solid rgba(62,72,79,0.15);
    border-left:4px solid; display:flex; align-items:flex-start; margin-top:20px; gap:14px;
    box-shadow: 0 0 30px rgba(0,0,0,0.2);
}
.alert-monsoon { border-color:#8ed5ff; }
.alert-heavy   { border-color:#ffb4ab; }
.alert-ok      { border-color:#4edea3; }

.alert-icon { font-size:1.6rem; flex-shrink:0; }

.alert-text h4 {
    color:#dae2fd;
    margin:0 0 4px;
    font-size:.95rem;
    font-weight:700;
    font-family:'Manrope', sans-serif;
}

.alert-text p  {
    color:#bdc8d1;
    margin:0;
    font-size:.85rem;
}

.stat-pill {
    display:inline-block;
    background:rgba(142,213,255,.05);
    border:1px solid rgba(142,213,255,.15);
    border-radius:8px;
    padding:6px 14px;
    font-size:.8rem;
    font-weight:600;
    color:#8ed5ff;
    margin:4px;
}
</style>
""", unsafe_allow_html=True)

# Render sidebar navigation
render_sidebar(active_page="Climate Impact Forecaster")

# Render top banner
render_page_banner(
    title="Climate Impact Forecaster",
    subtitle="Upcoming weather outlook for Kandy — monitor rainfall, temperature and monsoon conditions and their effect on tourist arrivals.",
    icon="🌦️",
)

# -------------------- USER INPUT CONTROLS --------------------
with st.container():
    c1, c2, c3 = st.columns([4, 4, 3])

    # Year selection filter
    with c1:
        SEL_YEARS = st.multiselect(
            'Years',
            list(range(2015, 2030)),
            default=list(range(2023, 2027))
        )

    # Rainfall threshold slider
    with c2:
        RAIN_THRESH = st.slider(
            'Heavy Rain threshold (mm/week)',
            100, 400, 150
        )

    # Toggle to show only future data
    with c3:
        st.write("")
        st.write("")
        SHOW_FUTURE_ONLY = st.checkbox(
            'Future weeks only ✔️',
            value=False
        )

    st.divider()

# Base directory for accessing data/models
BASE_DIR = Path(__file__).parent.parent

# -------------------- DATA LOADING FUNCTION --------------------
@st.cache_data
def load_festival_weekly():
    """
    Loads historical + predicted weekly data.
    Adds model predictions if available.
    """

    # Load base dataset
    df = pd.read_csv(BASE_DIR / "kandy_festival_demand_NOMISSING.csv")
    df["week_start"] = pd.to_datetime(df["week_start"])

    # Check if cached predictions exist
    cache_path = BASE_DIR / "models/predictions_cache.csv"

    if cache_path.exists():
        curr_max_date = df["week_start"].max()

        # Load predictions
        cdf = pd.read_csv(cache_path)

        # Filter only Random Forest predictions
        cdf = cdf[cdf["model_name"] == "random_forest"].copy()

        # Extract useful features from stored JSON
        def unpack_feats(row):
            feats = json.loads(row["features_used"])

            # Determine festival type
            pf = "Normal"
            if feats.get("is_esala_perahera"):
                pf = "Esala_Perahera"
            elif feats.get("is_vesak"):
                pf = "Vesak"
            elif feats.get("is_poson_perahera"):
                pf = "Poson_Perahera"

            row["primary_festival"] = pf

            # Extract weather features
            row["avg_weekly_rainfall_mm"] = feats.get("avg_weekly_rainfall_mm", 0)
            row["avg_temp_celsius"] = feats.get("avg_temp_celsius", 25.0)
            row["is_monsoon_week"] = feats.get("is_monsoon_week", 0)

            return row

        # Apply feature extraction
        cdf = cdf.apply(unpack_feats, axis=1)

        cdf["week_start"] = pd.to_datetime(cdf["week_start"])
        cdf["estimated_weekly_kandy_arrivals"] = cdf["predicted_arrivals"]

        # Keep only future predictions
        cdf = cdf[cdf["week_start"] > curr_max_date]

        # Append predictions to historical data
        if not cdf.empty:
            df = pd.concat([df, cdf], ignore_index=True)

    # Sort data chronologically
    df = df.sort_values("week_start").reset_index(drop=True)

    return df


# -------------------- LOAD & FILTER DATA --------------------
df_all = load_festival_weekly()

today = pd.Timestamp(datetime.date.today())

# Filter only future weeks if selected
if SHOW_FUTURE_ONLY:
    df_all = df_all[df_all["week_start"] >= today]

# Filter selected years
if SEL_YEARS:
    df_all = df_all[df_all["week_start"].dt.year.isin(SEL_YEARS)]

# Handle empty dataset
if df_all.empty:
    st.info('ℹ️ No weather data available to display at the moment.')
    st.stop()

# -------------------- SUMMARY METRICS --------------------
total_weeks = len(df_all)

# Count monsoon weeks
monsoon_wks = int(df_all["is_monsoon_week"].sum()) if "is_monsoon_week" in df_all.columns else 0

# Count heavy rain weeks
heavy_wks = len(df_all[df_all["avg_weekly_rainfall_mm"] > RAIN_THRESH]) if "avg_weekly_rainfall_mm" in df_all.columns else 0

# Average temperature
avg_temp = float(df_all["avg_temp_celsius"].mean()) if "avg_temp_celsius" in df_all.columns else 25.0

# Display stats
st.markdown(f"""
<div>
<span class="stat-pill">📅 {total_weeks} weeks shown</span>
<span class="stat-pill">🌧️ {monsoon_wks} monsoon weeks</span>
<span class="stat-pill">⛈️ {heavy_wks} heavy rain weeks (>{RAIN_THRESH} mm)</span>
<span class="stat-pill">🌡️ {avg_temp:.1f}°C avg temp</span>
</div><br>
""", unsafe_allow_html=True)

# -------------------- TREND CHART --------------------
st.markdown('<div class="section-header">📈 Temperature & Rainfall Trend</div>', unsafe_allow_html=True)

# Create subplot with dual axis
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Temperature line
if "avg_temp_celsius" in df_all.columns:
    fig.add_trace(go.Scatter(
        x=df_all["week_start"],
        y=df_all["avg_temp_celsius"],
        name="Avg Temp (°C)",
        mode="lines",
        line=dict(color="#f97316", width=2),
        fill="tozeroy",
        fillcolor="rgba(249,115,22,.08)"
    ), secondary_y=False)

# Rainfall bars
if "avg_weekly_rainfall_mm" in df_all.columns:
    fig.add_trace(go.Bar(
        x=df_all["week_start"],
        y=df_all["avg_weekly_rainfall_mm"],
        name="Weekly Rainfall (mm)",
        marker_color="#38bdf8",
        opacity=0.8
    ), secondary_y=True)

    # Highlight heavy rain weeks
    heavy_rain_df = df_all[df_all["avg_weekly_rainfall_mm"] > RAIN_THRESH]

    for _, row in heavy_rain_df.iterrows():
        fig.add_vrect(
            x0=row["week_start"],
            x1=row["week_start"] + pd.Timedelta(days=7),
            fillcolor="rgba(248,113,113,.12)",
            layer="below",
            line_width=0
        )

# Apply styling
fig.update_layout(
    height=400,
    margin=dict(l=0, r=160, t=20, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    hovermode="x unified"
)

# Render chart
st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

# -------------------- SCATTER PLOT --------------------
st.markdown('<div class="section-header">🔗 Rainfall vs Tourist Arrivals Correlation</div>', unsafe_allow_html=True)

# Create scatter plot if columns exist
if "avg_weekly_rainfall_mm" in df_all.columns and "estimated_weekly_kandy_arrivals" in df_all.columns:

    fig_scatter = px.scatter(
        df_all,
        x="avg_weekly_rainfall_mm",
        y="estimated_weekly_kandy_arrivals",
        color="primary_festival" if "primary_festival" in df_all.columns else None,
        title="Weather Impact on Tourist Arrivals"
    )

    st.plotly_chart(apply_plotly_theme(fig_scatter), use_container_width=True)

# -------------------- ALERT SYSTEM --------------------
st.markdown('<div class="section-header">⚠️ Weather Impact Alerts</div>', unsafe_allow_html=True)

# Take next 4 future weeks
future_alerts = df_all[df_all["week_start"] >= today].head(4)

# Generate alert cards
if not future_alerts.empty:
    alert_cols = st.columns(len(future_alerts))

    for i, (_, row) in enumerate(future_alerts.iterrows()):
        with alert_cols[i]:

            week_str = row["week_start"].strftime("%d %b %Y")
            rain_val = row.get("avg_weekly_rainfall_mm", 0)
            arr_val = row.get("estimated_weekly_kandy_arrivals", 0)

            # Heavy rain alert
            if rain_val > RAIN_THRESH:
                st.markdown(f"...", unsafe_allow_html=True)

            # Monsoon alert
            elif row.get("is_monsoon_week", 0) == 1:
                st.markdown(f"...", unsafe_allow_html=True)

            # Good weather alert
            else:
                st.markdown(f"...", unsafe_allow_html=True)

# -------------------- MONTHLY PATTERN --------------------
# Aggregate by month and visualize rainfall vs arrivals

# -------------------- FEATURE IMPORTANCE --------------------
# Loads trained XGBoost model and displays feature importance
# Helps understand how much weather affects predictions
