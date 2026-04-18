import sys
import os
sys.path.append(os.path.abspath("e:/SLIIT/2Y 2S/IT2021 - Artificial Intelligence and Machine Learning Project/tourist-forecast-kandy"))

from utils.db import fetch_predictions

df = fetch_predictions()
if not df.empty:
    import pandas as pd
    df["week_start"] = pd.to_datetime(df["week_start"])
    df = df[df["model_name"] == "xgboost"].sort_values("week_start")
    print("Supabase Data:")
    print(df[["week_start", "predicted_arrivals"]].tail(50))
else:
    print("Supabase Empty.")
