-- ============================================================
--  Tourist Demand Forecasting DSS — Supabase Schema
--  Run this entire script in: Supabase → SQL Editor → New Query
-- ============================================================

-- ─────────────────────────────────────────────────────────────
--  TABLE 1: national_tourism
--  Source: Sri_Lanka_Tourist_Forecast_Training_Dataset_2015_2025.csv
-- ─────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS national_tourism CASCADE;

CREATE TABLE national_tourism (
    id                          SERIAL PRIMARY KEY,
    year                        INTEGER NOT NULL,
    month                       INTEGER NOT NULL,
    month_name                  TEXT,
    tourist_arrivals            INTEGER,
    season                      TEXT,
    demand_level                TEXT,
    event_impact                TEXT,
    india_arrivals              INTEGER,
    uk_arrivals                 INTEGER,
    russia_arrivals             INTEGER,
    germany_arrivals            INTEGER,
    china_arrivals              INTEGER,
    other_arrivals              INTEGER,
    -- additional numeric columns from the CSV
    avg_length_of_stay_days     NUMERIC,
    revenue_usd_millions        NUMERIC,
    hotel_occupancy_rate_pct    NUMERIC,
    gdp_contribution_usd_millions NUMERIC,
    tourism_employment_thousands  NUMERIC,
    avg_spend_per_tourist_usd   NUMERIC,
    marketing_spend_usd_millions NUMERIC,
    visa_applications           INTEGER,
    visa_approvals              INTEGER,
    visa_approval_rate_pct      NUMERIC,
    online_search_index         NUMERIC,
    air_connectivity_index      NUMERIC,
    political_stability_index   NUMERIC,
    infrastructure_quality_index NUMERIC,
    exchange_rate_lkr_usd       NUMERIC,
    inflation_rate_pct          NUMERIC,
    competitive_dest_index      NUMERIC,
    covid_impact                INTEGER,
    easter_attack_impact        INTEGER,
    economic_crisis_impact      INTEGER,
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(year, month)
);

-- ─────────────────────────────────────────────────────────────
--  TABLE 2: kandy_weekly_data
--  Source: kandy_festival_demand_NOMISSING.csv
-- ─────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS kandy_weekly_data CASCADE;

CREATE TABLE kandy_weekly_data (
    id                              SERIAL PRIMARY KEY,
    week_start                      DATE NOT NULL,
    week_end                        DATE NOT NULL,
    year                            INTEGER,
    month                           INTEGER,
    week_of_year                    INTEGER,
    quarter                         INTEGER,
    primary_festival                TEXT,
    festival_intensity_score        INTEGER,
    festival_demand_multiplier      NUMERIC,
    is_esala_perahera               SMALLINT DEFAULT 0,
    is_esala_preparation            SMALLINT DEFAULT 0,
    is_esala_post_festival          SMALLINT DEFAULT 0,
    is_august_buildup               SMALLINT DEFAULT 0,
    is_poson_perahera               SMALLINT DEFAULT 0,
    is_vesak                        SMALLINT DEFAULT 0,
    is_sinhala_tamil_new_year       SMALLINT DEFAULT 0,
    is_christmas_new_year           SMALLINT DEFAULT 0,
    is_deepavali                    SMALLINT DEFAULT 0,
    is_thai_pongal                  SMALLINT DEFAULT 0,
    is_monthly_poya_week            SMALLINT DEFAULT 0,
    poya_days_away                  INTEGER,
    is_school_holiday               SMALLINT DEFAULT 0,
    is_any_festival                 SMALLINT DEFAULT 0,
    days_until_next_esala           INTEGER,
    weather_season                  TEXT,
    avg_weekly_rainfall_mm          NUMERIC,
    avg_temp_celsius                NUMERIC,
    avg_humidity_pct                NUMERIC,
    is_monsoon_week                 SMALLINT DEFAULT 0,
    weather_impact_on_tourism       TEXT,
    crisis_event                    TEXT,
    is_covid_period                 SMALLINT DEFAULT 0,
    is_easter_attack_period         SMALLINT DEFAULT 0,
    is_economic_crisis              SMALLINT DEFAULT 0,
    is_normal_operation             SMALLINT DEFAULT 0,
    estimated_weekly_kandy_arrivals INTEGER,
    created_at                      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(week_start)
);

-- ─────────────────────────────────────────────────────────────
--  TABLE 3: kandy_weather_daily
--  Source: Kandy_Weather_Dataset_Extended.csv
-- ─────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS kandy_weather_daily CASCADE;

CREATE TABLE kandy_weather_daily (
    id                          SERIAL PRIMARY KEY,
    time                        DATE NOT NULL UNIQUE,
    weathercode                 INTEGER,
    temperature_2m_max          NUMERIC,
    temperature_2m_min          NUMERIC,
    temperature_2m_mean         NUMERIC,
    apparent_temperature_max    NUMERIC,
    apparent_temperature_min    NUMERIC,
    apparent_temperature_mean   NUMERIC,
    sunrise                     TEXT,
    sunset                      TEXT,
    shortwave_radiation_sum     NUMERIC,
    precipitation_sum           NUMERIC,
    rain_sum                    NUMERIC,
    snowfall_sum                NUMERIC,
    precipitation_hours         NUMERIC,
    windspeed_10m_max           NUMERIC,
    windgusts_10m_max           NUMERIC,
    winddirection_10m_dominant  NUMERIC,
    et0_fao_evapotranspiration  NUMERIC,
    elevation                   NUMERIC,
    country                     TEXT,
    city                        TEXT,
    latitude                    NUMERIC,
    longitude                   NUMERIC,
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────
--  TABLE 4: predictions
--  Stores ML-generated forecasts pushed back from Python
-- ─────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS predictions CASCADE;

CREATE TABLE predictions (
    id                          SERIAL PRIMARY KEY,
    week_start                  DATE NOT NULL,
    week_end                    DATE,
    model_name                  TEXT NOT NULL,          -- 'random_forest' | 'lstm'
    predicted_arrivals          INTEGER,
    lower_bound                 INTEGER,
    upper_bound                 INTEGER,
    confidence_level            NUMERIC DEFAULT 0.95,
    features_used               JSONB,                 -- snapshot of input features
    is_future                   BOOLEAN DEFAULT TRUE,  -- FALSE = back-test on historic data
    generated_at                TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(week_start, model_name)
);

-- ─────────────────────────────────────────────────────────────
--  Row-Level Security (optional but recommended)
--  Enable below if you want public read access via anon key
-- ─────────────────────────────────────────────────────────────
-- ALTER TABLE national_tourism ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Allow public read" ON national_tourism FOR SELECT USING (true);
-- ALTER TABLE kandy_weekly_data ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Allow public read" ON kandy_weekly_data FOR SELECT USING (true);
-- ALTER TABLE kandy_weather_daily ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Allow public read" ON kandy_weather_daily FOR SELECT USING (true);
-- ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Allow public read" ON predictions FOR SELECT USING (true);

-- Done! ✅
SELECT 'Schema created successfully!' AS status;
