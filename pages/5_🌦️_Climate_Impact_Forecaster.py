"""
pages/5_🌦️_Climate_Impact_Forecaster.py  —  Climate Impact Forecaster
"""
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
from utils.sidebar import render_sidebar
from utils.auth import require_auth
from utils.theme import apply_plotly_theme, apply_custom_theme, render_page_banner

sys.path.insert(0, str(Path(__file__).parent.parent))

require_auth()

st.set_page_config(
    page_title="Climate Impact Forecaster | Kandy Tourism DSS",
    page_icon="🌦️", layout="wide"
)

apply_custom_theme()

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
.alert-text h4 { color:#dae2fd; margin:0 0 4px; font-size:.95rem; font-weight:700; font-family:'Manrope', sans-serif;}
.alert-text p  { color:#bdc8d1; margin:0; font-size:.85rem; }

.stat-pill {
    display:inline-block;background:rgba(142,213,255,.05);
    border:1px solid rgba(142,213,255,.15);border-radius:8px;
    padding:6px 14px;font-size:.8rem;font-weight:600;color:#8ed5ff;margin:4px;
}
</style>
""", unsafe_allow_html=True)

render_sidebar(active_page="Climate Impact Forecaster")

render_page_banner(
    title="Climate Impact Forecaster",
    subtitle="Upcoming weather outlook for Kandy — monitor rainfall, temperature and monsoon conditions and their effect on tourist arrivals.",
    icon="🌦️",
)

with st.container():
    c1, c2, c3 = st.columns([4, 4, 3])
    with c1:
        SEL_YEARS = st.multiselect('Years', list(range(2015, 2030)), default=list(range(2023, 2027)))
    with c2:
        RAIN_THRESH = st.slider('Heavy Rain threshold (mm/week)', 100, 400, 150)
    with c3:
        st.write("")
        st.write("")
        SHOW_FUTURE_ONLY = st.checkbox('Future weeks only ✔️', value=False)
    st.divider()

BASE_DIR = Path(__file__).parent.parent

@st.cache_data
def load_festival_weekly():
    df = pd.read_csv(BASE_DIR / "kandy_festival_demand_NOMISSING.csv")
    df["week_start"] = pd.to_datetime(df["week_start"])
    cache_path = BASE_DIR / "models/predictions_cache.csv"
    if cache_path.exists():
        curr_max_date = df["week_start"].max()
        cdf = pd.read_csv(cache_path)
        cdf = cdf[cdf["model_name"] == "random_forest"].copy()
        
        def unpack_feats(row):
            feats = json.loads(row["features_used"])
            pf = "Normal"
            if feats.get("is_esala_perahera"): pf = "Esala_Perahera"
            elif feats.get("is_vesak"): pf = "Vesak"
            elif feats.get("is_poson_perahera"): pf = "Poson_Perahera"
            
            # Additional logic embedded in constant structures
            row["primary_festival"] = pf
            row["avg_weekly_rainfall_mm"] = feats.get("avg_weekly_rainfall_mm", 0)
            row["avg_temp_celsius"] = feats.get("avg_temp_celsius", 25.0)
            row["is_monsoon_week"] = feats.get("is_monsoon_week", 0)
            return row
            
        cdf = cdf.apply(unpack_feats, axis=1)
        cdf["week_start"] = pd.to_datetime(cdf["week_start"])
        cdf["estimated_weekly_kandy_arrivals"] = cdf["predicted_arrivals"]
        cdf = cdf[cdf["week_start"] > curr_max_date]
        
        if not cdf.empty:
            df = pd.concat([df, cdf], ignore_index=True)
            
    df = df.sort_values("week_start").reset_index(drop=True)
    return df

df_all = load_festival_weekly()
today = pd.Timestamp(datetime.date.today())

if SHOW_FUTURE_ONLY:
    df_all = df_all[df_all["week_start"] >= today]
if SEL_YEARS:
    df_all = df_all[df_all["week_start"].dt.year.isin(SEL_YEARS)]

if df_all.empty:
    st.info('ℹ️ No weather data available to display at the moment.')
    st.stop()





total_weeks = len(df_all)
monsoon_wks = int(df_all["is_monsoon_week"].sum()) if "is_monsoon_week" in df_all.columns else 0
heavy_wks = len(df_all[df_all["avg_weekly_rainfall_mm"] > RAIN_THRESH]) if "avg_weekly_rainfall_mm" in df_all.columns else 0
avg_temp = float(df_all["avg_temp_celsius"].mean()) if "avg_temp_celsius" in df_all.columns else 25.0

st.markdown(f"""
<div><span class="stat-pill">📅 {total_weeks} weeks shown</span><span class="stat-pill">🌧️ {monsoon_wks} monsoon weeks</span><span class="stat-pill">⛈️ {heavy_wks} heavy rain weeks (>{RAIN_THRESH} mm)</span><span class="stat-pill">🌡️ {avg_temp:.1f}°C avg temp</span></div><br>
""", unsafe_allow_html=True)

st.markdown('<div class="section-header">📈 Temperature & Rainfall Trend</div>', unsafe_allow_html=True)

fig = make_subplots(specs=[[{"secondary_y": True}]])

if "avg_temp_celsius" in df_all.columns:
    fig.add_trace(go.Scatter(
        x=df_all["week_start"], y=df_all["avg_temp_celsius"],
        name="Avg Temp (°C)", mode="lines",
        line=dict(color="#f97316", width=2),
        fill="tozeroy", fillcolor="rgba(249,115,22,.08)"
    ), secondary_y=False)

if "avg_weekly_rainfall_mm" in df_all.columns:
    fig.add_trace(go.Bar(
        x=df_all["week_start"], y=df_all["avg_weekly_rainfall_mm"],
        name="Weekly Rainfall (mm)",
        marker_color="#38bdf8", opacity=0.8
    ), secondary_y=True)
    
    # Shade heavy rain weeks
    heavy_rain_df = df_all[df_all["avg_weekly_rainfall_mm"] > RAIN_THRESH]
    for _, row in heavy_rain_df.iterrows():
        fig.add_vrect(x0=row["week_start"], x1=row["week_start"] + pd.Timedelta(days=7),
                      fillcolor="rgba(248,113,113,.12)", layer="below", line_width=0)

fig.update_layout(
    height=400, margin=dict(l=0, r=160, t=20, b=0),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    hovermode="x unified", legend=dict(
        orientation="v", yanchor="top", y=1, xanchor="left", x=1.06,
        bgcolor="rgba(0,0,0,0)", font=dict(color="#dae2fd")
    ),
    xaxis=dict(gridcolor="rgba(62,72,79,0.15)", tickfont=dict(color="#bdc8d1")),
    yaxis=dict(title="Temperature (°C)", gridcolor="rgba(62,72,79,0.15)", tickfont=dict(color="#87929a")),
    yaxis2=dict(title="Rainfall (mm)", gridcolor="rgba(0,0,0,0)", tickfont=dict(color="#87929a"))
)
st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

st.markdown('<div class="section-header">🔗 Rainfall vs Tourist Arrivals Correlation</div>', unsafe_allow_html=True)
if "avg_weekly_rainfall_mm" in df_all.columns and "estimated_weekly_kandy_arrivals" in df_all.columns:
    fig_scatter = px.scatter(
        df_all, x="avg_weekly_rainfall_mm", y="estimated_weekly_kandy_arrivals",
        color="primary_festival" if "primary_festival" in df_all.columns else None,
        labels={"avg_weekly_rainfall_mm": "Rainfall (mm)", "estimated_weekly_kandy_arrivals": "Weekly Arrivals"},
        title="Weather Impact on Tourist Arrivals"
    )
    fig_scatter.update_traces(marker=dict(size=8, opacity=0.7))
    fig_scatter.update_layout(
        height=440, margin=dict(l=0, r=130, t=40, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(62,72,79,0.15)", tickfont=dict(color="#bdc8d1")),
        yaxis=dict(gridcolor="rgba(62,72,79,0.15)", tickfont=dict(color="#bdc8d1")),
        legend=dict(
            bgcolor="rgba(19,27,46,0.85)",
            bordercolor="rgba(62,72,79,0.3)",
            borderwidth=1,
            font=dict(color="#dae2fd", size=11),
            x=1.01, y=1,
            xanchor="left",
            yanchor="top",
            title=dict(text="Festival Type", font=dict(color="#8ed5ff", size=12))
        ),
        title=dict(font=dict(color="#dae2fd", family="Manrope"))
    )
    st.plotly_chart(apply_plotly_theme(fig_scatter), use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-header">⚠️ Weather Impact Alerts</div>', unsafe_allow_html=True)
future_alerts = df_all[df_all["week_start"] >= today].head(4)

if not future_alerts.empty:
    alert_cols = st.columns(len(future_alerts))
    for i, (_, row) in enumerate(future_alerts.iterrows()):
        with alert_cols[i]:
            week_str = row["week_start"].strftime("%d %b %Y")
            rain_val = row.get("avg_weekly_rainfall_mm", 0)
            arr_val = row.get("estimated_weekly_kandy_arrivals", 0)
            
            if rain_val > RAIN_THRESH:
                st.markdown(f"""
                <div class="alert-card alert-heavy" style="height: 100%; margin-top: 0;">
                    <div class="alert-icon">⛈️</div>
                    <div class="alert-text"><h4>Heavy Rain — {week_str}</h4><p><b>{arr_val:,.0f} arrivals.</b> {rain_val:.0f} mm rain forecast. Recommend indoor activities.</p></div>
                </div>""", unsafe_allow_html=True)
            elif row.get("is_monsoon_week", 0) == 1:
                st.markdown(f"""
                <div class="alert-card alert-monsoon" style="height: 100%; margin-top: 0;">
                    <div class="alert-icon">🌧️</div>
                    <div class="alert-text"><h4>Monsoon Week — {week_str}</h4><p>Forecasted {rain_val:.0f} mm. Prepare umbrellas and indoor dining facilities.</p></div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="alert-card alert-ok" style="height: 100%; margin-top: 0;">
                    <div class="alert-icon">☀️</div>
                    <div class="alert-text">
                        <h4>Favourable — {week_str}</h4>
                        <p>{arr_val:,.0f} exp. arrivals. Clear weather for outdoor tourism!</p>
                    </div>
                </div>""", unsafe_allow_html=True)

min_date = df_all["week_start"].min().strftime("%b %Y")
max_date = df_all["week_start"].max().strftime("%b %Y")
st.markdown(f'''
<div class="section-header" style="display:flex; align-items:center; gap:8px;">
    🗓️ Monthly Climate Pattern (Average) 
    <span style="font-size:0.6em; color:#87929a; font-weight:normal; margin-top:4px;">
        [{min_date} — {max_date}]
    </span>
</div>
''', unsafe_allow_html=True)
if "avg_weekly_rainfall_mm" in df_all.columns:
    df_all["month"] = df_all["week_start"].dt.month
    df_all["month_name"] = df_all["week_start"].dt.strftime("%b")
    monthly = df_all.groupby(["month", "month_name"]).agg({
        "avg_weekly_rainfall_mm": "mean",
        "estimated_weekly_kandy_arrivals": "mean"
    }).reset_index().sort_values("month")
    
    fig_monthly = make_subplots(specs=[[{"secondary_y": True}]])
    fig_monthly.add_trace(go.Bar(
        x=monthly["month_name"], y=monthly["avg_weekly_rainfall_mm"],
        name="Avg Rain (mm)", marker_color="rgba(56,189,248,.7)"
    ), secondary_y=False)
    
    fig_monthly.add_trace(go.Scatter(
        x=monthly["month_name"], y=monthly["estimated_weekly_kandy_arrivals"],
        name="Avg Arrivals", mode="lines+markers",
        line=dict(color="#34d399", width=2)
    ), secondary_y=True)
    
    fig_monthly.update_layout(
        height=300, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified", legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#dae2fd"), orientation="h", y=1.1),
        xaxis=dict(gridcolor="rgba(62,72,79,0.15)", tickfont=dict(color="#bdc8d1")),
        yaxis=dict(gridcolor="rgba(62,72,79,0.15)", tickfont=dict(color="#87929a")),
        yaxis2=dict(gridcolor="rgba(0,0,0,0)", showgrid=False, tickfont=dict(color="#87929a"))
    )
    st.plotly_chart(apply_plotly_theme(fig_monthly), use_container_width=True)

st.markdown('<div class="section-header">🧠 AI Feature Importance Analysis</div>', unsafe_allow_html=True)
st.markdown("This chart extracts the exact predictive weights from the underlying Machine Learning model to demonstrate how significantly **Weather Conditions** (like Rainfall and Temperature) impact tourist demand compared to calendar and festival factors. This fulfills the *Feature Importance Analysis* mitigation strategy.", unsafe_allow_html=True)

try:
    RF_PATH = BASE_DIR / "models" / "xgb_model.pkl"
    SCALER_PATH = BASE_DIR / "models" / "feature_scaler.pkl"
    
    if RF_PATH.exists() and SCALER_PATH.exists():
        with open(RF_PATH, "rb") as f:
            rf_model = pickle.load(f)
        with open(SCALER_PATH, "rb") as f:
            scaler_obj = pickle.load(f)
            
        feat_cols = []
        if isinstance(scaler_obj, tuple) and len(scaler_obj) > 1:
            feat_cols = scaler_obj[1]
        elif hasattr(rf_model, "feature_names_in_"):
            feat_cols = rf_model.feature_names_in_
            
        if hasattr(rf_model, "feature_importances_") and feat_cols:
            importances = rf_model.feature_importances_
            # Create a dataframe of top features
            imp_df = pd.DataFrame({"Feature": feat_cols, "Importance": importances})
            imp_df = imp_df.sort_values(by="Importance", ascending=True)
            
            # Filter to keep weather features and top other features to not crowd the chart
            weather_features = ["avg_weekly_rainfall_mm", "avg_temp_celsius", "avg_humidity_pct", "is_monsoon_week"]
            imp_df["Color"] = imp_df["Feature"].apply(lambda x: "#38bdf8" if x in weather_features else "#4edea3")
            
            # Take top 10 features plus any weather features that might not be in top 10
            top_10 = imp_df.tail(10)
            weather_df = imp_df[imp_df["Feature"].isin(weather_features)]
            plot_df = pd.concat([top_10, weather_df]).drop_duplicates().sort_values(by="Importance", ascending=True)
            
            # Format feature names
            plot_df["Feature"] = plot_df["Feature"].str.replace("_", " ").str.title()
            
            fig_imp = px.bar(
                plot_df, x="Importance", y="Feature", orientation="h",
                color="Color", color_discrete_map="identity",
                title="Model Feature Weights (Random Forest / XGBoost)"
            )
            fig_imp.update_layout(
                height=400, margin=dict(l=0, r=20, t=40, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(gridcolor="rgba(62,72,79,0.15)", tickfont=dict(color="#bdc8d1")),
                yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color="#bdc8d1")),
                title=dict(font=dict(color="#dae2fd", family="Manrope")),
                showlegend=False
            )
            
            st.plotly_chart(apply_plotly_theme(fig_imp), use_container_width=True)
        else:
            st.info("Feature importance data not found in the trained model.")
    else:
        st.warning("⚠️ Trained models not found. Please run the training pipeline to generate Feature Importance.")
except Exception as e:
    st.error(f"Could not load Feature Importance Analysis. Error: {str(e)}")

