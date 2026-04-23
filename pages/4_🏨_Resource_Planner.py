"""
pages/4_🏨_Resource_Planner.py  —  Resource Planner with Inline Filters
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import datetime
import json
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from scipy.optimize import linprog
from utils.sidebar import render_sidebar
from utils.auth import require_auth
from utils.theme import apply_plotly_theme, apply_custom_theme, render_page_banner
from utils.db import fetch_predictions

require_auth()

st.set_page_config(
    page_title="Resource Planner | Kandy Tourism DSS",
    page_icon="🏨", layout="wide"
)

apply_custom_theme()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=Manrope:wght@600;700;800&display=swap');

.rp-kpi-card {
    background: rgba(19, 27, 46, 0.6);
    backdrop-filter: blur(24px);
    border: 1px solid rgba(62, 72, 79, 0.2);
    border-radius: 14px; padding: 20px;
    transition: box-shadow .3s ease, transform .3s ease;
    display: flex; align-items: center; gap: 16px;
}
.rp-kpi-card:hover { transform: translateY(-3px); box-shadow: 0 0 40px rgba(142,213,255,0.06); }
.rp-icon-box {
    width: 52px; height: 52px; border-radius: 12px;
    background: linear-gradient(135deg, rgba(56,189,248,0.15) 0%, rgba(142,213,255,0.15) 100%);
    border: 1px solid rgba(56,189,248,0.3);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.6rem; flex-shrink: 0;
}
.rp-kpi-value { font-size: 1.8rem; font-weight: 800; color: #dae2fd; line-height: 1.1; font-family: 'Manrope', sans-serif; }
.rp-kpi-label { color: #bdc8d1; font-size: .75rem; font-weight: 600; font-family: 'Inter', sans-serif;
                 text-transform: uppercase; letter-spacing: .08em; margin-bottom: 2px;}
.rp-kpi-delta { font-size: .8rem; margin-top: 4px; font-weight: 600; font-family: 'Inter', sans-serif;}
.delta-up   { color: #4edea3; }
.delta-down { color: #ffb4ab; }
.delta-warn { color: #F59E0B; }

.opt-card {
    background: rgba(20, 31, 56, 0.55);
    border: 1px solid rgba(56,189,248,0.2);
    border-radius: 12px; padding: 18px;
}
.opt-card-title { font-size: 0.78rem; color: #bdc8d1; font-weight: 700; text-transform: uppercase; letter-spacing:.06em; margin-bottom:4px; }
.opt-card-value { font-size: 1.45rem; color: #4edea3; font-weight: 800; font-family: 'Manrope', sans-serif; }
.opt-card-sub   { font-size: 0.85rem; color: #dae2fd; margin-top: 2px; }
.opt-card-note  { font-size: 0.72rem; color: #87929a; margin-top: 4px; }

.filter-bar {
    background: rgba(20, 31, 56, 0.45);
    backdrop-filter: blur(24px); border: 1px solid rgba(57,184,253,0.15);
    border-radius: 16px; padding: 20px 26px; margin-bottom: 24px;
}
.section-header {
    color: #e2e8f0; font-size: 1rem; font-weight: 700; letter-spacing: .05em;
    text-transform: uppercase; margin: 24px 0 12px;
    padding-bottom: 6px; border-bottom: 2px solid #38BDF8;
}
</style>
""", unsafe_allow_html=True)

render_sidebar("Resource Planner")
BASE_DIR = Path(__file__).parent.parent

# ── Session State Defaults ──────────────────────────────────────────────────
DEFAULTS = {
    "rp_hotel_capacity":  500,
    "rp_market_share":    2.0,    # Expected percentage of total regional tourists the property captures
    "rp_occ_per_room":    2.0,
    "rp_staff_ratio":     15,
    "rp_van_ratio":       12,
    "rp_forward_weeks":   12,
    "rp_planning_week":   None,   # resolved after data loads
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Data Loading (Supabase-first) ───────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_data():
    # Historical CSV
    csv_path = BASE_DIR / "kandy_festival_demand_NOMISSING.csv"
    df_hist = pd.read_csv(csv_path, on_bad_lines="skip") if csv_path.exists() else pd.DataFrame()
    if not df_hist.empty:
        df_hist["week_start"] = pd.to_datetime(df_hist["week_start"])

    future_rows = []
    hist_max = df_hist["week_start"].max() if not df_hist.empty else pd.Timestamp("2000-01-01")

    def _parse_festival(feats: dict) -> str:
        if feats.get("is_esala_perahera"):          return "Esala_Perahera"
        if feats.get("is_esala_preparation"):       return "Esala_Prep"
        if feats.get("is_poson_perahera"):          return "Poson_Perahera"
        if feats.get("is_vesak"):                   return "Vesak"
        if feats.get("is_sinhala_tamil_new_year"):  return "Sinhala_Tamil_New_Year"
        if feats.get("is_christmas_new_year"):      return "Christmas_New_Year"
        if feats.get("is_deepavali"):               return "Deepavali"
        if feats.get("is_thai_pongal"):             return "Thai_Pongal"
        if feats.get("is_august_buildup"):          return "August_Buildup"
        return "Normal"

    # 1. Try Supabase
    try:
        preds = fetch_predictions()
        if not preds.empty:
            preds["week_start"] = pd.to_datetime(preds["week_start"])
            rf = preds[(preds["model_name"].isin(["xgboost", "random_forest"])) & (preds["week_start"] > hist_max)]
            for _, row in rf.iterrows():
                try:    feats = json.loads(row["features_used"])
                except: feats = {}
                future_rows.append({
                    "week_start":                       row["week_start"],
                    "estimated_weekly_kandy_arrivals":  row["predicted_arrivals"],
                    "primary_festival":                 _parse_festival(feats),
                    "avg_weekly_rainfall_mm":           feats.get("avg_weekly_rainfall_mm", 0),
                    "is_covid_period":                  0,
                })
    except Exception:
        pass

    # 2. Fallback: local cache CSV
    if not future_rows:
        pred_path = BASE_DIR / "models/predictions_cache.csv"
        if pred_path.exists():
            cdf = pd.read_csv(pred_path)
            cdf["week_start"] = pd.to_datetime(cdf["week_start"])
            rf = cdf[(cdf["model_name"].isin(["xgboost", "random_forest"])) & (cdf["week_start"] > hist_max)]
            for _, row in rf.iterrows():
                try:    feats = json.loads(row["features_used"])
                except: feats = {}
                future_rows.append({
                    "week_start":                       row["week_start"],
                    "estimated_weekly_kandy_arrivals":  row["predicted_arrivals"],
                    "primary_festival":                 _parse_festival(feats),
                    "avg_weekly_rainfall_mm":           feats.get("avg_weekly_rainfall_mm", 0),
                    "is_covid_period":                  0,
                })

    if future_rows:
        df_all = pd.concat([df_hist, pd.DataFrame(future_rows)], ignore_index=True)
    else:
        df_all = df_hist.copy()

    df_all = df_all.sort_values("week_start").reset_index(drop=True)
    df_all["year"] = df_all["week_start"].dt.year.astype("Int64")
    if "primary_festival" not in df_all.columns:
        df_all["primary_festival"] = "Normal"
    df_all["primary_festival"] = df_all["primary_festival"].fillna("Normal")
    if "avg_weekly_rainfall_mm" not in df_all.columns:
        df_all["avg_weekly_rainfall_mm"] = 0
    return df_all

df_all = load_data()

if df_all.empty:
    st.info("ℹ️ No forecast data available. Please run the training pipeline first.")
    st.stop()

# ── Build week options (future weeks only) ──────────────────────────────────
today          = pd.Timestamp(datetime.date.today())
next_week_ts   = today + pd.Timedelta(days=7)

future_df      = df_all[df_all["week_start"] >= today].copy()
all_dates      = df_all[df_all["week_start"] >= today - pd.Timedelta(days=60)]["week_start"].tolist()

FESTIVAL_ICONS = {
    "Esala_Perahera": "🐘", "Esala_Prep": "🎺", "Poson_Perahera": "🏯",
    "Vesak": "🪔", "Deepavali": "✨", "Sinhala_Tamil_New_Year": "🎊",
    "Christmas_New_Year": "🎄", "Monthly_Poya": "🌕",
    "August_Buildup": "📈", "Thai_Pongal": "🌾",
}

def week_label(ts):
    row = df_all[df_all["week_start"] == ts]
    fest = row.iloc[0]["primary_festival"] if not row.empty else "Normal"
    icon = FESTIVAL_ICONS.get(fest, "")
    suffix = f" {icon} {fest.replace('_',' ')}" if icon else ""
    return ts.strftime("%Y-%m-%d") + suffix

week_options  = [ts.strftime("%Y-%m-%d") for ts in all_dates]
week_labels   = [week_label(ts) for ts in all_dates]

# Default planning week = first future week
if st.session_state.rp_planning_week is None or st.session_state.rp_planning_week not in week_options:
    # Find first future week
    for ts in all_dates:
        if ts >= next_week_ts:
            st.session_state.rp_planning_week = ts.strftime("%Y-%m-%d")
            break
    else:
        st.session_state.rp_planning_week = week_options[0] if week_options else None

# ── Page Banner ─────────────────────────────────────────────────────────────
render_page_banner(
    title="Resource Planner",
    subtitle="Translate AI arrival forecasts into actionable hotel, transport fleet, and staff roster plans.",
    icon="🏨",
)

# ── Inline Filter Bar ────────────────────────────────────────────────────────

with st.container():
    st.markdown("<div style='padding: 0 0 24px 0; position:relative; z-index:10;'>", unsafe_allow_html=True)
    with st.form("rp_filters", border=False):

        # Row 1: Planning week + forward window
        fc1, fc2, fc3 = st.columns([3, 1.5, 1.5])
        with fc1:
            cur_idx = week_options.index(st.session_state.rp_planning_week) if st.session_state.rp_planning_week in week_options else 0
            sel_label = st.selectbox(
                "📅 Select Planning Week",
                options=week_labels,
                index=cur_idx,
                help="Select any week to see AI-predicted resource requirements. Festival weeks are marked with icons."
            )
            sel_week_str = week_options[week_labels.index(sel_label)]

        with fc2:
            fw_options = [4, 8, 12, 26, 52]
            fw_idx = fw_options.index(st.session_state.rp_forward_weeks) if st.session_state.rp_forward_weeks in fw_options else 2
            forward_weeks = st.selectbox(
                "📆 Forward Window",
                options=fw_options,
                index=fw_idx,
                format_func=lambda x: f"{x} weeks",
                help="How many weeks ahead the chart and planning table will show"
            )
        with fc3:
            col3a, col3b = st.columns(2)
            with col3a:
                hotel_capacity = st.number_input(
                    "🏨 Hotel Rooms",
                    min_value=1, max_value=5000,
                    value=st.session_state.rp_hotel_capacity,
                    step=10,
                    help="Total number of hotel rooms available in your property"
                )
            with col3b:
                market_share = st.number_input(
                    "🎯 Market Share (%)",
                    min_value=0.1, max_value=25.0,
                    value=float(st.session_state.rp_market_share),
                    step=0.5,
                    format="%.1f",
                    help="What percentage of total Kandy tourists does your property typically capture?"
                )

        # Row 2: Resource ratios
        fr1, fr2, fr3, fr4 = st.columns([1.5, 1.5, 1.5, 1])
        with fr1:
            occ_per_room = st.number_input(
                "👥 Tourists / Room",
                min_value=1.0, max_value=10.0,
                value=float(st.session_state.rp_occ_per_room),
                step=0.5,
                help="Average number of tourists sharing a room"
            )
        with fr2:
            staff_ratio = st.number_input(
                "🧑‍💼 Tourists / Staff",
                min_value=1, max_value=100,
                value=st.session_state.rp_staff_ratio,
                step=1,
                help="How many tourists each staff member can serve"
            )
        with fr3:
            van_ratio = st.number_input(
                "🚐 Tourists / Transport Unit",
                min_value=1, max_value=100,
                value=st.session_state.rp_van_ratio,
                step=1,
                help="How many tourists fit in one transport unit (mini-van, bus, etc.)"
            )
        with fr4:
            st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("⚡ Apply Settings", use_container_width=True)

    if submitted:
        st.session_state.rp_planning_week  = sel_week_str
        st.session_state.rp_forward_weeks  = forward_weeks
        st.session_state.rp_hotel_capacity = hotel_capacity
        st.session_state.rp_market_share   = market_share
        st.session_state.rp_occ_per_room   = occ_per_room
        st.session_state.rp_staff_ratio    = staff_ratio
        st.session_state.rp_van_ratio      = van_ratio
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── Resolved filter values ───────────────────────────────────────────────────
HOTEL_CAPACITY = st.session_state.rp_hotel_capacity
MARKET_SHARE   = st.session_state.rp_market_share
OCC_PER_ROOM   = st.session_state.rp_occ_per_room
STAFF_RATIO    = st.session_state.rp_staff_ratio
VAN_RATIO      = st.session_state.rp_van_ratio
FWD_WEEKS      = st.session_state.rp_forward_weeks
sel_date       = pd.to_datetime(st.session_state.rp_planning_week)

sel_rows = df_all[df_all["week_start"] == sel_date]
if sel_rows.empty:
    st.warning("⚠️ No data found for the selected week. Please pick another week.")
    st.stop()
sel_row = sel_rows.iloc[0]

regional_arrivals = int(sel_row.get("estimated_weekly_kandy_arrivals", 0))
festival          = str(sel_row.get("primary_festival", "Normal"))
rain              = float(sel_row.get("avg_weekly_rainfall_mm", 0))

# The core scaling fix: Macro (Kandy) -> Micro (Property)
arrivals        = int(regional_arrivals * (MARKET_SHARE / 100))

rooms_needed    = max(1, int(arrivals / OCC_PER_ROOM))
staff_needed    = max(1, int(arrivals / STAFF_RATIO))
transport_units = max(1, int(arrivals / VAN_RATIO))
occupancy_pct   = min(150.0, (rooms_needed / HOTEL_CAPACITY) * 100) # Cap display bug at 150%

# ── LP Optimization ──────────────────────────────────────────────────────────
MAX_PERM_STAFF  = max(1, int(HOTEL_CAPACITY * 0.15))
MAX_OWNED_VANS  = max(1, int(HOTEL_CAPACITY * 0.05))

c_staff = [150, 250]
res_staff = linprog(c_staff,
    A_ub=[[-1, -1], [1, 0]], b_ub=[-staff_needed, MAX_PERM_STAFF],
    bounds=[(0, None), (0, None)], method="highs")
opt_perm_staff = max(0, int(res_staff.x[0])) if res_staff.success else 0
opt_temp_staff = max(0, int(res_staff.x[1])) if res_staff.success else 0
opt_staff_cost = res_staff.fun if res_staff.success else 0

c_transport = [80, 150]
res_transport = linprog(c_transport,
    A_ub=[[-1, -1], [1, 0]], b_ub=[-transport_units, MAX_OWNED_VANS],
    bounds=[(0, None), (0, None)], method="highs")
opt_owned_vans    = max(0, int(res_transport.x[0])) if res_transport.success else 0
opt_hired_vans    = max(0, int(res_transport.x[1])) if res_transport.success else 0
opt_transport_cost = res_transport.fun if res_transport.success else 0

# ── Monte Carlo ──────────────────────────────────────────────────────────────
np.random.seed(42)
sim_arrivals       = np.random.normal(loc=arrivals, scale=max(1, arrivals * 0.12), size=5000)
sim_rooms          = sim_arrivals / OCC_PER_ROOM
mc_overflow_prob   = float(np.mean(sim_rooms > HOTEL_CAPACITY) * 100)
mc_overflow_rooms  = float(np.mean(np.maximum(0, sim_rooms - HOTEL_CAPACITY)))

# ── Page title ───────────────────────────────────────────────────────────────
sel_date_label = sel_date.strftime("%d %B %Y")
fest_badge = ""
if festival != "Normal":
    fest_icon = FESTIVAL_ICONS.get(festival, "🎉")
    fest_badge = f" &nbsp;<span style='background:rgba(245,158,11,0.15);border:1px solid rgba(245,158,11,0.3);border-radius:6px;padding:2px 8px;font-size:0.85rem;color:#F59E0B;font-weight:700'>{fest_icon} {festival.replace('_',' ')}</span>"
st.markdown(
    f"<h4 style='color:#F8FAFC;margin-bottom:6px;font-weight:700;'>"
    f"📋 Resource Requirements — Week of <span style='color:#38BDF8'>{sel_date_label}</span>{fest_badge}</h4>",
    unsafe_allow_html=True
)

# ── Alert Banners ────────────────────────────────────────────────────────────
if occupancy_pct > 85:
    st.error(f"🚨 **Critical Capacity Alert** — Occupancy pressure at **{occupancy_pct:.1f}%** for week of {sel_date_label}. Activate overflow accommodation partnerships and pre-book buses.")
elif occupancy_pct > 75:
    st.warning(f"⚠️ **High Occupancy** — {occupancy_pct:.1f}% pressure. Pre-position extra transport and notify hoteliers.")

if festival != "Normal":
    fest_icon = FESTIVAL_ICONS.get(festival, "🎉")
    st.info(f"{fest_icon} **Festival Week — {festival.replace('_', ' ')}** | Expect **{regional_arrivals:,}** regional tourists. At **{MARKET_SHARE:.1f}%** market share, target ~**{arrivals:,}** arrivals for your property.")
if rain > 150:
    st.info(f"🌧️ **Heavy Rainfall Forecast** — {rain:.0f} mm expected. Arrange covered transport options and visitor shelters.")

# ── KPI Cards ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Weekly Resource Requirements</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
occ_delta_cls   = "delta-down" if occupancy_pct > 85 else ("delta-warn" if occupancy_pct > 75 else "delta-up")
occ_delta_label = "⚠️ Critical!" if occupancy_pct > 100 else ("⚠️ High P." if occupancy_pct > 85 else ("🟡 High" if occupancy_pct > 75 else "✅ Normal"))

cards = [
    (c1, "🛬", "Property Arrivals",    f"{arrivals:,}",          f"Out of {regional_arrivals:,} regional", ""),
    (c2, "🧑‍💼", "Staff Required",       f"{staff_needed:,}",      f"+{int(staff_needed*0.1)} contingency", "delta-up"),
    (c3, "🚐", "Transport Units",      f"{transport_units:,}",   f"~{VAN_RATIO} tourists/unit", ""),
    (c4, "🏨", "Occupancy Pressure",   f"{occupancy_pct:.1f}%",  occ_delta_label, occ_delta_cls),
]

for col, icon, label, val, delta, dcls in cards:
    with col:
        st.markdown(f"""
        <div class="rp-kpi-card">
            <div class="rp-icon-box">{icon}</div>
            <div>
                <div class="rp-kpi-label">{label}</div>
                <div class="rp-kpi-value">{val}</div>
                <div class="rp-kpi-delta {dcls}">{delta}</div>
            </div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── LP & Monte Carlo result cards ────────────────────────────────────────────
st.markdown('<div class="section-header">🧠 AI-Optimized Operations (LP + Monte Carlo)</div>', unsafe_allow_html=True)

o1, o2, o3 = st.columns(3)
with o1:
    st.markdown(f"""
    <div class="opt-card">
        <div class="opt-card-title">Cost-Optimized Staffing</div>
        <div class="opt-card-value">${opt_staff_cost:,.0f}</div>
        <div class="opt-card-sub">{opt_perm_staff} Permanent &nbsp;|&nbsp; {opt_temp_staff} Temporary</div>
        <div class="opt-card-note">LP Constraint: Max {MAX_PERM_STAFF} permanent staff</div>
    </div>""", unsafe_allow_html=True)

with o2:
    st.markdown(f"""
    <div class="opt-card">
        <div class="opt-card-title">Cost-Optimized Transport</div>
        <div class="opt-card-value">${opt_transport_cost:,.0f}</div>
        <div class="opt-card-sub">{opt_owned_vans} Owned &nbsp;|&nbsp; {opt_hired_vans} Hired</div>
        <div class="opt-card-note">LP Constraint: Max {MAX_OWNED_VANS} owned vans</div>
    </div>""", unsafe_allow_html=True)

with o3:
    overflow_color = "#ffb4ab" if mc_overflow_prob > 15 else ("#F59E0B" if mc_overflow_prob > 5 else "#4edea3")
    st.markdown(f"""
    <div class="opt-card" style="border-color:rgba(255,180,171,0.2)">
        <div class="opt-card-title">Monte Carlo Risk Profile</div>
        <div class="opt-card-value" style="color:{overflow_color}">{mc_overflow_prob:.1f}% Overflow Risk</div>
        <div class="opt-card-sub">Expected shortfall: {mc_overflow_rooms:,.1f} rooms</div>
        <div class="opt-card-note">Simulation: 5,000 arrival volatility trials (±12%)</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Gauge + Forward Bar Chart ─────────────────────────────────────────────────
col_gauge, col_bar = st.columns([1, 1.6])

with col_gauge:
    st.markdown('<div class="section-header">🏨 Hotel Capacity Utilization</div>', unsafe_allow_html=True)
    gauge_color = "#4edea3" if occupancy_pct < 75 else ("#F59E0B" if occupancy_pct < 85 else "#ffb4ab")
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=occupancy_pct,
        title={"text": "Forecasted Room Occupancy", "font": {"color": "#dae2fd", "family": "Inter"}},
        number={"suffix": "%", "font": {"color": "#dae2fd"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "rgba(62,72,79,0.15)"},
            "bar":  {"color": gauge_color},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 2, "bordercolor": "rgba(62,72,79,0.15)",
            "steps": [
                {"range": [0, 75],  "color": "rgba(78,222,163,.12)"},
                {"range": [75, 85], "color": "rgba(245,158,11,.12)"},
                {"range": [85, 100],"color": "rgba(255,180,171,.12)"},
            ]
        }
    ))
    fig_gauge.update_layout(
        height=280, margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter", color="#bdc8d1")
    )
    st.plotly_chart(apply_plotly_theme(fig_gauge), use_container_width=True)

with col_bar:
    st.markdown(f'<div class="section-header">{FWD_WEEKS}-Week Resource Forecast</div>', unsafe_allow_html=True)
    fwd = df_all[df_all["week_start"] >= sel_date].head(FWD_WEEKS).copy()
    if not fwd.empty:
        fwd["week_label"] = fwd["week_start"].dt.strftime("W%U %b '%y")
        fwd["staff"]     = (fwd["estimated_weekly_kandy_arrivals"] * (MARKET_SHARE / 100) / STAFF_RATIO).astype(int)
        fwd["transport"] = (fwd["estimated_weekly_kandy_arrivals"] * (MARKET_SHARE / 100) / VAN_RATIO).astype(int)
        fwd["is_festival"] = fwd["primary_festival"].apply(lambda x: x != "Normal")

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=fwd["week_label"], y=fwd["staff"],
            name="Staff Needed",
            marker_color=[
                "rgba(245,158,11,0.85)" if f else "rgba(142,213,255,0.75)"
                for f in fwd["is_festival"]
            ],
        ))
        fig_bar.add_trace(go.Bar(
            x=fwd["week_label"], y=fwd["transport"],
            name="Transport Units",
            marker_color="rgba(78,222,163,0.65)",
        ))
        fig_bar.update_layout(
            barmode="group", height=280, margin=dict(l=0, r=0, t=20, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="rgba(62,72,79,0.1)", tickfont=dict(color="#87929a", size=9)),
            yaxis=dict(gridcolor="rgba(62,72,79,0.1)"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                        bgcolor="rgba(0,0,0,0)", font=dict(color="#dae2fd")),
        )
        st.plotly_chart(apply_plotly_theme(fig_bar), use_container_width=True)
        st.caption("🟡 Amber bars = festival weeks requiring extra resources")
    else:
        st.info("No future data available for the forward chart. Run a model retrain first.")

# ── Forward Planning Table ───────────────────────────────────────────────────
st.markdown(f'<div class="section-header">📋 {FWD_WEEKS}-Week Forward Planning Table</div>', unsafe_allow_html=True)

fwd_table = df_all[df_all["week_start"] >= sel_date].head(FWD_WEEKS).copy()

if not fwd_table.empty:
    fwd_table["property_arrivals"] = fwd_table["estimated_weekly_kandy_arrivals"] * (MARKET_SHARE / 100)
    fwd_table["Rooms Needed"] = (fwd_table["property_arrivals"] / OCC_PER_ROOM).astype(int)
    fwd_table["Occupancy %"]  = ((fwd_table["Rooms Needed"] / HOTEL_CAPACITY) * 100).round(1)

    disp = pd.DataFrame({
        "Week of":           fwd_table["week_start"].dt.strftime("%d %b %Y"),
        "Regional Total":    fwd_table["estimated_weekly_kandy_arrivals"].astype(int).apply(lambda x: f"{x:,}"),
        "Property Arrivals": fwd_table["property_arrivals"].astype(int).apply(lambda x: f"{x:,}"),
        "Rooms Needed":      fwd_table["Rooms Needed"].apply(lambda x: f"{x:,}"),
        "Staff Needed":      (fwd_table["property_arrivals"] / STAFF_RATIO).astype(int).apply(lambda x: f"{x:,}"),
        "Transport Units":   (fwd_table["property_arrivals"] / VAN_RATIO).astype(int).apply(lambda x: f"{x:,}"),
        "Occupancy %":       fwd_table["Occupancy %"].astype(str) + "%",
        "Event / Festival":  fwd_table["primary_festival"].str.replace("_", " "),
    })

    st.dataframe(disp, use_container_width=True, hide_index=True)

    # ── CSV Download ────────────────────────────────────────────────────────
    csv_bytes = disp.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Planning Table as CSV",
        data=csv_bytes,
        file_name=f"resource_plan_{sel_date.strftime('%Y-%m-%d')}_{FWD_WEEKS}wk.csv",
        mime="text/csv",
        use_container_width=False,
    )

st.caption(
    f"Settings: {MARKET_SHARE:.1f}% Market Share · {HOTEL_CAPACITY} rooms · {OCC_PER_ROOM:.1f} tourists/room · "
    f"{STAFF_RATIO} tourists/staff · {VAN_RATIO} tourists/transport unit · "
    f"Source: Supabase Predictions + Historical CSV"
)
