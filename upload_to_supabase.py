"""
upload_to_supabase.py
═══════════════════════════════════════════════════════════════
Reads the 3 local CSV files, cleans them, and uploads the data
to Supabase using the supabase-py client library.

Usage:
    1. pip install supabase pandas python-dotenv
    2. Create a .env file (see instructions at the bottom of this file)
       OR simply paste your credentials in the CONFIG section below.
    3. python upload_to_supabase.py
═══════════════════════════════════════════════════════════════
"""

import os
import math
import pandas as pd
from pathlib import Path
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# ─── Configuration ────────────────────────────────────────────
load_dotenv()  # loads from .env file if present

SUPABASE_URL = os.environ.get("SUPABASE_URL", "YOUR_SUPABASE_PROJECT_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "YOUR_SUPABASE_SERVICE_ROLE_KEY")

# Paths to the CSV files (relative to this script)
BASE_DIR = Path(__file__).parent
NATIONAL_CSV = BASE_DIR / "Sri_Lanka_Tourist_Forecast_Training_Dataset_2015_2025.csv"
KANDY_WEEKLY_CSV = BASE_DIR / "kandy_festival_demand_NOMISSING.csv"
WEATHER_CSV = BASE_DIR / "Kandy_Weather_Dataset_Extended.csv"

BATCH_SIZE = 200  # Number of rows to upsert at once


# ─── Helper Functions ─────────────────────────────────────────
def sanitize(val):
    """Replace NaN / Inf with None so Supabase accepts the JSON."""
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return val


def clean_row(row: dict) -> dict:
    """Apply sanitize() to every value in a row dictionary."""
    return {k: sanitize(v) for k, v in row.items()}


def batch_upsert(supabase: Client, table: str, records: list[dict], conflict_col: str):
    """Upsert records in batches, printing progress."""
    total = len(records)
    print(f"\n  Uploading {total} rows to '{table}' …")
    for i in range(0, total, BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        supabase.table(table).upsert(batch, on_conflict=conflict_col).execute()
        print(f"    ✔  {min(i + BATCH_SIZE, total)}/{total} rows done", end="\r")
    print(f"\n  ✅ '{table}' upload complete.")


# ─── Dataset 1: National Tourism ──────────────────────────────
def upload_national_tourism(supabase: Client):
    print("\n📂 Processing national tourism dataset …")
    df = pd.read_csv(NATIONAL_CSV, encoding="utf-8", on_bad_lines="skip")

    # Normalise column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Define ONLY the columns that exist in your Supabase Table
    # If you add more columns to Supabase later, add their names to this list
    db_columns = [
        "year", "month", "tourist_arrivals", "india_arrivals", "uk_arrivals",
        "russia_arrivals", "germany_arrivals", "china_arrivals", "other_arrivals",
        "visa_applications", "visa_approvals",
        "covid_impact", "easter_attack_impact", "economic_crisis_impact"
    ]

    # Filter the DataFrame to only include columns that are actually in the DB
    existing_cols = [c for c in db_columns if c in df.columns]
    df_filtered = df[existing_cols].copy()

    # Drop duplicates
    df_filtered = df_filtered.drop_duplicates(subset=["year", "month"])

    # Cast integer columns safely
    for col in existing_cols:
        df_filtered[col] = pd.to_numeric(df_filtered[col], errors="coerce").astype("Int64")

    # Clean and upload
    records = [clean_row(r) for r in df_filtered.to_dict(orient="records")]
    batch_upsert(supabase, "national_tourism", records, "year,month")


# ─── Dataset 2: Kandy Weekly Data ─────────────────────────────
def upload_kandy_weekly(supabase: Client):
    print("\n📂 Processing Kandy weekly festival/demand dataset …")
    df = pd.read_csv(KANDY_WEEKLY_CSV, encoding="utf-8", on_bad_lines="skip")

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Parse date columns
    df["week_start"] = pd.to_datetime(df["week_start"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["week_end"] = pd.to_datetime(df["week_end"], errors="coerce").dt.strftime("%Y-%m-%d")

    # Drop rows where week_start is null (can't upsert without the key)
    df = df.dropna(subset=["week_start"])
    df = df.drop_duplicates(subset=["week_start"])

    # Integer / float coercions
    int_cols = [
        "year", "month", "week_of_year", "quarter",
        "festival_intensity_score",
        "is_esala_perahera", "is_esala_preparation", "is_esala_post_festival",
        "is_august_buildup", "is_poson_perahera", "is_vesak",
        "is_sinhala_tamil_new_year", "is_christmas_new_year",
        "is_deepavali", "is_thai_pongal", "is_monthly_poya_week",
        "poya_days_away", "is_school_holiday", "is_any_festival",
        "days_until_next_esala", "avg_weekly_rainfall_mm", "avg_humidity_pct",
        "is_monsoon_week", "is_covid_period", "is_easter_attack_period",
        "is_economic_crisis", "is_normal_operation",
        "estimated_weekly_kandy_arrivals",
    ]
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    float_cols = ["festival_demand_multiplier", "avg_temp_celsius"]
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    records = [clean_row(r) for r in df.to_dict(orient="records")]
    batch_upsert(supabase, "kandy_weekly_data", records, "week_start")


# ─── Dataset 3: Kandy Weather (Daily) ─────────────────────────
def upload_kandy_weather(supabase: Client):
    print("\n📂 Processing Kandy daily weather dataset …")
    df = pd.read_csv(WEATHER_CSV, encoding="utf-8", on_bad_lines="skip")

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # The date column is called 'time'
    df["time"] = pd.to_datetime(df["time"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.dropna(subset=["time"])
    df = df.drop_duplicates(subset=["time"])

    # Numeric coercions
    float_cols = [
        "temperature_2m_max", "temperature_2m_min", "temperature_2m_mean",
        "apparent_temperature_max", "apparent_temperature_min", "apparent_temperature_mean",
        "shortwave_radiation_sum", "precipitation_sum", "rain_sum", "snowfall_sum",
        "precipitation_hours", "windspeed_10m_max", "windgusts_10m_max",
        "winddirection_10m_dominant", "et0_fao_evapotranspiration",
        "elevation", "latitude", "longitude",
    ]
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    int_cols = ["weathercode"]
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    records = [clean_row(r) for r in df.to_dict(orient="records")]
    batch_upsert(supabase, "kandy_weather_daily", records, "time")


# ─── Main ─────────────────────────────────────────────────────
def main():
    if SUPABASE_URL == "YOUR_SUPABASE_PROJECT_URL":
        print("❌  Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in your .env file first!")
        return

    print("🚀 Connecting to Supabase …")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print("   Connected ✅")

    upload_national_tourism(supabase)
    upload_kandy_weekly(supabase)
    upload_kandy_weather(supabase)

    print("\n\n🎉 All datasets uploaded successfully to Supabase!")
    print(f"   Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()


# ─── .env file template ───────────────────────────────────────
# Create a file called  .env  in the same folder as this script
# and paste the following (replace with your real values):
#
#   SUPABASE_URL=https://xxxxxxxxxxxxxxxxxxxx.supabase.co
#   SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
#
# Find these in: Supabase Dashboard → Project Settings → API
#   • Project URL  → SUPABASE_URL
#   • service_role (secret) key → SUPABASE_SERVICE_KEY
#   ⚠️  Use the service_role key (not the anon key) for uploads!
