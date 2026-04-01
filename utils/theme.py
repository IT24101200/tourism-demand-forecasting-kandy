import streamlit as st

# ── Design Tokens ────────────────────────────────
DARK_COLORS = {
    "bg":          "#0b1326",      # surface
    "surface":     "#171f33",      # surface-container
    "surface_low": "#131b2e",      # surface-container-low
    "surface_high":"#222a3d",      # surface-container-high
    "surface_glass":"rgba(6,14,32,0.6)", # surface-container-lowest with opacity
    "border":      "rgba(62,72,79,0.15)", # outline-variant at 15% (Ghost border)
    "accent":      "#38bdf8",      # primary-container 
    "accent_dim":  "#8ed5ff",      # primary
    "accent2":     "#4edea3",      # secondary
    "accent2_dim": "#00a572",      # secondary-container
    "danger":      "#ffb4ab",      # error
    "warning":     "#F59E0B",      # legacy warning
    "text_main":   "#dae2fd",      # on-surface (Never pure white)
    "text_muted":  "#bdc8d1",      # on-surface-variant
    "text_dim":    "#87929a",      # outline
}

LIGHT_COLORS = {
    "bg":          "#f8fafc",      # surface (slate-50)
    "surface":     "#ffffff",      # surface-container (white)
    "surface_low": "#f1f5f9",      # surface-container-low (slate-100)
    "surface_high":"#e2e8f0",      # surface-container-high (slate-200)
    "surface_glass":"rgba(255,255,255,0.7)", 
    "border":      "rgba(15,23,42,0.12)",
    "accent":      "#0284c7",      # sky-600
    "accent_dim":  "#0ea5e9",      # sky-500
    "accent2":     "#059669",      # emerald-600
    "accent2_dim": "#10b981",      # emerald-500
    "danger":      "#dc2626",      # red-600
    "warning":     "#d97706",      # amber-600
    "text_main":   "#0f172a",      # slate-900
    "text_muted":  "#475569",      # slate-600
    "text_dim":    "#64748b",      # slate-500
}

def get_theme():
    """Returns the active color dictionary based on session stream."""
    if "theme" not in st.session_state:
        st.session_state.theme = "dark"
    return DARK_COLORS if st.session_state.theme == "dark" else LIGHT_COLORS

def apply_custom_theme():
    """
    Applies the global design system dynamically supporting light and dark themes.
    """
    theme = get_theme()
    
    css = f"""
    <style>
        /* ── Fonts ────────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Manrope:wght@400;600;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif !important;
            color: {theme['text_main']} !important;
        }}

        /* ── Hide Streamlit chrome ────────────────── */
        #MainMenu {{visibility: hidden;}}
        footer    {{visibility: hidden;}}
        header    {{background: transparent !important;}}

        /* ── App Background ─────────────────────── */
        .stApp {{
            background: {theme['bg']} !important;
        }}
        .block-container {{
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            max-width: 1400px !important;
        }}

        /* ── Sidebar Navigation Pillar ──────────── */
        [data-testid="stSidebar"] {{
            background: {theme['surface_glass']} !important;
            backdrop-filter: blur(24px) !important;
            border-right: 1px solid {theme['border']} !important;
        }}
        [data-testid="stSidebar"] * {{
            color: {theme['text_main']} !important;
        }}
        [data-testid="stSidebarNav"] span {{
            font-family: 'Inter', sans-serif;
            font-size: 0.95rem;
            font-weight: 500;
        }}
        [data-testid="stSidebarNav"] a:hover {{
            background-color: {theme['surface_high']} !important;
            border-radius: 8px;
        }}
        /* Active State: The vertical light-pipe */
        [data-testid="stSidebarNav"] a[aria-current="page"] {{
            background-color: {theme['surface_low']} !important;
            border-left: 2px solid {theme['accent_dim']} !important;
            border-radius: 0 8px 8px 0;
        }}
        [data-testid="stSidebarNav"] a[aria-current="page"] span {{
            color: {theme['accent']} !important; 
        }}

        /* ── KPI Cards (The Signature Component) ──── */
        .kpi-card {{
            background: {theme['surface_low']};
            border: 1px solid {theme['border']};
            border-radius: 16px;
            padding: 27px; /* spacing-5 / 1.7rem */
            text-align: left;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            position: relative;
        }}
        .kpi-card:hover {{
            background: {theme['surface_high']};
            /* Ambient shadow / glow */
            box-shadow: 0 8px 30px rgba(0,0,0,0.08); 
        }}
        .kpi-card.positive-glow {{
            box-shadow: inset 0 0 0 1px {theme['accent2_dim']}, 0 4px 20px -10px {theme['accent2_dim']};
        }}
        
        .kpi-label {{
            color: {theme['text_muted']};
            font-size: 0.875rem; /* label-sm */
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-bottom: 8px;
            font-family: 'Inter', sans-serif;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .kpi-value {{
            color: {theme['text_main']};
            font-size: 2.25rem; /* display-sm */
            font-weight: 800;
            line-height: 1.1;
            font-family: 'Manrope', sans-serif;
            margin-bottom: 4px;
        }}
        
        .kpi-delta-pos {{ color: {theme['accent2']}; font-size: 0.82rem; font-weight: 700; font-family: 'Inter', sans-serif;}}
        .kpi-delta-neg {{ color: {theme['danger']};  font-size: 0.82rem; font-weight: 700; font-family: 'Inter', sans-serif;}}
        .kpi-delta-neu {{ color: {theme['text_dim']}; font-size: 0.82rem; font-weight: 600; font-family: 'Inter', sans-serif;}}

        /* ── Page Header (Editorial Authority) ────── */
        .page-header {{
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            margin-bottom: 32px;
            padding-bottom: 20px;
            /* Tonal transition boundary */
            border-bottom: 1px solid {theme['border']};
        }}
        .page-title {{
            font-family: 'Manrope', sans-serif;
            font-size: 2.5rem; /* headline-lg */
            font-weight: 800;
            color: {theme['text_main']};
            line-height: 1.1;
            letter-spacing: -0.02em;
        }}
        .page-title span.accent {{
            color: {theme['accent']};
        }}
        .page-subtitle {{
            color: {theme['text_muted']};
            font-size: 0.95rem;
            margin-top: 8px;
            font-family: 'Inter', sans-serif;
        }}
        
        /* ── Section Sub-header ──────────────────── */
        .section-header {{
            color: {theme['text_main']};
            font-size: 1.25rem;
            font-weight: 700;
            margin: 36px 0 16px 0;
            font-family: 'Manrope', sans-serif;
            letter-spacing: -0.01em;
        }}

        /* ── Glass Panel (Floating elements) ──────── */
        .glass-panel {{
            background: {theme['surface_glass']};
            backdrop-filter: blur(24px);
            border: 1px solid {theme['border']};
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        }}

        /* ── Action Buttons ──────────────────────── */
        button[data-testid="baseButton-primary"], .btn-primary {{
            background: linear-gradient(135deg, {theme['accent_dim']} 0%, {theme['accent']} 100%) !important;
            color: #ffffff !important; 
            border: none !important;
            border-radius: 8px !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 700 !important;
            padding: 0.55rem 1.6rem !important;
            transition: all 0.25s ease;
            box-shadow: 0 4px 14px rgba(0,0,0,0.1) !important;
        }}
        button[data-testid="baseButton-primary"]:hover, .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.15) !important;
        }}
        
        .stButton > button {{
            transition: all 0.2s ease !important;
            border-radius: 8px !important;
            border: 1px solid {theme['border']} !important;
            background: {theme['surface_low']} !important;
            color: {theme['text_main']} !important;
        }}
        .stButton > button:hover {{
            background: {theme['surface_high']} !important;
            color: {theme['accent_dim']} !important;
            border-color: {theme['accent_dim']} !important;
        }}

        /* ── Input Fields ────────────────────────── */
        .stTextInput > div > div, .stNumberInput > div > div,
        .stSelectbox > div > div, .stDateInput > div > div {{
            background-color: {theme['surface']} !important; 
            border: 1px solid {theme['border']} !important;
            border-radius: 8px !important;
            transition: all 0.2s ease;
        }}
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] div {{
            color: {theme['text_main']} !important;
        }}
        .stTextInput > div > div:focus-within,
        .stNumberInput > div > div:focus-within,
        .stSelectbox > div > div:focus-within {{
            border-color: {theme['accent']} !important;
            box-shadow: 0 0 0 1px {theme['accent']} !important;
        }}

        /* ── Sliders ─────────────────────────────── */
        .stSlider [data-baseweb="slider"] [role="slider"] {{
            background: {theme['accent']} !important;
            border: 2px solid {theme['surface']} !important;
        }}
        .stSlider [data-baseweb="slider"] div[data-testid="stSliderTrackFill"] {{
            background: linear-gradient(90deg, {theme['accent_dim']}, {theme['accent']}) !important;
        }}

        /* ── Tables & Dataframes ─────────────────── */
        [data-testid="stDataFrame"] {{
            border-radius: 12px !important;
            background: {theme['surface']} !important;
            border: 1px solid {theme['border']} !important;
        }}
        [data-testid="stTable"] {{
            background: transparent !important;
        }}
        th {{
            color: {theme['text_muted']} !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            border-bottom: 1px solid {theme['border']} !important;
            background: {theme['surface_low']} !important;
        }}
        td {{
            color: {theme['text_main']} !important;
            font-family: 'Inter', sans-serif !important;
            border-bottom: 1px solid {theme['border']} !important;
            font-size: 0.875rem !important;
        }}

        /* ── Tabs ────────────────────────────────── */
        [data-baseweb="tab-list"] {{
            background: transparent !important;
            gap: 16px !important;
            border-bottom: 1px solid {theme['border']} !important;
        }}
        button[role="tab"] {{
            background: transparent !important;
            padding: 0 12px 14px 12px !important;
            border-bottom: 2px solid transparent !important;
            border-radius: 0 !important;
        }}
        button[role="tab"] p {{
            color: {theme['text_muted']} !important;
            font-size: 0.95rem !important;
            font-weight: 500 !important;
            font-family: 'Inter', sans-serif !important;
        }}
        button[role="tab"][aria-selected="true"] {{
            border-bottom: 2px solid {theme['accent']} !important;
        }}
        button[role="tab"][aria-selected="true"] p {{
            color: {theme['accent']} !important;
            font-weight: 700 !important;
        }}

        /* ── Profile/Settings Container ──────────── */
        .profile-card {{
            background: {theme['surface']};
            color: {theme['text_main']} !important;
            border: 1px solid {theme['border']};
            border-radius: 16px;
            padding: 32px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        }}

        /* ── Info / Callouts ─────────────────────── */
        .insight-card {{
            background: {theme['surface_low']};
            border: 1px solid {theme['border']};
            border-left: 3px solid {theme['accent']};
            border-radius: 8px;
            padding: 16px 20px;
            margin: 16px 0;
        }}
        .insight-title {{
            color: {theme['accent']};
            font-size: 0.85rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 8px;
            font-family: 'Inter', sans-serif;
        }}
        .insight-text {{
            color: {theme['text_main']};
            font-size: 0.9rem;
            line-height: 1.6;
            font-family: 'Inter', sans-serif;
        }}

    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def apply_plotly_theme(fig):
    """
    Applies the active dynamic theme (Light/Dark) to Plotly charts.
    """
    theme = get_theme()
    
    fig.update_layout(
        font_family="Inter, sans-serif",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        colorway=[
            theme['accent_dim'], # Primary line
            theme['accent2'],    # Secondary line
            '#a7a9ff',            # Tertiary container (purpleish)
            '#ffdad6',            # error container
        ],
        legend=dict(
            font=dict(color=theme['text_muted'], size=12),
            bgcolor=theme['bg'],
            bordercolor=theme['border'],
            borderwidth=1,
            yanchor="top", y=0.99, xanchor="left", x=0.01
        ),
        margin=dict(t=40, b=40, l=40, r=20),
    )
    
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor=theme['border'],
        tickfont=dict(color=theme['text_muted'], size=11),
        title_font=dict(color=theme['text_muted'], size=12, family="Inter"),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=theme['border'],
        zeroline=False,
        linecolor=theme['border'],
        tickfont=dict(color=theme['text_muted'], size=11),
        title_font=dict(color=theme['text_muted'], size=12, family="Inter"),
    )
    return fig


def render_metric_card(title, value, delta=None, icon="", positive_trend=False):
    """Renders a Luminous Deep KPI metric card."""
    delta_html = ""
    glow_class = "positive-glow" if positive_trend else ""
    
    if delta is not None and str(delta).strip() != "":
        # Determine +/- purely from string for display logic
        is_pos = str(delta).strip().startswith("+") or (not str(delta).strip().startswith("-") and "0" not in str(delta))
        if "Critical" in str(delta) or "High" in str(delta): is_pos = False
        if "Normal" in str(delta): is_pos = True
        
        cls = "kpi-delta-pos" if is_pos else "kpi-delta-neg"
        delta_html = f"<div class='{cls}' style='margin-top:4px'>{delta}</div>"

    icon_html = f"<span style='margin-right:8px;font-size:1.2rem'>{icon}</span>" if icon else ""
    st.markdown(f"""
    <div class="kpi-card {glow_class}">
        <div class="kpi-label">{icon_html}{title}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def get_current_week_prediction():
    try:
        import pandas as pd
        from pathlib import Path
        import datetime
        
        cache_path = Path(__file__).parent.parent / "models" / "predictions_cache.csv"
        if not cache_path.exists(): 
            return None
            
        df = pd.read_csv(cache_path)
        df["week_start"] = pd.to_datetime(df["week_start"])
        df["week_end"] = pd.to_datetime(df["week_end"])
        df = df[df["model_name"] == "random_forest"]
        
        today = pd.Timestamp(datetime.date.today())
        current = df[(df["week_start"] <= today) & (df["week_end"] >= today)]
        
        if not current.empty:
            return int(current.iloc[0]["predicted_arrivals"])
            
        # Fallback to closest future week
        future = df[df["week_start"] >= today]
        if not future.empty:
            return int(future.iloc[0]["predicted_arrivals"])
    except Exception:
        pass
    return None

@st.cache_data(ttl=3600)
def get_next_week_prediction():
    try:
        import pandas as pd
        from pathlib import Path
        import datetime
        
        cache_path = Path(__file__).parent.parent / "models" / "predictions_cache.csv"
        if not cache_path.exists(): 
            return None
            
        df = pd.read_csv(cache_path)
        df["week_start"] = pd.to_datetime(df["week_start"])
        df = df[df["model_name"] == "random_forest"]
        df = df.sort_values(by="week_start")
        
        today = pd.Timestamp(datetime.date.today())
        
        # Get the first week that starts *strictly* after today's week
        future = df[df["week_start"] >= today + pd.Timedelta(days=7)]
        if not future.empty:
            return int(future.iloc[0]["predicted_arrivals"])
    except Exception:
        pass
    return None

def render_page_header(title, accent_word=None, subtitle=""):
    """
    Renders the page header with a live dynamic clock and forecast badges.
    """
    import datetime
    now = datetime.datetime.now()
    time_str = now.strftime("%I:%M %p")
    date_str = now.strftime("%d %b %Y")

    if accent_word and accent_word in title:
        left, right = title.split(accent_word, 1)
        title_html = f"{left}<span class='accent'>{accent_word}</span>{right}"
    else:
        title_html = title

    sub_html = f"<div class='page-subtitle'>{subtitle}</div>" if subtitle else ""
    
    pred_val = get_current_week_prediction()
    next_pred_val = get_next_week_prediction()
    
    badges_html = ""
    if pred_val or next_pred_val:
        badges_html += '<div style="display: flex; gap: 8px; margin-bottom: 10px; justify-content: flex-end;">'
        if pred_val:
            badges_html += f'<div style="background: rgba(78,222,163,0.1); border: 1px solid rgba(78,222,163,0.25); border-radius: 8px; padding: 4px 10px; color: #4edea3; font-family: \'Inter\', sans-serif; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em; display: flex; align-items: center; gap: 6px;"><span style="font-size:0.85rem">🎯</span> THIS WEEK: {pred_val:,}</div>'
        if next_pred_val:
            badges_html += f'<div style="background: rgba(142,213,255,0.1); border: 1px solid rgba(142,213,255,0.25); border-radius: 8px; padding: 4px 10px; color: #8ed5ff; font-family: \'Inter\', sans-serif; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em; display: flex; align-items: center; gap: 6px;"><span style="font-size:0.85rem">⏭️</span> NEXT WEEK: {next_pred_val:,}</div>'
        badges_html += '</div>'

    st.markdown(f"""
    <div class="page-header">
        <div>
            <div class="page-title">{title_html}</div>
            {sub_html}
        </div>
        <div style="display: flex; flex-direction: column; align-items: flex-end; justify-content: flex-end;">
            {badges_html}
            <div style="text-align: right; background: rgba(142,213,255,0.05); padding: 8px 16px; border-radius: 12px; border: 1px solid rgba(142,213,255,0.15); box-shadow: 0 0 20px rgba(0,0,0,0.1);">
                <div style="color: #8ed5ff; font-family: 'Manrope', sans-serif; font-size: 1.15rem; font-weight: 800; letter-spacing: 0.05em;">{time_str}</div>
                <div style="color: #87929a; font-family: 'Inter', sans-serif; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-top: 2px;">{date_str}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_insight_card(title, text):
    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-title">💡 {title}</div>
        <div class="insight-text">{text}</div>
    </div>
    """, unsafe_allow_html=True)


def render_page_banner(title: str, subtitle: str, icon: str = "🏔️",
                       show_predictions: bool = False):
    """
    Renders the premium page-header card shared across all pages.
    Matches the Bloomberg-style header of National Performance Canvas.

    Parameters
    ----------
    title       : plain-text page title  (e.g. "Kandy Demand Forecast")
    subtitle    : plain-text subtitle    (e.g. "Weekly predictions for Kandy district")
    icon        : emoji/char shown left of the accent bar (default: 🏔️)
    show_predictions : if True, show This Week / Next Week LSTM badges
    """
    import datetime
    now      = datetime.datetime.now()
    time_str = now.strftime("%I:%M %p")
    date_str = now.strftime("%d %b %Y").upper()

    # ── Live prediction badges (optional) ────────────────────────────────
    badge_this = badge_next = ""
    if show_predictions:
        pred_val      = get_current_week_prediction()
        next_pred_val = get_next_week_prediction()
        if pred_val:
            badge_this = (
                '<div style="display:inline-flex;align-items:center;gap:8px;padding:9px 18px;'
                'border-radius:999px;background:rgba(105,246,184,0.08);'
                'border:1px solid rgba(105,246,184,0.35);'
                'box-shadow:0 0 16px rgba(105,246,184,0.1);margin-right:4px;">'
                '<span style="font-size:0.95rem;">&#127919;</span>'
                '<span style="font-family:Inter,sans-serif;font-size:0.72rem;font-weight:700;'
                'letter-spacing:0.06em;color:#69f6b8;">THIS WEEK</span>'
                f'<span style="font-family:Manrope,sans-serif;font-size:0.98rem;font-weight:800;'
                f'color:#e1ffec;">{pred_val:,}</span>'
                '</div>'
            )
        if next_pred_val:
            badge_next = (
                '<div style="display:inline-flex;align-items:center;gap:8px;padding:9px 18px;'
                'border-radius:999px;background:rgba(57,184,253,0.08);'
                'border:1px solid rgba(57,184,253,0.35);'
                'box-shadow:0 0 16px rgba(57,184,253,0.1);">'
                '<span style="font-size:0.95rem;">&#128202;</span>'
                '<span style="font-family:Inter,sans-serif;font-size:0.72rem;font-weight:700;'
                'letter-spacing:0.06em;color:#39b8fd;">NEXT WEEK</span>'
                f'<span style="font-family:Manrope,sans-serif;font-size:0.98rem;font-weight:800;'
                f'color:#cef0ff;">{next_pred_val:,}</span>'
                '</div>'
            )

    badges_center = (
        f'<div style="display:flex;align-items:center;gap:8px;flex-shrink:0;">'
        f'{badge_this}{badge_next}'
        f'</div>'
    )

    # ── Clock widget ──────────────────────────────────────────────────────
    clock = (
        '<div style="flex-shrink:0;background:rgba(20,31,56,0.7);'
        'backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);'
        'border:1px solid rgba(57,184,253,0.2);border-radius:14px;'
        'padding:12px 20px;text-align:center;'
        'box-shadow:0 0 20px rgba(57,184,253,0.07);">'
        f'<div style="font-family:Manrope,sans-serif;font-size:1.45rem;font-weight:800;'
        f'color:#39b8fd;letter-spacing:0.04em;line-height:1;">{time_str}</div>'
        f'<div style="font-family:Inter,sans-serif;font-size:0.62rem;font-weight:700;'
        f'color:#6d758c;letter-spacing:0.1em;margin-top:3px;text-transform:uppercase;">{date_str}</div>'
        '</div>'
    )

    # ── Assemble card ─────────────────────────────────────────────────────
    html_parts = [
        '<div style="background:linear-gradient(135deg,#091328 0%,#060e20 60%,#0a1628 100%);',
        'border:1px solid rgba(57,184,253,0.15);border-radius:18px;',
        'padding:26px 34px 0 34px;margin-bottom:8px;position:relative;overflow:hidden;">',

        # glow blobs
        '<div style="position:absolute;top:-60px;right:-60px;width:240px;height:240px;',
        'border-radius:50%;background:radial-gradient(circle,rgba(57,184,253,0.07) 0%,transparent 70%);',
        'pointer-events:none;"></div>',
        '<div style="position:absolute;bottom:-40px;left:60px;width:180px;height:180px;',
        'border-radius:50%;background:radial-gradient(circle,rgba(105,246,184,0.05) 0%,transparent 70%);',
        'pointer-events:none;"></div>',

        # row
        '<div style="display:flex;align-items:center;justify-content:space-between;',
        'gap:20px;position:relative;z-index:1;">',

        # LEFT — icon + accent bar + text
        '<div style="display:flex;align-items:flex-start;gap:14px;flex:1;min-width:0;">',
        f'<div style="font-size:1.9rem;line-height:1;margin-top:6px;flex-shrink:0;">{icon}</div>',
        '<div style="width:3px;min-height:58px;border-radius:3px;flex-shrink:0;',
        'background:linear-gradient(180deg,#39b8fd 0%,#69f6b8 100%);',
        'box-shadow:0 0 10px rgba(57,184,253,0.45);margin-top:4px;"></div>',
        '<div>',
        f'<div style="font-family:Manrope,sans-serif;font-size:1.85rem;font-weight:800;',
        f'color:#dee5ff;line-height:1.1;letter-spacing:-0.022em;">',
        f'{title}</div>',
        f'<div style="font-family:Inter,sans-serif;font-size:0.85rem;color:#6d758c;',
        f'margin-top:5px;font-weight:500;">&#127472;&#127473;&nbsp; {subtitle}</div>',
        '</div>',
        '</div>',

        # CENTER — badges
        badges_center,

        # RIGHT — clock
        clock,

        '</div>',   # end row

        # bottom glow separator
        '<div style="height:2px;margin:22px -34px 0 -34px;',
        'background:linear-gradient(90deg,transparent 0%,rgba(57,184,253,0.35) 30%,',
        'rgba(105,246,184,0.3) 70%,transparent 100%);',
        'box-shadow:0 0 8px rgba(57,184,253,0.18);"></div>',

        '</div>'
    ]
    html = "".join(html_parts)

    st.markdown(html, unsafe_allow_html=True)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
