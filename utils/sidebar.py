"""
utils/sidebar.py  —  Shared sidebar for all Streamlit pages.
Call render_sidebar(active_page="National Overview") at the top of each page.
"""

import streamlit as st
from utils.auth import logout_button
from utils.theme import apply_custom_theme, get_theme

_NAV_PAGES = [
    ("🏠",  "National Overview",   "pages/1_🏠_National_Overview.py"),
    ("📈",  "Live Demand",         "pages/2__Live_Demand.py"),
    ("🎛️", "What-If Simulator",  "pages/3_🎛️_What_If_Simulator.py"),
    ("🏨",  "Resource Planner",    "pages/4_🏨_Resource_Planner.py"),
    ("🌦️", "Weather Impact",      "pages/5_🌦️_Weather_Impact.py"),
    ("🐘",  "Festival Forecaster", "pages/6_🐘_Festival_Forecaster.py"),
    ("📊",  "Report Generator",    "pages/7_📊_Report_Generator.py"),
    ("👤",  "Profile Management",  "pages/8_👤_Profile.py"),
]

def get_sidebar_css(theme):
    return f"""
<style>
/* ── Hide Streamlit's auto-generated top navigation ── */
[data-testid="stSidebarNav"] {{ display: none !important; }}

/* ── Sidebar background ── */
section[data-testid="stSidebar"] {{
    background: {theme['surface_glass']} !important;
    backdrop-filter: blur(24px) !important;
    border-right: 1px solid {theme['border']} !important;
}}
section[data-testid="stSidebar"] > div:first-child {{
    padding-top: 0 !important;
}}

/* ── Brand block ── */
.sb-brand {{
    display: flex; align-items: center; gap: 12px;
    padding: 22px 18px 18px;
    border-bottom: 1px solid {theme['border']};
    margin-bottom: 8px;
}}
.sb-icon {{
    width: 40px; height: 40px; border-radius: 11px; flex-shrink: 0;
    background: linear-gradient(135deg, {theme['surface_low']} 0%, {theme['surface_high']} 100%);
    border: 1px solid {theme['border']};
    box-shadow: inset 0 0 12px rgba(56,189,248,0.1);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.25rem;
}}
.sb-title {{ color: {theme['text_main']}; font-size: 0.95rem; font-family: 'Manrope', sans-serif; font-weight: 700; line-height: 1.2; }}
.sb-sub   {{ color: {theme['text_dim']}; font-size: 0.62rem; font-weight: 600; font-family: 'Inter', sans-serif;
            letter-spacing: 0.1em; text-transform: uppercase; }}

/* ── Section label ── */
.sb-label {{
    color: {theme['text_dim']}; font-size: 0.63rem; font-weight: 700; font-family: 'Inter', sans-serif;
    letter-spacing: 0.12em; text-transform: uppercase;
    padding: 14px 18px 8px; margin: 0;
}}

/* ── Active nav item (Light Pipe Style) ── */
.sb-active {{
    display: flex; align-items: center; gap: 12px;
    padding: 12px 18px; margin: 4px 14px;
    background: {theme['surface_low']};
    border-left: 3px solid {theme['accent_dim']};
    border-radius: 0 8px 8px 0;
    color: {theme['accent']}; font-size: 0.95rem; font-weight: 700; font-family: 'Inter', sans-serif;
    cursor: default;
}}

/* ── Inactive nav items — target the st.page_link anchor ── */
[data-testid="stPageLink"] {{
    margin: 4px 14px !important;
}}
[data-testid="stPageLink"] a {{
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    padding: 12px 18px !important;
    border-radius: 8px !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    color: {theme['text_muted']} !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
    text-decoration: none !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}}
[data-testid="stPageLink"] a:hover {{
    background: {theme['surface_high']} !important;
    color: {theme['text_main']} !important;
}}

/* ── Divider ── */
.sb-hr {{ border-top: 1px solid {theme['border']}; margin: 10px 14px; }}

/* ── Status row ── */
.sb-status {{
    display: flex; align-items: center; gap: 8px;
    padding: 8px 18px 4px;
    color: {theme['text_muted']}; font-size: 0.72rem;
}}
.sb-dot {{
    width: 7px; height: 7px; border-radius: 50%;
    background: {theme['accent2_dim']}; box-shadow: 0 0 6px {theme['accent2_dim']};
    flex-shrink: 0;
}}

/* ── Footer info ── */
.sb-footer {{
    padding: 4px 18px 14px;
    color: {theme['text_muted']}; font-size: 0.71rem; line-height: 1.65;
}}
.sb-badge {{
    display: inline-block; background: {theme['surface_low']};
    color: {theme['accent']}; border: 1px solid {theme['border']};
    border-radius: 6px; padding: 2px 9px;
    font-size: 0.67rem; font-weight: 600;
    letter-spacing: 0.05em; margin-top: 5px;
}}
</style>
"""


def render_sidebar(active_page: str = "", extra_content=None):
    """
    Render the shared sidebar.

    Parameters
    ----------
    active_page : str
        Label matching one of the nav items (e.g. "National Overview").
        That item is highlighted; others render as clickable st.page_link.
    extra_content : callable | None
        Optional callable for page-specific widgets (sliders, radios, etc.).
    """
    theme = get_theme()
    apply_custom_theme()
    st.markdown(get_sidebar_css(theme), unsafe_allow_html=True)
    
    with st.sidebar:
        # ── Brand ─────────────────────────────────────────────
        st.markdown("""
        <div class="sb-brand">
            <div class="sb-icon">🏔️</div>
            <div>
                <div class="sb-title">Kandy Tourism DSS</div>
                <div class="sb-sub">AI Demand Forecasting</div>
            </div>
        </div>""", unsafe_allow_html=True)

        # ── Navigation ─────────────────────────────────────────
        st.markdown('<div class="sb-label">Navigation</div>', unsafe_allow_html=True)

        for icon, label, path in _NAV_PAGES:
            if label.lower() == active_page.lower():
                # Active page: styled div (no link needed — already here)
                st.markdown(
                    f'<div class="sb-active">{icon}&nbsp;&nbsp;{label}</div>',
                    unsafe_allow_html=True,
                )
            else:
                # Inactive: real clickable Streamlit page link (styled via CSS)
                st.page_link(path, label=label, icon=icon)

        # ── Divider ────────────────────────────────────────────
        st.markdown('<div class="sb-hr"></div>', unsafe_allow_html=True)

        # ── Page-specific content (filters, settings, etc.) ────
        if extra_content:
            extra_content()
            st.markdown('<div class="sb-hr"></div>', unsafe_allow_html=True)

        # ── Footer ─────────────────────────────────────────────
        st.markdown("""
        <div class="sb-status">
            <div class="sb-dot"></div>
            <span>Live · Kandy District, Sri Lanka</span>
        </div>
        <div class="sb-footer">
            Tourist Demand Forecasting<br>&amp; Decision Support System<br>
            <span class="sb-badge">v1.0.0 · 2026</span>
        </div>""", unsafe_allow_html=True)
        
        # ── Theme Toggle ───────────────────────────────────────
        st.markdown('<div class="sb-hr"></div>', unsafe_allow_html=True)
        def toggle_theme():
            if st.session_state.theme == "dark":
                st.session_state.theme = "light"
            else:
                st.session_state.theme = "dark"
                
        is_dark = st.session_state.get("theme", "dark") == "dark"
        st.toggle(
            "🌙 Dark Mode" if is_dark else "🌞 Light Mode",
            value=is_dark,
            on_change=toggle_theme,
            key="theme_toggle_widget"
        )
        
        # ── Logout Button ──────────────────────────────────────
        logout_button()
