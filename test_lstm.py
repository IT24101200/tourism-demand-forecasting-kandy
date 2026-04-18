import sys
import os
import pandas as pd
import datetime

sys.path.append(os.path.abspath("e:/SLIIT/2Y 2S/IT2021 - Artificial Intelligence and Machine Learning Project/tourist-forecast-kandy"))

from utils.db import fetch_predictions

df = fetch_predictions()
if not df.empty:
    df["week_start"] = pd.to_datetime(df["week_start"])
    # get xgboost
    xgb = df[df["model_name"] == "xgboost"].sort_values("week_start")
    # get lstm
    lstm = df[df["model_name"] == "lstm"].sort_values("week_start")
    
    today = pd.Timestamp(datetime.date.today())
    print("Today is:", today)
    print("XGBoost Current:", xgb[(xgb["week_start"] <= today) & (xgb["week_end"] >= today)]["predicted_arrivals"].values)
    print("LSTM Current:", lstm[(lstm["week_start"] <= today) & (lstm["week_end"] >= today)]["predicted_arrivals"].values)
