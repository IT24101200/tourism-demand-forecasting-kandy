"""
pages/4_🏨_Resource_Planner.py
"""
import sys
from pathlib import Path
import datetime
import json
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from utils.sidebar import render_sidebar
from utils.auth import require_auth
from utils.theme import apply_plotly_theme, apply_custom_theme, render_page_banner

sys.path.insert(0, str(Path(__file__).parent.parent))

require_auth()

st.set_page_config(
    page_title="Resource Planner | Kandy Tourism DSS",
    page_icon="🏨", layout="wide"
)

apply_custom_theme()

st.markdown("""
<style>
.kpi-card {
    background: rgba(19, 27, 46, 0.6);
    backdrop-filter: blur(24px);
    border: 1px solid rgba(62, 72, 79, 0.15);
    border-radius: 14px; padding: 20px;
    transition: box-shadow .3s cubic-bezier(0.25, 0.8, 0.25, 1), transform .3s;
    display: flex; align-items: center; gap: 16px;
}
.kpi-card:hover { transform: translateY(-3px); box-shadow: 0 0 40px rgba(142,213,255,0.06); }
.kpi-icon-box {
    width: 52px; height: 52px; border-radius: 12px;
    background: linear-gradient(135deg, rgba(56,189,248,0.15) 0%, rgba(142,213,255,0.15) 100%);
    border: 1px solid rgba(56,189,248,0.3);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.6rem; flex-shrink: 0;
    box-shadow: inset 0 0 12px rgba(56,189,248,0.1);
}
.kpi-content { text-align: left; }
.kpi-value { font-size: 1.8rem; font-weight: 800; color: #dae2fd; line-height: 1.1; font-family: 'Manrope', sans-serif; }
.kpi-label { color: #bdc8d1; font-size: .75rem; font-weight: 600; font-family: 'Inter', sans-serif;
             text-transform: uppercase; letter-spacing: .08em; margin-bottom: 2px;}
.kpi-delta { font-size: .8rem; margin-top: 4px; font-weight: 600; font-family: 'Inter', sans-serif;}
.delta-up { color: #4edea3; }
.delta-down { color: #ffb4ab; }
</style>
""", unsafe_allow_html=True)

def _controls():
    st.sidebar.markdown('### ⚙️ Planner Settings')
    cap = st.sidebar.slider('Hotel Capacity (rooms)', 1, 1000, 500)
    occ = st.sidebar.number_input('Avg tourists / room', 1.0, 5.0, 2.0)
    staff = st.sidebar.number_input('Tourists per staff member', 5, 50, 15)
    van = st.sidebar.number_input('Tourists per transport unit', 5, 50, 12)
    st.sidebar.divider()
    return cap, occ, staff, van

HOTEL_CAPACITY, OCC_PER_ROOM, STAFF_RATIO, VAN_RATIO = _controls()
render_sidebar("Resource Planner")

BASE_DIR = Path(__file__).parent.parent

@st.cache_data
def load_data():
    csv_path = BASE_DIR / "kandy_festival_demand_NOMISSING.csv"
    if csv_path.exists():
        df_hist = pd.read_csv(csv_path, on_bad_lines="skip")
        df_hist["week_start"] = pd.to_datetime(df_hist["week_start"])
    else:
        df_hist = pd.DataFrame()
        
    pred_path = BASE_DIR / "models/predictions_cache.csv"
    if pred_path.exists():
        cdf = pd.read_csv(pred_path)
        cdf = cdf[cdf["model_name"] == "random_forest"].copy()
        
        def unpack_feats(row):
            feats = json.loads(row["features_used"])
            pf = "Normal"
            if feats.get("is_esala_perahera"): pf = "Esala_Perahera"
            elif feats.get("is_esala_preparation"): pf = "Esala_Prep"
            elif feats.get("is_poson_perahera"): pf = "Poson_Perahera"
            elif feats.get("is_vesak"): pf = "Vesak"
            elif feats.get("is_sinhala_tamil_new_year"): pf = "Sinhala_Tamil_New_Year"
            elif feats.get("is_christmas_new_year"): pf = "Christmas_New_Year"
            elif feats.get("is_deepavali"): pf = "Deepavali"
            elif feats.get("is_thai_pongal"): pf = "Thai_Pongal"
            elif feats.get("is_august_buildup"): pf = "August_Buildup"
            
            row["primary_festival"] = pf
            row["avg_weekly_rainfall_mm"] = feats.get("avg_weekly_rainfall_mm", 0)
            return row
            
        cdf = cdf.apply(unpack_feats, axis=1)
        cdf["week_start"] = pd.to_datetime(cdf["week_start"])
        cdf["estimated_weekly_kandy_arrivals"] = cdf["predicted_arrivals"]
    else:
        cdf = pd.DataFrame()
        
    df_all = pd.concat([df_hist, cdf]).sort_values("week_start").reset_index(drop=True)
    return df_all

df_all = load_data()

if df_all.empty:
    st.info('ℹ️ No forecast data available for resource planning at the moment.')
    st.stop()
    
today = datetime.datetime.combine(datetime.date.today(), datetime.time())
next_week_start = today + datetime.timedelta(days=7)
recent_and_future = df_all[df_all["week_start"] >= today - datetime.timedelta(days=60)].copy()

w_options = recent_and_future["week_start"].dt.strftime('%Y-%m-%d').tolist()
default_idx = 0
for i, dstr in enumerate(w_options):
    if dstr >= next_week_start.strftime('%Y-%m-%d'):
        default_idx = i
        break
        
sel_week_str = st.selectbox('📅 Select Planning Week', w_options, index=default_idx)
sel_date = pd.to_datetime(sel_week_str)
sel_row = df_all[df_all["week_start"] == sel_date].iloc[0]

arrivals = int(sel_row.get("estimated_weekly_kandy_arrivals", 0))
festival = sel_row.get("primary_festival", "Normal")
rain = sel_row.get("avg_weekly_rainfall_mm", 0)

rooms_needed = int(arrivals / OCC_PER_ROOM)
staff_needed = int(arrivals / STAFF_RATIO)
transport_units = int(arrivals / VAN_RATIO)
occupancy_pct = min(100.0, (rooms_needed / HOTEL_CAPACITY) * 100)



render_page_banner(
    title="Resort & Resource Planner",
    subtitle="Translate AI arrival forecasts into actionable operational requirements for your hotel, transport fleet, and staff rosters.",
    icon="🏨",
)

sel_date_label = sel_date.strftime('%d %B %Y')
st.markdown(f"<h4 style='color:#F8FAFC;margin-bottom:6px;font-weight:700;'>📋 Resource Requirements for the Week of <span style='color:var(--tropical-green)'>{sel_date_label}</span></h4>", unsafe_allow_html=True)

if occupancy_pct > 85:
    st.error(f"🚨 **Critical Capacity Alert** — Occupancy pressure at **{occupancy_pct:.1f}%** for week of {sel_date_label}. Consider activating overflow accommodation partnerships and pre-booking buses.")
elif occupancy_pct > 75:
    st.warning(f"⚠️ **High Occupancy** — {occupancy_pct:.1f}% pressure. Pre-position extra transport and notify hoteliers.")
    
if festival != "Normal":
    st.info(f"🎉 **Festival Week — {festival.replace('_', ' ')}** | Demand multiplier active. Expect {arrivals:,} arrivals. Coordinate with event organisers for traffic management.")
if rain > 150:
    st.info(f"🌧️ **Heavy Rainfall Forecast** — {rain:.0f} mm expected. Arrange covered transport options and visitor shelters.")

st.markdown('<div class="section-header">📊 Weekly Resource Requirements</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

cards = [
    (c1, "🛬", "Expected Arrivals", f"{arrivals:,}", ""),
    (c2, "👩‍💼", "Staff Required", f"{staff_needed:,}", f"+{int(staff_needed*0.1)} contingency"),
    (c3, "🚐", "Transport Units", f"{transport_units:,}", f"~{VAN_RATIO} tourists/unit"),
    (c4, "🏨", "Occupancy Pressure", f"{occupancy_pct:.1f}%", "⚠️ Critical!" if occupancy_pct > 85 else ("🟡 High" if occupancy_pct>75 else "✅ Normal"))
]

for col, icon, label, val, delta in cards:
    delta_cls = "delta-down" if "Critical" in delta else ("delta-up" if "Normal" in delta else "")
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon-box">{icon}</div>
            <div class="kpi-content">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{val}</div>
                <div class="kpi-delta {delta_cls}">{delta}</div>
            </div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col_gauge, col_bar = st.columns([1, 1.5])
with col_gauge:
    st.markdown('<div class="section-header">📈 Occupancy Pressure Gauge</div>', unsafe_allow_html=True)
    gauge_color = "#4edea3" if occupancy_pct < 75 else ("#F59E0B" if occupancy_pct < 85 else "#ffb4ab")
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=occupancy_pct,
        title={'text': "Hotel Occupancy Pressure", 'font': {'color': "#dae2fd", 'family': 'Inter'}},
        number={'suffix': "%", 'font': {'color': "#dae2fd"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "rgba(62, 72, 79, 0.15)"},
            'bar': {'color': gauge_color},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "rgba(62, 72, 79, 0.15)",
            'steps': [
                {'range': [0, 75], 'color': "rgba(78,222,163,.12)"},
                {'range': [75, 85], 'color': "rgba(245,158,11,.12)"},
                {'range': [85, 100], 'color': "rgba(255,180,171,.12)"}
            ]
        }
    ))
    fig_gauge.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter", color="#bdc8d1"))
    st.plotly_chart(apply_plotly_theme(fig_gauge), use_container_width=True)

with col_bar:
    st.markdown('<div class="section-header">12-Week Resource Forecast</div>', unsafe_allow_html=True)
    fwd = df_all[df_all["week_start"] >= sel_date].head(12).copy()
    if not fwd.empty:
        fwd["week_label"] = fwd["week_start"].dt.strftime("W%U\n%b %Y")
        fwd["staff"] = (fwd["estimated_weekly_kandy_arrivals"] / STAFF_RATIO).astype(int)
        fwd["transport"] = (fwd["estimated_weekly_kandy_arrivals"] / VAN_RATIO).astype(int)
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=fwd["week_label"], y=fwd["staff"], name="Staff Needed", marker_color="rgba(142,213,255,.8)"))
        fig_bar.add_trace(go.Bar(x=fwd["week_label"], y=fwd["transport"], name="Transport Units", marker_color="rgba(78,222,163,.7)"))
        
        fig_bar.update_layout(
            barmode="group", height=280, margin=dict(l=0, r=0, t=20, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="rgba(62, 72, 79, 0.1)"), yaxis=dict(gridcolor="rgba(62, 72, 79, 0.1)"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)", font=dict(color="#dae2fd"))
        )
        st.plotly_chart(apply_plotly_theme(fig_bar), use_container_width=True)

st.markdown('<div class="section-header">📋 4-Week Forward Planning Table</div>', unsafe_allow_html=True)
fwd4 = df_all[df_all["week_start"] >= sel_date].head(4).copy()
if not fwd4.empty:
    disp = pd.DataFrame({
        "Week of": fwd4["week_start"].dt.strftime("%d %b %Y"),
        "Arrivals Forecast": fwd4["estimated_weekly_kandy_arrivals"].astype(int).apply(lambda x: f"{x:,}"),
        "Staff Needed": (fwd4["estimated_weekly_kandy_arrivals"] / STAFF_RATIO).astype(int),
        "Occupancy %": ((fwd4["estimated_weekly_kandy_arrivals"] / OCC_PER_ROOM) / HOTEL_CAPACITY * 100).round(1).astype(str) + "%",
        "Event/Festival": fwd4.get("primary_festival", "Normal").str.replace("_", " ")
    })
    st.dataframe(disp, use_container_width=True, hide_index=True)
