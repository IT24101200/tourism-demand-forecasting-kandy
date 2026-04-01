"""
pages/1_🏠_National_Overview.py — Redesigned National Tourism Overview
"Luminous Cartographer" aesthetic — professional, data-rich, filter-driven
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import datetime
import base64
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.db import fetch_national_tourism
from utils.sidebar import render_sidebar
from utils.auth import require_auth
from utils.theme import apply_custom_theme, apply_plotly_theme, render_page_header, render_metric_card, get_theme, get_current_week_prediction, get_next_week_prediction

require_auth()
theme = get_theme()

st.set_page_config(
    page_title="National Tourism Overview | Kandy DSS",
    page_icon="🏔️", layout="wide", initial_sidebar_state="expanded",
)

apply_custom_theme()
render_sidebar(active_page="National Overview")

# ── Page CSS ─────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

/* ── Filter Bar ── */
.filter-bar {{
    background: rgba(20, 31, 56, 0.7);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(64, 72, 93, 0.4);
    border-radius: 16px;
    padding: 18px 24px;
    margin-bottom: 28px;
}}
.filter-label {{
    color: {theme['text_dim']};
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 6px;
}}

/* ── Badge chips (This Week / Next Week) ── */
.pred-badge {{
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 8px 16px;
    border-radius: 10px;
    font-family: 'Inter', sans-serif;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    white-space: nowrap;
}}
.pred-badge.this-week {{
    background: rgba(105,246,184,0.1);
    border: 1px solid rgba(105,246,184,0.25);
    color: {theme['accent2_dim']};
}}
.pred-badge.next-week {{
    background: rgba(57,184,253,0.1);
    border: 1px solid rgba(57,184,253,0.25);
    color: {theme['accent_dim']};
}}
.clock-chip {{
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    background: rgba(57,184,253,0.05);
    border: 1px solid rgba(57,184,253,0.15);
    border-radius: 10px;
    padding: 6px 16px;
}}
.clock-chip .time-text {{
    color: {theme['accent_dim']};
    font-family: 'Manrope', sans-serif;
    font-size: 1rem;
    font-weight: 800;
    letter-spacing: 0.05em;
}}
.clock-chip .date-text {{
    color: {theme['text_dim']};
    font-family: 'Inter', sans-serif;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    margin-top: 1px;
}}

/* ── Section headings ── */
.section-title {{
    color: {theme['text_main']};
    font-family: 'Manrope', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    margin-bottom: 2px;
}}
.section-sub {{
    color: {theme['text_muted']};
    font-family: 'Inter', sans-serif;
    font-size: 0.82rem;
    margin-bottom: 14px;
}}

/* ── Insight bullet ── */
.insight-bullet {{
    background: {theme['surface_low']};
    border-left: 3px solid {theme['accent_dim']};
    border-radius: 0 10px 10px 0;
    padding: 12px 16px;
    margin-bottom: 10px;
    color: {theme['text_muted']};
    font-size: .88rem;
    font-family: 'Inter', sans-serif;
}}
.insight-bullet strong {{ color: {theme['text_main']}; }}

/* ── Profile stat card ── */
.profile-stat-card {{
    background: {theme['surface_low']};
    border: 1px solid {theme['border']};
    border-radius: 14px;
    padding: 20px 22px;
    height: 100%;
    text-align: center;
}}
.profile-stat-label {{
    color: {theme['text_dim']};
    font-family: 'Inter', sans-serif;
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 8px;
}}
.profile-stat-value {{
    color: {theme['text_main']};
    font-family: 'Manrope', sans-serif;
    font-size: 1.8rem;
    font-weight: 800;
    line-height: 1.1;
}}
.profile-stat-sub {{
    color: {theme['text_muted']};
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    margin-top: 4px;
}}

/* ── Revenue forecast card ── */
.forecast-insight-card {{
    background: {theme['surface_low']};
    border: 1px solid {theme['border']};
    border-left: 3px solid {theme['accent2_dim']};
    border-radius: 0 12px 12px 0;
    padding: 14px 18px;
    margin-bottom: 10px;
}}
.forecast-insight-card .fi-title {{
    color: {theme['text_main']};
    font-family: 'Manrope', sans-serif;
    font-size: 0.95rem;
    font-weight: 700;
}}
.forecast-insight-card .fi-body {{
    color: {theme['text_muted']};
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    margin-top: 3px;
}}

/* ── Pulse dot ── */
.pulse-dot {{
    display: inline-block;
    width: 10px; height: 10px;
    border-radius: 50%;
    background: {theme['accent2']};
    box-shadow: 0 0 8px {theme['accent2']};
    animation: pulse 2s infinite;
}}
@keyframes pulse {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.6; transform: scale(1.3); }}
}}
</style>
""", unsafe_allow_html=True)


# ── Load data ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_national():
    local_csv = Path(__file__).parent.parent / "Sri_Lanka_Tourist_Forecast_Training_Dataset_2015_2025.csv"
    if local_csv.exists():
        df = pd.read_csv(local_csv, on_bad_lines="skip")
    else:
        try:
            df = fetch_national_tourism()
            if df.empty:
                raise ValueError("Empty response")
        except Exception as e:
            st.error(f"Could not load national data: {e}")
            return pd.DataFrame()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df["date"] = pd.to_datetime(
        df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2) + "-01"
    )
    for c in ["tourist_arrivals","revenue_usd_millions","hotel_occupancy_rate_pct",
              "india_arrivals","uk_arrivals","china_arrivals","germany_arrivals",
              "russia_arrivals","other_arrivals"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.sort_values("date").reset_index(drop=True)

df_all = load_national()

if df_all.empty:
    st.info("ℹ️ No national tourism data available. Please check back later.")
    st.stop()

all_years = sorted(df_all["year"].dropna().astype(int).unique())

# ── Premium Header ─────────────────────────────────────────────────────────
pred_val      = get_current_week_prediction()
next_pred_val = get_next_week_prediction()
now           = datetime.datetime.now()
time_str      = now.strftime("%I:%M %p")
date_str      = now.strftime("%d %b %Y").upper()

# Build badge HTML completely in Python (no f-string nesting issues)
badge_this = ""
badge_next = ""
if pred_val:
    badge_this = (
        '<div style="display:inline-flex;align-items:center;gap:8px;padding:10px 20px;'
        'border-radius:999px;background:rgba(105,246,184,0.08);'
        'border:1px solid rgba(105,246,184,0.35);'
        'box-shadow:0 0 18px rgba(105,246,184,0.12);">'
        '<span style="font-size:1rem;">&#127919;</span>'
        '<span style="font-family:Inter,sans-serif;font-size:0.75rem;font-weight:700;'
        'letter-spacing:0.06em;color:#69f6b8;">THIS WEEK</span>'
        f'<span style="font-family:Manrope,sans-serif;font-size:1rem;font-weight:800;'
        f'color:#e1ffec;">{pred_val:,}</span>'
        '</div>'
    )
if next_pred_val:
    badge_next = (
        '<div style="display:inline-flex;align-items:center;gap:8px;padding:10px 20px;'
        'border-radius:999px;background:rgba(57,184,253,0.08);'
        'border:1px solid rgba(57,184,253,0.35);'
        'box-shadow:0 0 18px rgba(57,184,253,0.12);">'
        '<span style="font-size:1rem;">&#128202;</span>'
        '<span style="font-family:Inter,sans-serif;font-size:0.75rem;font-weight:700;'
        'letter-spacing:0.06em;color:#39b8fd;">NEXT WEEK</span>'
        f'<span style="font-family:Manrope,sans-serif;font-size:1rem;font-weight:800;'
        f'color:#cef0ff;">{next_pred_val:,}</span>'
        '</div>'
    )

clock_html = (
    '<div style="flex-shrink:0;background:rgba(20,31,56,0.7);'
    'backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);'
    'border:1px solid rgba(57,184,253,0.2);border-radius:14px;'
    'padding:14px 22px;text-align:center;'
    'box-shadow:0 0 24px rgba(57,184,253,0.08);">'
    f'<div style="font-family:Manrope,sans-serif;font-size:1.55rem;font-weight:800;'
    f'color:#39b8fd;letter-spacing:0.04em;line-height:1;">{time_str}</div>'
    f'<div style="font-family:Inter,sans-serif;font-size:0.65rem;font-weight:700;'
    f'color:#6d758c;letter-spacing:0.1em;margin-top:4px;text-transform:uppercase;">{date_str}</div>'
    '</div>'
)

header_html = (
    '<div style="background:linear-gradient(135deg,#091328 0%,#060e20 60%,#0a1628 100%);'
    'border:1px solid rgba(57,184,253,0.15);border-radius:18px;'
    'padding:28px 36px 0 36px;margin-bottom:6px;position:relative;overflow:hidden;">'

    # ambient glow blobs (no comments)
    '<div style="position:absolute;top:-60px;right:-60px;width:260px;height:260px;'
    'border-radius:50%;background:radial-gradient(circle,rgba(57,184,253,0.07) 0%,transparent 70%);'
    'pointer-events:none;"></div>'
    '<div style="position:absolute;bottom:-40px;left:80px;width:200px;height:200px;'
    'border-radius:50%;background:radial-gradient(circle,rgba(105,246,184,0.05) 0%,transparent 70%);'
    'pointer-events:none;"></div>'

    # three-col flex row
    '<div style="display:flex;align-items:center;justify-content:space-between;'
    'gap:24px;position:relative;z-index:1;">'

    # LEFT: title + accent bar
    '<div style="display:flex;align-items:flex-start;gap:16px;flex:1;min-width:0;">'
    '<div style="width:4px;min-height:64px;border-radius:4px;flex-shrink:0;'
    'background:linear-gradient(180deg,#39b8fd 0%,#69f6b8 100%);'
    'box-shadow:0 0 12px rgba(57,184,253,0.5);margin-top:4px;"></div>'
    '<div>'
    '<div style="font-family:Manrope,sans-serif;font-size:2.1rem;font-weight:800;'
    'color:#dee5ff;line-height:1.1;letter-spacing:-0.025em;white-space:nowrap;">'
    'National Performance '
    '<span style="color:#39b8fd;text-shadow:0 0 20px rgba(57,184,253,0.4);">Canvas</span>'
    '</div>'
    '<div style="font-family:Inter,sans-serif;font-size:0.88rem;color:#6d758c;'
    'margin-top:6px;font-weight:500;letter-spacing:0.01em;">'
    '&#127472;&#127473;&nbsp; Strategic intelligence for Sri Lanka\'s hospitality sector'
    '</div>'
    '</div></div>'

    # CENTER: badges
    f'<div style="display:flex;align-items:center;gap:10px;flex-shrink:0;">'
    f'{badge_this}{badge_next}'
    '</div>'

    # RIGHT: clock
    + clock_html +

    '</div>'  # end flex row

    # bottom glow separator
    '<div style="height:2px;margin:24px -36px 0 -36px;'
    'background:linear-gradient(90deg,transparent 0%,rgba(57,184,253,0.35) 30%,'
    'rgba(105,246,184,0.3) 70%,transparent 100%);'
    'box-shadow:0 0 10px rgba(57,184,253,0.2);"></div>'

    '</div>'  # end outer card
)

st.markdown(header_html, unsafe_allow_html=True)
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)




# ── FILTER BAR ─────────────────────────────────────────────────────────────
# Persist filter state in session_state so Apply Filters actually gates the update
if "filter_year_range" not in st.session_state:
    st.session_state["filter_year_range"] = (all_years[max(0, len(all_years)-5)], all_years[-1])
if "filter_origin" not in st.session_state:
    st.session_state["filter_origin"] = "All"
if "filter_year" not in st.session_state:
    st.session_state["filter_year"] = all_years[-1]
if "filter_region" not in st.session_state:
    st.session_state["filter_region"] = "All Sri Lanka"

st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
fc1, fc2, fc3, fc4, fc5 = st.columns([2, 1.5, 1.5, 1.5, 1])
with fc1:
    st.markdown('<div class="filter-label">📅 Date Range (Years)</div>', unsafe_allow_html=True)
    staged_years = st.select_slider(
        "Year range", options=all_years,
        value=st.session_state["filter_year_range"],
        label_visibility="collapsed"
    )
with fc2:
    st.markdown('<div class="filter-label">🌍 Tourist Origin</div>', unsafe_allow_html=True)
    all_origins = ["All", "India", "UK", "China", "Germany", "Russia", "Other"]
    staged_origin = st.selectbox("Origin", all_origins,
        index=all_origins.index(st.session_state["filter_origin"]),
        label_visibility="collapsed")
with fc3:
    st.markdown('<div class="filter-label">🎯 Annual View</div>', unsafe_allow_html=True)
    staged_year = st.selectbox("Year", all_years,
        index=all_years.index(st.session_state["filter_year"]),
        label_visibility="collapsed")
with fc4:
    st.markdown('<div class="filter-label">🏔️ Region</div>', unsafe_allow_html=True)
    st.selectbox("Region", ["All Sri Lanka", "Kandy", "Colombo", "Galle", "Nuwaraeliya"],
        index=["All Sri Lanka","Kandy","Colombo","Galle","Nuwaraeliya"].index(st.session_state["filter_region"]),
        label_visibility="collapsed", key="filter_region_widget",
        help="⚠️ Regional breakdown coming soon — dataset currently covers all Sri Lanka.")
with fc5:
    st.markdown('<div class="filter-label">&nbsp;</div>', unsafe_allow_html=True)
    if st.button("Apply Filters ▶", type="primary", use_container_width=True):
        st.session_state["filter_year_range"] = staged_years
        st.session_state["filter_origin"]      = staged_origin
        st.session_state["filter_year"]        = staged_year
        st.session_state["filter_region"]      = st.session_state.get("filter_region_widget", "All Sri Lanka")
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# Read committed filter values
selected_years  = st.session_state["filter_year_range"]
selected_origin = st.session_state["filter_origin"]
selected_year   = st.session_state["filter_year"]
selected_region = st.session_state["filter_region"]

# ── Scoped data based on filter selections ─────────────────────────────────
year_from, year_to = selected_years
df_trend  = df_all[(df_all["year"] >= year_from) & (df_all["year"] <= year_to)].copy()
df_curr   = df_all[df_all["year"] == selected_year].copy()
df_prev   = df_all[df_all["year"] == selected_year - 1].copy() if (selected_year - 1) in all_years else pd.DataFrame()

# ── Apply origin filter to arrival columns where applicable ────────────────
origin_col_map = {"India": "india_arrivals", "UK": "uk_arrivals", "China": "china_arrivals",
                  "Germany": "germany_arrivals", "Russia": "russia_arrivals", "Other": "other_arrivals"}

if selected_origin != "All" and selected_origin in origin_col_map:
    origin_col = origin_col_map[selected_origin]
    if origin_col in df_curr.columns:
        # Replace tourist_arrivals with origin-specific arrivals for filtered KPI/charts
        df_curr   = df_curr.copy(); df_curr["tourist_arrivals"] = df_curr[origin_col]
        df_prev   = df_prev.copy(); df_prev["tourist_arrivals"] = df_prev[origin_col] if not df_prev.empty and origin_col in df_prev.columns else df_prev.get("tourist_arrivals", pd.Series())
        df_trend  = df_trend.copy(); df_trend["tourist_arrivals"] = df_trend[origin_col] if origin_col in df_trend.columns else df_trend["tourist_arrivals"]
        st.info(f"📌 Showing data filtered to **{selected_origin}** tourist origin only.")
    else:
        st.warning(f"Origin column for `{selected_origin}` not found in dataset. Showing all origins.")

has_rev = "revenue_usd_millions" in df_all.columns
has_occ = "hotel_occupancy_rate_pct" in df_all.columns

# ── KPI CARDS ──────────────────────────────────────────────────────────────
tot_arr      = df_curr["tourist_arrivals"].sum()
tot_arr_prev = df_prev["tourist_arrivals"].sum() if not df_prev.empty else 0
arr_yoy      = ((tot_arr - tot_arr_prev) / tot_arr_prev * 100) if tot_arr_prev > 0 else 0
rev_curr     = df_curr["revenue_usd_millions"].sum() if has_rev else 0
occ_curr     = df_curr["hotel_occupancy_rate_pct"].mean() if has_occ else 0
peak_idx     = df_curr["tourist_arrivals"].idxmax() if not df_curr.empty else None
peak_month   = str(df_curr.loc[peak_idx, "month_name"]) if peak_idx is not None and "month_name" in df_curr.columns else "N/A"
peak_arr     = int(df_curr.loc[peak_idx, "tourist_arrivals"]) if peak_idx is not None else 0

k1, k2, k3, k4 = st.columns(4)
with k1:
    tr_txt = f"↗ {arr_yoy:.1f}% YoY" if arr_yoy >= 0 else f"↘ {abs(arr_yoy):.1f}% YoY"
    render_metric_card("Total Arrivals", f"{tot_arr:,.0f}", tr_txt, "👥", positive_trend=(arr_yoy>=0))
with k2:
    if has_rev:
        if "exchange_rate_lkr_usd" in df_curr.columns:
            rev_lkr_b = (df_curr["revenue_usd_millions"] * df_curr["exchange_rate_lkr_usd"]).sum() / 1000
        else:
            rev_lkr_b = (rev_curr * 300.0) / 1000
        render_metric_card("Total Revenue", f"LKR {rev_lkr_b:,.1f}B", f"≈ ${rev_curr:,.1f}M USD", "💵")
    else:
        render_metric_card("Total Revenue", "—", "LKR Billions", "💵")
with k3:
    render_metric_card("Avg. Occupancy", f"{occ_curr:.1f}%" if has_occ else "—", "STABLE", "🛏️")
with k4:
    render_metric_card("Peak Month", f"{peak_month} {selected_year}", f"{peak_arr:,.0f} proj.", "📅")

st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

# ── SECTION 1: HISTORICAL TREND CHART ─────────────────────────────────────
st.markdown(f"""
<div class="section-title">📈 Historical Arrivals & Revenue Trend</div>
<div class="section-sub">Correlation analysis of visitor volume vs economic yield ({year_from}–{year_to})</div>
""", unsafe_allow_html=True)

fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
plot_df = df_trend.dropna(subset=["date","tourist_arrivals"]).copy()

fig_trend.add_trace(go.Scatter(
    x=plot_df["date"], y=plot_df["tourist_arrivals"],
    name="Arrivals", mode="lines", line_shape="spline",
    line=dict(color=theme['accent'], width=4),
    fill="tozeroy", fillcolor=f"rgba(2,132,199,0.12)",
    hovertemplate="<b>%{x|%b %Y}</b><br>Arrivals: %{y:,.0f}<extra></extra>",
), secondary_y=False)

if has_rev:
    if "exchange_rate_lkr_usd" in plot_df.columns:
        plot_df["rev_lkr_b"] = (plot_df["revenue_usd_millions"] * plot_df["exchange_rate_lkr_usd"]) / 1000
    else:
        plot_df["rev_lkr_b"] = (plot_df["revenue_usd_millions"] * 300.0) / 1000
    fig_trend.add_trace(go.Scatter(
        x=plot_df["date"], y=plot_df["rev_lkr_b"],
        name="Revenue (LKR B)", mode="lines+markers", line_shape="spline",
        line=dict(color=theme['accent2'], width=2, dash="dash"),
        marker=dict(size=4, color=theme['accent2']),
        hovertemplate="<b>%{x|%b %Y}</b><br>Revenue: LKR %{y:.1f}B<extra></extra>",
    ), secondary_y=True)

fig_trend.update_layout(
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color=theme['text_dim'], family="Inter"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
    hovermode="x unified",
    xaxis=dict(gridcolor=theme['border'], gridwidth=1, zeroline=False, dtick="M12"),
    yaxis=dict(title="Tourist Arrivals", gridcolor=theme['border'], gridwidth=1, griddash="dot", zeroline=False),
    yaxis2=dict(title="Revenue (LKR B)", gridcolor="rgba(0,0,0,0)", zeroline=False, overlaying="y", side="right"),
    height=380, margin=dict(l=0, r=0, t=10, b=0),
)
st.plotly_chart(apply_plotly_theme(fig_trend), use_container_width=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ── SECTION 2: BOTTOM 3-COL (DONUT + TABLE + GEO PULSE) ──────────────────
b1, b2, b3 = st.columns([1.2, 1.8, 1], gap="large")

with b1:
    st.markdown(f'<div class="section-title">🌍 Arrivals by Origin</div><div class="section-sub">{selected_year} tourist mix analysis</div>', unsafe_allow_html=True)
    origin_map = {"India":"india_arrivals","UK":"uk_arrivals","China":"china_arrivals","Germany":"germany_arrivals","Russia":"russia_arrivals","Other":"other_arrivals"}
    origin_data = {k: float(df_curr[v].sum()) for k,v in origin_map.items() if v in df_curr.columns and df_curr[v].sum()>0}
    if origin_filter := (selected_origin if selected_origin != "All" else None):
        origin_data = {k:v for k,v in origin_data.items() if k == origin_filter} or origin_data
    if origin_data:
        origin_data = dict(sorted(origin_data.items(), key=lambda x:x[1], reverse=True))
        fig_donut = go.Figure(go.Pie(
            labels=list(origin_data.keys()), values=list(origin_data.values()),
            hole=0.72,
            marker=dict(colors=[theme['accent'], theme['accent2'], theme['warning'], theme['danger'], "#8b5cf6", theme['text_dim']]),
            textinfo='none', hoverinfo='label+percent+value'
        ))
        fig_donut.update_layout(
            annotations=[dict(text=f"<span style='font-size:1.6rem;font-weight:800'>{selected_year}</span><br><span style='font-size:0.6rem;letter-spacing:0.05em;'>MIX</span>", x=0.5, y=0.5, font_size=20, showarrow=False)],
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=theme['text_dim'], family="Inter"),
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05, bgcolor="rgba(0,0,0,0)"),
            height=310, margin=dict(l=0, r=10, t=10, b=10),
        )
        st.plotly_chart(apply_plotly_theme(fig_donut), use_container_width=True)
    else:
        st.info("Origin breakdown unavailable for selected filters.")

with b2:
    st.markdown(f'<div class="section-title">📋 Annual Summary</div><div class="section-sub">Global tourism performance timeline ({year_from}–{year_to})</div>', unsafe_allow_html=True)
    agg_dict = {"Total Arrivals": ("tourist_arrivals", "sum")}
    if has_rev:
        if "exchange_rate_lkr_usd" in df_trend.columns:
            df_trend["revenue_lkr_b"] = (df_trend["revenue_usd_millions"] * df_trend["exchange_rate_lkr_usd"]) / 1000
        else:
            df_trend["revenue_lkr_b"] = (df_trend["revenue_usd_millions"] * 300.0) / 1000
        agg_dict["Revenue (LKR B)"] = ("revenue_lkr_b", "sum")
    annual = df_trend.groupby("year").agg(**agg_dict).reset_index()
    annual["Growth %"] = annual["Total Arrivals"].pct_change().mul(100).round(1)
    annual = annual.sort_values("year", ascending=False).rename(columns={"year": "YEAR", "Total Arrivals": "TOTAL ARRIVALS"})
    def color_growth(val):
        color = theme['accent2'] if pd.notna(val) and val >= 0 else theme['danger'] if pd.notna(val) else theme['text_dim']
        return f"color: {color}; font-weight: 700;"
    fmt = {"TOTAL ARRIVALS": "{:,.0f}", "Growth %": "{:+.1f}%"}
    if has_rev: fmt["Revenue (LKR B)"] = "LKR {:,.1f}B"
    st.dataframe(
        annual.style.format(fmt, na_rep="—").map(color_growth, subset=["Growth %"]),
        use_container_width=True, hide_index=True, height=310
    )

with b3:
    map_bg_path = Path(__file__).parent.parent / "assets" / "sri_lanka_pulse_map.png"
    bg_style = f"linear-gradient(135deg, {theme['surface_high']} 0%, {theme['surface']} 100%)"
    if map_bg_path.exists():
        with open(map_bg_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
            bg_style = f"url('data:image/png;base64,{encoded}') center / cover no-repeat"
    st.markdown(f"""
    <div style="background: {bg_style}; border-radius: 14px; height: 310px; position: relative;
                border: 1px solid {theme['border']}; overflow: hidden;">
        <div style="position:absolute;bottom:20px;left:20px;">
            <div style="color:{theme['text_dim']};font-size:0.65rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;">Geographic Pulse</div>
            <div style="color:{theme['text_main']};font-size:1.1rem;font-weight:800;margin-bottom:6px;">Kandy District</div>
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                <div class="pulse-dot"></div>
                <div style="color:{theme['text_muted']};font-size:0.75rem;font-weight:600;">OPTIMAL OCCUPANCY</div>
            </div>
            <div style="color:{theme['text_main']};font-size:1.5rem;font-weight:800;">{occ_curr:.0f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 3: TOURIST PROFILE ANALYTICS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(f"""
<div class="section-title">👤 Tourist Profile Analytics</div>
<div class="section-sub">Breakdown of visitor composition and seasonal patterns for {selected_year}</div>
""", unsafe_allow_html=True)

pa1, pa2, pa3 = st.columns(3, gap="large")

with pa1:
    # Monthly arrivals bar chart
    monthly_df = df_curr.dropna(subset=["tourist_arrivals"]).copy()
    if not monthly_df.empty and "month" in monthly_df.columns:
        monthly_df["month_label"] = pd.to_datetime(monthly_df["date"]).dt.strftime("%b")
        fig_monthly = go.Figure(go.Bar(
            x=monthly_df["month_label"], y=monthly_df["tourist_arrivals"],
            marker=dict(color=monthly_df["tourist_arrivals"], colorscale=[[0, theme['surface_high']], [1, theme['accent']]]),
            hovertemplate="%{x}: %{y:,.0f}<extra></extra>",
            text=monthly_df["tourist_arrivals"].apply(lambda v: f"{v/1000:.0f}k"),
            textposition="outside", textfont=dict(color=theme['text_muted'], size=10)
        ))
        fig_monthly.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=theme['text_dim'], family="Inter"),
            xaxis=dict(gridcolor=theme['border']),
            yaxis=dict(gridcolor=theme['border']),
            height=260, margin=dict(l=0, r=0, t=10, b=0),
            title=dict(text="Monthly Arrivals", font=dict(color=theme['text_main'], size=13), x=0)
        )
        st.plotly_chart(apply_plotly_theme(fig_monthly), use_container_width=True)
    else:
        st.info("Monthly data not available.")

with pa2:
    # Country proportions as a horizontal bar
    if origin_data:
        total_known = sum(origin_data.values())
        colors_list = [theme['accent'], theme['accent2'], theme['warning'], theme['danger'], "#8b5cf6", theme['text_dim']]
        fig_origin_bar = go.Figure()
        for i, (country, val) in enumerate(origin_data.items()):
            fig_origin_bar.add_trace(go.Bar(
                name=country, x=[val/total_known*100], y=["Share"],
                orientation="h",
                marker_color=colors_list[i % len(colors_list)],
                hovertemplate=f"{country}: %{{x:.1f}}%<extra></extra>",
                text=f"{country}<br>{val/total_known*100:.1f}%",
                textposition="inside", insidetextanchor="middle",
                textfont=dict(color="#fff", size=11, family="Inter")
            ))
        fig_origin_bar.update_layout(
            barmode="stack", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=theme['text_dim'], family="Inter"),
            showlegend=False, height=260,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            title=dict(text="Origin Share (%)", font=dict(color=theme['text_main'], size=13), x=0)
        )
        st.plotly_chart(apply_plotly_theme(fig_origin_bar), use_container_width=True)

with pa3:
    # Occupancy gauge
    if has_occ and occ_curr > 0:
        fig_occ_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=occ_curr,
            number={"suffix": "%", "font": {"color": theme['text_main'], "size": 36}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": theme['border'], "tickfont": {"color": theme['text_dim']}},
                "bar": {"color": theme['accent'] if occ_curr < 80 else theme['accent2']},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 60], "color": theme['surface_high']},
                    {"range": [60, 80], "color": theme['surface_low']},
                ],
                "threshold": {"line": {"color": theme['warning'], "width": 3}, "thickness": 0.75, "value": 80}
            }
        ))
        fig_occ_gauge.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", font=dict(color=theme['text_main'], family="Inter"),
            height=260, margin=dict(l=20, r=20, t=30, b=10),
            title=dict(text="Avg Hotel Occupancy", font=dict(color=theme['text_main'], size=13), x=0.5, xanchor="center")
        )
        st.plotly_chart(apply_plotly_theme(fig_occ_gauge), use_container_width=True)
    else:
        st.info("Occupancy data unavailable.")

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 4: REVENUE FORECASTING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(f"""
<div class="section-title">💰 Revenue Forecasting</div>
<div class="section-sub">Projected revenue trajectory based on historical trend extrapolation</div>
""", unsafe_allow_html=True)

if has_rev:
    # Build a simple linear-extrapolation forecast for the next 2 years
    annual_rev = df_all.groupby("year").agg(total_rev=("revenue_usd_millions","sum")).reset_index()
    annual_rev = annual_rev.dropna(subset=["total_rev"])

    if len(annual_rev) >= 3:
        import numpy as np
        x = annual_rev["year"].values
        y = annual_rev["total_rev"].values
        coeffs = np.polyfit(x, y, 1)
        forecast_years = [all_years[-1]+1, all_years[-1]+2]
        forecast_revs  = [max(0, coeffs[0]*yr + coeffs[1]) for yr in forecast_years]

        # Combine for chart
        hist_years = list(x)
        hist_revs  = list(y)

        rf1, rf2 = st.columns([2, 1], gap="large")
        with rf1:
            fig_rev_fore = go.Figure()
            fig_rev_fore.add_trace(go.Scatter(
                x=hist_years, y=hist_revs,
                name="Historical Revenue",
                mode="lines+markers", line=dict(color=theme['accent'], width=3),
                marker=dict(size=6, color=theme['accent']),
                fill="tozeroy", fillcolor="rgba(2,132,199,0.1)",
                hovertemplate="Year %{x}: $%{y:,.1f}M<extra></extra>"
            ))
            fig_rev_fore.add_trace(go.Scatter(
                x=forecast_years, y=forecast_revs,
                name="Projected Revenue",
                mode="lines+markers", line=dict(color=theme['warning'], width=3, dash="dot"),
                marker=dict(size=8, color=theme['warning'], symbol="diamond"),
                hovertemplate="Year %{x}: $%{y:,.1f}M (Projected)<extra></extra>"
            ))
            # Connect last historical to first forecast
            fig_rev_fore.add_trace(go.Scatter(
                x=[hist_years[-1], forecast_years[0]],
                y=[hist_revs[-1], forecast_revs[0]],
                mode="lines", line=dict(color=theme['warning'], width=2, dash="dot"),
                showlegend=False, hoverinfo="skip"
            ))
            fig_rev_fore.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color=theme['text_dim'], family="Inter"),
                legend=dict(orientation="h", y=1.1, bgcolor="rgba(0,0,0,0)"),
                xaxis=dict(gridcolor=theme['border'], dtick=1),
                yaxis=dict(title="Revenue (USD M)", gridcolor=theme['border']),
                hovermode="x unified",
                height=300, margin=dict(l=0, r=0, t=10, b=0)
            )
            st.plotly_chart(apply_plotly_theme(fig_rev_fore), use_container_width=True)

        with rf2:
            # Insight cards
            growth_rate = coeffs[0] / (y.mean()) * 100 if y.mean() > 0 else 0
            cards = [
                ("📈 Annual Revenue Trend", f"+${coeffs[0]:,.1f}M/year avg. growth", f"Linear trend across {len(hist_years)} years"),
                (f"🔮 {forecast_years[0]} Projection", f"${forecast_revs[0]:,.1f}M USD", f"≈ LKR {forecast_revs[0]*300/1000:,.1f}B"),
                (f"🔮 {forecast_years[1]} Projection", f"${forecast_revs[1]:,.1f}M USD", f"≈ LKR {forecast_revs[1]*300/1000:,.1f}B"),
                ("📊 Compound Growth", f"{growth_rate:.1f}%", "Average annual rate"),
            ]
            for icon_title, value, sub in cards:
                st.markdown(f"""
                <div class="forecast-insight-card">
                    <div class="fi-title">{icon_title}</div>
                    <div style="font-family:'Manrope',sans-serif;font-size:1.35rem;font-weight:800;color:{theme['text_main']};margin:4px 0 2px 0;">{value}</div>
                    <div class="fi-body">{sub}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Not enough historical revenue data for forecasting.")
else:
    st.info("Revenue data column not found in dataset.")

# ── SECTION 5: AI INSIGHTS ────────────────────────────────────────────────
st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
st.markdown(f'<div class="section-title">💡 AI Insights Engine</div><div class="section-sub">Auto-generated strategic observations for {selected_year}</div>', unsafe_allow_html=True)

insights = []
if arr_yoy >= 20:
    insights.append(f"📈 <strong>Exceptional Growth Year</strong> — {selected_year} recorded {arr_yoy:.1f}% YoY growth in arrivals, significantly above the regional average.")
elif arr_yoy >= 5:
    insights.append(f"✅ <strong>Steady Growth</strong> — Arrivals grew {arr_yoy:.1f}% vs prior year, indicating healthy and sustained tourism momentum.")
elif arr_yoy < 0:
    insights.append(f"⚠️ <strong>Decline Alert</strong> — Arrivals fell {abs(arr_yoy):.1f}% YoY. This may reflect external disruptions (economic, weather, or geopolitical). Action recommended.")

if has_occ and occ_curr > 80:
    insights.append(f"🏨 <strong>High Occupancy Pressure</strong> — Average hotel occupancy at {occ_curr:.1f}%. Pre-booking overflow accommodation is advised for peak weeks.")
elif has_occ and occ_curr < 50:
    insights.append(f"🏨 <strong>Low Occupancy Noted</strong> — {occ_curr:.1f}% average occupancy suggests opportunity for targeted promotions or event-driven campaigns.")

if origin_data:
    top_country = max(origin_data, key=origin_data.get)
    top_pct = origin_data[top_country] / sum(origin_data.values()) * 100
    insights.append(f"🌍 <strong>Dominant Origin: {top_country}</strong> — Accounts for {top_pct:.1f}% of all arrivals. Consider dedicated marketing campaigns for this market.")

if pred_val:
    insights.append(f"🎯 <strong>Current Week Forecast</strong> — The AI model predicts <strong>{pred_val:,}</strong> Kandy arrivals this week.")

if not insights:
    insights.append("ℹ️ Apply filters and select a year to generate AI insights.")

for ins in insights:
    st.markdown(f'<div class="insight-bullet">{ins}</div>', unsafe_allow_html=True)

# ── EXPORT ────────────────────────────────────────────────────────────────
st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
col_dl, _ = st.columns([1, 4])
with col_dl:
    csv_data = df_curr.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Export Report as CSV", data=csv_data,
        file_name=f"tourism_national_{selected_year}.csv",
        use_container_width=True, type="primary"
    )
