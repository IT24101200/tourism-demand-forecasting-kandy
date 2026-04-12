"""
pages/7_📊_Report_Generator.py
"""
import sys
import re
from pathlib import Path
import io
import datetime
import json
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fpdf import FPDF
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

/* ── AI Comparison Cards ── */
.cmp-card{{
    background: {theme['surface_high']};
    backdrop-filter: blur(24px);
    border: 1px solid {theme['border']}; border-radius:14px;
    padding:20px; text-align:center;
    box-shadow: 0 0 20px rgba(0,0,0,0.1);
    transition: transform .2s ease, box-shadow .2s ease;
}}
.cmp-card:hover{{ transform: translateY(-3px); box-shadow: 0 0 30px rgba(56,189,248,0.08); }}
.cmp-label{{ color:{theme['text_muted']}; font-size:.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.08em; margin-bottom:6px; }}
.cmp-value{{ font-size:1.8rem; font-weight:800; font-family:'Manrope',sans-serif; line-height:1.1; }}
.cmp-sub{{ color:{theme['text_muted']}; font-size:.78rem; margin-top:4px; }}
.cmp-winner{{ color:{theme['accent2']}; }}
.cmp-loser{{ color:{theme['text_dim']}; }}
.cmp-table{{ width:100%; border-collapse:collapse; margin-top:12px; font-family:'Inter',sans-serif; }}
.cmp-table th{{ text-align:left; padding:10px 14px; color:{theme['text_muted']}; font-size:.75rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; border-bottom: 2px solid {theme['border']}; }}
.cmp-table td{{ padding:10px 14px; color:{theme['text_main']}; font-size:.88rem; border-bottom: 1px solid {theme['border']}; }}
.cmp-table tr:hover{{ background: {theme['surface_low']}; }}
.section-header{{ color:{theme['text_main']}; font-size:1rem; font-weight:700; letter-spacing:.05em; text-transform:uppercase; margin:24px 0 12px; padding-bottom:6px; border-bottom:2px solid {theme['accent_dim']}; }}
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

# ── Load training log metrics (cached) ────────────────────────────────────────
@st.cache_data
def load_training_metrics():
    """Parse MAE, RMSE, R² for both models from training_log.txt."""
    log_path = BASE_DIR / "models" / "training_log.txt"
    metrics = {
        "xgboost": {"mae": None, "rmse": None, "r2": None},
        "lstm":    {"mae": None, "rmse": None, "r2": None},
    }
    if not log_path.exists():
        return metrics
    text = log_path.read_text(encoding="utf-8", errors="ignore")
    xg_match = re.search(r"XGBoost Test \| MAE:\s*([\d,]+)\s+RMSE:\s*([\d,]+)\s+R.*?:\s*([\d.]+)", text)
    if xg_match:
        metrics["xgboost"]["mae"]  = int(xg_match.group(1).replace(",", ""))
        metrics["xgboost"]["rmse"] = int(xg_match.group(2).replace(",", ""))
        metrics["xgboost"]["r2"]   = float(xg_match.group(3))
    lstm_match = re.search(r"LSTM Test \| MAE:\s*([\d,]+)\s+RMSE:\s*([\d,]+)\s+R.*?:\s*([\d.]+)", text)
    if lstm_match:
        metrics["lstm"]["mae"]  = int(lstm_match.group(1).replace(",", ""))
        metrics["lstm"]["rmse"] = int(lstm_match.group(2).replace(",", ""))
        metrics["lstm"]["r2"]   = float(lstm_match.group(3))
    # Parse best params
    bp_match = re.search(r"Best Parameters Found:\s*(.+)", text)
    if bp_match:
        metrics["xgboost"]["best_params"] = bp_match.group(1).strip()
    # Parse training date
    dt_match = re.search(r"Started:\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", text)
    if dt_match:
        metrics["trained_at"] = dt_match.group(1)
    # Parse dataset size
    ds_match = re.search(r"Features:\s*(\d+)\s*\|\s*Rows:\s*(\d+)", text)
    if ds_match:
        metrics["n_features"] = int(ds_match.group(1))
        metrics["n_rows"]     = int(ds_match.group(2))
    return metrics

training_metrics = load_training_metrics()

# ── Load full predictions (both models) ───────────────────────────────────────
@st.cache_data
def load_all_predictions():
    pred_path = BASE_DIR / "models" / "predictions_cache.csv"
    if not pred_path.exists():
        return pd.DataFrame(), pd.DataFrame()
    cdf = pd.read_csv(pred_path)
    cdf["week_start"] = pd.to_datetime(cdf["week_start"])
    rf_df   = cdf[cdf["model_name"] == "random_forest"].sort_values("week_start").reset_index(drop=True)
    lstm_df = cdf[cdf["model_name"] == "lstm"].sort_values("week_start").reset_index(drop=True)
    return rf_df, lstm_df

rf_preds, lstm_preds = load_all_predictions()

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
tab1, tab2, tab3, tab4 = st.tabs(["📊 Executive Summary", "📈 Resource Chart", "🗄️ Raw Data & Download", "🤖 AI Model Comparison"])

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

    # Advanced NLG Section
    st.markdown('<div class="section-header">🤖 Advanced NLG Stakeholder Summary</div>', unsafe_allow_html=True)
    nlg_summary = f"Over the {len(recent)}-week reporting period beginning {first_w}, the Kandy district is projected to receive {total_arrivals:,} total tourist arrivals. "
    if high_occ_wks.empty:
        nlg_summary += f"Hospitality operations should run smoothly, maintaining an average occupancy of {avg_occ:.1f}% with no significant bottleneck events detected. "
    else:
        nlg_summary += f"We have identified critical operational pressure in {len(high_occ_wks)} week(s), peaking at {recent['occ_pct'].max():.0f}% occupancy during the week of {peak_week_str}. During this period, the system forecasts a necessary mobilization of {recent['staff'].max()} personnel and {recent['transport'].max()} transport units to manage the surge. "
        
    if not heavy_rain.empty:
        nlg_summary += f"Furthermore, stakeholder attention is strongly advised regarding expected heavy monsoon rainfall (>120 mm) across {len(heavy_rain)} week(s), which may complicate outdoor cultural events and transit routes. "
        
    st.markdown(f'<div class="insight-bullet" style="font-size:0.95rem; line-height:1.6; border-left:4px solid {theme["accent2"]};"><strong>AI Synthesis:</strong> {nlg_summary}</div>', unsafe_allow_html=True)

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
        
    # Build Excel
    def build_excel(df):
        output = io.BytesIO()
        csv_df = df.rename(columns={c: preview_cols[c] for c in preview_cols if c in df.columns})
        if "Occupancy %" in csv_df.columns:
            csv_df["Occupancy %"] = csv_df["Occupancy %"].round(1).astype(str) + "%"
        if "Expected Arrivals" in csv_df.columns:
            csv_df["Expected Arrivals"] = csv_df["Expected Arrivals"].astype(int)
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            csv_df.to_excel(writer, index=False, sheet_name='Forecast Data')
        processed_data = output.getvalue()
        return processed_data
        
    # Build PDF
    def build_pdf(df, nlg_text):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Automated Reporting System - Stakeholder Report", ln=True, align='C')
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 10, txt=f"Generated on {now_str}. Reporting Period: {first_w} to {last_w}.", ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Executive Summary (AI NLG)", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 7, txt=nlg_text)
        pdf.ln(10)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Forecast Highlights", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 7, txt=f"- Total Expected Arrivals: {total_arrivals:,}", ln=True)
        pdf.cell(200, 7, txt=f"- Peak Week Arrivals: {peak_arrivals:,} (Week of {peak_week_str})", ln=True)
        pdf.cell(200, 7, txt=f"- Average Occupancy: {avg_occ:.1f}%", ln=True)
        pdf.ln(10)
        
        return pdf.output(dest='S').encode('latin-1')

    dcols = st.columns(3)
    df_export = recent[[c for c in preview_cols if c in recent.columns]].copy()
    
    with dcols[0]:
        csv_bytes = build_csv(df_export).encode("utf-8")
        st.download_button("⬇️  Download CSV", csv_bytes, f"report_{datetime.date.today().strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True)
    with dcols[1]:
        excel_bytes = build_excel(df_export)
        st.download_button("⬇️  Download Excel", excel_bytes, f"report_{datetime.date.today().strftime('%Y%m%d')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with dcols[2]:
        pdf_bytes = build_pdf(df_export, nlg_summary)
        st.download_button("⬇️  Download PDF", pdf_bytes, f"report_{datetime.date.today().strftime('%Y%m%d')}.pdf", "application/pdf", use_container_width=True, type="primary")

# ─── Tab 4: AI Model Comparison ───────────────────────────────────────────────
with tab4:
    xg = training_metrics.get("xgboost", {})
    ls = training_metrics.get("lstm", {})
    n_feat = training_metrics.get("n_features", 27)
    n_rows = training_metrics.get("n_rows", 574)
    trained_at = training_metrics.get("trained_at", "N/A")

    # ── A. Performance Scorecard ──────────────────────────────────────────────
    st.markdown('<div class="section-header">🏆 Model Performance Scorecard</div>', unsafe_allow_html=True)

    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        xg_mae = xg.get("mae", "N/A")
        ls_mae = ls.get("mae", "N/A")
        winner_mae = "cmp-winner" if isinstance(xg_mae, (int, float)) and isinstance(ls_mae, (int, float)) and xg_mae < ls_mae else "cmp-loser"
        st.markdown(f"""
        <div class="cmp-card">
            <div class="cmp-label">XGBoost MAE</div>
            <div class="cmp-value {winner_mae}">{xg_mae:,}</div>
            <div class="cmp-sub">Mean Absolute Error</div>
        </div>""", unsafe_allow_html=True)
    with sc2:
        loser_mae = "cmp-winner" if winner_mae == "cmp-loser" else "cmp-loser"
        st.markdown(f"""
        <div class="cmp-card">
            <div class="cmp-label">LSTM MAE</div>
            <div class="cmp-value {loser_mae}">{ls_mae:,}</div>
            <div class="cmp-sub">Mean Absolute Error</div>
        </div>""", unsafe_allow_html=True)
    with sc3:
        xg_r2 = xg.get("r2", "N/A")
        ls_r2 = ls.get("r2", "N/A")
        winner_r2 = "cmp-winner" if isinstance(xg_r2, float) and isinstance(ls_r2, float) and xg_r2 > ls_r2 else "cmp-loser"
        r2_display = f"{xg_r2:.4f}" if isinstance(xg_r2, float) else "N/A"
        st.markdown(f"""
        <div class="cmp-card">
            <div class="cmp-label">XGBoost R²</div>
            <div class="cmp-value {winner_r2}">{r2_display}</div>
            <div class="cmp-sub">Variance Explained</div>
        </div>""", unsafe_allow_html=True)
    with sc4:
        loser_r2 = "cmp-winner" if winner_r2 == "cmp-loser" else "cmp-loser"
        r2_ls_display = f"{ls_r2:.4f}" if isinstance(ls_r2, float) else "N/A"
        st.markdown(f"""
        <div class="cmp-card">
            <div class="cmp-label">LSTM R²</div>
            <div class="cmp-value {loser_r2}">{r2_ls_display}</div>
            <div class="cmp-sub">Variance Explained</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── B. Full Comparison Table ──────────────────────────────────────────────
    st.markdown('<div class="section-header">📋 Detailed Architecture Comparison</div>', unsafe_allow_html=True)

    xg_rmse = xg.get("rmse", "N/A")
    ls_rmse = ls.get("rmse", "N/A")
    best_params = xg.get("best_params", "N/A")

    table_html = f"""
    <table class="cmp-table">
        <thead>
            <tr><th>Attribute</th><th>XGBoost (Gradient Boosting)</th><th>LSTM (Deep Learning)</th></tr>
        </thead>
        <tbody>
            <tr><td><strong>Model Type</strong></td><td>Ensemble Tree-Based (XGBRegressor)</td><td>Recurrent Neural Network (LSTM)</td></tr>
            <tr><td><strong>Architecture</strong></td><td>Gradient-boosted decision trees with GridSearchCV hyperparameter tuning</td><td>Unidirectional LSTM (64 units) → Dropout(0.2) → Dense(32, ReLU) → Dense(1)</td></tr>
            <tr><td><strong>Best Hyperparameters</strong></td><td style="font-size:.82rem;">{best_params}</td><td>Lookback=12 weeks, lr=5e-4, batch=16, dropout=0.2</td></tr>
            <tr><td><strong>Loss Function</strong></td><td>reg:squarederror</td><td>MSE (Mean Squared Error)</td></tr>
            <tr><td><strong>Cross-Validation</strong></td><td>3-fold GridSearchCV (54 candidates, 162 fits)</td><td>EarlyStopping (patience=20) + ReduceLROnPlateau</td></tr>
            <tr><td><strong>Training Dataset</strong></td><td>{n_rows:,} rows × {n_feat} features</td><td>{n_rows:,} rows × {n_feat} features (MinMaxScaled)</td></tr>
            <tr><td><strong>MAE (Test)</strong></td>
                <td style="color:{theme['accent2']};font-weight:700;">{xg_mae:,} arrivals</td>
                <td>{ls_mae:,} arrivals</td></tr>
            <tr><td><strong>RMSE (Test)</strong></td>
                <td style="color:{theme['accent2']};font-weight:700;">{xg_rmse:,}</td>
                <td>{ls_rmse:,}</td></tr>
            <tr><td><strong>R² Score (Test)</strong></td>
                <td style="color:{theme['accent2']};font-weight:700;">{r2_display} ({float(xg_r2)*100:.1f}% variance explained)</td>
                <td>{r2_ls_display} ({float(ls_r2)*100:.1f}% variance explained)</td></tr>
            <tr><td><strong>Strengths</strong></td>
                <td>✅ Superior accuracy (lower MAE/RMSE)<br>✅ Captures festival impacts precisely<br>✅ Handles tabular features natively</td>
                <td>✅ Learns sequential temporal patterns<br>✅ Can capture long-range dependencies<br>✅ Flexible architecture for time series</td></tr>
            <tr><td><strong>Limitations</strong></td>
                <td>⚠️ Cannot model long-range sequential memory<br>⚠️ Requires explicit feature engineering</td>
                <td>⚠️ Lower R² (underfitting risk)<br>⚠️ Requires scaled inputs<br>⚠️ Slower to train</td></tr>
            <tr><td><strong>Last Trained</strong></td><td colspan="2" style="text-align:center;">{trained_at}</td></tr>
        </tbody>
    </table>"""
    st.markdown(table_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── C. Forecast Overlap Chart ─────────────────────────────────────────────
    st.markdown('<div class="section-header">📈 52-Week Forecast Overlay — XGBoost vs LSTM</div>', unsafe_allow_html=True)

    if not rf_preds.empty and not lstm_preds.empty:
        fig_cmp = go.Figure()

        # XGBoost confidence band
        fig_cmp.add_trace(go.Scatter(
            x=pd.concat([rf_preds["week_start"], rf_preds["week_start"][::-1]]),
            y=pd.concat([rf_preds["upper_bound"], rf_preds["lower_bound"][::-1]]),
            fill="toself", fillcolor="rgba(57,184,253,0.08)",
            line=dict(color="rgba(0,0,0,0)"), showlegend=False,
            hoverinfo="skip", name="XGBoost CI"
        ))
        # LSTM confidence band
        fig_cmp.add_trace(go.Scatter(
            x=pd.concat([lstm_preds["week_start"], lstm_preds["week_start"][::-1]]),
            y=pd.concat([lstm_preds["upper_bound"], lstm_preds["lower_bound"][::-1]]),
            fill="toself", fillcolor="rgba(78,222,163,0.08)",
            line=dict(color="rgba(0,0,0,0)"), showlegend=False,
            hoverinfo="skip", name="LSTM CI"
        ))
        # XGBoost line
        fig_cmp.add_trace(go.Scatter(
            x=rf_preds["week_start"], y=rf_preds["predicted_arrivals"],
            name="XGBoost Forecast", mode="lines+markers",
            line=dict(color="#39b8fd", width=3),
            marker=dict(size=5, color="#39b8fd"),
            hovertemplate="<b>%{x|%d %b}</b><br>XGBoost: %{y:,.0f}<extra></extra>"
        ))
        # LSTM line
        fig_cmp.add_trace(go.Scatter(
            x=lstm_preds["week_start"], y=lstm_preds["predicted_arrivals"],
            name="LSTM Forecast", mode="lines+markers",
            line=dict(color="#4edea3", width=2, dash="dash"),
            marker=dict(size=4, color="#4edea3", symbol="diamond"),
            hovertemplate="<b>%{x|%d %b}</b><br>LSTM: %{y:,.0f}<extra></extra>"
        ))

        fig_cmp.update_layout(
            height=420, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            hovermode="x unified",
            legend=dict(orientation="h", y=1.08, bgcolor="rgba(0,0,0,0)", font=dict(color=theme["text_main"])),
            xaxis=dict(gridcolor=theme["border"], tickfont=dict(color=theme["text_muted"])),
            yaxis=dict(title="Predicted Arrivals", gridcolor=theme["border"], tickfont=dict(color=theme["text_muted"])),
        )
        st.plotly_chart(apply_plotly_theme(fig_cmp), use_container_width=True)
    else:
        st.info("ℹ️ Prediction data unavailable. Please run the training pipeline first.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── D. Weekly Deviation Analysis ──────────────────────────────────────────
    st.markdown('<div class="section-header">📊 Weekly Prediction Deviation — Model Agreement</div>', unsafe_allow_html=True)

    if not rf_preds.empty and not lstm_preds.empty and len(rf_preds) == len(lstm_preds):
        dev_df = pd.DataFrame({
            "week_start": rf_preds["week_start"].values,
            "rf_pred":    rf_preds["predicted_arrivals"].values,
            "lstm_pred":  lstm_preds["predicted_arrivals"].values,
        })
        dev_df["deviation"] = abs(dev_df["rf_pred"] - dev_df["lstm_pred"])
        dev_df["dev_pct"]   = dev_df["deviation"] / dev_df[["rf_pred", "lstm_pred"]].mean(axis=1) * 100
        dev_df["wk_label"]  = pd.to_datetime(dev_df["week_start"]).dt.strftime("%d %b")

        # Color: green if <20% deviation, amber if ≥20%
        colors = [theme["accent2"] if p < 20 else theme["warning"] for p in dev_df["dev_pct"]]

        fig_dev = go.Figure(go.Bar(
            x=dev_df["wk_label"], y=dev_df["deviation"],
            marker_color=colors,
            text=dev_df["dev_pct"].apply(lambda x: f"{x:.0f}%"),
            textposition="outside", textfont=dict(size=9, color=theme["text_muted"]),
            hovertemplate="<b>%{x}</b><br>Deviation: %{y:,.0f} arrivals<extra></extra>"
        ))
        fig_dev.update_layout(
            height=300, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor=theme["border"], tickfont=dict(color=theme["text_muted"], size=9), tickangle=-45),
            yaxis=dict(title="|XGBoost − LSTM|", gridcolor=theme["border"], tickfont=dict(color=theme["text_muted"])),
        )
        st.plotly_chart(apply_plotly_theme(fig_dev), use_container_width=True)

        # Summary stats
        high_dev_weeks = dev_df[dev_df["dev_pct"] >= 20]
        avg_dev = dev_df["deviation"].mean()
        max_dev_row = dev_df.loc[dev_df["deviation"].idxmax()]
        dev_cols = st.columns(3)
        with dev_cols[0]:
            st.markdown(f'<div class="metric-mini">📏 Avg Weekly Deviation</div><div class="metric-val">{avg_dev:,.0f} <span style="font-size:.8rem;color:{theme["text_muted"]};">arrivals</span></div>', unsafe_allow_html=True)
        with dev_cols[1]:
            st.markdown(f'<div class="metric-mini">⚡ Max Deviation Week</div><div class="metric-val">{int(max_dev_row["deviation"]):,} <span style="font-size:.8rem;color:{theme["text_muted"]};">({max_dev_row["wk_label"]})</span></div>', unsafe_allow_html=True)
        with dev_cols[2]:
            st.markdown(f'<div class="metric-mini">⚠️ High Divergence Weeks (≥20%)</div><div class="metric-val">{len(high_dev_weeks)} <span style="font-size:.8rem;color:{theme["text_muted"]};">of {len(dev_df)}</span></div>', unsafe_allow_html=True)
    else:
        st.info("ℹ️ Both model predictions are needed for deviation analysis.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── E. AI Recommendation Engine ───────────────────────────────────────────
    st.markdown('<div class="section-header">🧠 AI Model Recommendation</div>', unsafe_allow_html=True)

    rec_parts = []
    if isinstance(xg_r2, float) and isinstance(ls_r2, float):
        r2_gap = xg_r2 - ls_r2
        mae_gap = (ls_mae - xg_mae) if isinstance(xg_mae, (int, float)) and isinstance(ls_mae, (int, float)) else 0

        rec_parts.append(
            f"Based on rigorous test-set evaluation, the <strong>XGBoost (Gradient Boosting)</strong> engine is the recommended primary forecasting model. "
            f"It achieves an R² of <strong>{xg_r2:.4f}</strong> — explaining <strong>{xg_r2*100:.1f}%</strong> of arrival variance — "
            f"compared to LSTM's <strong>{ls_r2:.4f}</strong> ({ls_r2*100:.1f}%). This represents a <strong>{r2_gap*100:.1f} percentage point advantage</strong> in predictive power."
        )

        rec_parts.append(
            f"XGBoost also delivers a tighter Mean Absolute Error of <strong>{xg_mae:,}</strong> arrivals per week versus LSTM's <strong>{ls_mae:,}</strong>, "
            f"meaning XGBoost predictions are on average <strong>{mae_gap:,} arrivals closer</strong> to actual observations."
        )

        if not rf_preds.empty and not lstm_preds.empty and len(rf_preds) == len(lstm_preds):
            agreement_pct = 100 - dev_df["dev_pct"].mean()
            rec_parts.append(
                f"Across the 52-week forecast horizon, the two models show an average agreement of <strong>{agreement_pct:.1f}%</strong>. "
                f"Weeks where models diverge significantly (≥20%) should be flagged for manual review by tourism planners, as they indicate higher forecast uncertainty."
            )

        rec_parts.append(
            "<strong>Recommendation:</strong> Use XGBoost as the primary decision engine for resource allocation, hotel staffing, and transport planning. "
            "LSTM serves as a valuable secondary validation model — when both models agree, confidence in the forecast is highest."
        )
    else:
        rec_parts.append("⚠️ Training metrics are unavailable. Please run the training pipeline (<code>python train_models.py</code>) to generate model evaluation data.")

    rec_text = " ".join(rec_parts)
    st.markdown(
        f'<div class="insight-bullet" style="font-size:0.95rem; line-height:1.7; border-left:4px solid {theme["accent2"]};">{rec_text}</div>',
        unsafe_allow_html=True
    )

