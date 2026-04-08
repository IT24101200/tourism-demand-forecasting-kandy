"""
pages/9_⚙️_System_Admin.py  —  System Administration & MLOps
"""
import sys
import os
import subprocess
from pathlib import Path
import pandas as pd
import streamlit as st

# Setup Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.auth import require_admin
from utils.sidebar import render_sidebar
from utils.theme import apply_custom_theme, render_page_banner
from utils.db import get_service_client

# 1. Require Admin Access 
require_admin()

st.set_page_config(
    page_title="System Admin | Kandy Tourism DSS",
    page_icon="⚙️",
    layout="wide"
)

apply_custom_theme()
render_sidebar(active_page="System Admin")

render_page_banner(
    title="System Administration",
    subtitle="Elevated command center for access control, MLOps, and server infrastructure.",
    icon="⚙️",
)

st.markdown("""
<style>
.admin-card {
    background: rgba(19, 27, 46, 0.4);
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 12px; padding: 20px; margin-bottom: 20px;
}
.admin-card h4 { color: #8ed5ff; margin-top: 0; font-family: 'Manrope', sans-serif;}
.terminal {
    background: #000; color: #0f0; font-family: monospace;
    padding: 15px; border-radius: 8px; font-size: 0.8rem;
    height: 300px; overflow-y: scroll;
}
</style>
""", unsafe_allow_html=True)

# Helper function to get service client securely
@st.cache_resource
def init_srv_client():
    try:
        return get_service_client()
    except Exception as e:
        return None

sb_admin = init_srv_client()

if not sb_admin:
    st.error("Admin capabilities suspended: Service key not configured in backend.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["👥 Access Management", "🧠 MLOps Engine", "🛠️ System Logs"])

with tab1:
    st.markdown("<div class='admin-card'><h4>User Profiles Database</h4>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns([2, 1])
    try:
        resp = sb_admin.table("user_profiles").select("*").order("created_at").execute()
        users_df = pd.DataFrame(resp.data)
        if not users_df.empty:
            with col_a:
                st.dataframe(
                    users_df[["email", "full_name", "role", "hotel_name"]], 
                    use_container_width=True, hide_index=True
                )
            
            with col_b:
                st.markdown("**Update User Role**")
                selected_email = st.selectbox("Select User by Email", users_df["email"].tolist())
                new_role = st.selectbox("Promote/Demote to", ["System Administrator", "Hotel Manager", "Tour Operator", "Government Official", "Other"])
                
                if st.button("Apply Role Change", type="primary"):
                    target_id = users_df[users_df["email"] == selected_email].iloc[0]["id"]
                    try:
                        sb_admin.table("user_profiles").update({"role": new_role}).eq("id", target_id).execute()
                        st.success(f"Role updated successfully for {selected_email}.")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Failed to update role: {err}")
                        
                st.divider()
                st.markdown("**Danger Zone**")
                del_email = st.selectbox("Select User to Terminate", users_df["email"].tolist(), key="del_mail")
                if st.button("Delete User Account", type="primary"):
                    target_id = users_df[users_df["email"] == del_email].iloc[0]["id"]
                    try:
                        sb_admin.auth.admin.delete_user(target_id)
                        st.success(f"User {del_email} permanently removed from the system.")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Server refused deletion. Error: {err}")
        else:
            st.info("No external user profiles found in database.")
    except Exception as e:
        st.error(f"Failed to fetch profiles: {e}")
        
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<div class='admin-card'><h4>AI Pipeline Override</h4>", unsafe_allow_html=True)
    st.markdown("Use this terminal to force an off-schedule re-training of the Machine Learning models. This will overwrite the `predictions_cache.csv` and broadcast new data to all users.")
    
    if st.button("🚀 Trigger Model Retraining (52 Weeks)", use_container_width=True):
        st.info("Initiating `train_models.py` subprocess — this takes several minutes. Keep the page open.")
        try:
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf-8"
            env["TF_ENABLE_ONEDNN_OPTS"] = "0"

            cmd = [sys.executable, str(Path(__file__).parent.parent / "train_models.py")]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding="utf-8", env=env)
            output = result.stdout

            # ── Parse push summary from output ──────────────────────────
            rows_pushed, date_start, date_end, supabase_ok = None, None, None, False

            for line in output.splitlines():
                if "Saved" in line and "records to" in line:
                    parts = line.strip().split()
                    for i, p in enumerate(parts):
                        if p.isdigit():
                            rows_pushed = int(p)
                            break
                if "Date range:" in line:
                    parts = line.split("Date range:")[-1].strip().split("-->")
                    if len(parts) == 2:
                        date_start = parts[0].strip()
                        date_end   = parts[1].strip()
                if "SUCCESS:" in line and "rows pushed to Supabase" in line:
                    supabase_ok = True

            # ── Display summary cards ────────────────────────────────────
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Weeks Generated", f"{rows_pushed // 2 if rows_pushed else '?'}", "52-week horizon")
            with col2:
                st.metric("Forecast Window", f"{date_start or '?'}", f"→ {date_end or '?'}")
            with col3:
                if supabase_ok:
                    st.success("☁️ Supabase: PUSHED")
                else:
                    st.warning("💾 Supabase: LOCAL ONLY")

            st.success("✅ Models successfully re-trained and predictions refreshed.")
            with st.expander("Show Full Console Output"):
                st.code(output, language="bash")

            log_path = Path(__file__).parent.parent / "models" / "training_log.txt"
            with open(log_path, "w", encoding="utf-8") as lf:
                lf.write(output)

        except subprocess.CalledProcessError as e:
            st.error("❌ Model training failed. View trace below.")
            with st.expander("Show Error Trace", expanded=True):
                st.code(e.stderr, language="bash")
        except Exception as e:
            st.error(f"Execution Error: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='admin-card'><h4>Base Data Ingestion</h4>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload new historical dataset (kandy_festival_demand_NOMISSING.csv)", type="csv")
    if uploaded_file is not None:
        if st.button("Overwrite Server Master Data"):
            try:
                dest_path = Path(__file__).parent.parent / "kandy_festival_demand_NOMISSING.csv"
                with open(dest_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("Master dataset updated! Please retrain models to propagate changes.")
            except Exception as e:
                st.error(f"Failed to overwrite data: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown("<div class='admin-card'><h4>Server Activity Logs</h4>", unsafe_allow_html=True)
    log_file = Path(__file__).parent.parent / "models" / "training_log.txt"
    if log_file.exists():
        log_content = log_file.read_text(errors="replace")
        st.code(log_content, language="bash")
        if st.button("Clear Log"):
            log_file.unlink()
            st.rerun()
    else:
        st.info("No server logs found. System is nominal.")
    st.markdown("</div>", unsafe_allow_html=True)
