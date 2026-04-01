# pages/6_🐘_Festival_Forecaster.py
# ─────────────────────────────────────────────────────────────────────────────
# Festival Forecaster — Cultural Event Impact Analysis
# Data: kandy_festival_demand_NOMISSING.csv
# ─────────────────────────────────────────────────────────────────────────────

from pathlib import Path
import datetime
import json
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from utils.sidebar import render_sidebar
from utils.auth import require_auth, get_base64_of_bin_file
from utils.theme import apply_plotly_theme, apply_custom_theme, render_page_banner

require_auth()

st.set_page_config(
    page_title="Festival Forecaster | Kandy Tourism DSS",
    page_icon="🐘",
    layout="wide",
)

from utils.theme import apply_custom_theme
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
    display: flex;
    gap: 16px;
    align-items: center;
}
.insight-box img { width: 80px; height: 80px; border-radius: 10px; object-fit: cover;}
.insight-text h4{color:#dae2fd;margin:0 0 4px;font-size:.95rem;font-family:'Manrope', sans-serif;}
.insight-text p{color:#bdc8d1;margin:0;font-size:.85rem;line-height:1.4;}
</style>
""", unsafe_allow_html=True)

render_sidebar(active_page="Festival Forecaster")

BASE_DIR = Path(__file__).parent.parent

@st.cache_data
def load_festival():
    df = pd.read_csv(BASE_DIR / "kandy_festival_demand_NOMISSING.csv")
    df["week_start"] = pd.to_datetime(df["week_start"])
    cache_path = BASE_DIR / "models/predictions_cache.csv"
    if cache_path.exists():
        curr_max_date = df["week_start"].max()
        cdf = pd.read_csv(cache_path)
        cdf = cdf[cdf["model_name"] == "random_forest"]
        cdf["week_start"] = pd.to_datetime(cdf["week_start"])
        cdf = cdf[cdf["week_start"] > curr_max_date]
        
        new_rows = []
        for _, row in cdf.iterrows():
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
            
            new_rows.append({
                "week_start": row["week_start"],
                "estimated_weekly_kandy_arrivals": row["predicted_arrivals"],
                "primary_festival": pf,
                "festival_demand_multiplier": feats.get("festival_demand_multiplier", 1.0)
            })
        if new_rows:
            future_df = pd.DataFrame(new_rows)
            df = pd.concat([df, future_df], ignore_index=True)
            
    df = df.sort_values("week_start").reset_index(drop=True)
    return df

df = load_festival()

today            = datetime.date.today()
next_week_start  = today + datetime.timedelta(days=7)
thirty_days_out  = today + datetime.timedelta(days=30)
today_pd         = pd.Timestamp(today)
next_week_pd     = pd.Timestamp(next_week_start)
thirty_days_pd   = pd.Timestamp(thirty_days_out)

upcoming_30 = df[
    (df["week_start"] >= today_pd) &
    (df["week_start"] <= thirty_days_pd) &
    (df["primary_festival"] != "Normal")
].sort_values("week_start")


render_page_banner(
    title="Festival Forecaster",
    subtitle="Discover upcoming Kandy festivals and how they drive tourist surges. Plan ahead for Esala Perahera, Vesak, Poson, and more.",
    icon="🐘",
)


FESTIVAL_META = {
    "Esala_Perahera":      {"icon": "🐘", "color": "#F59E0B", "desc": "The world-famous Kandy Esala Perahera — 10-day Buddhist pageant with decorated elephants."},
    "Esala_Prep":          {"icon": "🎺", "color": "#F59E0B", "desc": "Preparation weeks leading up to Esala Perahera. Hotels fill fast, prices surge."},
    "Poson_Perahera":      {"icon": "🏯", "color": "#b09af7", "desc": "Poson Poya festival celebrating Buddhism's arrival in Sri Lanka."},
    "Vesak":               {"icon": "🪔", "color": "#4edea3", "desc": "Vesak Poya — the holiest Buddhist festival marking Buddha's birth, enlightenment & death."},
    "Deepavali":           {"icon": "✨", "color": "#ffb4ab", "desc": "Deepavali — Festival of Lights celebrated by Tamil Hindus across Sri Lanka."},
    "Sinhala_Tamil_New_Year": {"icon": "🎊", "color": "#8ed5ff", "desc": "Sinhala & Tamil New Year — nationwide celebration drawing domestic & diaspora tourists."},
    "Christmas_New_Year":  {"icon": "🎄", "color": "#4edea3", "desc": "Christmas & New Year period — peak international tourist season for Kandy."},
    "Monthly_Poya":        {"icon": "🌕", "color": "#8ed5ff", "desc": "Full-moon (Poya) public holidays — temples fill with devotees and cultural visitors."},
    "August_Buildup":      {"icon": "📈", "color": "#ffb4ab", "desc": "August pre-festival buildup — arrivals rise as tourists book ahead for Esala Perahera."},
    "Thai_Pongal":         {"icon": "🌾", "color": "#4edea3", "desc": "Thai Pongal — Tamil harvest festival, popular especially in the Hill Country."},
}

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

with st.sidebar:
    st.markdown("### 🎪 Festival Filter")
    all_festivals = fst_stats["primary_festival"].tolist()
    sel_fests = st.multiselect(
        "Select Festivals",
        all_festivals,
        default=all_festivals[:5],
        format_func=lambda x: x.replace("_", " "),
    )
    if not sel_fests:
        sel_fests = all_festivals
    show_covid = st.checkbox("Include COVID period", value=False)
    st.divider()

if not show_covid:
    df_plot = df[df["is_covid_period"] == 0].copy()
else:
    df_plot = df.copy()

st.markdown('<div class="section-header">🎯 Festival Impact on Tourist Arrivals</div>', unsafe_allow_html=True)

filtered_stats = fst_stats[fst_stats["primary_festival"].isin(sel_fests)].head(6)
cols = st.columns(len(filtered_stats))
for i, (_, row) in enumerate(filtered_stats.iterrows()):
    meta = FESTIVAL_META.get(row["primary_festival"], {"icon": "🎉", "color": "#94a3b8"})
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

st.markdown('<div class="section-header">📊 Demand Multiplier by Festival</div>', unsafe_allow_html=True)

chart_df = fst_stats[fst_stats["primary_festival"].isin(sel_fests)].copy()
chart_df["label"] = chart_df["primary_festival"].str.replace("_", " ")
chart_df["color"] = chart_df["primary_festival"].map(
    lambda x: FESTIVAL_META.get(x, {}).get("color", "#6366f1")
)
chart_df = chart_df.sort_values("avg_multiplier", ascending=True)

fig_bar = go.Figure(go.Bar(
    x=chart_df["avg_multiplier"],
    y=chart_df["label"],
    orientation="h",
    marker=dict(
        color=chart_df["color"],
        opacity=0.85,
        line=dict(color="rgba(255,255,255,.1)", width=1),
    ),
    text=[f"×{m:.2f}  (+{s:.0f}%)" for m, s in zip(chart_df["avg_multiplier"], chart_df["surge_pct"])],
    textposition="outside",
    textfont=dict(color="#bdc8d1", size=11, family="Inter"),
    hovertemplate="<b>%{y}</b><br>Multiplier: %{x:.2f}<extra></extra>",
))
fig_bar.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    height=max(300, len(chart_df) * 55),
    xaxis=dict(title="Demand Multiplier", gridcolor="rgba(62,72,79,0.15)", tickfont=dict(color="#87929a"), range=[0, max(chart_df["avg_multiplier"])*1.35]),
    yaxis=dict(tickfont=dict(color="#dae2fd", size=12)),
    margin=dict(l=0, r=120, t=20, b=20),
)
st.plotly_chart(apply_plotly_theme(fig_bar), use_container_width=True)

st.markdown('<div class="section-header">📅 Annual Festival Arrival Timeline</div>', unsafe_allow_html=True)

col_l, col_r = st.columns([3, 2])
with col_l:
    current_month_start = pd.Timestamp(today.replace(day=1))
    timeline = df_plot[
        (df_plot["primary_festival"].isin(sel_fests + ["Normal"])) &
        (df_plot["week_start"] >= current_month_start)
    ].copy()
    if timeline.empty:
        max_year = df_plot["year"].max()
        timeline = df_plot[
            (df_plot["primary_festival"].isin(sel_fests + ["Normal"])) &
            (df_plot["year"] == max_year)
        ].copy()
    timeline["label"] = timeline["primary_festival"].str.replace("_", " ")
    timeline["is_upcoming"] = timeline["week_start"] >= today_pd

    fig_time = px.scatter(
        timeline, x="week_start", y="estimated_weekly_kandy_arrivals",
        color="primary_festival",
        color_discrete_map={k: v["color"] for k, v in FESTIVAL_META.items()},
        hover_data=["primary_festival", "festival_demand_multiplier"],
        title="Festival Arrival Timeline",
        labels={"week_start": "Week", "estimated_weekly_kandy_arrivals": "Arrivals",
                "primary_festival": "Festival"},
        size="festival_demand_multiplier",
        size_max=18,
    )
    fig_time.update_traces(marker=dict(opacity=0.8))
    fig_time.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=380,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#bdc8d1"), title_text=""),
        xaxis=dict(gridcolor="rgba(62,72,79,0.15)", tickfont=dict(color="#87929a")),
        yaxis=dict(gridcolor="rgba(62,72,79,0.15)", tickfont=dict(color="#87929a")),
        title=dict(font=dict(color="#dae2fd", size=13)),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(apply_plotly_theme(fig_time), use_container_width=True)

with col_r:
    st.markdown('<div class="section-header">💡 Festival Insights Engine</div>', unsafe_allow_html=True)
    top3 = fst_stats.head(3)
    for _, row in top3.iterrows():
        meta = FESTIVAL_META.get(row["primary_festival"], {"icon": "🎉"})
        surge = row["surge_pct"]
        weeks = int(row["num_weeks"])
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
                   Observed across {weeks} historical weeks. <b>{int(row["avg_arrivals"]):,} arrivals/week.</b></p>
            </div>
        </div>""", unsafe_allow_html=True)

    esala = fst_stats[fst_stats["primary_festival"] == "Esala_Perahera"]
    if not esala.empty:
        esala_pct = esala.iloc[0]["surge_pct"]
        st.info(f"🐘 **Esala Perahera** causes a **{esala_pct:.0f}% surge** over normal weeks — the single largest tourism driver in Kandy.")
