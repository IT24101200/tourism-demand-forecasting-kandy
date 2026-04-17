"""
utils/db.py
══════════════════════════════════════════════
Shared Supabase client and data-fetching helpers
used by both the training pipeline and Streamlit.
Credential priority:
  1. Streamlit secrets (st.secrets) — cloud deployment
  2. .env file / environment variables — local dev
══════════════════════════════════════════════
"""

import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_client: Client | None = None


def _get_secret(key: str) -> str:
    """Read a secret from Streamlit secrets (cloud) or env vars (local)."""
    try:
        import streamlit as st
        return st.secrets.get(key, os.environ.get(key, ""))
    except Exception:
        return os.environ.get(key, "")


def get_client() -> Client:
    """Return a cached Supabase client (anon key – read access)."""
    global _client
    if _client is None:
        url = _get_secret("SUPABASE_URL")
        key = _get_secret("SUPABASE_ANON_KEY")
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_ANON_KEY must be set "
                "in .env or Streamlit secrets."
            )
        _client = create_client(url, key)
    return _client


def get_service_client() -> Client:
    """Return a Supabase client using the service-role key (write access)."""
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in your .env file."
        )
    return create_client(url, key)


# ── Fetch helpers ─────────────────────────────────────────────

def fetch_national_tourism() -> pd.DataFrame:
    """Fetch all rows from national_tourism, return as DataFrame."""
    try:
        sb = get_client()
        resp = sb.table("national_tourism").select("*").order("year,month").execute()
        return pd.DataFrame(resp.data)
    except Exception:
        import streamlit as st
        st.error("Database connection failed.")
        return pd.DataFrame()


def fetch_kandy_weekly() -> pd.DataFrame:
    """Fetch all rows from kandy_weekly_data, sorted by week_start."""
    try:
        sb = get_client()
        resp = (
            sb.table("kandy_weekly_data")
            .select("*")
            .order("week_start")
            .execute()
        )
        return pd.DataFrame(resp.data)
    except Exception:
        import streamlit as st
        st.error("Database connection failed.")
        return pd.DataFrame()


def fetch_predictions(model: str | None = None) -> pd.DataFrame:
    """Fetch predictions, optionally filtered by model_name."""
    try:
        sb = get_client()
        q = sb.table("predictions").select("*").order("week_start")
        if model:
            q = q.eq("model_name", model)
        resp = q.execute()
        return pd.DataFrame(resp.data)
    except Exception:
        import streamlit as st
        st.error("Database connection failed.")
        return pd.DataFrame()


def fetch_weather_daily() -> pd.DataFrame:
    """Fetch all rows from kandy_weather_daily."""
    try:
        sb = get_client()
        resp = (
            sb.table("kandy_weather_daily")
            .select("*")
            .order("time")
            .execute()
        )
        return pd.DataFrame(resp.data)
    except Exception:
        import streamlit as st
        st.error("Database connection failed.")
        return pd.DataFrame()
