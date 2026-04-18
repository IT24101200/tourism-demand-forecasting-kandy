import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.auth import require_auth, load_user_profile
from utils.db import get_client
from utils.theme import apply_custom_theme, get_theme, render_page_banner
from utils.sidebar import render_sidebar

require_auth()
theme = get_theme()

st.set_page_config(
    page_title="Profile | Tourist DSS",
    page_icon="👤", layout="wide"
)

apply_custom_theme()
render_sidebar(active_page="Profile Management")

st.markdown(f"""
<style>
.profile-card {{
    background: {theme['surface_low']};
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    border: 1px solid {theme['border']};
    border-top: 4px solid {theme['accent_dim']};
    margin-bottom: 2rem;
}}
.profile-stat {{ margin-bottom: 1.25rem; }}
.profile-label {{
    font-size: 0.85rem; color: {theme['text_muted']}; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.3rem;
}}
.profile-value {{ font-size: 1.15rem; color: {theme['text_main']}; font-weight: 700; }}
</style>
""", unsafe_allow_html=True)

render_page_banner(
    title="Account Settings",
    subtitle="Manage your personal information, security preferences, and system access.",
    icon="👤",
)

user = st.session_state.get("user")
profile = st.session_state.get("user_profile")

# Graceful fallback — build from user metadata rather than hard-stopping
if not profile and user:
    profile = load_user_profile(user)
    st.session_state["user_profile"] = profile

if not user:
    st.warning("Session expired. Please log out and log back in.")
    st.stop()

# Ensure profile is always a dict
if not isinstance(profile, dict):
    profile = {}



tab1, tab2 = st.tabs(["👤 Profile Information", "🔐 Security Settings"])

with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    col_info, col_edit = st.columns([1, 1.2], gap="large")
    
    with col_info:
        st.markdown("#### Your Credentials")
        st.markdown(f"""
        <div class="profile-card">
            <div class="profile-stat">
                <div class="profile-label">Email Address</div>
                <div class="profile-value">{user.email}</div>
            </div>
            <div class="profile-stat">
                <div class="profile-label">Full Name</div>
                <div class="profile-value">{profile.get('full_name', 'N/A')}</div>
            </div>
            <div class="profile-stat">
                <div class="profile-label">System Role</div>
                <div class="profile-value">{profile.get('role', 'N/A')}</div>
            </div>
            <div class="profile-stat">
                <div class="profile-label">Organization / Hotel</div>
                <div class="profile-value">{profile.get('hotel_name', 'N/A')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_edit:
        st.markdown("#### Update Information")
        st.caption("Keep your public profile up to date for reports and logging.")
        
        with st.form("update_profile_form"):
            new_name = st.text_input("Full Name", value=profile.get('full_name', ''))
            new_hotel = st.text_input("Organization / Hotel Name", value=profile.get('hotel_name', ''))
            submit = st.form_submit_button("Save Changes", type="primary")
            
            if submit:
                try:
                    sb = get_client()
                    resp = sb.table("user_profiles").update({
                        "full_name": new_name,
                        "hotel_name": new_hotel
                    }).eq("id", user.id).execute()
                    
                    if resp.data:
                        st.session_state["user_profile"] = resp.data[0]
                        st.success("✅ Profile updated successfully!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Failed to update profile: {e}")

with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    col_sec1, col_sec2 = st.columns([1, 1], gap="large")
    
    with col_sec1:
        st.markdown("#### Change Password")
        st.caption("Ensure your account is using a long, random password to stay secure.")
        
        with st.form("change_password_form"):
            new_pass = st.text_input("New Password", type="password")
            confirm_pass = st.text_input("Confirm New Password", type="password")
            submit_pass = st.form_submit_button("Update Password", type="primary")
            
            if submit_pass:
                if len(new_pass) < 8:
                    st.error("❌ Password must be at least 8 characters long.")
                elif new_pass != confirm_pass:
                    st.error("❌ Passwords do not match. Please try again.")
                else:
                    try:
                        sb = get_client()
                        res = sb.auth.update_user({"password": new_pass})
                        if res.user:
                            st.success("✅ Password updated successfully! Next time you log in, please use the new password.")
                    except Exception as e:
                        st.error(f"Failed to update password: {str(e)}")
                        
    with col_sec2:
        st.markdown("#### Security Recommendations")
        st.info("""
        **Best Practices:**
        * Use at least 12 characters
        * Mix uppercase, lowercase, numbers, and symbols
        * Do not reuse passwords from other sites
        * Do not share your login credentials with colleagues
        """)
        
        st.markdown("<br>#### Danger Zone", unsafe_allow_html=True)
        st.caption("Permanently delete your account and all associated data. This action cannot be undone.")
        
        with st.form("delete_account_form"):
            st.error("⚠️ Warning: This will permanently erase your profile.")
            confirm_del = st.text_input("Type 'DELETE' to confirm", placeholder="DELETE")
            submit_del = st.form_submit_button("Permanently Delete Account", use_container_width=True)
            
            if submit_del:
                if confirm_del != "DELETE":
                    st.error("Please type 'DELETE' exactly to confirm your choice.")
                else:
                    try:
                        import os
                        from supabase import create_client
                        s_url = os.environ.get("SUPABASE_URL")
                        s_key = os.environ.get("SUPABASE_SERVICE_KEY")
                        
                        if not s_key:
                            st.error("Backend misconfiguration: Missing service key constraint.")
                        else:
                            admin_sb = create_client(s_url, s_key)
                            
                            # First manually drop from profile
                            try:
                                admin_sb.table("user_profiles").delete().eq("id", user.id).execute()
                            except:
                                pass
                                
                            # Delete from auth.users via admin
                            admin_sb.auth.admin.delete_user(user.id)
                            
                            st.session_state["user"] = None
                            st.session_state["user_profile"] = None
                            st.rerun()
                    except Exception as e:
                        st.error(f"Deletion failed: {e}")

st.divider()
col_btn, _ = st.columns([1, 4])
with col_btn:
    if st.button("Logout of Session", type="primary", use_container_width=True):
        try:
            sb = get_client()
            sb.auth.sign_out()
        except:
            pass
        st.session_state["user"] = None
        st.session_state["user_profile"] = None
        st.rerun()
