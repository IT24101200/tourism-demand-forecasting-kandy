"""
pages/2_📈_Kandy_Forecast.py  —  Kandy Weekly Forecast Dashboard
"""

import sys
import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler
from utils.db import fetch_kandy_weekly, fetch_predictions
from utils.sidebar import render_sidebar
from utils.auth import require_auth
from utils.theme import apply_custom_theme, apply_plotly_theme, render_page_banner, render_metric_card
import json

require_auth()

st.set_page_config(
    page_title="Live Demand Monitoring | Tourist DSS",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_theme()
render_sidebar(active_page="Live Demand")

BASE_DIR = Path(__file__).parent.parent

@st.cache_data(ttl=3600)  # Cache for 1 hour, then re-fetch from Supabase
def load_data():
    hist_df = pd.read_csv(BASE_DIR / "kandy_festival_demand_NOMISSING.csv", on_bad_lines="skip")
    hist_df.columns = [c.strip().lower().replace(" ", "_") for c in hist_df.columns]
    hist_df["week_start"] = pd.to_datetime(hist_df["week_start"])
    hist_df = hist_df.dropna(subset=["estimated_weekly_kandy_arrivals"])
    hist_df = hist_df.sort_values("week_start").reset_index(drop=True)

    rf_df, lstm_df = pd.DataFrame(), pd.DataFrame()

    # ── PRIMARY: Try Supabase first ───────────────────────────────
    try:
        preds_all = fetch_predictions()   # reads Supabase `predictions` table
        if not preds_all.empty:
            preds_all["week_start"] = pd.to_datetime(preds_all["week_start"])
            rf_raw  = preds_all[preds_all["model_name"] == "xgboost"].copy()
            lstm_df = preds_all[preds_all["model_name"] == "lstm"].copy()

            # Unpack features_used JSON for RF rows
            def unpack_feats(row):
                try:
                    feats = json.loads(row["features_used"])
                    for k, v in feats.items():
                        row[k] = v
                except Exception:
                    pass
                return row

            rf_df = rf_raw.apply(unpack_feats, axis=1)
            return hist_df, rf_df, lstm_df
    except Exception:
        pass   # Supabase unreachable — fall through to local CSV

    # ── FALLBACK: Local CSV cache ─────────────────────────────────
    cache_path = BASE_DIR / "models/predictions_cache.csv"
    if cache_path.exists():
        cdf = pd.read_csv(cache_path)
        cdf["week_start"] = pd.to_datetime(cdf["week_start"])
        rf_raw  = cdf[cdf["model_name"] == "xgboost"].copy()
        lstm_df = cdf[cdf["model_name"] == "lstm"].copy()

        def unpack_feats(row):
            try:
                feats = json.loads(row["features_used"])
                for k, v in feats.items():
                    row[k] = v
            except Exception:
                pass
            return row

        rf_df = rf_raw.apply(unpack_feats, axis=1)

    return hist_df, rf_df, lstm_df

hist_df, rf_df, lstm_df = load_data()

render_page_banner(
    title="Live Demand Monitoring Dashboard",
    subtitle="Hotel Manager & Tour Operator Intelligence · AI-Powered Demand Tracking",
    icon="📈",
    show_predictions=True,
)

# ── Session State Defaults ──────────────────────────────────────────────
if "live_model_choice"       not in st.session_state: st.session_state.live_model_choice       = "Both"
if "live_show_ci"            not in st.session_state: st.session_state.live_show_ci            = True
if "live_hist_weeks"         not in st.session_state: st.session_state.live_hist_weeks         = 26
if "live_search_week"        not in st.session_state: st.session_state.live_search_week        = "Select a week..."
if "live_view_mode"          not in st.session_state: st.session_state.live_view_mode          = "Historical + Forecast"
if "live_forecast_start"     not in st.session_state: st.session_state.live_forecast_start     = datetime.date.today()

week_series = [hist_df["week_start"]]
if not rf_df.empty and "week_start" in rf_df.columns:
    week_series.append(rf_df["week_start"])
all_weeks = sorted(pd.concat(week_series).dropna().unique())
all_weeks_str = ["Select a week..."] + [pd.Timestamp(w).strftime("%Y-%m-%d") for w in all_weeks]

# ── Filter Bar CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
  .filter-bar {
      background: rgba(20, 31, 56, 0.45);
      backdrop-filter: blur(24px); border: 1px solid rgba(57,184,253,0.15);
      border-radius: 16px; padding: 18px 24px; margin-bottom: 24px;
      box-shadow: 0 0 20px rgba(0,0,0,0.1);
  }
  .forecast-warning-card {
      background: rgba(251, 191, 36, 0.08);
      border: 1px solid rgba(251, 191, 36, 0.4);
      border-left: 4px solid #fbbf24;
      border-radius: 12px;
      padding: 20px 24px;
      margin: 24px 0;
  }
  .forecast-warning-card .warn-title {
      color: #fbbf24; font-size: 1.05rem; font-weight: 800;
      font-family: 'Manrope', sans-serif; margin-bottom: 6px;
  }
  .forecast-warning-card .warn-body {
      color: #cbd5e1; font-size: 0.88rem; line-height: 1.6;
  }
</style>""", unsafe_allow_html=True)

# ── Filter Form ─────────────────────────────────────────────────────────
with st.container():
    st.markdown("<div style='padding: 0 0 24px 0; position:relative; z-index:10;'>", unsafe_allow_html=True)
    with st.form("live_demand_filters", border=False):
        # Row 1: Model, CI toggle, Hist weeks, Apply
        fc1, fc2, fc3, fc4 = st.columns([2, 1.5, 2, 1])
        with fc1:
            m_choice = st.selectbox("🤖 Active Model", ["Both", "xgboost", "lstm"],
                                    index=["Both", "xgboost", "lstm"].index(st.session_state.live_model_choice))
        with fc2:
            s_ci = st.toggle("Show 95% CI Zone", value=st.session_state.live_show_ci)
        with fc3:
            h_weeks = st.slider("Historical Weeks Pivot", 12, 104, st.session_state.live_hist_weeks)
        with fc4:
            st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Apply View", use_container_width=True)

        # Row 2: View mode + Forecast start date + Search week
        st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
        rc1, rc2, rc3 = st.columns([2.5, 2, 3])
        with rc1:
            view_mode = st.radio(
                "📅 View Mode",
                ["Historical + Forecast", "Next 52 Weeks Only"],
                index=["Historical + Forecast", "Next 52 Weeks Only"].index(
                    st.session_state.live_view_mode
                    if st.session_state.live_view_mode in ["Historical + Forecast", "Next 52 Weeks Only"]
                    else "Historical + Forecast"
                ),
                horizontal=True
            )
        with rc2:
            forecast_start = st.date_input(
                "🗓️ Forecast Start Date",
                value=st.session_state.live_forecast_start,
                help="Starting point for the 52-week (1 year) forward prediction window."
            )
        with rc3:
            try:
                idx = all_weeks_str.index(st.session_state.live_search_week)
            except ValueError:
                idx = 0
            s_week = st.selectbox("🔍 Search Single Week Drill-down", all_weeks_str, index=idx)

        if submitted:
            st.session_state.live_model_choice   = m_choice
            st.session_state.live_show_ci        = s_ci
            st.session_state.live_hist_weeks     = h_weeks
            st.session_state.live_search_week    = s_week
            st.session_state.live_view_mode      = view_mode
            st.session_state.live_forecast_start = forecast_start
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ── Resolved filter values ──────────────────────────────────────────────
model_choice   = st.session_state.live_model_choice
show_ci        = st.session_state.live_show_ci
hist_weeks     = st.session_state.live_hist_weeks
search_week    = st.session_state.live_search_week if st.session_state.live_search_week != "Select a week..." else None
view_mode      = st.session_state.live_view_mode
forecast_start = pd.Timestamp(st.session_state.live_forecast_start)
forecast_end   = forecast_start + pd.Timedelta(weeks=52)  # full 1-year window

# ── Apply View Mode Filtering ───────────────────────────────────────────
if view_mode == "Next 52 Weeks Only":
    # Filter predictions to the 52-week window
    rf_display   = rf_df[(rf_df["week_start"] >= forecast_start) & (rf_df["week_start"] < forecast_end)].copy() if not rf_df.empty else pd.DataFrame()
    lstm_display = lstm_df[(lstm_df["week_start"] >= forecast_start) & (lstm_df["week_start"] < forecast_end)].copy() if not lstm_df.empty else pd.DataFrame()
    plot_hist    = pd.DataFrame()  # Hide historical trace in this mode

    # ── No-data Warning Card (Supabase-aware message) ───────────────
    if rf_display.empty and lstm_display.empty:
        st.markdown(f"""
        <div class="forecast-warning-card">
            <div class="warn-title">⚠️ No Predictions Found for This Window</div>
            <div class="warn-body">
                There are no cached model predictions between
                <strong>{forecast_start.strftime('%d %b %Y')}</strong> and
                <strong>{forecast_end.strftime('%d %b %Y')}</strong>.<br><br>
                The system checks <strong>Supabase first</strong>, then your local cache file.
                The training pipeline generates predictions for the next <strong>52 weeks (1 year)</strong>
                after the last training date. If your selected start date is beyond that window,
                please go to <strong>⚙️ System Admin → MLOps Engine</strong> and trigger a model retrain
                to generate fresh forecasts.
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    rf_display   = rf_df.copy()   if not rf_df.empty   else pd.DataFrame()
    lstm_display = lstm_df.copy() if not lstm_df.empty else pd.DataFrame()
    plot_hist    = hist_df.tail(hist_weeks)

# ── Week Deep-Dive Card ─────────────────────────────────────────────────
if search_week and view_mode != "Next 52 Weeks Only":
    st.markdown(f'<div class="section-header">🔍 Week Deep-Dive: {search_week}</div>', unsafe_allow_html=True)

    h_row = hist_df[hist_df["week_start"] == search_week]
    r_row = rf_display[rf_display["week_start"] == search_week] if not rf_display.empty else pd.DataFrame()

    val_arr = None
    is_historic = False
    details = []

    if not h_row.empty:
        val_arr = h_row.iloc[0].get("estimated_weekly_kandy_arrivals")
        is_historic = True
        rain = h_row.iloc[0].get("rainfall_mm")
        if pd.notna(rain): details.append(f"🌧️ Rainfall: {rain:.1f} mm")
    elif not r_row.empty:
        val_arr = r_row.iloc[0].get("predicted_arrivals")

    row_for_events = r_row if not r_row.empty else h_row
    if not row_for_events.empty:
        if row_for_events.iloc[0].get("is_esala_perahera") == 1: details.append("🎭 Peak: Esala Perahera")
        if row_for_events.iloc[0].get("is_monsoon_week") == 1: details.append("⛈️ High Rain Risk (Monsoon)")
        fest = row_for_events.iloc[0].get("primary_festival")
        if pd.notna(fest) and fest != "Normal" and str(fest).lower() != 'nan':
            details.append(f"🎉 Festival: {fest}")

    badge = "<span style='background:#34d399; color:#064e3b; padding:4px 8px; border-radius:4px; font-size:0.8rem; font-weight:800;'>Historical Actual</span>" if is_historic else "<span style='background:#818cf8; color:#312e81; padding:4px 8px; border-radius:4px; font-size:0.8rem; font-weight:800;'>Future Forecast</span>"
    det_html = "<br>".join([f"<span style='color:#e2e8f0; font-size:0.95rem; font-weight:500;'>{d}</span>" for d in details])
    if not det_html: det_html = "<span style='color:#64748b; font-size:0.95rem; font-style:italic;'>No major events or warnings flagged.</span>"
    arr_str = f"{int(val_arr):,}" if pd.notna(val_arr) else "N/A"

    st.markdown(f"""
    <div style="background:linear-gradient(135deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.6) 100%); border:1px solid #334155; border-radius:12px; padding:24px; margin-bottom:28px; display:flex; gap:24px; align-items:center; box-shadow:0 8px 16px rgba(0,0,0,0.15);">
        <div style="flex:1;">
            <div style="color:#94a3b8; font-weight:600; margin-bottom:12px; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.05em;">Timeline Status</div>
            {badge}
        </div>
        <div style="flex:1.5; border-left:1px solid #334155; padding-left:24px;">
            <div style="color:#94a3b8; font-weight:600; margin-bottom:4px; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.05em;">Weekly Arrivals</div>
            <div style="color:#f8fafc; font-size:2.2rem; font-weight:800; font-family:'Manrope',sans-serif; line-height:1;">{arr_str}</div>
        </div>
        <div style="flex:2.5; border-left:1px solid #334155; padding-left:24px;">
            <div style="color:#94a3b8; font-weight:600; margin-bottom:8px; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.05em;">Insight Details</div>
            {det_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── KPI Cards ───────────────────────────────────────────────────────────
kc1, kc2, kc3, kc4 = st.columns(4)

if view_mode == "Next 52 Weeks Only":
    # KPIs reflect the 52-week forecast window
    if not rf_display.empty:
        fc_avg   = int(rf_display["predicted_arrivals"].mean())
        fc_peak  = rf_display.loc[rf_display["predicted_arrivals"].idxmax()]
        fc_peak_date  = pd.Timestamp(fc_peak["week_start"]).strftime("%d %b %Y")
        fc_peak_arr   = int(fc_peak["predicted_arrivals"])
        fc_monsoon    = int(rf_display["is_monsoon_week"].sum()) if "is_monsoon_week" in rf_display.columns else 0
        fc_window_label = f"{forecast_start.strftime('%d %b')} → {forecast_end.strftime('%d %b %Y')}"

        with kc1:
            render_metric_card("Forecast Avg (52wk)", f"{fc_avg:,}", fc_window_label, "📊")
        with kc2:
            render_metric_card("Peak Forecast Week", fc_peak_date, f"{fc_peak_arr:,} arrivals", "📅")
        with kc3:
            render_metric_card("Monsoon Weeks Ahead", str(fc_monsoon), "high-rain weeks in window", "🌦️")
        with kc4:
            render_metric_card("Weeks in Window", str(len(rf_display)), "forecast weeks loaded", "🤖")
    else:
        with kc1:
            render_metric_card("Forecast Avg (52wk)", "—", "No data in window", "📊")
        with kc2:
            render_metric_card("Peak Forecast Week", "—", "No data", "📅")
        with kc3:
            render_metric_card("Monsoon Weeks Ahead", "—", "No data", "🌦️")
        with kc4:
            render_metric_card("Weeks in Window", "0", "No predictions found", "🤖")
else:
    # KPIs reflect recent historical data
    recent  = hist_df.tail(26)
    prev26  = hist_df.iloc[-52:-26]
    if not recent.empty and not prev26.empty:
        avg_recent       = int(recent["estimated_weekly_kandy_arrivals"].mean())
        avg_prev_period  = int(prev26["estimated_weekly_kandy_arrivals"].mean())
        chg_pct = ((avg_recent - avg_prev_period) / avg_prev_period * 100) if avg_prev_period > 0 else 0
    else:
        avg_recent, chg_pct = 0, 0

    if not recent.empty:
        peak_idx  = recent["estimated_weekly_kandy_arrivals"].idxmax()
        peak_week = recent.loc[peak_idx]
        peak_date = peak_week["week_start"].strftime("%d %b %Y")
        peak_arr  = int(peak_week["estimated_weekly_kandy_arrivals"])
    else:
        peak_date, peak_arr = "-", 0

    monsoon_weeks = int(rf_display["is_monsoon_week"].sum()) if not rf_display.empty and "is_monsoon_week" in rf_display.columns else 0
    next_rf_avg   = int(rf_display["predicted_arrivals"].mean()) if not rf_display.empty else 0
    delta_str     = f"+{abs(chg_pct):.1f}% vs prev period" if chg_pct >= 0 else f"-{abs(chg_pct):.1f}% vs prev period"

    with kc1:
        render_metric_card("Avg Weekly Arrivals", f"{avg_recent:,}", delta_str, "📊", positive_trend=(chg_pct >= 0))
    with kc2:
        render_metric_card("Peak Week (Displayed)", peak_date, f"{peak_arr:,} arrivals", "📅")
    with kc3:
        render_metric_card("Monsoon Weeks", str(monsoon_weeks), "high rain risk weeks", "🌦️")
    with kc4:
        render_metric_card("XGBoost 26-wk Avg", f"{next_rf_avg:,}", "predicted weekly arrivals", "🤖")

# ── Chart Title ─────────────────────────────────────────────────────────
if view_mode == "Next 52 Weeks Only":
    st.markdown(
        f'<div class="section-header">📅 Next 52 Weeks Forecast: '
        f'{forecast_start.strftime("%d %b %Y")} → {forecast_end.strftime("%d %b %Y")}</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown('<div class="section-header">📊 Historical vs. Forecasted Arrivals</div>', unsafe_allow_html=True)

# ── Main Chart ──────────────────────────────────────────────────────────
fig = go.Figure()

# Historical trace (hidden in "Next 26 Weeks Only" mode)
anomalies_high, anomalies_low = pd.DataFrame(), pd.DataFrame()
if not plot_hist.empty:
    fig.add_trace(go.Scatter(
        x=plot_hist["week_start"], y=plot_hist["estimated_weekly_kandy_arrivals"],
        name="Historical (Actual)", mode="lines",
        line=dict(color="#38BDF8", width=2.5),
        fill="tozeroy", fillcolor="rgba(56,189,248,0.15)",
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Actual: %{y:,.0f}<extra></extra>"
    ))

    # Anomaly Detection
    mean_arr       = plot_hist["estimated_weekly_kandy_arrivals"].mean()
    std_arr        = plot_hist["estimated_weekly_kandy_arrivals"].std()
    threshold_upper = mean_arr + 1.8 * std_arr
    threshold_lower = max(0, mean_arr - 1.8 * std_arr)
    anomalies_high  = plot_hist[plot_hist["estimated_weekly_kandy_arrivals"] > threshold_upper]
    anomalies_low   = plot_hist[plot_hist["estimated_weekly_kandy_arrivals"] < threshold_lower]

    if not anomalies_high.empty:
        fig.add_trace(go.Scatter(x=anomalies_high["week_start"], y=anomalies_high["estimated_weekly_kandy_arrivals"],
                                 mode="markers", marker=dict(color="#fb7185", size=10, symbol="triangle-up"),
                                 name="Surge Anomaly", hoverinfo="skip"))
    if not anomalies_low.empty:
        fig.add_trace(go.Scatter(x=anomalies_low["week_start"], y=anomalies_low["estimated_weekly_kandy_arrivals"],
                                 mode="markers", marker=dict(color="#818cf8", size=10, symbol="triangle-down"),
                                 name="Drop Anomaly", hoverinfo="skip"))

    # Online Learning Trend Line
    try:
        online_model = SGDRegressor(loss='squared_error', penalty=None, learning_rate='invscaling', random_state=42)
        scaler = StandardScaler()
        X = np.arange(len(plot_hist)).reshape(-1, 1)
        X_scaled = scaler.fit_transform(X)
        y = plot_hist["estimated_weekly_kandy_arrivals"].values
        for i in range(len(X_scaled)):
            online_model.partial_fit(X_scaled[i:i+1], y[i:i+1])
        trend_y = online_model.predict(X_scaled)
        fig.add_trace(go.Scatter(
            x=plot_hist["week_start"], y=trend_y,
            name="SGD Online Trend", mode="lines",
            line=dict(color="#f43f5e", width=2, dash="dashdot"),
            hovertemplate="<b>%{x|%d %b %Y}</b><br>Online Trend: %{y:,.0f}<extra></extra>"
        ))
    except Exception:
        pass

# Festival annotations from forecast data
if not rf_display.empty:
    for _, row in rf_display.iterrows():
        if row.get("is_esala_perahera", 0) == 1:
            fig.add_vrect(x0=row["week_start"], x1=row["week_start"] + pd.Timedelta(days=7),
                          fillcolor="rgba(56,189,248,0.06)", layer="below", line_width=0)
            fig.add_annotation(x=row["week_start"], y=row["predicted_arrivals"],
                               text="🎭 Esala", showarrow=True, arrowhead=1, arrowcolor="#fde047",
                               font=dict(color="#fde047"), bgcolor="rgba(0,0,0,0.6)")

        fest = row.get("primary_festival")
        if pd.notna(fest) and str(fest).lower() != "nan" and fest != "Normal" and row.get("is_esala_perahera", 0) != 1:
            fig.add_annotation(x=row["week_start"], y=row["predicted_arrivals"],
                               text=fest, showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor="#ef4444",
                               ax=0, ay=-40, font=dict(color="#fde047", size=11, family="Inter"))

# XGBoost forecast trace
if model_choice in ["Both", "xgboost"] and not rf_display.empty:
    fig.add_trace(go.Scatter(
        x=rf_display["week_start"], y=rf_display["predicted_arrivals"],
        name="XGBoost Forecast", mode="lines+markers",
        line=dict(color="#34d399", width=2, dash="dot"),
        hovertemplate="<b>%{x|%d %b %Y}</b><br>XGBoost: %{y:,.0f}<extra></extra>"
    ))
    if show_ci and "lower_bound" in rf_display.columns:
        fig.add_trace(go.Scatter(
            x=pd.concat([rf_display["week_start"], rf_display["week_start"][::-1]]),
            y=pd.concat([rf_display["upper_bound"], rf_display["lower_bound"][::-1]]),
            fill="toself", fillcolor="rgba(52,211,153,0.1)",
            line=dict(color="rgba(0,0,0,0)"), hoverinfo="skip", showlegend=True, name="XGBoost 95% CI"
        ))

# LSTM forecast trace
if model_choice in ["Both", "lstm"] and not lstm_display.empty:
    fig.add_trace(go.Scatter(
        x=lstm_display["week_start"], y=lstm_display["predicted_arrivals"],
        name="LSTM Forecast", mode="lines",
        line=dict(color="#fb923c", width=2, dash="dash"),
        hovertemplate="<b>%{x|%d %b %Y}</b><br>LSTM Pred: %{y:,.0f}<extra></extra>"
    ))

fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", family="Inter"),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#334155", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified",
    xaxis=dict(gridcolor="#1e293b"),
    yaxis=dict(gridcolor="#1e293b", title="Weekly Arrivals"),
    margin=dict(l=0, r=0, t=40, b=0),
    height=450
)

if search_week and view_mode != "Next 26 Weeks Only":
    fig.add_vline(x=pd.to_datetime(search_week), line_width=2.5, line_dash="dash", line_color="#38bdf8")
    fig.add_annotation(x=pd.to_datetime(search_week), y=1, yref="paper", text="<b>Selected Week Focus</b>",
                       showarrow=False, font=dict(color="#38bdf8", size=12), bgcolor="rgba(15,23,42,0.8)", bordercolor="#38bdf8", borderpad=4)

st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

# ── Anomalies Insight Card ──────────────────────────────────────────────
num_anom = len(anomalies_high) + len(anomalies_low)
if num_anom > 0 and view_mode != "Next 26 Weeks Only":
    st.markdown(f"""
    <div style="background:rgba(251,113,133,0.06); border-left:4px solid #fb7185; padding:16px 20px; border-radius:12px; margin-top:20px; box-shadow:0 0 16px rgba(0,0,0,0.1);">
        <span style="color:#fb7185; font-weight:800; font-size:1.05rem; font-family:'Manrope',sans-serif;">🚨 {num_anom} Anomalies Detected in Focus Range</span><br>
        <span style="color:#bdc8d1; font-size:0.9rem; margin-top:4px; display:inline-block;">The system flagged unusual deviations (marked by triangles on the chart) in recent historical data deviating 1.8σ from the moving average. These often align with unpredicted micro-events or macro travel disruptions.</span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── Forecast Breakdown Table ────────────────────────────────────────────
if view_mode == "Next 26 Weeks Only":
    table_title = f"🗓️ Next 26-Week Forecast: {forecast_start.strftime('%d %b %Y')} → {forecast_end.strftime('%d %b %Y')}"
else:
    table_title = "🗓️ 26-Week Forecast Breakdown"

st.markdown(f'<div class="section-header">{table_title}</div>', unsafe_allow_html=True)

table_source = rf_display if not rf_display.empty else pd.DataFrame()
if not table_source.empty:
    tbl = table_source[["week_start", "predicted_arrivals"]].copy()
    tbl["week_start"] = pd.to_datetime(tbl["week_start"])
    tbl["Month"] = tbl["week_start"].dt.strftime("%b %Y")

    avg_for_labels = int(table_source["predicted_arrivals"].mean())

    def demand_label(row):
        if row.get("is_esala_perahera", 0) == 1:  return "🎭 Peak — Esala Perahera"
        if row.get("is_monsoon_week", 0) == 1:     return "🌧️ Monsoon — Lower Demand"
        if row.get("is_christmas_new_year", 0) == 1: return "🎄 Holiday — High Demand"
        if row.get("predicted_arrivals", 0) > avg_for_labels * 1.1: return "📈 High Demand"
        if row.get("predicted_arrivals", 0) < avg_for_labels * 0.9: return "📉 Low Demand"
        return "✅ Normal"

    tbl["Risk / Event"] = table_source.apply(demand_label, axis=1)
    tbl = tbl[["week_start", "Month", "predicted_arrivals", "Risk / Event"]]
    tbl.columns = ["Week Start", "Month", "Predicted Arrivals", "Risk / Event"]

    st.dataframe(tbl, use_container_width=True, hide_index=True)

    fname = f"kandy_forecast_{forecast_start.strftime('%Y%m%d')}.csv" if view_mode == "Next 26 Weeks Only" else "kandy_26week_forecast.csv"
    st.download_button(
        "⬇️  Download Forecast CSV",
        tbl.to_csv(index=False).encode("utf-8"),
        fname,
        "text/csv"
    )
else:
    st.info("🔄 No forecast data found for this window. Run the model training pipeline first.")

st.caption("Forecast sourced from `predictions_cache.csv` · Models: XGBoost/RF + LSTM · DSS v1.0.0")
