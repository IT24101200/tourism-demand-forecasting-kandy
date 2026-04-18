# ══════════════════════════════════════════════════════════════
#  DEPLOYMENT GUIDE — Tourist Demand Forecasting DSS
#  Streamlit Community Cloud (Recommended, FREE)
# ══════════════════════════════════════════════════════════════

## ✅ Pre-deployment checklist

Before deploying, make sure you have completed:

1. [ ] Ran `supabase_schema.sql` in your Supabase SQL Editor
2. [ ] Ran `python upload_to_supabase.py` to upload all CSV data
3. [ ] Ran `python train_models.py` to train models and push predictions
4. [ ] Pushed your project to a **public GitHub repository**

---

## 📁 Step 0 — Push to GitHub

```bash
# In your project folder (tourist-forecast-kandy):
git init
git add .
git commit -m "Initial DSS commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/tourist-forecast-kandy.git
git push -u origin main
```

> ⚠️ Make sure `.gitignore` is in place — it was already created for you.  
> The `.env` file and `models/*.pkl/.h5/.keras` files will NOT be pushed.

---

## 🚀 Step 1 — Deploy on Streamlit Community Cloud

1. Go to **[share.streamlit.io](https://share.streamlit.io)** and sign in with GitHub.
2. Click **"New app"**.
3. Fill in:
   - **Repository**: `YOUR_USERNAME/tourist-forecast-kandy`
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. Click **"Advanced settings"** → **"Secrets"** and paste:

```toml
SUPABASE_URL = "https://coxfyqezwrbensbvcuxl.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNveGZ5cWV6d3JiZW5zYnZjdXhsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM5OTIwNDIsImV4cCI6MjA4OTU2ODA0Mn0.o9QrMgNCXY0TN6hKOfatra907CPGtc5WCmAP2oh4PSI"
```

5. Click **"Deploy!"**

Your app will be live at:
`https://YOUR_USERNAME-tourist-forecast-kandy-app-XXXX.streamlit.app`

---

## 📦 Step 2 — Handle the Trained Models

> **Important:** Because `models/*.pkl` and `models/*.keras` are in `.gitignore`,  
> they won't be on GitHub. The What-If Simulator needs the RF model to work.

**Option A (Recommended): Remove models from .gitignore for this project**

In your `.gitignore`, change:
```
models/
```
to:
```
models/*.h5
# (keep .pkl and .keras files so RF model is available on cloud)
```
Then commit and push the `models/` folder:
```bash
git add models/rf_model.pkl models/feature_scaler.pkl
git commit -m "Add trained models"
git push
```

**Option B: Re-run training from Supabase on cloud**

The `train_models.py` script can be triggered from a terminal (not from Streamlit Cloud directly). The forecast data is already in Supabase, so Pages 1 & 2 always work. Only the What-If Simulator needs the local `.pkl` file.

---

## 🔁 Alternative: Deploy on Render.com

1. Go to [render.com](https://render.com) and create a free account.
2. Click **"New" → "Web Service"** and connect your GitHub repo.
3. Configure:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
4. Under **"Environment Variables"**, add:
   - `SUPABASE_URL` = `https://coxfyqezwrbensbvcuxl.supabase.co`
   - `SUPABASE_ANON_KEY` = `eyJhbGci...`
5. Click **"Create Web Service"**.

---

## 🏃 Running Locally

```powershell
# Install dependencies
pip install -r requirements.txt

# (Optional) Train models first
python upload_to_supabase.py   # only needed once
python train_models.py          # trains RF + LSTM, pushes predictions

# Start the app
streamlit run app.py
```

Open your browser to: `http://localhost:8501`
