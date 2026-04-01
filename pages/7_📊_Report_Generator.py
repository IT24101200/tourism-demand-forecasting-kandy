"""
pages/7_📊_Report_Generator.py
"""
import sys
from pathlib import Path
import io
import datetime
import json
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.sidebar import render_sidebar
from utils.auth import require_auth
from utils.theme import apply_plotly_theme, apply_custom_theme, render_page_banner, get_theme

sys.path.insert(0, str(Path(__file__).parent.parent))

require_auth()

st.set_page_config(
    page_title="Report Generator | Kandy Tourism DSS",
    page_icon="📊", layout="wide"
)

theme = get_theme()
apply_custom_theme()

st.markdown(f"""
<style>
.report-header{{
    background: {theme['surface_high']};
    backdrop-filter: blur(24px);
    border: 1px solid {theme['border']}; border-radius:12px;
    padding:20px 24px;margin-bottom:20px;
    box-shadow: 0 0 30px rgba(0,0,0,0.1);
}}
.rh-title{{font-size:1.3rem;font-weight:800;color:{theme['text_main']};margin-bottom:2px;font-family:'Manrope', sans-serif;}}
.rh-sub{{color:{theme['text_muted']};font-size:.82rem;}}

.filter-bar{{
    background: {theme['surface_high']};
    border: 1px solid {theme['border']}; border-radius:12px;
    padding:16px 20px; margin-bottom:18px;
    box-shadow: 0 0 20px rgba(0,0,0,0.08);
}}
.filter-bar-title{{
    font-size:.78rem;font-weight:700;color:{theme['text_muted']};
    letter-spacing:.07em;text-transform:uppercase;margin-bottom:10px;
}}

.week-card{{
    background: {theme['surface_high']};
    backdrop-filter: blur(24px);
    border: 1px solid {theme['border']}; border-radius:14px;
    padding:16px 18px;margin-bottom:12px;
    display:flex;align-items:center;justify-content:space-between;
    transition:border-color .2s;
    box-shadow: 0 0 20px rgba(0,0,0,0.1);
}}
.week-card:hover{{border-color:{theme['accent_dim']};}}
.wc-week{{color:{theme['text_muted']};font-size:.78rem;font-weight:600;letter-spacing:.05em;}}
.wc-festival{{color:{theme['warning']};font-size:.85rem;font-weight:700;}}
.wc-arrivals{{color:{theme['text_main']};font-size:1.5rem;font-weight:800;font-family:'Manrope', sans-serif;}}
.wc-chip{{
    display:inline-block;border-radius:20px;padding:2px 10px;font-size:.72rem;font-weight:600;
}}
.chip-peak{{background:rgba(239,68,68,0.1);color:{theme['danger']};border:1px solid rgba(239,68,68,0.2);}}
.chip-moderate{{background:rgba(245,158,11,0.1);color:{theme['warning']};border:1px solid rgba(245,158,11,0.2);}}
.chip-normal{{background:rgba(16,185,129,0.1);color:{theme['accent2']};border:1px solid rgba(16,185,129,0.2);}}

.insight-bullet{{
    background: {theme['surface_high']};
    border-left:3px solid {theme['accent_dim']};border-radius:0 10px 10px 0;
    padding:12px 16px;margin-bottom:10px;color:{theme['text_muted']};font-size:.88rem;
    box-shadow: 0 0 20px rgba(0,0,0,0.1);
}}
.insight-bullet strong{{color:{theme['text_main']};}}

.metric-mini{{font-size:0.78rem;font-weight:600;color:{theme['text_muted']};margin-bottom:2px;font-family:'Inter',sans-serif;}}
.metric-val{{font-size:1.35rem;font-weight:800;color:{theme['text_main']};font-family:'Manrope',sans-serif;margin-bottom:12px;}}
</style>
""", unsafe_allow_html=True)

render_sidebar(active_page="Report Generator")

BASE_DIR = Path(__file__).parent.parent

# ── Data Loading (cached – raw, unfiltered) ───────────────────────────────────
@st.cache_data
def load_raw_data():
    csv_path = BASE_DIR / "kandy_festival_demand_NOMISSING.csv"
    df_hist = pd.DataFrame()
    if csv_path.exists():
        df_hist = pd.read_csv(csv_path, on_bad_lines="skip")
        df_hist["week_start"] = pd.to_datetime(df_hist["week_start"])
        df_hist["is_future"] = False

    pred_path = BASE_DIR / "models/predictions_cache.csv"
    cdf = pd.DataFrame()
    if pred_path.exists():
        cdf = pd.read_csv(pred_path)
        cdf = cdf[cdf["model_name"] == "random_forest"].copy()

        def unpack_feats(row):
            try:
                feats = json.loads(row["features_used"])
            except Exception:
                feats = {}
            pf = "Normal"
            if feats.get("is_esala_perahera"):          pf = "Esala Perahera"
            elif feats.get("is_esala_preparation"):     pf = "Esala Prep"
            elif feats.get("is_poson_perahera"):        pf = "Poson Perahera"
            elif feats.get("is_vesak"):                 pf = "Vesak"
            elif feats.get("is_sinhala_tamil_new_year"):pf = "Sinhala Tamil New Year"
            elif feats.get("is_christmas_new_year"):    pf = "Christmas / New Year"
            elif feats.get("is_deepavali"):             pf = "Deepavali"
            elif feats.get("is_thai_pongal"):           pf = "Thai Pongal"
            elif feats.get("is_august_buildup"):        pf = "August Buildup"
            row["primary_festival"]        = pf
            row["avg_weekly_rainfall_mm"]  = feats.get("avg_weekly_rainfall_mm", 0)
            row["festival_demand_multiplier"] = feats.get("festival_demand_multiplier", 1.0)
            return row

        cdf = cdf.apply(unpack_feats, axis=1)
        cdf["week_start"] = pd.to_datetime(cdf["week_start"])
        cdf["estimated_weekly_kandy_arrivals"] = cdf["predicted_arrivals"]
        cdf["is_future"] = True

    df_all = pd.concat([df_hist, cdf]).sort_values("week_start").reset_index(drop=True)
    if "primary_festival" not in df_all.columns:
        df_all["primary_festival"] = "Normal"
    if "avg_weekly_rainfall_mm" not in df_all.columns:
        df_all["avg_weekly_rainfall_mm"] = 0.0
    return df_all

df_raw = load_raw_data()

# ── Page Banner ───────────────────────────────────────────────────────────────
render_page_banner(
    title="Automated Report Generator",
    subtitle="Apply filters, explore the forecast, and download a ready-to-share CSV action plan for hotel managers and tour operators.",
    icon="📊",
)

# ── Fixed constants ────────────────────────────────────────────────────────────
HOTEL_CAP   = 20000   # rooms
OCC_PPL     = 2.0     # avg tourists per room
STAFF_RATIO = 15      # tourists per staff member
VAN_RATIO   = 12      # tourists per van

# ── Inline Filter Bar ─────────────────────────────────────────────────────────
st.markdown('<div class="filter-bar"><div class="filter-bar-title">🔍 Report Priorities</div>', unsafe_allow_html=True)
fc1, fc2, fc3, fc4 = st.columns([1.5, 1.5, 1.3, 1.1])
with fc1:
    FEST_FILTER = st.selectbox(
        "🗓️ Event Type",
        ["All Weeks", "Festivals Only", "Normal Weeks Only"],
        help="Filter weeks by festival presence.",
        key="fest_filter"
    )
with fc2:
    WEATHER_FILTER = st.selectbox(
        "🌦️ Weather Condition",
        ["All Weather", "High Rainfall (>100 mm)", "Clear / Moderate (≤100 mm)"],
        help="Filter weeks by expected rainfall.",
        key="weather_filter"
    )
with fc3:
    MIN_OCC = st.slider(
        "🏨 Min Occupancy %",
        min_value=0, max_value=95, value=0, step=5,
        help="Only include weeks where expected occupancy meets this minimum.",
        key="min_occ"
    )
with fc4:
    report_wks = st.number_input(
        "📅 Weeks to Output",
        min_value=1, max_value=26, value=26, step=1,
        help="How many forecast weeks to load (Max 26).",
        key="report_wks"
    )
st.markdown('</div>', unsafe_allow_html=True)



# ── Apply Filters (always on fresh slice of raw data) ─────────────────────────
df_work = df_raw.copy()

# Calculate occupancy FIRST (needed for occupancy filter & display)
df_work["occ_pct"] = (df_work["estimated_weekly_kandy_arrivals"] / OCC_PPL) / HOTEL_CAP * 100

# Event filter
if FEST_FILTER == "Festivals Only":
    df_work = df_work[df_work["primary_festival"] != "Normal"]
elif FEST_FILTER == "Normal Weeks Only":
    df_work = df_work[df_work["primary_festival"] == "Normal"]

# Weather filter
if WEATHER_FILTER == "High Rainfall (>100 mm)":
    df_work = df_work[df_work["avg_weekly_rainfall_mm"] > 100]
elif WEATHER_FILTER == "Clear / Moderate (≤100 mm)":
    df_work = df_work[df_work["avg_weekly_rainfall_mm"] <= 100]

# Occupancy filter
if MIN_OCC > 0:
    df_work = df_work[df_work["occ_pct"] >= MIN_OCC]

# Future only → generated predictions
future_df = df_work[df_work["is_future"] == True].copy()

if future_df.empty:
    if df_work.empty:
        st.warning("⚠️ No data matches your current filters. Try widening the filters above.")
        st.stop()
    else:
        st.info(f"ℹ️ No future predictions match these filters — showing latest historic matching weeks instead.")
        recent = df_work.tail(int(report_wks)).copy()
else:
    recent = future_df.head(int(report_wks)).copy()

if recent.empty:
    st.warning("⚠️ No forecast data available for the selected filters.")
    st.stop()

# ── Resource calculations (always recalculated from current sidebar values) ───
recent = recent.copy()
recent["occ_pct"]   = (recent["estimated_weekly_kandy_arrivals"] / OCC_PPL) / HOTEL_CAP * 100
recent["staff"]     = (recent["estimated_weekly_kandy_arrivals"] / STAFF_RATIO).astype(int)
recent["transport"] = (recent["estimated_weekly_kandy_arrivals"] / VAN_RATIO).astype(int)
recent["wk"]        = recent["week_start"].dt.strftime("%d %b")

# ── Summary stats ─────────────────────────────────────────────────────────────
total_arrivals  = int(recent["estimated_weekly_kandy_arrivals"].sum())
peak_idx        = recent["estimated_weekly_kandy_arrivals"].idxmax()
peak_row        = recent.loc[peak_idx]
peak_arrivals   = int(peak_row["estimated_weekly_kandy_arrivals"])
peak_week_str   = peak_row["week_start"].strftime("%d %b")
avg_occ         = recent["occ_pct"].mean()
now_str         = datetime.datetime.now().strftime("%d %B %Y, %H:%M")
first_w         = recent["week_start"].min().strftime("%d %b %Y")
last_w          = recent["week_start"].max().strftime("%d %b %Y")

# ── Report header ─────────────────────────────────────────────────────────────
active_filters = []
if FEST_FILTER    != "All Weeks":            active_filters.append(FEST_FILTER)
if WEATHER_FILTER != "All Weather":          active_filters.append(WEATHER_FILTER)
if MIN_OCC        >  0:                      active_filters.append(f"Occ ≥ {MIN_OCC}%")
filter_tag = (" &nbsp;·&nbsp; ".join(active_filters)) if active_filters else "No Active Filters"

st.markdown(f"""
<div class="report-header">
    <div class="rh-title">📋 Forecast Report — Kandy District Tourism</div>
    <div class="rh-sub">
        {len(recent)} weeks &nbsp;|&nbsp; {first_w} → {last_w} &nbsp;|&nbsp; Generated: {now_str}
        &nbsp;|&nbsp; <span style='color:{theme["accent2"]};font-weight:600;'>Filters: {filter_tag}</span>
    </div>
</div>""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Executive Summary", "📈 Resource Chart", "🗄️ Raw Data & Download"])

# ─── Tab 1: Executive Summary ─────────────────────────────────────────────────
with tab1:
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-mini">📅 Report Period</div><div class="metric-val">{len(recent)} weeks</div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-mini">👥 Total Expected Arrivals</div><div class="metric-val">{total_arrivals:,}</div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-mini">📈 Peak Week</div><div class="metric-val">{peak_arrivals:,} <span style="font-size:.8rem;color:{theme["accent_dim"]};">({peak_week_str})</span></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-mini">🏨 Avg Occupancy</div><div class="metric-val">{avg_occ:.1f}%</div>', unsafe_allow_html=True)

    st.divider()

    # AI Insights
    st.markdown('<div class="section-header">💡 AI Insights — Auto-Generated</div>', unsafe_allow_html=True)
    insights = [
        f"📈 <strong>Peak Demand in Week of {peak_week_str}</strong> — Expected {peak_arrivals:,} arrivals. Festival: {peak_row.get('primary_festival', 'Normal')}."
    ]
    heavy_rain = recent[recent["avg_weekly_rainfall_mm"] > 120]
    if not heavy_rain.empty:
        wks_str = ", ".join(heavy_rain["week_start"].dt.strftime("%d %b").tolist())
        insights.append(f"🌧️ <strong>Heavy Rainfall (>120 mm) in {len(heavy_rain)} week(s)</strong>: {wks_str}. Recommend indoor packages and covered transport.")

    high_occ_wks = recent[recent["occ_pct"] > 85]
    if not high_occ_wks.empty:
        insights.append(f"🏨 <strong>Occupancy pressure >85% in {len(high_occ_wks)} week(s)</strong> — peak {recent['occ_pct'].max():.0f}%. Pre-book overflow accommodation and alert partner hotels.")
    else:
        insights.append(f"🏨 <strong>Occupancy comfortable at {avg_occ:.0f}% avg</strong>. No overflow risk in the current {len(recent)}-week window.")

    insights.append(f"🧑‍💼 <strong>Peak staffing: {recent['staff'].max()} personnel</strong>. Peak transport units needed: {recent['transport'].max()}.")

    for ins in insights:
        st.markdown(f'<div class="insight-bullet">{ins}</div>', unsafe_allow_html=True)

    st.divider()

    # Week-by-week cards
    st.markdown('<div class="section-header">🗓️ Week-by-Week Breakdown</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for i, (_, row) in enumerate(recent.iterrows()):
        arr   = int(row["estimated_weekly_kandy_arrivals"])
        fest  = str(row.get("primary_festival", "Normal"))
        week  = row["week_start"].strftime("%d %b %Y")
        rain  = float(row.get("avg_weekly_rainfall_mm", 0))
        occ   = float(row["occ_pct"])

        if   occ > 85: chip = '<span class="wc-chip chip-peak">⚡ Peak</span>'
        elif occ > 75: chip = '<span class="wc-chip chip-moderate">🟡 Busy</span>'
        else:          chip = '<span class="wc-chip chip-normal">✅ Normal</span>'

        html = f"""
        <div class="week-card">
            <div>
                <div class="wc-week">Week of {week}</div>
                <div class="wc-festival">{fest}</div>
                <div style="color:{theme['text_muted']};font-size:.8rem;margin-top:4px;">
                    🏨 {occ:.0f}% occ &nbsp; 🌧️ {rain:.0f} mm
                </div>
            </div>
            <div style="text-align:right;">
                <div class="wc-arrivals">{arr:,}</div>
                <div style="color:{theme['text_dim']};font-size:.72rem;margin-bottom:4px;">arrivals</div>
                {chip}
            </div>
        </div>"""
        with [c1, c2, c3][i % 3]:
            st.markdown(html, unsafe_allow_html=True)

# ─── Tab 2: Resource Chart ────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-header">Resource Requirements by Week</div>', unsafe_allow_html=True)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=recent["wk"], y=recent["staff"], name="Staff Needed", marker_color=theme["accent_dim"]),
        secondary_y=False
    )
    fig.add_trace(
        go.Bar(x=recent["wk"], y=recent["transport"], name="Transport Units", marker_color=theme["accent2_dim"]),
        secondary_y=False
    )
    fig.add_trace(
        go.Scatter(
            x=recent["wk"], y=recent["occ_pct"],
            name="Occupancy %", mode="lines+markers+text",
            line=dict(color=theme["danger"], dash="dot"),
            text=recent["occ_pct"].apply(lambda x: f"{x:.0f}%"),
            textposition="top center"
        ),
        secondary_y=True
    )
    fig.update_layout(
        barmode="group", height=400, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.1, bgcolor="rgba(0,0,0,0)", font=dict(color=theme["text_main"])),
        xaxis=dict(gridcolor=theme["border"]),
        yaxis=dict(title="Count", gridcolor=theme["border"], tickfont=dict(color=theme["text_muted"])),
        yaxis2=dict(title="Occupancy %", showgrid=False),
    )
    st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

# ─── Tab 3: Raw Data & Download ───────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-header">⬇️ Filtered Data & Export</div>', unsafe_allow_html=True)
    st.markdown(
        f"📄 This report contains **{len(recent)} week(s)** starting **{first_w}**, filtered by: "
        f"*{filter_tag}*. Arrivals, resource requirements, weather, and festival metadata included."
    )

    # Interactive preview table
    preview_cols = {
        "week_start": "Week Start",
        "primary_festival": "Event / Festival",
        "estimated_weekly_kandy_arrivals": "Expected Arrivals",
        "avg_weekly_rainfall_mm": "Rainfall (mm)",
        "staff": "Staff Needed",
        "transport": "Transport Units",
        "occ_pct": "Occupancy %",
    }
    display_df = recent[[c for c in preview_cols if c in recent.columns]].copy()
    display_df.rename(columns={c: preview_cols[c] for c in preview_cols if c in display_df.columns}, inplace=True)
    if "Occupancy %" in display_df.columns:
        display_df["Occupancy %"] = display_df["Occupancy %"].round(1)
    st.dataframe(display_df, use_container_width=True)

    # Build CSV
    def build_csv(df):
        out = io.StringIO()
        csv_df = df.rename(columns={c: preview_cols[c] for c in preview_cols if c in df.columns})
        if "Occupancy %" in csv_df.columns:
            csv_df["Occupancy %"] = csv_df["Occupancy %"].round(1).astype(str) + "%"
        if "Expected Arrivals" in csv_df.columns:
            csv_df["Expected Arrivals"] = csv_df["Expected Arrivals"].astype(int)
        csv_df.to_csv(out, index=False)
        return out.getvalue()

    csv_bytes = build_csv(recent[[c for c in preview_cols if c in recent.columns]].copy()).encode("utf-8")
    fname = f"kandy_tourism_report_{datetime.date.today().strftime('%Y%m%d')}.csv"
    st.download_button("⬇️  Download Filtered CSV Report", csv_bytes, fname, "text/csv", type="primary")
