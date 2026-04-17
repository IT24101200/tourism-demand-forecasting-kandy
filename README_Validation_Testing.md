# 📕 README 3: Validation, Error Handling & Testing

## 1. Validation Techniques

### 1.1 Authentication Validation

#### Frontend (Login Form) — `utils/auth.py:405-428`
| Validation | Rule | Error Message |
|-----------|------|---------------|
| Empty fields | Email and password must not be empty | `"Please enter your email and password."` |
| Email format | Regex: `^[\w\.-]+@[\w\.-]+\.\w+$` | `"Please provide a valid email format."` |

#### Frontend (Signup Form) — `utils/auth.py:463-509`
| Validation | Rule | Error Message |
|-----------|------|---------------|
| Required fields | Email, password, and name must not be empty | `"Please fill in all required fields."` |
| Email format | Regex: `^[\w\.-]+@[\w\.-]+\.\w+$` | `"Please provide a valid email format."` |
| Password length | Minimum 6 characters | `"Password must be at least 6 characters."` |
| Role selection | Constrained to 4 options via `st.selectbox` | UI-enforced (dropdown) |

#### Backend (Database Constraint) — `sql/02_auth_schema.sql:6`
```sql
CHECK (role IN ('Hotel Manager', 'Tour Operator', 'Government Official', 'Other', 'System Administrator'))
```

### 1.2 Profile Update Validation

#### Page: Profile Management — `pages/8_👤_Profile.py`
| Validation | Rule | Error Message |
|-----------|------|---------------|
| Password length | Minimum 8 characters (stricter than signup) | `"Password must be at least 8 characters long."` |
| Password match | New password == Confirm password | `"Passwords do not match. Please try again."` |
| Account deletion | User must type `"DELETE"` exactly | `"Please type 'DELETE' exactly to confirm your choice."` |

### 1.3 Data Ingestion Validation — `upload_to_supabase.py`

| Validation | Rule | Location |
|-----------|------|----------|
| NaN/Inf sanitization | All NaN, Inf values replaced with `None` | `sanitize()` → line 39-45 |
| Column normalization | Strip whitespace, lowercase, underscore spaces | All upload functions |
| Duplicate removal | `drop_duplicates(subset=[key_column])` | Lines 86, 110, 149 |
| Date parsing | `pd.to_datetime(errors="coerce")` — invalid dates become NaT | Lines 105-106, 147 |
| Null key filtering | Rows with null primary keys dropped before upload | `dropna(subset=["week_start"])` / `dropna(subset=["time"])` |
| Type coercion | Explicit `pd.to_numeric(errors="coerce").astype("Int64")` | Lines 89-90, 126-133, 160-167 |
| URL check | Blocks execution if SUPABASE_URL is still default placeholder | Line 175-177 |

### 1.4 Model Training Validation — `train_models.py`

| Validation | Rule | Location |
|-----------|------|----------|
| Empty data check | If Supabase returns empty, raises ValueError and falls back to CSV | `load_data()` → line 80 |
| Column existence | `if col in df.columns` check before processing every feature | `preprocess()` → lines 128-138 |
| Date validity | `dropna(subset=["week_start", TARGET_COL])` | Line 123 |
| Feature availability | `get_feature_list()` only includes features present in DataFrame | Line 166 |
| OOD prevention | `year` and `quarter` removed from features to prevent scaled value > 1.0 | Lines 170-171 |
| Scaler compatibility | Feature vector padded/trimmed to match training dimensions | Lines 536-538 |
| Non-negative predictions | `max(0, round(prediction))` applied to all outputs | Lines 552-553 |
| Service key check | Training skips Supabase push if service key is missing/placeholder | Line 446-450 |

### 1.5 UI Component Input Validation

#### Custom Demand Forecaster — `pages/3_🎛️_Custom_Demand_Forecaster.py`
| Widget | Constraint | Method |
|--------|-----------|--------|
| Week of Year | Range: 1–52 | `st.slider(min_value=1, max_value=52)` |
| Month | Range: 1–12 | `st.slider(min_value=1, max_value=12)` |
| Rainfall (mm) | Range: 0–500 | `st.slider(min_value=0, max_value=500)` |
| Temperature (°C) | Range: 18–35 | `st.slider(min_value=18, max_value=35)` |
| Humidity (%) | Range: 50–100 | `st.slider(min_value=50, max_value=100)` |
| Festival intensity | Range: 1–10 | `st.slider(min_value=1, max_value=10)` |
| Crisis flags | Binary (0/1) | `st.checkbox()` |

#### Resource Planner — `pages/4_🏨_Resource_Planner.py`
| Widget | Constraint | Method |
|--------|-----------|--------|
| Hotel Capacity | Range: 1000–50000 | `st.number_input()` with min/max |
| Market Share % | Range: 1–100 | `st.slider()` |
| Staff Ratio | Range: 1–100 | `st.number_input()` |
| Transport Ratio | Range: 1–100 | `st.number_input()` |

#### Climate Impact Forecaster — `pages/5_🌦️_Climate_Impact_Forecaster.py`
| Widget | Constraint | Method |
|--------|-----------|--------|
| Years filter | Multi-select from 2015–2029 | `st.multiselect()` |
| Rain threshold | Range: 100–400 mm/week | `st.slider()` |

### 1.6 Business Logic Validation

| Rule | Implementation | Location |
|------|---------------|----------|
| Admin-only page access | `require_admin()` checks `profile.role == "System Administrator"` | `utils/auth.py:532-539` |
| Master admin override | Email `it24101200@my.sliit.lk` always promoted to System Administrator | `utils/auth.py:65-66` |
| Prediction non-negativity | All predictions floored at 0 | `train_models.py:552-553` |
| CI bounds non-negative | Lower bound enforced ≥ 0 | `train_models.py:567` |
| Occupancy capping | Gauge range 0–100% | Resource Planner gauge config |

---

## 2. Error Handling

### 2.1 UI Errors

| Error Type | Handling Strategy | Location |
|-----------|-------------------|----------|
| Missing model files | Display `st.warning()` with instructions to run training | `pages/3_*.py:270-279` |
| Empty dataset | Display `st.info()` message and `st.stop()` | `pages/1_*.py:232-234` |
| Invalid filter state | Session state defaults initialized if missing | `pages/1_*.py:349-356` |
| No profile loaded | Graceful fallback — build from `user.user_metadata` | `pages/8_*.py:52-54` |
| Non-dict profile | Force `profile = {}` if not isinstance dict | `pages/8_*.py:61-62` |

### 2.2 Backend/Server Errors

| Error Type | Handling Strategy | Location |
|-----------|-------------------|----------|
| Supabase connection failure | Try/except → `st.error("Database connection failed.")` + return empty DataFrame | `utils/db.py:61-68, 73-85, 89-100, 105-117` |
| Missing credentials | `RuntimeError` with descriptive message | `utils/db.py:38-41, 51-53` |
| Service client unavailable | `st.error()` + `st.stop()` on admin page | `pages/9_*.py:63-65` |
| Auth sign-in failure | Parse error string for specific messages | `utils/auth.py:421-428` |
| Auth sign-up failure | Parse error for "already registered", "password", "rate limit" | `utils/auth.py:500-509` |
| Profile update failure | `st.error(f"Failed to update profile: {e}")` | `pages/8_*.py:116-117` |
| Password update failure | `st.error(f"Failed to update password: {str(e)}")` | `pages/8_*.py:143-144` |
| Account deletion failure | `st.error(f"Deletion failed: {e}")` | `pages/8_*.py:191-192` |
| Admin role change failure | `st.error(f"Failed to update role: {err}")` | `pages/9_*.py:94-95` |
| Admin user deletion failure | `st.error(f"Server refused deletion. Error: {err}")` | `pages/9_*.py:107` |

### 2.3 Database Errors

| Error Type | Handling Strategy | Location |
|-----------|-------------------|----------|
| Table not found | Non-blocking try/except in `load_user_profile()` | `utils/auth.py:54-62` |
| RLS policy denial | Silent pass — falls back to metadata | `utils/auth.py:61-62` |
| Duplicate key on upsert | `ON CONFLICT ... DO UPDATE` handles gracefully | `train_models.py:458` |
| Batch upload failure | Per-batch try/except with progress reporting | `upload_to_supabase.py:57-60` |

### 2.4 AI/Model-Related Errors

| Error Type | Handling Strategy | Location |
|-----------|-------------------|----------|
| Model file missing | Check `Path.exists()` → return `None` → show warning | `pages/3_*.py:215-216, 270-279` |
| LSTM load failure | Try/except wrapping `tf.keras.models.load_model()` | `pages/3_*.py:222-226` |
| Scaler format mismatch | Handle both tuple and direct scaler object | `pages/3_*.py:232-239` |
| Feature dimension mismatch | Pad/trim to match training dimensions | `train_models.py:536-539` |
| Training subprocess crash | `subprocess.CalledProcessError` caught → show stderr trace | `pages/9_*.py:168-173` |
| Prediction NaN | `fillna(0)` on all feature inputs before prediction | `train_models.py:523, 533` |
| Supabase push failure | Continue with local-only save; log warning | `train_models.py:462-465` |
| JSON parse error in features_used | Try/except in `unpack_feats()` | `pages/2_*.py:55-62` |

### 2.5 Error Display Patterns

The system uses a consistent error display hierarchy:

1. **`st.error()`** — Blocking/critical errors (auth failures, missing service keys, crashes)
2. **`st.warning()`** — Recoverable issues (missing model, fallback to CSV)
3. **`st.info()`** — Informational (empty data, pending features)
4. **`st.success()`** — Confirmations (profile updated, training complete)

---

## 3. Edge Cases

### 3.1 Authentication Edge Cases

| Edge Case | System Behavior |
|-----------|-----------------|
| User refreshes page after login | `require_auth()` checks `st.session_state["user"]`; if present, loads profile if missing |
| User metadata is None | `load_user_profile()` builds empty dict defaults | 
| `user_profiles` table doesn't exist | Try/except silently passes — uses metadata fallback |
| Rate-limited signup (Supabase limit) | Specific error caught → `"Too many signup attempts. Supabase requires you to wait an hour."` |
| Admin email hardcoded override | `it24101200@my.sliit.lk` always gets System Administrator role regardless of DB value |
| Session state cleared (rerun) | `init_session_state()` initializes defaults |

### 3.2 Data Loading Edge Cases

| Edge Case | System Behavior |
|-----------|-----------------|
| Supabase unreachable | Falls back to local CSV files |
| Empty Supabase response | Raises ValueError → falls through to CSV |
| CSV has bad encoding | `on_bad_lines="skip"` silently skips corrupted rows |
| Missing columns in CSV | `if col in df.columns` guard before every operation |
| Date parsing failure | `errors="coerce"` converts bad dates to NaT → dropped by `dropna()` |
| Numeric conversion failure | `errors="coerce"` converts bad values to NaN → filled by `fillna()` |
| No predictions exist yet | Pages show empty charts; National Overview shows no badges |
| Predictions cache CSV missing | Returns empty DataFrames; pages degrade gracefully |

### 3.3 AI/Model Edge Cases

| Edge Case | System Behavior |
|-----------|-----------------|
| Model not trained yet | `st.warning()` with training instructions; `st.stop()` |
| XGBoost model file corrupted | `pickle.load()` would throw → caught by `load_model()` |
| LSTM model incompatible TF version | Try/except wrapping model load | 
| Year > 2025 in features | `year` removed from feature list to prevent OOD |
| Negative prediction values | Floored to 0 with `max(0, round(value))` |
| LSTM drift over long horizon | Autoregressive mode uses exogenous future features to anchor |
| Empty training data | `train_test_split` would fail — no explicit guard (relies on data always existing) |
| Feature scaler saved as tuple | Code handles both tuple format `(scaler, feat_cols, y_scaler)` and plain scaler |
| Zero-division in metrics | Protected by conditional checks (`if tot_arr_prev > 0`) |

### 3.4 UI Edge Cases

| Edge Case | System Behavior |
|-----------|-----------------|
| Cache stale after retrain | TTL-based auto-refresh (1 hour); manual clear via Streamlit menu |
| Browser window too narrow | `layout="wide"` + responsive Plotly charts |
| User navigates to admin page without admin role | `require_admin()` shows error + `st.stop()` |
| Profile is not a dict | Explicit `isinstance(profile, dict)` check → default to `{}` |
| Filter returns zero rows | Charts render empty; tables show "No data" |
| Large dataset download | CSV export uses `st.download_button()` — served in-memory |

---

## 4. Test Cases

### 4.1 Authentication Test Cases

| # | Test Case | Input | Expected Outcome | Actual Behavior |
|---|-----------|-------|-------------------|-----------------|
| A1 | Login with valid credentials | Valid email + password | Dashboard loads, sidebar shows user name | ✅ Session state set, redirect to National Overview |
| A2 | Login with invalid credentials | Wrong password | Error: "Invalid credentials." | ✅ Supabase returns error, caught and displayed |
| A3 | Login with unconfirmed email | Unverified email | Error: "Please verify your email address first." | ✅ Specific error string matched |
| A4 | Login with empty fields | Empty email or password | Error: "Please enter your email and password." | ✅ Frontend validation blocks submission |
| A5 | Login with invalid email format | "notanemail" | Error: "Please provide a valid email format." | ✅ Regex validation fails |
| A6 | Signup with all valid fields | Name, email, password ≥ 6, role | Success message, redirect to login tab | ✅ Account created, profile inserted |
| A7 | Signup with short password | Password = "abc" | Error: "Password must be at least 6 characters." | ✅ Frontend validation |
| A8 | Signup with duplicate email | Already registered email | Error: "Email already registered." | ✅ Supabase error matched |
| A9 | Signup rate limited | Many rapid signups | Error: "Too many signup attempts..." | ✅ Rate limit error matched |
| A10 | Access admin page as non-admin | Hotel Manager role user | Error: "Access Denied." + `st.stop()` | ✅ `require_admin()` blocks |

### 4.2 Profile Management Test Cases

| # | Test Case | Input | Expected Outcome |
|---|-----------|-------|-------------------|
| P1 | Update display name | New name "John Doe" | Profile card and session state updated |
| P2 | Update hotel name | "Grand Hotel Kandy" | Database row updated, success message |
| P3 | Change password (valid) | 8+ char matching passwords | "Password updated successfully!" |
| P4 | Change password (too short) | 5 char password | Error: "Password must be at least 8 characters long." |
| P5 | Change password (mismatch) | Different confirm password | Error: "Passwords do not match." |
| P6 | Delete account (correct) | Type "DELETE" | Account and profile removed, redirect to login |
| P7 | Delete account (wrong text) | Type "delete" (lowercase) | Error: "Please type 'DELETE' exactly." |
| P8 | Delete account (no service key) | SUPABASE_SERVICE_KEY missing | Error: "Backend misconfiguration" |
| P9 | Logout | Click logout button | Session cleared, redirect to auth page |

### 4.3 Data Loading Test Cases

| # | Test Case | Condition | Expected Outcome |
|---|-----------|-----------|-------------------|
| D1 | Load from Supabase (success) | Supabase online | DataFrame populated from DB |
| D2 | Load from Supabase (failure) | Supabase offline | Fallback to local CSV |
| D3 | Load with missing CSV | No local CSV exists | `st.error("Database connection failed.")` |
| D4 | Load with corrupt CSV rows | Malformed CSV lines | Bad rows skipped via `on_bad_lines="skip"` |
| D5 | Load predictions (no model filter) | `model=None` | Returns all models (XGBoost + LSTM) |
| D6 | Load predictions (filtered) | `model="xgboost"` | Returns only XGBoost predictions |
| D7 | Cache behavior | Same page reloaded within 1 hour | Data served from cache |

### 4.4 AI Model Test Cases

| # | Test Case | Input | Expected Outcome |
|---|-----------|-------|-------------------|
| M1 | XGBoost prediction (normal week) | Month=3, no festival, low rain | Arrivals ≈ baseline mean |
| M2 | XGBoost prediction (Esala Perahera) | is_esala_perahera=1, intensity=10 | Arrivals significantly above baseline |
| M3 | XGBoost prediction (COVID crisis) | is_covid_period=1 | Arrivals near zero |
| M4 | XGBoost prediction (monsoon) | is_monsoon_week=1, rainfall=300mm | Arrivals below baseline |
| M5 | LSTM 1-step prediction | Last 12 weeks of data | Prediction within reasonable range |
| M6 | LSTM 52-step autoregressive | Full 52-week future window | No extreme drift or collapse |
| M7 | Model file missing | Delete xgb_model.pkl | Warning displayed, page stops |
| M8 | Feature dimension mismatch | Extra/missing feature columns | Padding/trimming handles gracefully |
| M9 | Training pipeline complete run | `python train_models.py` | Both models saved, predictions generated, Supabase updated |
| M10 | Negative prediction guard | Model outputs negative value | Floored to 0 |

### 4.5 System Admin Test Cases

| # | Test Case | Input | Expected Outcome |
|---|-----------|-------|-------------------|
| S1 | View all users | Admin logs in | User table displayed with emails, names, roles |
| S2 | Change user role | Select user → Promote to Admin | Role updated in database |
| S3 | Delete user account | Select user → Delete | User removed from auth.users + profile |
| S4 | Trigger retraining | Click retrain button | Subprocess runs, models updated, summary displayed |
| S5 | Retraining failure | Corrupt training data | Error trace displayed with stderr |
| S6 | Upload new dataset | Upload CSV file | Master dataset overwritten |
| S7 | View training logs | Log file exists | Console output displayed |
| S8 | Clear training logs | Click clear button | Log file deleted |

### 4.6 Report Generator Test Cases

| # | Test Case | Input | Expected Outcome |
|---|-----------|-------|-------------------|
| R1 | Generate PDF report | Click download PDF | PDF file downloads with forecast tables |
| R2 | Generate Excel report | Click download Excel | XLSX file with structured data |
| R3 | AI Model Comparison | View comparison tab | XGBoost vs LSTM metrics displayed |
| R4 | No predictions available | Empty predictions table | Graceful empty state |

### 4.7 Resource Planner Test Cases

| # | Test Case | Input | Expected Outcome |
|---|-----------|-------|-------------------|
| RP1 | Capacity utilization gauge | Occupancy at 50% | Green bar, low pressure |
| RP2 | Capacity utilization gauge | Occupancy at 80% | Amber bar, medium pressure |
| RP3 | Capacity utilization gauge | Occupancy at 95% | Red bar, high pressure |
| RP4 | Monte Carlo simulation | Run 1000 iterations | Overflow probability and avg overflow rooms displayed |
| RP5 | Forward resource chart | 8-week forecast | Staff and transport bars with festival highlighting |

---

## 5. Code References

### 5.1 Validation Implementation Locations

| Validation Type | File | Lines | Description |
|----------------|------|-------|-------------|
| Email regex | `utils/auth.py` | 20-21 | `is_valid_email()` function |
| Login field check | `utils/auth.py` | 405-409 | Empty + format check |
| Signup field check | `utils/auth.py` | 463-469 | Empty + format + length check |
| Password match | `pages/8_👤_Profile.py` | 133-136 | Confirm password comparison |
| Delete confirmation | `pages/8_👤_Profile.py` | 165-166 | Exact string match "DELETE" |
| Role constraint | `sql/02_auth_schema.sql` | 6 | SQL CHECK constraint |
| Admin role constraint | `sql/03_admin_schema.sql` | 5-7 | Extended CHECK with System Administrator |
| Data type coercion | `upload_to_supabase.py` | 89-90, 126-133 | `pd.to_numeric().astype("Int64")` |
| NaN sanitization | `upload_to_supabase.py` | 39-50 | `sanitize()` + `clean_row()` |
| Feature OOD guard | `train_models.py` | 168-171 | Remove year/quarter from features |
| Prediction floor | `train_models.py` | 552-553 | `max(0, round(value))` |

### 5.2 Error Handling Logic Locations

| Error Category | File | Lines | Description |
|---------------|------|-------|-------------|
| Auth login errors | `utils/auth.py` | 421-428 | Parse Supabase error strings |
| Auth signup errors | `utils/auth.py` | 500-509 | Handle duplicate, password, rate limit |
| DB connection failed | `utils/db.py` | 61-68, 73-85, 89-100, 105-117 | Try/except → `st.error()` + empty DF |
| Missing credentials | `utils/db.py` | 38-41, 51-53 | RuntimeError |
| Model not found | `pages/3_*.py` | 270-279 | `st.warning()` + `st.stop()` |
| LSTM load failure | `pages/3_*.py` | 222-226 | Try/except, print error |
| Training crash | `pages/9_*.py` | 168-173 | CalledProcessError → show stderr |
| Profile load fallback | `utils/auth.py` | 54-62 | Try Supabase, except pass |
| Session expired | `pages/8_*.py` | 56-58 | `st.warning()` + `st.stop()` |
| Admin access denied | `utils/auth.py` | 532-539 | `st.error()` + `st.stop()` |
| Supabase push failure | `train_models.py` | 462-465 | Print error, continue with local |
| Admin service key missing | `pages/9_*.py` | 63-65 | `st.error()` + `st.stop()` |
| File upload error | `pages/9_*.py` | 185-186 | `st.error()` |
| Account deletion error | `pages/8_*.py` | 174-175, 191-192 | `st.error()` |
| JSON feature parse error | `pages/2_*.py` | 55-62, 77-82 | Try/except pass on each row |
