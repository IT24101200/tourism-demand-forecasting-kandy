"""
app.py  —  Tourist Demand Forecasting & Decision Support System
Streamlit multipage entry point / Home redirect
"""

import streamlit as st
from pathlib import Path
from utils.sidebar import render_sidebar
from utils.auth import require_auth

from utils.theme import apply_custom_theme

st.set_page_config(
    page_title="Kandy Tourist Forecast DSS",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_theme()
require_auth()

# Redirect visitors to the Home page
st.switch_page("pages/1_🏠_National_Overview.py")
