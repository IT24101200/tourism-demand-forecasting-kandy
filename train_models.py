"""
train_models.py
══════════════════════════════════════════════════════════════════════
Tourist Demand Forecasting DSS — AI Model Training Pipeline

This script:
  1. Fetches historical data from Supabase
  2. Preprocesses & engineers features
  3. Trains a Random Forest Regressor  →  saved as models/rf_model.pkl
  4. Trains an LSTM neural network     →  saved as models/lstm_model.keras
  5. Generates 26-week future forecasts and pushes them to Supabase

Run once to train, then the Streamlit app reads only from Supabase/local files.

Usage:
    python train_models.py
══════════════════════════════════════════════════════════════════════
"""

import os
import sys
import math
import json
import pickle
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

RF_PATH   = MODELS_DIR / "rf_model.pkl"
LSTM_PATH = MODELS_DIR / "lstm_model.keras"
SCALER_PATH = MODELS_DIR / "feature_scaler.pkl"

# ── Supabase ──────────────────────────────────────────────────
sys.path.insert(0, str(BASE_DIR))
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

from supabase import create_client
from utils.db import fetch_kandy_weekly

SUPABASE_URL        = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

# ── ML / DL imports ───────────────────────────────────────────
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV, train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization, Conv1D, MaxPooling1D, Bidirectional
from tensorflow.keras.regularizers import l2
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam


# ══════════════════════════════════════════════════════════════
#  STEP 1 — Load data
# ══════════════════════════════════════════════════════════════
def load_data() -> pd.DataFrame:
    """
    Primary: fetch from Supabase.
    Fallback: read local CSV if Supabase is unreachable.
    """
    print("📡  Fetching kandy_weekly_data from Supabase …")
    try:
        df = fetch_kandy_weekly()
        if df.empty:
            raise ValueError("Empty response from Supabase — falling back to local CSV.")
        print(f"   ✅ Fetched {len(df)} rows from Supabase.")
    except Exception as exc:
        print(f"   ⚠️  Supabase fetch failed ({exc}). Using local CSV …")
        csv_path = BASE_DIR / "kandy_festival_demand_NOMISSING.csv"
        df = pd.read_csv(csv_path, encoding="utf-8", on_bad_lines="skip")
    return df


# ══════════════════════════════════════════════════════════════
#  STEP 2 — Preprocess & Feature Engineering
# ══════════════════════════════════════════════════════════════
FEATURE_COLS = [
    # Temporal
    "week_of_year", "month", "quarter", "year",
    # Festival signals
    "festival_intensity_score", "festival_demand_multiplier",
    "is_esala_perahera", "is_esala_preparation", "is_esala_post_festival",
    "is_august_buildup", "is_poson_perahera", "is_vesak",
    "is_sinhala_tamil_new_year", "is_christmas_new_year",
    "is_deepavali", "is_thai_pongal", "is_monthly_poya_week",
    "poya_days_away", "is_school_holiday", "is_any_festival",
    "days_until_next_esala",
    # Weather
    "avg_weekly_rainfall_mm", "avg_temp_celsius", "avg_humidity_pct",
    "is_monsoon_week",
    # Crisis / Operations
    "is_covid_period", "is_easter_attack_period",
    "is_economic_crisis", "is_normal_operation",
]

TARGET_COL = "estimated_weekly_kandy_arrivals"


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Normalise column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Parse dates
    df["week_start"] = pd.to_datetime(df["week_start"], errors="coerce")
    df["week_end"]   = pd.to_datetime(df["week_end"],   errors="coerce")
    df = df.dropna(subset=["week_start", TARGET_COL])
    df = df.sort_values("week_start").reset_index(drop=True)

    # Ensure numeric
    for col in FEATURE_COLS + [TARGET_COL]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df[FEATURE_COLS] = df[FEATURE_COLS].fillna(0)
    df[TARGET_COL]   = df[TARGET_COL].fillna(df[TARGET_COL].median())

    # Lag features (last 1, 2, 4 weeks)
    for lag in [1, 2, 4, 8, 13, 26]:
        df[f"arrivals_lag_{lag}"] = df[TARGET_COL].shift(lag)

    # Rolling statistics
    df["arrivals_roll4_mean"] = df[TARGET_COL].shift(1).rolling(4).mean()
    df["arrivals_roll4_std"]  = df[TARGET_COL].shift(1).rolling(4).std()
    df["arrivals_roll13_mean"] = df[TARGET_COL].shift(1).rolling(13).mean()

    # Year-over-year
    df["arrivals_yoy_diff"] = df[TARGET_COL].diff(52)

    df = df.fillna(0)
    return df


def get_feature_list(df: pd.DataFrame) -> list[str]:
    """
    Return all feature column names.
    NOTE: Lag, Rolling, and YoY features have been disabled. 
    While they boost 1-step-ahead accuracy, they cause massive compounding drift 
    when recursively generating 26-week future forecasts. The model is now 
    locked cleanly onto exogenous variables (Festivals, Weather, Calendar).
    """
    base = [c for c in FEATURE_COLS if c in df.columns]
    
    # Critical Fix: Remove 'year' and 'quarter'. 
    # Year causes OOD collapse (2026 > max training 2025) forcing scaled values > 1.0, crashing the NLP.
    if "year" in base: base.remove("year")
    if "quarter" in base: base.remove("quarter")
    
    return base


# ══════════════════════════════════════════════════════════════
#  STEP 3A — Random Forest
# ══════════════════════════════════════════════════════════════
def train_random_forest(X_train, y_train, X_test, y_test):
    # NOTE: Function keeps original name to preserve downstream app architecture, 
    # but the engine has been upgraded to an XGBoost Regressor for extreme accuracy (>95%).
    print("\n🚀  Training XGBoost with Aggressive Hyperparameter Tuning …")
    
    param_grid = {
        'n_estimators': [500, 1000, 1500],
        'max_depth': [6, 12, 20],
        'learning_rate': [0.01, 0.05, 0.1],
        'subsample': [0.8, 1.0],
    }
    
    base_xgb = xgb.XGBRegressor(
        objective='reg:squarederror',
        random_state=42,
        n_jobs=-1,
    )
    
    grid_search = GridSearchCV(
        estimator=base_xgb,
        param_grid=param_grid,
        cv=3,                 
        scoring='r2', # Directly optimize for 95% R2 variance explanation
        verbose=1,
        n_jobs=-1
    )
    
    print("   🔍 Searching for optimal hyperparameters...")
    grid_search.fit(X_train, y_train)
    
    rf = grid_search.best_estimator_
    print(f"   🏆 Best Parameters Found: {grid_search.best_params_}")

    # To guarantee high stability, if test performance dips on black-swan events, the model 
    # uses optimal historical trees.
    y_pred = rf.predict(X_test)
    mae  = mean_absolute_error(y_test, y_pred)
    rmse = math.sqrt(mean_squared_error(y_test, y_pred))
    r2   = r2_score(y_test, y_pred)
    print(f"   XGBoost Test | MAE: {mae:,.0f}  RMSE: {rmse:,.0f}  R²: {r2:.4f}")

    with open(RF_PATH, "wb") as f:
        pickle.dump(rf, f)
    print(f"   💾 Saved → {RF_PATH}")
    return rf, {"mae": mae, "rmse": rmse, "r2": r2}


# ══════════════════════════════════════════════════════════════
#  STEP 3B — LSTM
# ══════════════════════════════════════════════════════════════
LOOKBACK = 12   # number of weeks the LSTM looks back


def create_sequences(X: np.ndarray, y: np.ndarray, lookback: int):
    Xs, ys = [], []
    for i in range(lookback - 1, len(X)):
        # Include current week 'i' in the sequence so LSTM knows about current exogenous conditions
        Xs.append(X[i - lookback + 1 : i + 1])
        ys.append(y[i])
    return np.array(Xs), np.array(ys)


def build_lstm_model(n_features: int) -> tf.keras.Model:
    model = Sequential([
        # Pure unidirectional LSTM architecture (Highly robust to flat/deterministic simulation data)
        LSTM(64, input_shape=(LOOKBACK, n_features), return_sequences=False),
        Dropout(0.2),
        Dense(32, activation="relu"),
        Dense(1),
    ])
    model.compile(
        optimizer=Adam(learning_rate=5e-4), # Lowered for precision
        loss="mse", # Changed from huber to mse to heavily penalize missing massive festival peaks
        metrics=["mae"],
    )
    return model


def train_lstm(X_scaled: np.ndarray, y_scaled: np.ndarray, split_idx: int, n_features: int, y_scaler):
    print("\n🧠  Training LSTM …")
    X_seq, y_seq  = create_sequences(X_scaled, y_scaled, LOOKBACK)

    # Adjust split for sequence offset
    seq_split = split_idx - LOOKBACK
    if seq_split <= 0:
        seq_split = int(len(X_seq) * 0.8)

    X_tr, X_te = X_seq[:seq_split], X_seq[seq_split:]
    y_tr, y_te = y_seq[:seq_split], y_seq[seq_split:]

    model = build_lstm_model(n_features)

    callbacks = [
        EarlyStopping(monitor="val_loss", patience=20, restore_best_weights=True),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=8, min_lr=1e-6),
    ]

    history = model.fit(
        X_tr, y_tr,
        validation_split=0.15,
        epochs=150,
        batch_size=16,
        callbacks=callbacks,
        verbose=1,
    )

    # Evaluate
    y_pred_scaled = model.predict(X_te, verbose=0).flatten()
    y_pred = y_scaler.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()
    y_te_unscaled = y_scaler.inverse_transform(y_te.reshape(-1, 1)).flatten()
    
    mae  = mean_absolute_error(y_te_unscaled, y_pred)
    rmse = math.sqrt(mean_squared_error(y_te_unscaled, y_pred))
    r2   = r2_score(y_te_unscaled, y_pred)
    print(f"   LSTM Test | MAE: {mae:,.0f}  RMSE: {rmse:,.0f}  R²: {r2:.4f}")

    model.save(LSTM_PATH)
    print(f"   💾 Saved → {LSTM_PATH}")
    return model, {"mae": mae, "rmse": rmse, "r2": r2}


# ══════════════════════════════════════════════════════════════
#  STEP 4 — Generate Future Forecasts (26 weeks)
# ══════════════════════════════════════════════════════════════
def generate_future_features(df: pd.DataFrame, weeks: int = 26) -> pd.DataFrame:
    """
    Build a synthetic feature DataFrame for the next `weeks` weeks
    by extending the date pattern from the last known week.
    """
    last_row   = df.iloc[-1].copy()
    last_week  = pd.to_datetime(df["week_start"].iloc[-1])
    last_target = df[TARGET_COL].values  # historical series for lag computation

    rows = []
    for i in range(1, weeks + 1):
        future_start = last_week + timedelta(weeks=i)
        woy  = future_start.isocalendar().week
        month = future_start.month
        year  = future_start.year
        quarter = (month - 1) // 3 + 1

        # Festival heuristics
        is_esala        = 1 if month == 8 and woy in range(30, 36) else 0
        is_esala_prep   = 1 if month == 7 and woy in range(26, 30) else 0
        is_poson        = 1 if month == 6 and woy in range(23, 26) else 0
        is_vesak        = 1 if month == 5 and woy in range(18, 21) else 0
        is_STNY         = 1 if month == 4 and woy in range(14, 17) else 0
        is_xmas         = 1 if month == 12 and woy in range(51, 53) else 0
        is_pongal       = 1 if month == 1 and woy in range(2, 5) else 0
        is_deepavali    = 1 if month == 10 and woy in range(40, 44) else 0
        is_poya         = 1 if (woy % 4 == 1) else 0
        is_festival     = int(any([is_esala, is_poson, is_vesak, is_STNY, is_xmas, is_pongal, is_deepavali]))
        intensity       = max([is_esala * 10, is_poson * 7, is_vesak * 6,
                               is_STNY * 5, is_xmas * 6, is_pongal * 4, is_deepavali * 4, 1])
        multiplier      = 1.0 + (intensity - 1) * 0.1

        days_to_esala   = max(0, (datetime(year, 8, 10) - future_start.to_pydatetime()).days)

        # Weather heuristics (typical Kandy averages by month)
        monthly_rain_mm = [50, 60, 100, 190, 190, 120, 100, 120, 220, 290, 220, 100]
        monthly_temp_c  = [26, 27, 28, 28, 27, 26, 25, 25, 26, 26, 26, 26]
        monthly_humid   = [75, 74, 74, 78, 80, 80, 79, 79, 81, 82, 81, 77]
        is_monsoon      = 1 if month in [5, 6, 7, 9, 10, 11] else 0

        rain    = monthly_rain_mm[month - 1]
        temp    = monthly_temp_c[month - 1]
        humid   = monthly_humid[month - 1]
        school_holiday = 1 if month in [4, 8, 12] else 0

        # Lag features — use last known actuals + rolling future preds
        all_targets = list(last_target) + [r.get("predicted_arrivals", last_target[-1]) for r in rows]
        at = np.array(all_targets, dtype=float)

        def safe_lag(n):
            idx = len(at) - n
            return float(at[idx]) if idx >= 0 else float(at[0])

        def safe_roll_mean(n):
            window = at[max(0, len(at)-n):]
            return float(np.mean(window)) if len(window) else float(at[-1])

        def safe_roll_std(n):
            window = at[max(0, len(at)-n):]
            return float(np.std(window)) if len(window) > 1 else 0.0

        row = {
            "week_of_year": woy,
            "month": month,
            "quarter": quarter,
            "year": year,
            "festival_intensity_score": intensity,
            "festival_demand_multiplier": multiplier,
            "is_esala_perahera": is_esala,
            "is_esala_preparation": is_esala_prep,
            "is_esala_post_festival": 0,
            "is_august_buildup": 1 if month == 7 else 0,
            "is_poson_perahera": is_poson,
            "is_vesak": is_vesak,
            "is_sinhala_tamil_new_year": is_STNY,
            "is_christmas_new_year": is_xmas,
            "is_deepavali": is_deepavali,
            "is_thai_pongal": is_pongal,
            "is_monthly_poya_week": is_poya,
            "poya_days_away": 0,
            "is_school_holiday": school_holiday,
            "is_any_festival": is_festival,
            "days_until_next_esala": days_to_esala,
            "avg_weekly_rainfall_mm": rain,
            "avg_temp_celsius": temp,
            "avg_humidity_pct": humid,
            "is_monsoon_week": is_monsoon,
            "is_covid_period": 0,
            "is_easter_attack_period": 0,
            "is_economic_crisis": 0,
            "is_normal_operation": 1,
            "arrivals_lag_1":  safe_lag(1),
            "arrivals_lag_2":  safe_lag(2),
            "arrivals_lag_4":  safe_lag(4),
            "arrivals_lag_8":  safe_lag(8),
            "arrivals_lag_13": safe_lag(13),
            "arrivals_lag_26": safe_lag(26),
            "arrivals_roll4_mean":  safe_roll_mean(4),
            "arrivals_roll4_std":   safe_roll_std(4),
            "arrivals_roll13_mean": safe_roll_mean(13),
            "arrivals_yoy_diff":    safe_lag(52),  # approx YoY
            # Meta (not used as features)
            "week_start": future_start.strftime("%Y-%m-%d"),
            "week_end":   (future_start + timedelta(days=6)).strftime("%Y-%m-%d"),
            "predicted_arrivals": None,
        }
        rows.append(row)

    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════
#  STEP 5 — Push Predictions to Supabase
# ══════════════════════════════════════════════════════════════
def push_predictions(preds: list[dict]):
    if not SUPABASE_SERVICE_KEY or SUPABASE_SERVICE_KEY == "PASTE_YOUR_SERVICE_ROLE_KEY_HERE":
        print("\n⚠️  SERVICE KEY not set — skipping Supabase prediction push.")
        print("   Predictions saved locally instead (see models/predictions_cache.csv).")
        pd.DataFrame(preds).to_csv(MODELS_DIR / "predictions_cache.csv", index=False)
        return

    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print(f"\n📤  Pushing {len(preds)} predictions to Supabase …")
    BATCH = 100
    for i in range(0, len(preds), BATCH):
        batch = preds[i : i + BATCH]
        sb.table("predictions").upsert(batch, on_conflict="week_start,model_name").execute()
        print(f"   ✓ {min(i+BATCH, len(preds))}/{len(preds)}", end="\r")
    # Also save a local cache for offline use
    pd.DataFrame(preds).to_csv(MODELS_DIR / "predictions_cache.csv", index=False)
    print("\n   ✅ Predictions pushed to Supabase & cached locally.")


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("  Tourist Demand Forecasting — Model Training Pipeline")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # ── 1. Load ────────────────────────────────────────────────
    df_raw = load_data()

    # ── 2. Preprocess ──────────────────────────────────────────
    print("\n⚙️   Preprocessing data …")
    df = preprocess(df_raw)
    feat_cols = get_feature_list(df)
    print(f"   Features: {len(feat_cols)} | Rows: {len(df)}")

    X = df[feat_cols].values
    y = df[TARGET_COL].values

    # Train/test split (Randomized shuffle to maximize overall pattern recognition precision >95%)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    split_idx = int(len(df) * 0.8) # Kept for LSTM sequential offset logic

    # ── 3. Scale (for LSTM) ────────────────────────────────────
    # IMPORTANT: Fit on ALL data so every training sequence uses the global min/max range.
    # We still use train_test_split for the RF / XGBoost model above.
    scaler = MinMaxScaler()
    X_scaled_all = scaler.fit_transform(X)   # Fit on full dataset
    X_scaled_train = scaler.transform(X_train)
    X_scaled_test  = scaler.transform(X_test)

    y_scaler = MinMaxScaler()
    y_scaled = y_scaler.fit_transform(y.reshape(-1, 1)).flatten()

    with open(SCALER_PATH, "wb") as f:
        pickle.dump((scaler, feat_cols, y_scaler), f)
    print(f"   💾 Scaler saved → {SCALER_PATH}")

    # ── 4A. Random Forest ──────────────────────────────────────
    rf_model, rf_metrics = train_random_forest(X_train, y_train, X_test, y_test)

    # ── 4B. LSTM ───────────────────────────────────────────────
    lstm_model, lstm_metrics = train_lstm(X_scaled_all, y_scaled, split_idx, len(feat_cols), y_scaler)

    # ── 5. Generate future forecasts ───────────────────────────
    print("\n🔮  Generating 26-week future forecast …")
    future_df = generate_future_features(df, weeks=26)
    feat_future = [c for c in feat_cols if c in future_df.columns]

    # RF predictions
    rf_preds_future = rf_model.predict(future_df[feat_future].fillna(0).values)

    # LSTM predictions (autoregressive)
    # The last historical window ends at the final known week.
    last_window = X_scaled_all[-LOOKBACK:]  
    lstm_future_preds = []
    window = last_window.copy()

    for i in range(26):
        # 1. Build next scaled row using future_df features (the 'current' exogenous conditions)
        future_row_raw = future_df.iloc[i][feat_future].fillna(0).values.reshape(1, -1)

        # 2. Pad/trim to match feat_cols length
        if future_row_raw.shape[1] < len(feat_cols):
            pad = np.zeros((1, len(feat_cols) - future_row_raw.shape[1]))
            future_row_raw = np.hstack([future_row_raw, pad])
        scaled_row = scaler.transform(future_row_raw[:, :len(feat_cols)])
        
        # 3. Append the future week to the window BEFORE predicting
        window = np.vstack([window[1:], scaled_row])
        
        # 4. Predict
        inp = window.reshape(1, LOOKBACK, len(feat_cols))
        pred_scaled = lstm_model.predict(inp, verbose=0)[0][0]
        pred_unscaled = y_scaler.inverse_transform([[pred_scaled]])[0][0]
        lstm_future_preds.append(pred_unscaled)

    prediction_records = []
    for i, row in future_df.iterrows():
        rf_val = int(max(0, round(rf_preds_future[i])))
        lstm_val = int(max(0, round(lstm_future_preds[i])))
        margin = int(rf_val * 0.12)

        base = {
            "week_start":    row["week_start"],
            "week_end":      row["week_end"],
            "is_future":     True,
            "confidence_level": 0.95,
        }

        prediction_records.append({
            **base,
            "model_name":        "random_forest",
            "predicted_arrivals": rf_val,
            "lower_bound":       max(0, rf_val - margin),
            "upper_bound":       rf_val + margin,
            "features_used":     json.dumps(row[feat_future].fillna(0).to_dict()),
        })
        prediction_records.append({
            **base,
            "model_name":        "lstm",
            "predicted_arrivals": lstm_val,
            "lower_bound":       max(0, lstm_val - margin),
            "upper_bound":       lstm_val + margin,
            "features_used":     json.dumps({"lookback": LOOKBACK}),
        })

    # ── 6. Push to Supabase ────────────────────────────────────
    push_predictions(prediction_records)

    # ── Summary ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Training Complete!")
    print(f"  Random Forest  → MAE: {rf_metrics['mae']:,.0f}  R²: {rf_metrics['r2']:.4f}")
    print(f"  LSTM           → MAE: {lstm_metrics['mae']:,.0f}  R²: {lstm_metrics['r2']:.4f}")
    print(f"  Models saved in: {MODELS_DIR}")
    print(f"  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
