# pages/6_🐘_Festival_Forecaster.py
# ─────────────────────────────────────────────────────────────────────────────
# Festival Forecaster — Cultural Event Impact Analysis
# ─────────────────────────────────────────────────────────────────────────────

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import datetime
import json
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from utils.sidebar import render_sidebar
from utils.auth import require_auth, get_base64_of_bin_file
from utils.theme import apply_plotly_theme, apply_custom_theme, render_page_banner
from utils.db import fetch_predictions

require_auth()

st.set_page_config(
    page_title="Festival Forecaster | Kandy Tourism DSS",
    page_icon="🐘",
    layout="wide",
)

apply_custom_theme()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.section-header{
    color:#e2e8f0;font-size:1rem;font-weight:700;letter-spacing:.05em;
    text-transform:uppercase;margin:24px 0 12px;
    padding-bottom:6px;border-bottom:2px solid #38BDF8;
}
.festival-stat {
    background: rgba(19, 27, 46, 0.6);
    backdrop-filter: blur(24px);
    border: 1px solid rgba(62,72,79,0.15); border-radius:14px;
    padding:18px 16px;text-align:center;
    box-shadow: 0 0 30px rgba(0,0,0,0.2);
}
.fs-icon{font-size:2rem;margin-bottom:6px;}
.fs-name{color:#dae2fd;font-size:.85rem;font-weight:700;letter-spacing:.02em;text-transform:uppercase; font-family:'Inter', sans-serif;}
.fs-pct{font-size:2rem;font-weight:800;color:#8ed5ff;font-family:'Manrope', sans-serif;}
.fs-sub{color:#bdc8d1;font-size:.8rem;font-weight:600;}
.insight-box{
    background: rgba(19, 27, 46, 0.6);
    backdrop-filter: blur(24px);
    border: 1px solid rgba(62,72,79,0.15); border-radius:12px;
    padding:14px 18px;margin-bottom:10px;
    box-shadow: 0 0 30px rgba(0,0,0,0.2);
    display: flex; gap: 16px; align-items: center;
}
.insight-box img { width: 80px; height: 80px; border-radius: 10px; object-fit: cover;}
.insight-text h4{color:#dae2fd;margin:0 0 4px;font-size:.95rem;font-family:'Manrope', sans-serif;}
.insight-text p{color:#bdc8d1;margin:0;font-size:.85rem;line-height:1.4;}

/* Countdown Cards */
.countdown-row { display:flex; gap:14px; margin-bottom:24px; }
.countdown-card {
    flex:1; background:rgba(19,27,46,0.55); backdrop-filter:blur(20px);
    border:1px solid rgba(56,189,248,0.18); border-radius:14px;
    padding:16px 18px; position:relative; overflow:hidden;
}
.countdown-card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
    background:linear-gradient(90deg,#38BDF8,#6366f1);
}
.cd-days { font-family:'Manrope',sans-serif; font-size:2.2rem; font-weight:800; color:#38BDF8; line-height:1; }
.cd-label { color:#94a3b8; font-size:0.65rem; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; }
.cd-name { color:#e2e8f0; font-size:0.88rem; font-weight:700; margin-top:6px; font-family:'Manrope',sans-serif; }
.cd-date { color:#64748b; font-size:0.75rem; margin-top:2px; }
.cd-arrivals { color:#34d399; font-size:0.78rem; font-weight:600; margin-top:4px; }

/* Filter bar */
.filter-bar {
    background: rgba(20, 31, 56, 0.45);
    backdrop-filter: blur(24px); border: 1px solid rgba(57,184,253,0.15);
    border-radius: 16px; padding: 18px 24px; margin-bottom: 24px;
    box-shadow: 0 0 20px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

render_sidebar(active_page="Festival Forecaster")

BASE_DIR = Path(__file__).parent.parent

# ── Session state defaults ──────────────────────────────────────────────────
if "ff_view_mode"     not in st.session_state: st.session_state.ff_view_mode     = "All Data"
if "ff_show_covid"    not in st.session_state: st.session_state.ff_show_covid    = False
if "ff_show_normal"   not in st.session_state: st.session_state.ff_show_normal   = False
if "ff_min_arrivals"  not in st.session_state: st.session_state.ff_min_arrivals  = 0
if "ff_year_min"      not in st.session_state: st.session_state.ff_year_min      = 2025
if "ff_year_max"      not in st.session_state: st.session_state.ff_year_max      = 2027
if "ff_sel_fests"     not in st.session_state: st.session_state.ff_sel_fests     = []

# ── Data Loading (Supabase-first) ───────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_festival():
    df = pd.read_csv(BASE_DIR / "kandy_festival_demand_NOMISSING.csv")
    df["week_start"] = pd.to_datetime(df["week_start"])
    curr_max_date = df["week_start"].max()

    future_rows = []

    # 1. Try Supabase predictions first
    try:
        preds_all = fetch_predictions()
        if not preds_all.empty:
            preds_all["week_start"] = pd.to_datetime(preds_all["week_start"])
            rf_preds = preds_all[
                (preds_all["model_name"] == "random_forest") &
                (preds_all["week_start"] > curr_max_date)
            ]
            for _, row in rf_preds.iterrows():
                try:
                    feats = json.loads(row["features_used"])
                except Exception:
                    feats = {}
                pf = "Normal"
                if feats.get("is_esala_perahera"):          pf = "Esala_Perahera"
                elif feats.get("is_esala_preparation"):     pf = "Esala_Prep"
                elif feats.get("is_poson_perahera"):        pf = "Poson_Perahera"
                elif feats.get("is_vesak"):                 pf = "Vesak"
                elif feats.get("is_sinhala_tamil_new_year"): pf = "Sinhala_Tamil_New_Year"
                elif feats.get("is_christmas_new_year"):    pf = "Christmas_New_Year"
                elif feats.get("is_deepavali"):             pf = "Deepavali"
                elif feats.get("is_thai_pongal"):           pf = "Thai_Pongal"
                elif feats.get("is_august_buildup"):        pf = "August_Buildup"
                future_rows.append({
                    "week_start": row["week_start"],
                    "estimated_weekly_kandy_arrivals": row["predicted_arrivals"],
                    "primary_festival": pf,
                    "festival_demand_multiplier": feats.get("festival_demand_multiplier", 1.0),
                    "is_covid_period": 0,
                })
    except Exception:
        pass   # Supabase unreachable — fall through to local cache

    # 2. Fallback: local predictions_cache.csv
    if not future_rows:
        cache_path = BASE_DIR / "models/predictions_cache.csv"
        if cache_path.exists():
            cdf = pd.read_csv(cache_path)
            cdf = cdf[cdf["model_name"] == "random_forest"]
            cdf["week_start"] = pd.to_datetime(cdf["week_start"])
            cdf = cdf[cdf["week_start"] > curr_max_date]
            for _, row in cdf.iterrows():
                try:
                    feats = json.loads(row["features_used"])
                except Exception:
                    feats = {}
                pf = "Normal"
                if feats.get("is_esala_perahera"):          pf = "Esala_Perahera"
                elif feats.get("is_esala_preparation"):     pf = "Esala_Prep"
                elif feats.get("is_poson_perahera"):        pf = "Poson_Perahera"
                elif feats.get("is_vesak"):                 pf = "Vesak"
                elif feats.get("is_sinhala_tamil_new_year"): pf = "Sinhala_Tamil_New_Year"
                elif feats.get("is_christmas_new_year"):    pf = "Christmas_New_Year"
                elif feats.get("is_deepavali"):             pf = "Deepavali"
                elif feats.get("is_thai_pongal"):           pf = "Thai_Pongal"
                elif feats.get("is_august_buildup"):        pf = "August_Buildup"
                future_rows.append({
                    "week_start": row["week_start"],
                    "estimated_weekly_kandy_arrivals": row["predicted_arrivals"],
                    "primary_festival": pf,
                    "festival_demand_multiplier": feats.get("festival_demand_multiplier", 1.0),
                    "is_covid_period": 0,
                })

    if future_rows:
        future_df = pd.DataFrame(future_rows)
        df = pd.concat([df, future_df], ignore_index=True)

    df = df.sort_values("week_start").reset_index(drop=True)

    # Always recompute year from week_start — future rows from predictions
    # don't carry a 'year' column, so the CSV's pre-existing 'year' column
    # will have NaN for those rows after concat, silently breaking year filter.
    df["year"] = df["week_start"].dt.year.astype(int)

    # Guard: ensure critical numeric columns exist and have no NaN
    if "festival_demand_multiplier" not in df.columns:
        df["festival_demand_multiplier"] = 1.0
    df["festival_demand_multiplier"] = df["festival_demand_multiplier"].fillna(1.0)

    if "is_covid_period" not in df.columns:
        df["is_covid_period"] = 0
    df["is_covid_period"] = df["is_covid_period"].fillna(0).astype(int)

    if "primary_festival" not in df.columns:
        df["primary_festival"] = "Normal"
    df["primary_festival"] = df["primary_festival"].fillna("Normal")

    return df

df = load_festival()

# ── Metadata ────────────────────────────────────────────────────────────────
today           = datetime.date.today()
today_pd        = pd.Timestamp(today)
thirty_days_pd  = pd.Timestamp(today + datetime.timedelta(days=30))

FESTIVAL_META = {
    "Esala_Perahera":         {"icon": "🐘", "color": "#F59E0B", "desc": "The world-famous Kandy Esala Perahera — 10-day Buddhist pageant with decorated elephants."},
    "Esala_Prep":             {"icon": "🎺", "color": "#F59E0B", "desc": "Preparation weeks leading up to Esala Perahera. Hotels fill fast, prices surge."},
    "Poson_Perahera":         {"icon": "🏯", "color": "#b09af7", "desc": "Poson Poya festival celebrating Buddhism's arrival in Sri Lanka."},
    "Vesak":                  {"icon": "🪔", "color": "#4edea3", "desc": "Vesak Poya — the holiest Buddhist festival marking Buddha's birth, enlightenment & death."},
    "Deepavali":              {"icon": "✨", "color": "#ffb4ab", "desc": "Deepavali — Festival of Lights celebrated by Tamil Hindus across Sri Lanka."},
    "Sinhala_Tamil_New_Year": {"icon": "🎊", "color": "#8ed5ff", "desc": "Sinhala & Tamil New Year — nationwide celebration drawing domestic & diaspora tourists."},
    "Christmas_New_Year":     {"icon": "🎄", "color": "#4edea3", "desc": "Christmas & New Year period — peak international tourist season for Kandy."},
    "Monthly_Poya":           {"icon": "🌕", "color": "#8ed5ff", "desc": "Full-moon (Poya) public holidays — temples fill with devotees and cultural visitors."},
    "August_Buildup":         {"icon": "📈", "color": "#ffb4ab", "desc": "August pre-festival buildup — arrivals rise as tourists book ahead for Esala Perahera."},
    "Thai_Pongal":            {"icon": "🌾", "color": "#4edea3", "desc": "Thai Pongal — Tamil harvest festival, popular especially in the Hill Country."},
}

# ── Festival statistics (full dataset, pre-filter) ──────────────────────────
fst_stats = (
    df[df["primary_festival"] != "Normal"]
    .groupby("primary_festival")
    .agg(
        avg_arrivals=("estimated_weekly_kandy_arrivals", "mean"),
        avg_multiplier=("festival_demand_multiplier", "mean"),
        num_weeks=("week_start", "count"),
    )
    .reset_index()
)
normal_avg = df[df["primary_festival"] == "Normal"]["estimated_weekly_kandy_arrivals"].mean()
fst_stats["surge_pct"] = ((fst_stats["avg_arrivals"] / normal_avg) - 1) * 100
fst_stats = fst_stats.sort_values("surge_pct", ascending=False)
all_festivals = fst_stats["primary_festival"].tolist()

# Initialise sel_fests default once
if not st.session_state.ff_sel_fests:
    st.session_state.ff_sel_fests = all_festivals[:5]

available_years = sorted(df["year"].dropna().unique().astype(int).tolist())
year_min_global = min(available_years) if available_years else 2015
year_max_global = max(available_years) if available_years else 2027

# ── Upcoming festival alerts (keep both per user preference) ──────────────
upcoming_30 = df[
    (df["week_start"] >= today_pd) &
    (df["week_start"] <= thirty_days_pd) &
    (df["primary_festival"] != "Normal")
].sort_values("week_start")

# ── Page Banner ─────────────────────────────────────────────────────────────
render_page_banner(
    title="Festival Forecaster",
    subtitle="Discover upcoming Kandy festivals and how they drive tourist surges. Plan ahead for Esala Perahera, Vesak, Poson, and more.",
    icon="🐘",
)

# ── Existing Alert Banners (kept per user preference) ───────────────────────
if not upcoming_30.empty:
    for _, urow in upcoming_30.iterrows():
        fest_name  = urow["primary_festival"].replace("_", " ")
        days_ahead = (urow["week_start"].date() - today).days
        meta       = FESTIVAL_META.get(urow["primary_festival"], {"icon": "🎉"})
        icon       = meta["icon"]
        mult       = urow["festival_demand_multiplier"]
        pred_arr   = int(urow.get("estimated_weekly_kandy_arrivals", 0))
        if days_ahead <= 7:
            st.error(
                f"🚨 **Upcoming Event Alert: {icon} {fest_name} next week** — "
                f"Prepare for a surge! Demand multiplier: ×{mult:.2f}. "
                f"**Expected Arrivals: {pred_arr:,}**. "
                f"Coordinate staffing, transport and accommodation NOW."
            )
        else:
            st.warning(
                f"⏰ **{icon} {fest_name}** in {days_ahead} days (week of "
                f"{urow['week_start'].strftime('%d %b %Y')}). "
                f"Expected demand multiplier: ×{mult:.2f}. "
                f"**Predicted Arrivals: {pred_arr:,}**."
            )

# ── Next Festival Countdown Cards ────────────────────────────────────────────
upcoming_all = df[
    (df["week_start"] > today_pd) &
    (df["primary_festival"] != "Normal")
].sort_values("week_start").drop_duplicates(subset=["primary_festival"]).head(3)

if not upcoming_all.empty:
    st.markdown('<div class="countdown-row">', unsafe_allow_html=True)
    card_cols = st.columns(len(upcoming_all))
    for i, (_, urow) in enumerate(upcoming_all.iterrows()):
        days = (urow["week_start"].date() - today).days
        meta = FESTIVAL_META.get(urow["primary_festival"], {"icon": "🎉", "color": "#38BDF8"})
        arr  = int(urow.get("estimated_weekly_kandy_arrivals", 0))
        with card_cols[i]:
            st.markdown(f"""
            <div class="countdown-card">
                <div class="cd-label">Upcoming Festival</div>
                <div class="cd-name">{meta['icon']} {urow['primary_festival'].replace('_', ' ')}</div>
                <div class="cd-days">{days}<span style="font-size:1rem;color:#64748b"> days</span></div>
                <div class="cd-date">{urow['week_start'].strftime('%d %b %Y')}</div>
                <div class="cd-arrivals">~{arr:,} expected arrivals</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Inline Filter Bar ────────────────────────────────────────────────────────
st.markdown('<div class="filter-bar"></div>', unsafe_allow_html=True)

with st.container():
    st.markdown("<div style='margin-top:-70px; padding: 0 24px 24px 24px; position:relative; z-index:10;'>", unsafe_allow_html=True)
    with st.form("festival_filters", border=False):
        # Row 1
        r1c1, r1c2, r1c3 = st.columns([3, 2, 2])
        with r1c1:
            sel_fests = st.multiselect(
                "🎪 Festival Selection",
                all_festivals,
                default=st.session_state.ff_sel_fests,
                format_func=lambda x: x.replace("_", " "),
            )
        with r1c2:
            view_mode = st.radio(
                "📂 View Mode",
                ["All Data", "Historical Only", "Future Only"],
                index=["All Data", "Historical Only", "Future Only"].index(st.session_state.ff_view_mode),
                horizontal=True
            )
        with r1c3:
            min_arrivals = st.slider(
                "🔻 Min Arrivals Threshold",
                min_value=0,
                max_value=5000,
                value=st.session_state.ff_min_arrivals,
                step=100,
                help="Hide weeks where predicted arrivals fall below this number"
            )

        # Row 2
        r2c1, r2c2, r2c3, r2c4 = st.columns([3, 1.2, 1.2, 1])
        with r2c1:
            year_range = st.select_slider(
                "📅 Year Range",
                options=available_years,
                value=(
                    max(year_min_global, st.session_state.ff_year_min),
                    min(year_max_global, st.session_state.ff_year_max)
                )
            )
        with r2c2:
            show_covid = st.toggle("☣️ COVID Period", value=st.session_state.ff_show_covid)
        with r2c3:
            show_normal = st.toggle("📊 Show Normal Weeks", value=st.session_state.ff_show_normal)
        with r2c4:
            st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Apply Filters", use_container_width=True)

    if submitted:
        st.session_state.ff_sel_fests    = sel_fests if sel_fests else all_festivals
        st.session_state.ff_view_mode    = view_mode
        st.session_state.ff_min_arrivals = min_arrivals
        st.session_state.ff_year_min     = year_range[0]
        st.session_state.ff_year_max     = year_range[1]
        st.session_state.ff_show_covid   = show_covid
        st.session_state.ff_show_normal  = show_normal
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── Resolved filter values ───────────────────────────────────────────────────
_sel_fests    = st.session_state.ff_sel_fests or all_festivals
_view_mode    = st.session_state.ff_view_mode
_min_arr      = st.session_state.ff_min_arrivals
_yr_min       = st.session_state.ff_year_min
_yr_max       = st.session_state.ff_year_max
_show_covid   = st.session_state.ff_show_covid
_show_normal  = st.session_state.ff_show_normal

# ── Single df_filtered feeds all charts ─────────────────────────────────────
df_filtered = df.copy()

# COVID filter
if not _show_covid and "is_covid_period" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["is_covid_period"] == 0]

# Year range
df_filtered = df_filtered[
    (df_filtered["year"] >= _yr_min) &
    (df_filtered["year"] <= _yr_max)
]

# View mode (historical vs future)
if _view_mode == "Historical Only":
    df_filtered = df_filtered[df_filtered["week_start"] < today_pd]
elif _view_mode == "Future Only":
    df_filtered = df_filtered[df_filtered["week_start"] >= today_pd]

# Min arrivals threshold
df_filtered = df_filtered[df_filtered["estimated_weekly_kandy_arrivals"] >= _min_arr]

# Festival selection (keep Normal rows if show_normal is on)
festival_mask = df_filtered["primary_festival"].isin(_sel_fests)
if _show_normal:
    festival_mask = festival_mask | (df_filtered["primary_festival"] == "Normal")
df_chart = df_filtered[festival_mask].copy()

# Recalculate stats from filtered data
fst_stats_filtered = (
    df_chart[df_chart["primary_festival"] != "Normal"]
    .groupby("primary_festival")
    .agg(
        avg_arrivals=("estimated_weekly_kandy_arrivals", "mean"),
        avg_multiplier=("festival_demand_multiplier", "mean"),
        num_weeks=("week_start", "count"),
    )
    .reset_index()
)
if not df_chart.empty:
    n_avg = df_chart[df_chart["primary_festival"] == "Normal"]["estimated_weekly_kandy_arrivals"].mean()
    n_avg = n_avg if pd.notna(n_avg) else normal_avg
    fst_stats_filtered["surge_pct"] = ((fst_stats_filtered["avg_arrivals"] / n_avg) - 1) * 100
    fst_stats_filtered = fst_stats_filtered.sort_values("surge_pct", ascending=False)

# ── Section 1: Festival Impact Stat Cards ────────────────────────────────────
st.markdown('<div class="section-header">🎯 Festival Impact on Tourist Arrivals</div>', unsafe_allow_html=True)

if fst_stats_filtered.empty:
    st.info("No festival data matches the current filters. Try expanding the year range or adjusting the min arrivals threshold.")
else:
    top_cards = fst_stats_filtered[fst_stats_filtered["primary_festival"].isin(_sel_fests)].head(6)
    cols = st.columns(max(1, len(top_cards)))
    for i, (_, row) in enumerate(top_cards.iterrows()):
        meta  = FESTIVAL_META.get(row["primary_festival"], {"icon": "🎉", "color": "#94a3b8"})
        surge = row["surge_pct"]
        with cols[i]:
            st.markdown(f"""
            <div class="festival-stat">
                <div class="fs-icon">{meta["icon"]}</div>
                <div class="fs-name">{row["primary_festival"].replace("_", " ")}</div>
                <div class="fs-pct">+{surge:.0f}%</div>
                <div class="fs-sub">{int(row["avg_arrivals"]):,} avg arrivals/wk</div>
            </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Section 2: Demand Multiplier Bar Chart ───────────────────────────────────
st.markdown('<div class="section-header">📊 Demand Multiplier by Festival</div>', unsafe_allow_html=True)

if not fst_stats_filtered.empty:
    chart_df = fst_stats_filtered[fst_stats_filtered["primary_festival"].isin(_sel_fests)].copy()
    chart_df["label"] = chart_df["primary_festival"].str.replace("_", " ")
    chart_df["color"] = chart_df["primary_festival"].map(
        lambda x: FESTIVAL_META.get(x, {}).get("color", "#6366f1")
    )
    chart_df = chart_df.sort_values("avg_multiplier", ascending=True)

    fig_bar = go.Figure(go.Bar(
        x=chart_df["avg_multiplier"],
        y=chart_df["label"],
        orientation="h",
        marker=dict(color=chart_df["color"], opacity=0.85, line=dict(color="rgba(255,255,255,.1)", width=1)),
        text=[f"×{m:.2f}  (+{s:.0f}%)" for m, s in zip(chart_df["avg_multiplier"], chart_df["surge_pct"])],
        textposition="outside",
        textfont=dict(color="#bdc8d1", size=11, family="Inter"),
        hovertemplate="<b>%{y}</b><br>Multiplier: %{x:.2f}<extra></extra>",
    ))
    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=max(300, len(chart_df) * 55),
        xaxis=dict(title="Demand Multiplier", gridcolor="rgba(62,72,79,0.15)", tickfont=dict(color="#87929a"),
                   range=[0, max(chart_df["avg_multiplier"]) * 1.35]),
        yaxis=dict(tickfont=dict(color="#dae2fd", size=12)),
        margin=dict(l=0, r=120, t=20, b=20),
    )
    st.plotly_chart(apply_plotly_theme(fig_bar), use_container_width=True)
else:
    st.info("No data to display for the selected filters.")

# ── Section 3: Festival Timeline + Insights ──────────────────────────────────
st.markdown('<div class="section-header">📅 Festival Arrival Timeline</div>', unsafe_allow_html=True)

col_l, col_r = st.columns([3, 2])

with col_l:
    timeline = df_chart.copy()
    if timeline.empty:
        st.info("No timeline data for the current filters.")
    else:
        timeline["label"] = timeline["primary_festival"].str.replace("_", " ")
        timeline["is_upcoming"] = timeline["week_start"] >= today_pd

        fig_time = px.scatter(
            timeline, x="week_start", y="estimated_weekly_kandy_arrivals",
            color="primary_festival",
            color_discrete_map={k: v["color"] for k, v in FESTIVAL_META.items()},
            hover_data=["primary_festival", "festival_demand_multiplier"],
            labels={"week_start": "Week", "estimated_weekly_kandy_arrivals": "Arrivals",
                    "primary_festival": "Festival"},
            size="festival_demand_multiplier",
            size_max=18,
        )
        fig_time.update_traces(marker=dict(opacity=0.8))
        fig_time.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=380,
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#bdc8d1"), title_text=""),
            xaxis=dict(gridcolor="rgba(62,72,79,0.15)", tickfont=dict(color="#87929a"),
                       title=f"Year Range: {_yr_min} – {_yr_max}"),
            yaxis=dict(gridcolor="rgba(62,72,79,0.15)", tickfont=dict(color="#87929a")),
            title=dict(font=dict(color="#dae2fd", size=13)),
            margin=dict(l=0, r=0, t=20, b=0),
        )
        # Draw "Today" line for All Data / Future Only modes
        if _view_mode != "Historical Only":
            fig_time.add_vline(x=today_pd, line_width=2, line_dash="dash", line_color="#38BDF8")
            fig_time.add_annotation(
                x=today_pd, y=1, yref="paper", text="<b>Today</b>",
                showarrow=False, font=dict(color="#38BDF8", size=11),
                bgcolor="rgba(15,23,42,0.8)", bordercolor="#38BDF8", borderpad=3
            )
        st.plotly_chart(apply_plotly_theme(fig_time), use_container_width=True)

with col_r:
    st.markdown('<div class="section-header">💡 Festival Insights Engine</div>', unsafe_allow_html=True)
    top3_src = fst_stats_filtered if not fst_stats_filtered.empty else fst_stats
    top3 = top3_src[top3_src["primary_festival"].isin(_sel_fests)].head(3)
    for _, row in top3.iterrows():
        meta   = FESTIVAL_META.get(row["primary_festival"], {"icon": "🎉"})
        surge  = row["surge_pct"]
        weeks  = int(row["num_weeks"])
        img_name = "general_festival_thumb_1774175544601.png"
        if row["primary_festival"] == "Esala_Perahera":
            img_name = "esala_perahera_thumb_1774175478609.png"
        img_path = BASE_DIR / "assets" / img_name
        img_b64 = ""
        if img_path.exists():
            img_b64 = f"data:image/png;base64,{get_base64_of_bin_file(str(img_path))}"

        st.markdown(f"""
        <div class="insight-box">
            <img src="{img_b64}">
            <div class="insight-text">
                <h4>{meta["icon"]} {row["primary_festival"].replace("_", " ")} — +{surge:.1f}% surge</h4>
                <p>{meta.get("desc","Cultural event with significant tourism impact.")}<br>
                   Observed across {weeks} weeks in filter. <b>{int(row["avg_arrivals"]):,} arrivals/week.</b></p>
            </div>
        </div>""", unsafe_allow_html=True)

    esala = top3_src[top3_src["primary_festival"] == "Esala_Perahera"]
    if not esala.empty:
        esala_pct = esala.iloc[0]["surge_pct"]
        st.info(f"🐘 **Esala Perahera** causes a **{esala_pct:.0f}% surge** over normal weeks — the single largest tourism driver in Kandy.")

st.caption(f"Data: {_view_mode} · Years: {_yr_min}–{_yr_max} · Min Arrivals: {_min_arr:,} · Sources: Historical CSV + Supabase Predictions")
