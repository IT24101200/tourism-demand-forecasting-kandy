# 📙 README 2: Database Documentation

## 1. Database Overview

### 1.1 Database Type
**Supabase (Hosted PostgreSQL)** — A cloud-hosted PostgreSQL database accessed via the Supabase REST API using the `supabase-py` Python client library.

### 1.2 Connection Architecture
The system uses two levels of database access:

| Client Type | Key Used | Purpose | Code Location |
|-------------|----------|---------|---------------|
| **Anon Client** | `SUPABASE_ANON_KEY` | Read-only access for all Streamlit pages | `utils/db.py:31-43` → `get_client()` |
| **Service Client** | `SUPABASE_SERVICE_KEY` | Full read/write/delete access for admin and training pipeline | `utils/db.py:46-54` → `get_service_client()` |

### 1.3 Credential Priority
1. **Streamlit Secrets** (`st.secrets`) — Used in cloud deployment (Streamlit Community Cloud)
2. **Environment Variables** (`.env` file) — Used in local development
3. Fallback function: `_get_secret()` in `utils/db.py:22-28`

### 1.4 General Structure
```
Supabase PostgreSQL
├── public.national_tourism          (Monthly national stats)
├── public.kandy_weekly_data         (Weekly Kandy demand + festivals + weather)
├── public.kandy_weather_daily       (Daily weather observations)
├── public.predictions               (ML-generated forecasts)
├── public.user_profiles             (User account metadata)
└── auth.users                       (Supabase built-in auth table)
```

---

## 2. Tables Description

### 2.1 Table: `national_tourism`

**Purpose:** Stores monthly national-level tourism statistics for all of Sri Lanka (2015–2025). Primary data source for the National Overview dashboard.

**Source CSV:** `Sri_Lanka_Tourist_Forecast_Training_Dataset_2015_2025.csv`

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| `id` | `SERIAL` | NO | Auto-increment primary key |
| `year` | `INTEGER` | NO | Calendar year |
| `month` | `INTEGER` | NO | Month number (1-12) |
| `month_name` | `TEXT` | YES | Month name (e.g., "January") |
| `tourist_arrivals` | `INTEGER` | YES | Total tourist arrivals for the month |
| `season` | `TEXT` | YES | Season classification |
| `demand_level` | `TEXT` | YES | Demand level category |
| `event_impact` | `TEXT` | YES | Notable event impact descriptor |
| `india_arrivals` | `INTEGER` | YES | Arrivals from India |
| `uk_arrivals` | `INTEGER` | YES | Arrivals from United Kingdom |
| `russia_arrivals` | `INTEGER` | YES | Arrivals from Russia |
| `germany_arrivals` | `INTEGER` | YES | Arrivals from Germany |
| `china_arrivals` | `INTEGER` | YES | Arrivals from China |
| `other_arrivals` | `INTEGER` | YES | Arrivals from other countries |
| `avg_length_of_stay_days` | `NUMERIC` | YES | Average tourist stay duration |
| `revenue_usd_millions` | `NUMERIC` | YES | Tourism revenue in USD millions |
| `hotel_occupancy_rate_pct` | `NUMERIC` | YES | Average hotel occupancy rate (%) |
| `gdp_contribution_usd_millions` | `NUMERIC` | YES | Tourism GDP contribution |
| `tourism_employment_thousands` | `NUMERIC` | YES | Tourism sector employment |
| `avg_spend_per_tourist_usd` | `NUMERIC` | YES | Average spending per tourist |
| `marketing_spend_usd_millions` | `NUMERIC` | YES | Government tourism marketing spend |
| `visa_applications` | `INTEGER` | YES | Total visa applications |
| `visa_approvals` | `INTEGER` | YES | Total visa approvals |
| `visa_approval_rate_pct` | `NUMERIC` | YES | Visa approval percentage |
| `online_search_index` | `NUMERIC` | YES | Online search interest index |
| `air_connectivity_index` | `NUMERIC` | YES | Air connectivity score |
| `political_stability_index` | `NUMERIC` | YES | Political stability metric |
| `infrastructure_quality_index` | `NUMERIC` | YES | Infrastructure quality score |
| `exchange_rate_lkr_usd` | `NUMERIC` | YES | LKR to USD exchange rate |
| `inflation_rate_pct` | `NUMERIC` | YES | Monthly inflation rate |
| `competitive_dest_index` | `NUMERIC` | YES | Competitive destination index |
| `covid_impact` | `INTEGER` | YES | COVID-19 impact flag (0/1) |
| `easter_attack_impact` | `INTEGER` | YES | Easter attack impact flag (0/1) |
| `economic_crisis_impact` | `INTEGER` | YES | Economic crisis impact flag (0/1) |
| `created_at` | `TIMESTAMPTZ` | NO | Row creation timestamp (auto) |

**Primary Key:** `id`
**Unique Constraint:** `(year, month)`

---

### 2.2 Table: `kandy_weekly_data`

**Purpose:** Stores weekly-level historical demand data for Kandy District, enriched with festival indicators, weather averages, and crisis flags. This is the **primary training dataset** for the ML models.

**Source CSV:** `kandy_festival_demand_NOMISSING.csv`

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| `id` | `SERIAL` | NO | Auto-increment primary key |
| `week_start` | `DATE` | NO | Start date of the week (Monday) |
| `week_end` | `DATE` | NO | End date of the week (Sunday) |
| `year` | `INTEGER` | YES | Calendar year |
| `month` | `INTEGER` | YES | Month number |
| `week_of_year` | `INTEGER` | YES | ISO week number |
| `quarter` | `INTEGER` | YES | Calendar quarter (1-4) |
| `primary_festival` | `TEXT` | YES | Dominant festival name or "Normal" |
| `festival_intensity_score` | `INTEGER` | YES | Festival intensity (1-10 scale) |
| `festival_demand_multiplier` | `NUMERIC` | YES | Demand multiplier (1.0 = normal) |
| `is_esala_perahera` | `SMALLINT` | YES | Esala Perahera week flag (0/1) |
| `is_esala_preparation` | `SMALLINT` | YES | Esala preparation week flag |
| `is_esala_post_festival` | `SMALLINT` | YES | Post-Esala week flag |
| `is_august_buildup` | `SMALLINT` | YES | August buildup flag |
| `is_poson_perahera` | `SMALLINT` | YES | Poson Perahera flag |
| `is_vesak` | `SMALLINT` | YES | Vesak week flag |
| `is_sinhala_tamil_new_year` | `SMALLINT` | YES | Sinhala/Tamil New Year flag |
| `is_christmas_new_year` | `SMALLINT` | YES | Christmas/New Year flag |
| `is_deepavali` | `SMALLINT` | YES | Deepavali week flag |
| `is_thai_pongal` | `SMALLINT` | YES | Thai Pongal flag |
| `is_monthly_poya_week` | `SMALLINT` | YES | Monthly Poya day flag |
| `poya_days_away` | `INTEGER` | YES | Days until next Poya day |
| `is_school_holiday` | `SMALLINT` | YES | School holiday period flag |
| `is_any_festival` | `SMALLINT` | YES | Any festival active flag |
| `days_until_next_esala` | `INTEGER` | YES | Days until next Esala Perahera |
| `weather_season` | `TEXT` | YES | Weather season classification |
| `avg_weekly_rainfall_mm` | `NUMERIC` | YES | Average weekly rainfall (mm) |
| `avg_temp_celsius` | `NUMERIC` | YES | Average temperature (°C) |
| `avg_humidity_pct` | `NUMERIC` | YES | Average humidity (%) |
| `is_monsoon_week` | `SMALLINT` | YES | Monsoon period flag |
| `weather_impact_on_tourism` | `TEXT` | YES | Weather impact descriptor |
| `crisis_event` | `TEXT` | YES | Active crisis event name |
| `is_covid_period` | `SMALLINT` | YES | COVID-19 period flag |
| `is_easter_attack_period` | `SMALLINT` | YES | Easter attack period flag |
| `is_economic_crisis` | `SMALLINT` | YES | Economic crisis flag |
| `is_normal_operation` | `SMALLINT` | YES | Normal operations flag |
| `estimated_weekly_kandy_arrivals` | `INTEGER` | YES | **TARGET VARIABLE** — weekly arrivals |
| `created_at` | `TIMESTAMPTZ` | NO | Row creation timestamp (auto) |

**Primary Key:** `id`
**Unique Constraint:** `(week_start)`

---

### 2.3 Table: `kandy_weather_daily`

**Purpose:** Stores daily weather observations for Kandy City from Open-Meteo historical data. Used for weather-tourism correlation analysis.

**Source CSV:** `Kandy_Weather_Dataset_Extended.csv`

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| `id` | `SERIAL` | NO | Auto-increment primary key |
| `time` | `DATE` | NO | Observation date |
| `weathercode` | `INTEGER` | YES | WMO weather code |
| `temperature_2m_max` | `NUMERIC` | YES | Max temperature at 2m (°C) |
| `temperature_2m_min` | `NUMERIC` | YES | Min temperature at 2m (°C) |
| `temperature_2m_mean` | `NUMERIC` | YES | Mean temperature at 2m (°C) |
| `apparent_temperature_max` | `NUMERIC` | YES | Max apparent temperature (°C) |
| `apparent_temperature_min` | `NUMERIC` | YES | Min apparent temperature (°C) |
| `apparent_temperature_mean` | `NUMERIC` | YES | Mean apparent temperature (°C) |
| `sunrise` | `TEXT` | YES | Sunrise time (ISO format) |
| `sunset` | `TEXT` | YES | Sunset time (ISO format) |
| `shortwave_radiation_sum` | `NUMERIC` | YES | Solar radiation total (MJ/m²) |
| `precipitation_sum` | `NUMERIC` | YES | Total precipitation (mm) |
| `rain_sum` | `NUMERIC` | YES | Total rain (mm) |
| `snowfall_sum` | `NUMERIC` | YES | Total snowfall (cm) |
| `precipitation_hours` | `NUMERIC` | YES | Hours with precipitation |
| `windspeed_10m_max` | `NUMERIC` | YES | Max wind speed at 10m (km/h) |
| `windgusts_10m_max` | `NUMERIC` | YES | Max wind gusts at 10m (km/h) |
| `winddirection_10m_dominant` | `NUMERIC` | YES | Dominant wind direction (°) |
| `et0_fao_evapotranspiration` | `NUMERIC` | YES | Evapotranspiration (mm) |
| `elevation` | `NUMERIC` | YES | Station elevation (m) |
| `country` | `TEXT` | YES | Country name |
| `city` | `TEXT` | YES | City name |
| `latitude` | `NUMERIC` | YES | Station latitude |
| `longitude` | `NUMERIC` | YES | Station longitude |
| `created_at` | `TIMESTAMPTZ` | NO | Row creation timestamp (auto) |

**Primary Key:** `id`
**Unique Constraint:** `(time)`

---

### 2.4 Table: `predictions`

**Purpose:** Stores ML-generated weekly tourist arrival forecasts from both XGBoost and LSTM models. Written by `train_models.py` and read by all forecasting dashboards.

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| `id` | `SERIAL` | NO | Auto-increment primary key |
| `week_start` | `DATE` | NO | Forecast week start date |
| `week_end` | `DATE` | YES | Forecast week end date |
| `model_name` | `TEXT` | NO | Model identifier: `'xgboost'` or `'lstm'` |
| `predicted_arrivals` | `INTEGER` | YES | Predicted tourist arrivals |
| `lower_bound` | `INTEGER` | YES | 95% CI lower bound |
| `upper_bound` | `INTEGER` | YES | 95% CI upper bound |
| `confidence_level` | `NUMERIC` | YES | Confidence level (default 0.95) |
| `features_used` | `JSONB` | YES | Snapshot of input features as JSON |
| `is_future` | `BOOLEAN` | YES | TRUE = future prediction; FALSE = back-test |
| `generated_at` | `TIMESTAMPTZ` | NO | Prediction generation timestamp (auto) |

**Primary Key:** `id`
**Unique Constraint:** `(week_start, model_name)` — ensures one prediction per model per week; upserts overwrite on retrain.

---

### 2.5 Table: `user_profiles`

**Purpose:** Stores user account metadata linked to Supabase Auth. Created automatically via database trigger on user signup.

**Schema File:** `sql/02_auth_schema.sql`

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| `id` | `UUID` | NO | Primary key — references `auth.users(id)` |
| `email` | `TEXT` | NO | User email address |
| `full_name` | `TEXT` | YES | User's display name |
| `role` | `TEXT` | YES | System role (constrained) |
| `hotel_name` | `TEXT` | YES | User's hotel or organization |
| `created_at` | `TIMESTAMPTZ` | NO | Account creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | NO | Last update timestamp |

**Primary Key:** `id` (UUID)
**Foreign Key:** `id` → `auth.users(id) ON DELETE CASCADE`
**Check Constraint:** `role IN ('Hotel Manager', 'Tour Operator', 'Government Official', 'Other', 'System Administrator')`

**Row Level Security (RLS) Policies:**
| Policy Name | Operation | Rule |
|-------------|-----------|------|
| `Users can view own profile` | SELECT | `auth.uid() = id` |
| `Users can update own profile` | UPDATE | `auth.uid() = id` |
| `System Administrators can manage all profiles` | ALL | `(SELECT role FROM user_profiles WHERE id = auth.uid()) = 'System Administrator'` |

**Auto-Creation Trigger:**
```sql
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();
```
The `handle_new_user()` function extracts `full_name`, `role`, and `hotel_name` from `raw_user_meta_data` and inserts a new row into `user_profiles`.

---

## 3. Table Relationships

### 3.1 Entity-Relationship Diagram

```
auth.users (Supabase built-in)
    │
    │ 1:1 (ON DELETE CASCADE)
    ▼
user_profiles
    (id UUID → auth.users.id)


national_tourism ←── No FK relationship ──→ kandy_weekly_data
    (Monthly national)                       (Weekly Kandy)
                                                │
                                                │ Logical link via
                                                │ week_start dates
                                                ▼
                                            predictions
                                            (week_start + model_name)


kandy_weather_daily ←── Logical link via date ──→ kandy_weekly_data
    (Daily granularity)                           (Weekly granularity)
```

### 3.2 Relationship Types

| Relationship | Type | Description |
|-------------|------|-------------|
| `auth.users` → `user_profiles` | **1:1** | Each auth user has exactly one profile. CASCADE delete removes profile when user is deleted. |
| `kandy_weekly_data` → `predictions` | **Logical (no FK)** | Predictions extend future weeks beyond the historical `kandy_weekly_data` date range. Linked by `week_start` date values. |
| `kandy_weather_daily` → `kandy_weekly_data` | **Logical (no FK)** | Daily weather data is aggregated to weekly averages stored in `kandy_weekly_data`. No foreign key enforced. |
| `national_tourism` → `kandy_weekly_data` | **None** | Separate datasets at different granularities (monthly vs weekly). No direct relationship. |

---

## 4. UI ↔ Database Mapping

### 4.1 Per-Component Mapping

| UI Page | Tables Used | Reads | Inserts | Updates | Deletes |
|---------|------------|-------|---------|---------|---------|
| **National Overview** | `national_tourism`, `predictions` | ✅ All national stats, current/next week predictions | ❌ | ❌ | ❌ |
| **Live Demand** | `kandy_weekly_data`, `predictions` | ✅ Historical weekly data, XGBoost + LSTM forecasts | ❌ | ❌ | ❌ |
| **Custom Demand Forecaster** | None (local files) | ❌ | ❌ | ❌ | ❌ |
| **Resource Planner** | `kandy_weekly_data`, `predictions` | ✅ Forecast data for capacity planning | ❌ | ❌ | ❌ |
| **Climate Impact Forecaster** | None (local CSV + model files) | ❌ | ❌ | ❌ | ❌ |
| **Festival Forecaster** | `kandy_weekly_data`, `predictions` | ✅ Festival-tagged weekly data + forecasts | ❌ | ❌ | ❌ |
| **Report Generator** | `kandy_weekly_data`, `predictions` | ✅ Forecast data for report compilation | ❌ | ❌ | ❌ |
| **Profile Management** | `user_profiles`, `auth.users` | ✅ User profile | ❌ | ✅ Name, hotel | ✅ Account |
| **System Admin** | `user_profiles`, `auth.users` | ✅ All profiles | ❌ | ✅ Roles | ✅ Accounts |
| **Auth (Login/Signup)** | `user_profiles`, `auth.users` | ✅ Auth verification | ✅ New user+profile | ❌ | ❌ |
| **Training Pipeline** | `kandy_weekly_data`, `predictions` | ✅ Training data | ✅ New predictions (upsert) | ✅ Existing predictions (upsert) | ❌ |

---

## 5. Data Flow

### 5.1 Complete Data Flow Diagram

```
 ┌─────────────────────────────────────────────────────────────────┐
 │                     DATA INGESTION (One-time)                  │
 │                                                                 │
 │  Local CSVs ──▶ upload_to_supabase.py ──▶ Supabase Tables      │
 │  • Sri_Lanka_Tourist_*.csv  → national_tourism                 │
 │  • kandy_festival_*.csv     → kandy_weekly_data                │
 │  • Kandy_Weather_*.csv      → kandy_weather_daily              │
 └───────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │                  MODEL TRAINING (Periodic)                      │
 │                                                                 │
 │  train_models.py                                                │
 │  1. Fetch kandy_weekly_data from Supabase (or local CSV)       │
 │  2. Preprocess + feature engineering                           │
 │  3. Train XGBoost (GridSearchCV) → xgb_model.pkl              │
 │  4. Train LSTM (Keras) → lstm_model.keras                      │
 │  5. Generate 52-week forecasts for both models                 │
 │  6. Save to predictions_cache.csv (local)                      │
 │  7. Upsert to predictions table (Supabase)                    │
 └───────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │                   UI DATA CONSUMPTION                           │
 │                                                                 │
 │  utils/db.py                                                    │
 │  ├── fetch_national_tourism()  → SELECT * FROM national_tourism │
 │  ├── fetch_kandy_weekly()      → SELECT * FROM kandy_weekly_data│
 │  ├── fetch_predictions(model)  → SELECT * FROM predictions      │
 │  └── fetch_weather_daily()     → SELECT * FROM kandy_weather_daily│
 │                                                                 │
 │  Fallback: if Supabase fails → read local CSV files            │
 │                                                                 │
 │  Cache: @st.cache_data(ttl=3600) — 1 hour for most pages      │
 │         @st.cache_data(ttl=300)  — 5 minutes for National page │
 └───────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │                      USER INTERACTION                           │
 │                                                                 │
 │  User views charts → Filters data → Downloads reports          │
 │  Admin retrains models → New predictions pushed to Supabase    │
 │  User updates profile → user_profiles table updated            │
 │  User signs up → auth.users + user_profiles rows created       │
 └─────────────────────────────────────────────────────────────────┘
```

---

## 6. Queries & Code References

### 6.1 Key Database Operations

| Operation | Code Location | SQL Equivalent |
|-----------|---------------|----------------|
| Fetch national tourism | `utils/db.py:59-68` | `SELECT * FROM national_tourism ORDER BY year, month` |
| Fetch Kandy weekly data | `utils/db.py:71-85` | `SELECT * FROM kandy_weekly_data ORDER BY week_start` |
| Fetch predictions (all) | `utils/db.py:88-100` | `SELECT * FROM predictions ORDER BY week_start` |
| Fetch predictions (filtered) | `utils/db.py:93-94` | `SELECT * FROM predictions WHERE model_name = ? ORDER BY week_start` |
| Fetch weather daily | `utils/db.py:103-117` | `SELECT * FROM kandy_weather_daily ORDER BY time` |
| User login | `utils/auth.py:411-428` | Supabase GoTrue: `auth.sign_in_with_password()` |
| User signup | `utils/auth.py:471-509` | `auth.sign_up()` + `INSERT INTO user_profiles` |
| Load user profile | `utils/auth.py:54-62` | `SELECT * FROM user_profiles WHERE id = ? LIMIT 1` |
| Update profile | `pages/8_*.py:107-110` | `UPDATE user_profiles SET full_name=?, hotel_name=? WHERE id=?` |
| Update role (admin) | `pages/9_*.py:91` | `UPDATE user_profiles SET role=? WHERE id=?` |
| Delete user (admin) | `pages/9_*.py:103` | `auth.admin.delete_user(id)` (CASCADE deletes profile) |
| Delete own account | `pages/8_*.py:181-186` | `DELETE FROM user_profiles WHERE id=?` + `auth.admin.delete_user(id)` |
| Upsert predictions | `train_models.py:456-458` | `INSERT INTO predictions (...) ON CONFLICT (week_start, model_name) DO UPDATE SET ...` |
| Upload national data | `upload_to_supabase.py:65-94` | Batch `UPSERT` on `national_tourism` conflict `(year, month)` |
| Upload weekly data | `upload_to_supabase.py:98-136` | Batch `UPSERT` on `kandy_weekly_data` conflict `(week_start)` |
| Upload weather data | `upload_to_supabase.py:140-170` | Batch `UPSERT` on `kandy_weather_daily` conflict `(time)` |

### 6.2 Database Connection Handling

| Concern | Implementation | Location |
|---------|----------------|----------|
| Client singleton | Global `_client` variable, initialized once | `utils/db.py:19,31-43` |
| Secret resolution | `_get_secret()` — tries `st.secrets` then `os.environ` | `utils/db.py:22-28` |
| Service client | No singleton — creates fresh client each time | `utils/db.py:46-54` |
| Connection error handling | All `fetch_*` functions wrapped in try/except; display `st.error()` and return empty DataFrame | `utils/db.py:61-68,73-85,89-100,105-117` |
| Batch upload | `batch_upsert()` with configurable `BATCH_SIZE=200` | `upload_to_supabase.py:53-61` |
| NaN sanitization | `sanitize()` replaces NaN/Inf with None for JSON compatibility | `upload_to_supabase.py:39-50` |
