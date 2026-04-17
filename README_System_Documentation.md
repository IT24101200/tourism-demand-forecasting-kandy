# 📘 README 1: Full System & AI + Software Documentation

## 1. System Overview

### 1.1 Purpose
The **Tourist Demand Forecasting & Decision Support System (DSS)** is an AI-powered web application designed for Kandy District, Sri Lanka. It forecasts weekly tourist arrivals using machine learning models and provides actionable intelligence for hospitality stakeholders including hotel managers, tour operators, and government officials.

### 1.2 Key Features & Functionalities
| # | Feature | Description |
|---|---------|-------------|
| 1 | National Performance Canvas | Historical national tourism analytics with revenue, arrivals, and origin breakdowns |
| 2 | Live Demand Monitoring | Real-time XGBoost & LSTM forecast visualization with confidence intervals |
| 3 | Custom Demand Forecaster | Interactive what-if simulator for hypothetical scenario modeling |
| 4 | Resource Planner | Hotel capacity utilization, staffing, and transport planning tools |
| 5 | Climate Impact Forecaster | Weather-tourism correlation analysis with monsoon impact alerts |
| 6 | Festival Forecaster | Festival-driven demand prediction with cultural event calendars |
| 7 | Automated Report Generator | PDF/Excel report generation with AI model comparison analytics |
| 8 | Profile Management | User account settings, password management, and account deletion |
| 9 | System Administration | MLOps engine, access management, and server activity logs (admin only) |

### 1.3 Overall Architecture

```
┌───────────────────────────────────────────────────┐
│                  FRONTEND (Streamlit)              │
│  app.py → pages/1_*.py … pages/9_*.py             │
│  utils/theme.py  │  utils/sidebar.py              │
├───────────────────────────────────────────────────┤
│                AUTHENTICATION LAYER               │
│  utils/auth.py → Supabase GoTrue Auth             │
├───────────────────────────────────────────────────┤
│                 DATA ACCESS LAYER                 │
│  utils/db.py → Supabase PostgreSQL (REST API)     │
│  Local CSV Fallback (kandy_festival_demand_*.csv) │
├───────────────────────────────────────────────────┤
│              AI / ML ENGINE (Offline)             │
│  train_models.py → XGBoost + LSTM                 │
│  models/xgb_model.pkl  │  models/lstm_model.keras │
│  models/feature_scaler.pkl                        │
│  models/predictions_cache.csv (offline fallback)  │
├───────────────────────────────────────────────────┤
│                 CLOUD DATABASE                    │
│  Supabase PostgreSQL                              │
│  Tables: national_tourism, kandy_weekly_data,     │
│          kandy_weather_daily, predictions,         │
│          user_profiles                            │
└───────────────────────────────────────────────────┘
```

**Technology Stack:**
- **Frontend Framework:** Streamlit ≥ 1.35.0
- **Visualization:** Plotly ≥ 5.15.0
- **ML Models:** XGBoost ≥ 1.7.0, TensorFlow/Keras ≥ 2.13.0, scikit-learn ≥ 1.3.0
- **Database:** Supabase (hosted PostgreSQL) with Python client ≥ 1.2.0
- **Data Processing:** Pandas ≥ 2.0.0, NumPy ≥ 1.24.0
- **Reports:** FPDF ≥ 1.7.2, OpenPyXL ≥ 3.1.0
- **Design:** Glassmorphic UI with Inter & Manrope typography, dark/light theme toggle

---

## 2. UI Components Breakdown

### 2.1 Entry Point — `app.py`
| Attribute | Detail |
|-----------|--------|
| **Description** | Minimal entry point that redirects to the National Overview page |
| **Functionality** | Applies global theme, enforces authentication, then calls `st.switch_page()` |
| **Backend Interaction** | Calls `require_auth()` which triggers Supabase auth check |
| **AI Connection** | None directly |
| **Data Flow** | User visit → Auth check → Redirect to Page 1 |

### 2.2 Page 1: National Overview — `pages/1_🏠_National_Overview.py`
| Attribute | Detail |
|-----------|--------|
| **Description** | Strategic national-level tourism analytics dashboard |
| **Functionality** | Displays KPI cards (Total Arrivals, Revenue, Occupancy, Peak Month), historical trend chart with dual y-axis (arrivals + revenue), arrivals-by-origin donut chart, annual summary table, geographic pulse card, tourist profile analytics, revenue forecasting with linear extrapolation, and AI insights engine |
| **Backend Interaction** | Reads `national_tourism` table via `fetch_national_tourism()` in `utils/db.py`; fallback to local CSV `Sri_Lanka_Tourist_Forecast_Training_Dataset_2015_2025.csv` |
| **AI Connection** | Displays current/next week AI predictions via `get_current_week_prediction()` and `get_next_week_prediction()` from `utils/theme.py`; generates rule-based AI insights (growth analysis, occupancy alerts, origin dominance) |
| **Data Flow** | Load national CSV/Supabase → Apply year/origin/region filters → Compute KPIs → Render Plotly charts → Generate insights → Export CSV |
| **APIs Used** | `fetch_national_tourism()`, `fetch_predictions()` |

### 2.3 Page 2: Live Demand Monitoring — `pages/2__Live_Demand.py`
| Attribute | Detail |
|-----------|--------|
| **Description** | Real-time Kandy weekly demand monitoring with XGBoost and LSTM forecast overlay |
| **Functionality** | Historical vs. forecasted arrivals Plotly chart with 95% confidence intervals, model selection (XGBoost/LSTM/Both), view modes (Next 52 Weeks Only / Historical + Forecast), festival annotations, monsoon week detection, anomaly detection engine using SGDRegressor, metric cards (historical average, forecast average, monsoon weeks, XGBoost 26-wk average) |
| **Backend Interaction** | Reads `kandy_weekly_data` and `predictions` tables via `fetch_kandy_weekly()` and `fetch_predictions()`; fallback to local CSVs |
| **AI Connection** | Directly displays XGBoost and LSTM forecast outputs; uses `SGDRegressor` for real-time anomaly detection on historical data |
| **Data Flow** | Load historical data + predictions → Split by model_name → Unpack features_used JSON → Merge for chart → Detect anomalies → Render |
| **APIs Used** | `fetch_kandy_weekly()`, `fetch_predictions()` |

### 2.4 Page 3: Custom Demand Forecaster — `pages/3_🎛️_Custom_Demand_Forecaster.py`
| Attribute | Detail |
|-----------|--------|
| **Description** | Interactive what-if simulator allowing users to model hypothetical scenarios |
| **Functionality** | Quick presets (Peak Esala Perahera, Monsoon Crash, Post-COVID Recovery, etc.), three-tab parameter panel (Timeline, Geopolitics, Weather), real-time XGBoost prediction (no submit button — updates dynamically), scenario comparison radar chart, AI-generated strategic recommendations, confidence interval visualization, LSTM comparison panel |
| **Backend Interaction** | Loads pre-trained model from `models/xgb_model.pkl` and scaler from `models/feature_scaler.pkl`; reads baseline stats from `kandy_festival_demand_NOMISSING.csv` |
| **AI Connection** | **Direct inference** — loads XGBoost (.pkl) and LSTM (.keras) models, constructs feature vectors from user inputs, runs `model.predict()` in real-time |
| **Data Flow** | User adjusts sliders → Feature vector constructed → Scaler transforms → Model predicts → Results rendered with charts and recommendations |
| **APIs Used** | Local model files only (no database call) |

### 2.5 Page 4: Resource Planner — `pages/4_🏨_Resource_Planner.py`
| Attribute | Detail |
|-----------|--------|
| **Description** | Hotel capacity planning and resource forecasting tool |
| **Functionality** | Interactive planning parameters (hotel capacity, market share %, staff-to-tourist ratio, transport ratio), week-level resource projections, Hotel Capacity Utilization gauge (0-100% with green/amber/red zones), forward resource bar chart (staff + transport), Monte Carlo simulation for overflow risk analysis, festival timeline Gantt chart, capacity status matrix, advanced analytics tabs |
| **Backend Interaction** | Reads `kandy_weekly_data` via `fetch_kandy_weekly()` and predictions via `fetch_predictions()`; fallback to local CSV |
| **AI Connection** | Uses XGBoost predictions to project staffing, transport, and capacity needs; Monte Carlo simulation runs 1000 iterations with ±15% uncertainty |
| **Data Flow** | Load forecast data → Apply planning parameters → Calculate room/staff/transport needs → Monte Carlo simulation → Render dashboards |
| **APIs Used** | `fetch_kandy_weekly()`, `fetch_predictions()` |

### 2.6 Page 5: Climate Impact Forecaster — `pages/5_🌦️_Climate_Impact_Forecaster.py`
| Attribute | Detail |
|-----------|--------|
| **Description** | Weather-tourism correlation analyzer with monsoon impact alerts |
| **Functionality** | Rainfall vs. arrivals scatter plot with trendlines, monsoon/heavy rain/optimal weather alerts, temperature and humidity analysis, correlation coefficient computation, rainfall threshold selector, year-based filtering, XGBoost-based weather sensitivity analysis |
| **Backend Interaction** | Reads `kandy_festival_demand_NOMISSING.csv` and `predictions_cache.csv`; loads XGBoost model for weather sensitivity predictions |
| **AI Connection** | Loads `xgb_model.pkl` to compute weather sensitivity — predicts arrivals at different rainfall levels to show marginal impact |
| **Data Flow** | Load weekly data + predictions → Filter by years → Merge weather features → Compute correlations → Generate alerts → Render charts |
| **APIs Used** | Local CSV files, `models/xgb_model.pkl` |

### 2.7 Page 6: Festival Forecaster — `pages/6_🐘_Festival_Forecaster.py`
| Attribute | Detail |
|-----------|--------|
| **Description** | Festival-driven demand prediction with Kandy's cultural event calendar |
| **Functionality** | Festival timeline with demand multipliers, festival impact comparison charts, festival-specific arrival forecasts, Esala Perahera deep-dive analytics, festival preparation lead-time analysis, historical festival demand patterns |
| **Backend Interaction** | Reads `kandy_weekly_data` and `predictions` tables; fallback to local CSV |
| **AI Connection** | Visualizes XGBoost predictions filtered by festival periods; shows how festival binary flags influence model output |
| **Data Flow** | Load weekly + prediction data → Filter by festival flags → Compute festival-specific metrics → Render timeline and comparison charts |
| **APIs Used** | `fetch_kandy_weekly()`, `fetch_predictions()` |

### 2.8 Page 7: Report Generator — `pages/7_📊_Report_Generator.py`
| Attribute | Detail |
|-----------|--------|
| **Description** | Automated PDF/Excel report generator with AI model comparison module |
| **Functionality** | 26-week forecast reports with PDF and Excel export, week-by-week demand cards with festival flags and peak/normal classification, AI Model Comparison tab (XGBoost vs LSTM side-by-side metrics, winner/loser badges, comparison table), resource allocation insights, executive summary generation |
| **Backend Interaction** | Reads `kandy_weekly_data` and `predictions` tables; reads `kandy_festival_demand_NOMISSING.csv` |
| **AI Connection** | Compares XGBoost and LSTM predictions side-by-side; evaluates metrics (MAE, RMSE, R²) from training output stored in model artifacts |
| **Data Flow** | Load predictions → Format as weekly cards → Generate PDF/Excel → Allow download |
| **APIs Used** | `fetch_kandy_weekly()`, `fetch_predictions()` |

### 2.9 Page 8: Profile Management — `pages/8_👤_Profile.py`
| Attribute | Detail |
|-----------|--------|
| **Description** | User account settings and security management |
| **Functionality** | Profile information display (email, name, role, organization), profile update form, password change form with validation, account deletion with "DELETE" confirmation, logout button |
| **Backend Interaction** | Reads/updates `user_profiles` table; uses Supabase Auth for password update and account deletion |
| **AI Connection** | None |
| **Data Flow** | Load profile from session → Display → User updates → Write to `user_profiles` table |
| **APIs Used** | `get_client()` → `user_profiles` table, `supabase.auth.update_user()`, `supabase.auth.admin.delete_user()` |

### 2.10 Page 9: System Admin — `pages/9_⚙️_System_Admin.py`
| Attribute | Detail |
|-----------|--------|
| **Description** | Elevated admin panel for access control and MLOps |
| **Functionality** | Access Management tab (user list, role promotion/demotion, account deletion), MLOps Engine tab (trigger model retraining via subprocess, display training summary cards, dataset upload), System Logs tab (view/clear training logs) |
| **Backend Interaction** | Uses `get_service_client()` with service-role key for full table access; runs `train_models.py` as subprocess |
| **AI Connection** | Triggers the complete ML training pipeline (`train_models.py`) which retrains XGBoost and LSTM and pushes new predictions |
| **Data Flow** | Admin clicks retrain → `subprocess.run(train_models.py)` → Models retrained → Predictions pushed to Supabase → Console output parsed and displayed |
| **APIs Used** | `get_service_client()` → `user_profiles`, `supabase.auth.admin`, subprocess execution |

---

## 3. AI Component Details

### 3.1 XGBoost Regressor

| Attribute | Detail |
|-----------|--------|
| **Type** | Gradient Boosted Decision Trees (Regression) |
| **Library** | `xgboost.XGBRegressor` |
| **Purpose** | Predict weekly tourist arrivals in Kandy District |
| **Model File** | `models/xgb_model.pkl` |
| **Training Method** | `GridSearchCV` with 3-fold CV, optimizing R² score |
| **Hyperparameters** | n_estimators: [500, 1000, 1500], max_depth: [6, 12, 20], learning_rate: [0.01, 0.05, 0.1], subsample: [0.8, 1.0] |
| **Train/Test Split** | 80/20 randomized shuffle (`random_state=42`) |

**Input Features (24 features):**

| Category | Features |
|----------|----------|
| **Temporal** | `week_of_year`, `month` |
| **Festival Signals** | `festival_intensity_score`, `festival_demand_multiplier`, `is_esala_perahera`, `is_esala_preparation`, `is_esala_post_festival`, `is_august_buildup`, `is_poson_perahera`, `is_vesak`, `is_sinhala_tamil_new_year`, `is_christmas_new_year`, `is_deepavali`, `is_thai_pongal`, `is_monthly_poya_week`, `poya_days_away`, `is_school_holiday`, `is_any_festival`, `days_until_next_esala` |
| **Weather** | `avg_weekly_rainfall_mm`, `avg_temp_celsius`, `avg_humidity_pct`, `is_monsoon_week` |
| **Crisis** | `is_covid_period`, `is_easter_attack_period`, `is_economic_crisis`, `is_normal_operation` |

> **Note:** `year` and `quarter` are deliberately excluded from features because they cause out-of-distribution (OOD) collapse when predicting into 2026+ (values exceed max training range of 2025).

**Output:** Integer — predicted weekly tourist arrivals with 95% confidence bounds (±12% margin).

**Preprocessing & Feature Engineering:**
1. Column name normalization (lowercase, underscore)
2. Date parsing and sorting
3. Numeric coercion with `pd.to_numeric(errors="coerce")`
4. Missing value imputation: median for weather features, zero for binary flags
5. Lag features computed but excluded from final model to prevent recursive drift
6. `MinMaxScaler` fitted on full dataset, saved in `models/feature_scaler.pkl`

**Limitations:**
- Festival heuristics for future predictions are rule-based approximations
- Weather for future weeks uses monthly climatological averages, not actual forecasts
- No external API integration for real-time weather data

### 3.2 LSTM (Long Short-Term Memory) Neural Network

| Attribute | Detail |
|-----------|--------|
| **Type** | Sequence-to-One Regression (Time Series) |
| **Library** | `tensorflow.keras` |
| **Purpose** | Capture sequential temporal patterns in tourist arrivals |
| **Model File** | `models/lstm_model.keras` |
| **Architecture** | Sequential: LSTM(64) → Dropout(0.2) → Dense(32, relu) → Dense(1) |
| **Lookback Window** | 12 weeks |
| **Optimizer** | Adam (lr=5e-4) |
| **Loss Function** | MSE (to penalize missing festival peaks) |
| **Callbacks** | EarlyStopping(patience=20), ReduceLROnPlateau(factor=0.5, patience=8) |
| **Epochs** | Up to 150 (early stopping typically triggers earlier) |
| **Batch Size** | 16 |

**Input:** Scaled feature sequences of shape `(batch, 12, n_features)` using MinMaxScaler.

**Target Scaling:** `MinMaxScaler` applied to target variable (`estimated_weekly_kandy_arrivals`). The `y_scaler` is saved as part of `feature_scaler.pkl` tuple.

**Output:** Single continuous value (inverse-scaled to actual arrivals count).

**Autoregressive Forecasting:**
For future predictions, the LSTM uses a sliding window approach:
1. Start with the last 12 known scaled feature rows
2. For each future week, construct exogenous features, scale them, append to window
3. Predict next value, slide window forward
4. Repeat for 52 weeks

**Limitations:**
- Autoregressive mode can accumulate drift over long horizons
- Unidirectional architecture (bidirectional was removed for simulation data robustness)
- Requires full training data context (cannot do one-shot inference like XGBoost)

### 3.3 Anomaly Detection (Live Demand Page)

| Attribute | Detail |
|-----------|--------|
| **Type** | Online Learning Regression |
| **Library** | `sklearn.linear_model.SGDRegressor` |
| **Purpose** | Detect anomalous weeks in historical arrivals data |
| **Scope** | Live Demand page only (Page 2) |
| **Method** | Fits SGD on week_of_year → arrivals, flags residuals > 2σ as anomalies |

### 3.4 Revenue Forecasting (National Overview)

| Attribute | Detail |
|-----------|--------|
| **Type** | Linear Extrapolation |
| **Library** | `numpy.polyfit` (degree 1) |
| **Purpose** | Project next 2 years of national tourism revenue |
| **Scope** | National Overview page only (Page 1) |

### 3.5 How Predictions Are Used in the UI

| UI Location | Model | Usage |
|-------------|-------|-------|
| National Overview header badges | XGBoost | "This Week" and "Next Week" prediction display |
| Live Demand chart | Both | Historical vs. forecasted overlay with CI bands |
| Custom Demand Forecaster | Both | Real-time what-if scenario predictions |
| Resource Planner | XGBoost | Calculate staff, rooms, transport requirements |
| Climate Impact Forecaster | XGBoost | Weather sensitivity analysis |
| Festival Forecaster | Both | Festival-period demand projections |
| Report Generator | Both | Weekly forecast cards and AI model comparison |

---

## 4. CRUD Operations per UI Component

### 4.1 National Overview (Page 1)
| Operation | Data | Location |
|-----------|------|----------|
| **Read** | National tourism statistics (arrivals, revenue, occupancy, origins) | `fetch_national_tourism()` → `national_tourism` table |
| **Read** | Current/next week predictions | `fetch_predictions()` → `predictions` table |
| **Create** | None | — |
| **Update** | None | — |
| **Delete** | None | — |

### 4.2 Live Demand (Page 2)
| Operation | Data | Location |
|-----------|------|----------|
| **Read** | Kandy weekly historical data | `fetch_kandy_weekly()` → `kandy_weekly_data` table |
| **Read** | XGBoost + LSTM predictions | `fetch_predictions()` → `predictions` table |
| **Create** | None | — |
| **Update** | None | — |
| **Delete** | None | — |

### 4.3 Custom Demand Forecaster (Page 3)
| Operation | Data | Location |
|-----------|------|----------|
| **Read** | Pre-trained XGBoost model | `models/xgb_model.pkl` (local file) |
| **Read** | Feature scaler | `models/feature_scaler.pkl` (local file) |
| **Read** | LSTM model | `models/lstm_model.keras` (local file) |
| **Read** | Baseline statistics | `kandy_festival_demand_NOMISSING.csv` (local file) |
| **Create** | None | — |
| **Update** | None | — |
| **Delete** | None | — |

### 4.4 Resource Planner (Page 4)
| Operation | Data | Location |
|-----------|------|----------|
| **Read** | Kandy weekly + predictions data | `fetch_kandy_weekly()`, `fetch_predictions()` |
| **Create** | None | — |
| **Update** | None | — |
| **Delete** | None | — |

### 4.5 Climate Impact Forecaster (Page 5)
| Operation | Data | Location |
|-----------|------|----------|
| **Read** | Historical weekly data | `kandy_festival_demand_NOMISSING.csv` |
| **Read** | Predictions + XGBoost model | `models/predictions_cache.csv`, `models/xgb_model.pkl` |
| **Create** | None | — |
| **Update** | None | — |
| **Delete** | None | — |

### 4.6 Festival Forecaster (Page 6)
| Operation | Data | Location |
|-----------|------|----------|
| **Read** | Kandy weekly + predictions data | `fetch_kandy_weekly()`, `fetch_predictions()` |
| **Create** | None | — |
| **Update** | None | — |
| **Delete** | None | — |

### 4.7 Report Generator (Page 7)
| Operation | Data | Location |
|-----------|------|----------|
| **Read** | Kandy weekly + predictions data | `fetch_kandy_weekly()`, `fetch_predictions()` |
| **Create** | PDF/Excel report files (client-side download) | Generated in-memory, sent via `st.download_button()` |
| **Update** | None | — |
| **Delete** | None | — |

### 4.8 Profile Management (Page 8)
| Operation | Data | Location |
|-----------|------|----------|
| **Read** | User profile | `user_profiles` table via `get_client()` |
| **Create** | None (created at signup) | — |
| **Update** | Full name, hotel organization | `user_profiles.update()` |
| **Update** | Password | `supabase.auth.update_user()` |
| **Delete** | User account + profile | `user_profiles.delete()` + `auth.admin.delete_user()` |

### 4.9 System Admin (Page 9)
| Operation | Data | Location |
|-----------|------|----------|
| **Read** | All user profiles | `user_profiles` table via `get_service_client()` |
| **Update** | User roles | `user_profiles.update(role)` |
| **Delete** | User accounts | `auth.admin.delete_user()` |
| **Create** | Training log file | `models/training_log.txt` (local) |
| **Update** | Master dataset | `kandy_festival_demand_NOMISSING.csv` (file upload) |
| **Create** | New predictions | via `train_models.py` subprocess → `predictions` table + `predictions_cache.csv` |

### 4.10 Authentication Flow (utils/auth.py)
| Operation | Data | Location |
|-----------|------|----------|
| **Create** | New user account | `supabase.auth.sign_up()` + `user_profiles.insert()` |
| **Read** | User session/profile | `supabase.auth.sign_in_with_password()` + `user_profiles.select()` |
| **Update** | None during auth flow | — |
| **Delete** | Session on logout | `supabase.auth.sign_out()` |

---

## 5. System Integration Flow

### 5.1 End-to-End Workflow

```
┌────────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   DATA INGESTION   │────▶│  MODEL TRAINING  │────▶│ PREDICTION STORE │
│ upload_to_supabase │     │ train_models.py  │     │ Supabase + CSV   │
│     .py            │     │                  │     │                  │
│ Local CSVs ──────▶ │     │ XGBoost + LSTM   │     │ predictions      │
│ Supabase Tables    │     │ Grid Search CV   │     │ table +          │
│                    │     │ 52-week forecast  │     │ predictions      │
│                    │     │                  │     │ _cache.csv       │
└────────────────────┘     └──────────────────┘     └────────┬─────────┘
                                                             │
                                                             ▼
┌────────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│    USER BROWSER    │◀────│   STREAMLIT UI   │◀────│   DATA LAYER     │
│                    │     │ 9 Pages + Theme  │     │ utils/db.py      │
│ Plotly Charts      │     │ Glassmorphic CSS │     │ fetch_* helpers  │
│ PDF/Excel Reports  │     │ Dark/Light Mode  │     │ Supabase Client  │
│ Interactive Sliders│     │                  │     │ CSV Fallback     │
└────────────────────┘     └──────────────────┘     └──────────────────┘
```

### 5.2 Authentication Flow
1. User visits `app.py` → `require_auth()` called
2. No session → `render_auth_page()` displays login/signup form
3. Login: `supabase.auth.sign_in_with_password()` → user stored in `st.session_state["user"]`
4. Profile loaded via `load_user_profile()` → stored in `st.session_state["user_profile"]`
5. Admin check: if email == `it24101200@my.sliit.lk` → role forced to `System Administrator`
6. Each page calls `require_auth()` at top; admin pages call `require_admin()`

### 5.3 Data Loading Strategy (Dual-Source)
1. **Primary:** Fetch from Supabase via REST API (`utils/db.py`)
2. **Fallback:** If Supabase is unreachable, read from local CSV files
3. **Caching:** Streamlit `@st.cache_data(ttl=3600)` caches data for 1 hour

### 5.4 Model Training Pipeline Flow
1. `train_models.py` loads data from Supabase (fallback: local CSV)
2. Preprocessing: column normalization, date parsing, numeric coercion, lag features
3. Feature selection: 24 exogenous features (year/quarter excluded)
4. Train/test split: 80/20 randomized (XGBoost) + sequential (LSTM)
5. XGBoost: GridSearchCV with 54 parameter combinations
6. LSTM: 12-week lookback, up to 150 epochs with early stopping
7. Future features generated for 52 weeks using heuristic rules
8. Predictions saved locally to `models/predictions_cache.csv`
9. Predictions pushed to Supabase `predictions` table via upsert

---

## 6. Code References

### 6.1 UI → Backend Connections
| UI File | Backend Call | Purpose |
|---------|-------------|---------|
| `pages/1_*.py:207-228` | `fetch_national_tourism()` | Load national stats |
| `pages/1_*.py:239-240` | `get_current_week_prediction()`, `get_next_week_prediction()` | Header badges |
| `pages/2_*.py:36-85` | `fetch_kandy_weekly()`, `fetch_predictions()` | Load historical + forecast data |
| `pages/3_*.py:212-240` | `pickle.load(RF_PATH)`, `tf.keras.models.load_model()` | Load models for inference |
| `pages/4_*.py` | `fetch_kandy_weekly()`, `fetch_predictions()` | Resource planning data |
| `pages/5_*.py:76-115` | Local CSV + `pickle.load()` | Weather data + XGBoost model |
| `pages/6_*.py` | `fetch_kandy_weekly()`, `fetch_predictions()` | Festival analysis data |
| `pages/7_*.py` | `fetch_kandy_weekly()`, `fetch_predictions()` | Report generation data |
| `pages/8_*.py:106-110` | `sb.table("user_profiles").update()` | Profile update |
| `pages/9_*.py:74-111` | `sb_admin.table("user_profiles").select()` | Admin user management |

### 6.2 Backend → AI Connections
| Backend File | AI Call | Purpose |
|-------------|---------|---------|
| `train_models.py:179-222` | `train_xgboost()` | Train XGBoost with GridSearchCV |
| `train_models.py:256-296` | `train_lstm()` | Train LSTM with Keras |
| `train_models.py:302-410` | `generate_future_features()` | Build 52-week synthetic feature matrix |
| `train_models.py:523` | `rf_model.predict()` | XGBoost inference on future data |
| `train_models.py:531-548` | `lstm_model.predict()` | LSTM autoregressive inference |
| `train_models.py:416-467` | `push_predictions()` | Save predictions to Supabase + CSV |

### 6.3 AI Implementation Locations
| Component | File | Lines | Description |
|-----------|------|-------|-------------|
| XGBoost training | `train_models.py` | 176-222 | GridSearchCV + model save |
| LSTM architecture | `train_models.py` | 240-253 | Keras Sequential model definition |
| LSTM training | `train_models.py` | 256-296 | Training loop with callbacks |
| Feature engineering | `train_models.py` | 92-173 | Feature list + preprocessing |
| Future feature generation | `train_models.py` | 302-410 | Heuristic-based future data |
| Real-time XGBoost inference | `pages/3_*.py` | 212-240 | Load and predict in Custom Forecaster |
| Anomaly detection | `pages/2_*.py` | ~350-380 | SGDRegressor on historical data |
| Weather sensitivity | `pages/5_*.py` | ~250-300 | XGBoost sensitivity curves |
