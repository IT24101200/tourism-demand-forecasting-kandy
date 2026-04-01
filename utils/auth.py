import streamlit as st
import re
import base64
from utils.db import get_client as get_supabase_client


def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()


def init_session_state():
    if "user" not in st.session_state:
        st.session_state["user"] = None
    if "user_profile" not in st.session_state:
        st.session_state["user_profile"] = None


def is_valid_email(email: str) -> bool:
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email) is not None


def toggle_auth_mode():
    st.session_state['auth_mode'] = (
        'signup' if st.session_state.get('auth_mode', 'login') == 'login' else 'login'
    )


def load_user_profile(user):
    """
    Build user_profile dict from available sources:
    1. user.user_metadata (set at sign-up — always available)
    2. Supabase user_profiles table (if it exists)
    Returns a plain dict always — never None.
    """
    # Start with metadata from the auth user object
    meta = {}
    if hasattr(user, 'user_metadata') and user.user_metadata:
        meta = dict(user.user_metadata)
    elif hasattr(user, 'identities') and user.identities:
        # Some Supabase versions nest metadata differently
        meta = {}

    profile = {
        "full_name": meta.get("full_name") or meta.get("name") or "",
        "hotel_organization": meta.get("hotel_organization") or "",
        "hotel_name": meta.get("hotel_organization") or meta.get("hotel_name") or "",
        "role": meta.get("role") or "Tourism Analyst",
        "email": getattr(user, 'email', ""),
    }

    # Optionally try fetching from a user_profiles table (non-blocking)
    try:
        sb = get_supabase_client()
        resp = sb.table("user_profiles").select("*").eq("id", user.id).limit(1).execute()
        if resp.data:
            db_row = resp.data[0]
            # Merge DB row over metadata defaults
            profile.update({k: v for k, v in db_row.items() if v})
    except Exception:
        pass  # Table may not exist — that's fine, we use metadata

    return profile


def render_auth_page():
    init_session_state()
    if 'auth_mode' not in st.session_state:
        st.session_state['auth_mode'] = 'login'
    mode = st.session_state['auth_mode']

    # ── CSS injected once before any layout ─────────────────────────────────
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Manrope:wght@700;800&display=swap');

    /* Hide chrome */
    #MainMenu, header, footer { visibility: hidden !important; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* Zero out Streamlit padding — target BOTH old and new block container names */
    div[data-testid="stMainBlockContainer"],
    div[data-testid="stAppViewBlockContainer"],
    .block-container {
        padding: 0 !important;
        max-width: 100vw !important;
    }

    /* Background */
    .stApp { background: #070E20 !important; font-family: 'Inter', sans-serif; }

    /* Blobs */
    .auth-blobs { position:fixed;inset:0;z-index:0;overflow:hidden;pointer-events:none; }
    .blob { position:absolute;border-radius:50%;filter:blur(90px);
            animation:drift 14s ease-in-out infinite alternate; }
    .blob-1 { width:520px;height:520px;background:rgba(14,165,233,0.28);
              top:-120px;left:-120px;animation-duration:15s; }
    .blob-2 { width:380px;height:380px;background:rgba(99,102,241,0.22);
              bottom:-80px;right:-80px;animation-duration:11s; }
    @keyframes drift {
        0%   { transform:translate(0,0) scale(1); }
        100% { transform:translate(20px,-15px) scale(0.95); }
    }

    /* Column borders & bg */
    [data-testid="stHorizontalBlock"] { gap:0 !important; align-items:stretch !important; }

    /* Left column background */
    [data-testid="stHorizontalBlock"] > [data-testid="stVerticalBlock"]:first-child {
        background: linear-gradient(155deg,rgba(6,13,31,0.97) 0%,rgba(14,165,233,0.06) 100%);
        border-right: 1px solid rgba(56,189,248,0.13);
    }

    /* Right column background */
    [data-testid="stHorizontalBlock"] > [data-testid="stVerticalBlock"]:last-child {
        background: rgba(9,16,34,0.95);
    }

    /* ── Left hero div ─────────────────────────────────────── */
    .auth-hero {
        padding: 56px 48px;
        display:flex; flex-direction:column; justify-content:center;
        min-height: 100vh; box-sizing:border-box;
    }
    .hero-eyebrow {
        display:inline-flex;align-items:center;gap:7px;
        background:rgba(56,189,248,0.1);border:1px solid rgba(56,189,248,0.28);
        color:#38BDF8;font-size:0.67rem;font-weight:700;letter-spacing:0.12em;
        text-transform:uppercase;padding:5px 13px;border-radius:100px;
        margin-bottom:26px;width:fit-content;
    }
    .hero-title {
        font-family:'Manrope',sans-serif;font-size:2.5rem;font-weight:800;
        line-height:1.22;color:#F8FAFC;margin-bottom:16px;
    }
    .hero-title span { color:#38BDF8; }
    .hero-desc {
        color:rgba(148,163,184,0.85);font-size:0.93rem;line-height:1.75;
        max-width:340px;margin-bottom:32px;
    }
    .hero-stats { display:flex;gap:12px;flex-wrap:wrap;margin-bottom:28px; }
    .stat-pill {
        background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
        border-radius:12px;padding:12px 16px;min-width:78px;
    }
    .stat-num {
        font-family:'Manrope',sans-serif;font-size:1.5rem;font-weight:800;color:#38BDF8;line-height:1;
    }
    .stat-lbl { color:#475569;font-size:0.63rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin-top:3px; }
    .feat-list { list-style:none;padding:0;margin:0; }
    .feat-list li { color:#64748B;font-size:0.82rem;margin-bottom:9px;display:flex;align-items:center;gap:8px; }
    .feat-list li::before { content:"";display:block;width:5px;height:5px;border-radius:50%;background:#38BDF8;flex-shrink:0; }

    /* ── Right panel header banner ─────────────────────────── */
    .form-header-banner {
        position:relative;
        background:rgba(255,255,255,0.03);
        border:1px solid rgba(56,189,248,0.15);
        border-radius:16px;padding:20px 22px 16px;
        margin-bottom:0px;overflow:hidden;
    }
    .form-header-banner::before {
        content:'';position:absolute;top:0;left:0;right:0;height:2.5px;
        background:linear-gradient(90deg,#0EA5E9,#6366F1,#10B981,#0EA5E9);
        background-size:200% auto;animation:shimmer 4s linear infinite;
    }
    @keyframes shimmer { 0%{background-position:0% center} 100%{background-position:200% center} }
    .banner-top-row { display:flex;align-items:center;justify-content:space-between;margin-bottom:12px; }
    .banner-logo-row { display:flex;align-items:center;gap:9px; }
    .banner-logo-icon {
        width:32px;height:32px;border-radius:9px;
        background:linear-gradient(135deg,#0EA5E9,#6366F1);
        display:flex;align-items:center;justify-content:center;font-size:0.9rem;
    }
    .banner-logo-name { font-family:'Manrope',sans-serif;font-weight:800;font-size:0.84rem;color:#F8FAFC; }
    .banner-logo-sub  { color:#475569;font-size:0.58rem;letter-spacing:0.08em;text-transform:uppercase; }
    .mode-badge {
        display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:100px;
        font-size:0.62rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
        background:rgba(56,189,248,0.1);border:1px solid rgba(56,189,248,0.25);color:#38BDF8;
        animation:badge-pulse 3s ease-in-out infinite;
    }
    @keyframes badge-pulse {
        0%,100% { box-shadow:0 0 0 0 rgba(56,189,248,0); }
        50%      { box-shadow:0 0 9px 2px rgba(56,189,248,0.2); }
    }
    .banner-title { font-family:'Manrope',sans-serif;font-size:1.5rem;font-weight:800;color:#F8FAFC;margin-bottom:3px; }
    .banner-sub { color:#64748B;font-size:0.77rem; }

    /* ── Streamlit widget overrides ────────────────────────── */
    [data-testid="stTextInput"] label {
        color:#94A3B8 !important;font-size:0.7rem !important;font-weight:600 !important;
        letter-spacing:0.05em !important;text-transform:uppercase !important;
    }
    [data-testid="stTextInput"] > div > div {
        background:rgba(255,255,255,0.04) !important;
        border:1.5px solid rgba(255,255,255,0.09) !important;border-radius:10px !important;
    }
    [data-testid="stTextInput"] > div > div:focus-within {
        border-color:#38BDF8 !important;box-shadow:0 0 0 3px rgba(56,189,248,0.12) !important;
    }
    [data-testid="stTextInput"] input { color:#F8FAFC !important; }
    [data-testid="stTextInput"] input::placeholder { color:#334155 !important; }

    [data-testid="stForm"] button[data-testid="baseButton-formSubmit"] {
        background:linear-gradient(135deg,#0EA5E9 0%,#6366F1 100%) !important;
        color:#fff !important;border-radius:11px !important;font-weight:700 !important;
        width:100% !important;height:47px !important;font-size:0.88rem !important;
        border:none !important;box-shadow:0 5px 18px rgba(14,165,233,0.26) !important;
    }
    [data-testid="stForm"] { border:none !important;padding:0 !important; }

    button[data-testid="baseButton-primary"] {
        background:linear-gradient(135deg,#0EA5E9,#6366F1) !important;
        border:none !important;color:#fff !important;border-radius:9px !important;
        font-weight:700 !important;font-size:0.79rem !important;
        box-shadow:0 4px 13px rgba(14,165,233,0.26) !important;
    }
    button[data-testid="baseButton-secondary"] {
        background:rgba(255,255,255,0.04) !important;
        border:1px solid rgba(255,255,255,0.08) !important;
        color:#64748B !important;border-radius:9px !important;font-weight:600 !important;font-size:0.79rem !important;
    }

    .auth-divider {
        display:flex;align-items:center;margin:12px 0;color:#1E293B;
        font-size:0.66rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;
    }
    .auth-divider::before,.auth-divider::after { content:'';flex:1;border-bottom:1px solid rgba(255,255,255,0.06); }
    .auth-divider::before { margin-right:0.6em; }
    .auth-divider::after  { margin-left:0.6em; }

    .google-btn {
        display:flex;align-items:center;justify-content:center;gap:9px;
        width:100%;padding:10px 15px;background:rgba(255,255,255,0.04);
        border:1.5px solid rgba(255,255,255,0.09);border-radius:11px;color:#94A3B8;
        font-weight:600;font-family:'Inter',sans-serif;font-size:0.82rem;cursor:pointer;
    }

    [data-testid="stCheckbox"] label span { color:#64748B !important;font-size:0.78rem !important; }
    [data-testid="stAlert"] { border-radius:10px !important; }
    .auth-footer { text-align:center;margin-top:12px;color:#475569;font-size:0.74rem; }
    .auth-footer a { color:#38BDF8;font-weight:600;text-decoration:none; }
    </style>

    <div class="auth-blobs">
        <div class="blob blob-1"></div>
        <div class="blob blob-2"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Two-column layout ────────────────────────────────────────────────────
    col_left, col_right = st.columns([1.15, 1.0])

    # ── LEFT: hero panel ─────────────────────────────────────────────────────
    with col_left:
        # Load pre-encoded Kandy images safely (zero nested f-strings)
        import pathlib as _pl
        _brain = _pl.Path(r"C:\Users\CHAMA COMPUTERS\.gemini\antigravity\brain\03f8db02-d634-41dc-b373-3a5269a583c3")
        try:
            _hero_b64     = (_brain / "hero_b64.txt").read_text().strip()
            _perahera_b64 = (_brain / "perahera_b64.txt").read_text().strip()
            _imgs_ok = True
        except Exception:
            _imgs_ok = False

        # Build image grid via concatenation — avoids nested f-string brace conflicts
        _img_css = (
            '<style>'
            '.h-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:18px 0}'
            '.h-card{position:relative;border-radius:14px;overflow:hidden;height:126px;'
            'border:1px solid rgba(56,189,248,0.2);box-shadow:0 4px 24px rgba(0,0,0,0.4)}'
            '.h-card img{width:100%;height:100%;object-fit:cover;filter:brightness(0.78) saturate(1.15)}'
            '.h-card-wide{grid-column:1/-1;height:158px}'
            '.h-ov{position:absolute;bottom:0;left:0;right:0;padding:9px 13px;'
            'background:linear-gradient(transparent,rgba(4,9,22,0.93));'
            'color:#F8FAFC;font-size:0.67rem;font-weight:600;letter-spacing:0.04em}'
            '.h-tag{display:inline-block;background:rgba(56,189,248,0.2);'
            'border:1px solid rgba(56,189,248,0.38);color:#38BDF8;border-radius:100px;'
            'padding:2px 8px;font-size:0.58rem;margin-bottom:3px;font-weight:700}'
            '.h-stats{display:flex;flex-direction:column;justify-content:center;padding:14px;'
            'background:linear-gradient(135deg,rgba(14,165,233,0.1),rgba(99,102,241,0.12))}'
            '</style>'
        )
        if _imgs_ok:
            _img_grid_html = (
                _img_css
                + '<div class="h-grid">'
                + '<div class="h-card h-card-wide">'
                + '<img src="data:image/png;base64,' + _hero_b64 + '" alt="Kandy Temple at Golden Hour">'
                + '<div class="h-ov"><span class="h-tag">&#x1F4CD; Kandy, Sri Lanka</span>'
                + '<br>Temple of the Tooth &mdash; Sri Dalada Maligawa</div></div>'
                + '<div class="h-card">'
                + '<img src="data:image/png;base64,' + _perahera_b64 + '" alt="Esala Perahera Festival">'
                + '<div class="h-ov"><span class="h-tag">&#x1F3AD; Festival</span>'
                + '<br>Esala Perahera Procession</div></div>'
                + '<div class="h-card"><div class="h-stats">'
                + '<div style="color:#38BDF8;font-size:0.56rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">&#x1F4CA; Platform Stats</div>'
                + '<div style="color:#F8FAFC;font-size:1.4rem;font-weight:800;line-height:1.1">96%</div>'
                + '<div style="color:#64748B;font-size:0.63rem;margin-bottom:9px">AI Forecast Accuracy</div>'
                + '<div style="color:#F8FAFC;font-size:1.4rem;font-weight:800;line-height:1.1">574+</div>'
                + '<div style="color:#64748B;font-size:0.63rem;margin-bottom:9px">Weeks of Training Data</div>'
                + '<div style="color:#F8FAFC;font-size:1.4rem;font-weight:800;line-height:1.1">8</div>'
                + '<div style="color:#64748B;font-size:0.63rem">Intelligence Dashboards</div>'
                + '</div></div></div>'
            )
        else:
            _img_grid_html = (
                '<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px">'
                '<div class="stat-pill"><div class="stat-num">574+</div><div class="stat-lbl">Weeks of Data</div></div>'
                '<div class="stat-pill"><div class="stat-num">96%</div><div class="stat-lbl">Accuracy</div></div>'
                '<div class="stat-pill"><div class="stat-num">8</div><div class="stat-lbl">Dashboards</div></div>'
                '</div>'
            )

        # Single safe st.markdown with no f-string interpolation
        _hero_html = (
            '<div class="auth-hero">'
            '<div class="hero-eyebrow">&#x1F3D4;&#xFE0F;&nbsp;&nbsp;Kandy, Sri Lanka</div>'
            '<div class="hero-title">The Intelligence<br>Layer for <span>Kandy\'s</span><br>Tourism Sector.</div>'
            '<p class="hero-desc">AI-driven demand forecasting, real-time weather and festival analytics'
            ' &mdash; purpose-built for hospitality leaders in Kandy.</p>'
            + _img_grid_html
            + '<ul class="feat-list">'
            '<li>AI-powered weekly arrival forecasting</li>'
            '<li>Festival &amp; weather impact analysis</li>'
            '<li>Resource &amp; capacity planning tools</li>'
            '<li>What-If scenario simulator</li>'
            '</ul></div>'
        )
        st.markdown(_hero_html, unsafe_allow_html=True)

    # ── RIGHT: header banner (HTML only, no wrapper div) + Streamlit widgets ─
    with col_right:
        # Padding for the right column content
        st.markdown("<div style='padding:48px 40px 0 40px'>", unsafe_allow_html=True)

        # Dynamic header banner — HTML only (no full-height wrapper!)
        badge_icon  = "🔐" if mode == 'login' else "✨"
        badge_label = "Sign In Mode" if mode == 'login' else "Register Mode"
        banner_title = "Welcome back 👋" if mode == 'login' else "Create account ✨"
        banner_sub   = ("Sign in to your intelligence dashboard"
                        if mode == 'login' else "Join the Kandy DSS forecasting network")

        st.markdown(f"""
        <div class="form-header-banner">
            <div class="banner-top-row">
                <div class="banner-logo-row">
                    <div class="banner-logo-icon">📊</div>
                    <div>
                        <div class="banner-logo-name">Kandy DSS</div>
                        <div class="banner-logo-sub">Tourism Intelligence</div>
                    </div>
                </div>
                <div class="mode-badge">{badge_icon}&nbsp;{badge_label}</div>
            </div>
            <div class="banner-title">{banner_title}</div>
            <div class="banner-sub">{banner_sub}</div>
        </div>
        """, unsafe_allow_html=True)

        st.write("")  # small spacer

        # ── Tab toggle ────────────────────────────────────────────────────────
        t1, t2 = st.columns(2)
        with t1:
            if st.button("🔐  Sign In", key="tab_login", use_container_width=True,
                         type="primary" if mode == 'login' else "secondary"):
                st.session_state['auth_mode'] = 'login'
                st.rerun()
        with t2:
            if st.button("✨  Register", key="tab_signup", use_container_width=True,
                         type="primary" if mode == 'signup' else "secondary"):
                st.session_state['auth_mode'] = 'signup'
                st.rerun()

        st.write("")

        # ── LOGIN FORM ────────────────────────────────────────────────────────
        if mode == 'login':
            if st.session_state.get('signup_success_msg'):
                st.success("✅ Account created! Check your email to verify (or log in directly if auto-confirm is on).")
                st.session_state['signup_success_msg'] = False
                
            with st.form("login_form", clear_on_submit=False):
                email    = st.text_input("Work Email", placeholder="you@hotel.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                rc1, rc2 = st.columns([1, 1])
                with rc1:
                    st.checkbox("Remember me")
                with rc2:
                    st.markdown(
                        "<div style='text-align:right;margin-top:6px'>"
                        "<a href='#' style='color:#38BDF8;font-size:0.75rem;"
                        "text-decoration:none;font-weight:500'>Forgot password?</a></div>",
                        unsafe_allow_html=True
                    )
                submitted = st.form_submit_button("Access Dashboard →", use_container_width=True)

            if submitted:
                if not email or not password:
                    st.error("Please enter your email and password.")
                elif not is_valid_email(email):
                    st.error("Please provide a valid email format.")
                else:
                    try:
                        supabase = get_supabase_client()
                        response = supabase.auth.sign_in_with_password(
                            {"email": email, "password": password}
                        )
                        if response.user:
                            st.session_state["user"] = response.user
                            # ← Fetch profile immediately after login
                            st.session_state["user_profile"] = load_user_profile(response.user)
                            st.rerun()
                    except Exception as e:
                        err = str(e)
                        if "Invalid login credentials" in err:
                            st.error("Invalid credentials.")
                        elif "Email not confirmed" in err:
                            st.error("📧 Please verify your email address first.")
                        else:
                            st.error(f"Login failed: {err}")

            st.markdown('<div class="auth-divider">or continue with</div>', unsafe_allow_html=True)
            st.markdown("""
                <button class="google-btn">
                    <img src="https://www.gstatic.com/images/branding/product/1x/gsa_512dp.png" width="17">
                    Continue with Google
                </button>
            """, unsafe_allow_html=True)
            st.markdown(
                "<div class='auth-footer'>Don't have an account? "
                "<a href='#'>Get started →</a></div>",
                unsafe_allow_html=True
            )

        # ── SIGN UP FORM ──────────────────────────────────────────────────────
        else:
            with st.form("signup_form", clear_on_submit=False):
                error_placeholder = st.empty()
                email = st.text_input("Work Email", placeholder="you@hotel.com")
                n1, n2 = st.columns(2)
                with n1:
                    name  = st.text_input("Full Name", placeholder="Jane Silva")
                with n2:
                    hotel = st.text_input("Hotel / Org", placeholder="Hotel Kandy")
                role_options = ["Hotel Manager", "Tour Operator", "Government Official", "Other"]
                role = st.selectbox("System Role", role_options)
                password = st.text_input("Password (min 6 chars)", type="password", placeholder="••••••••")
                st.markdown(
                    "<div style='color:#475569;font-size:0.71rem;margin-bottom:4px'>"
                    "By signing up you agree to our Terms &amp; Privacy Policy.</div>",
                    unsafe_allow_html=True
                )
                submitted = st.form_submit_button("Create My Account →", use_container_width=True)

            if submitted:
                if not email or not password or not name:
                    error_placeholder.error("Please fill in all required fields.")
                elif not is_valid_email(email):
                    error_placeholder.error("Please provide a valid email format.")
                elif len(password) < 6:
                    error_placeholder.error("Password must be at least 6 characters.")
                else:
                    try:
                        supabase = get_supabase_client()
                        response = supabase.auth.sign_up({
                            "email": email,
                            "password": password,
                            "options": {
                                "data": {
                                    "full_name": name, 
                                    "hotel_name": hotel,
                                    "role": role
                                }
                            }
                        })
                        if response.user:
                            # Try to create their user_profile manually in case the trigger is missing
                            try:
                                supabase.table("user_profiles").insert({
                                    "id": response.user.id,
                                    "email": email,
                                    "full_name": name,
                                    "hotel_name": hotel,
                                    "role": role
                                }).execute()
                            except Exception:
                                pass # Might fail due to RLS or trigger already handling it
                                
                            st.session_state['signup_success_msg'] = True
                            st.session_state['auth_mode'] = 'login'
                            st.rerun()
                    except Exception as e:
                        err = str(e)
                        if "User already registered" in err:
                            error_placeholder.error("Email already registered.")
                        elif "Password should be at least" in err:
                            error_placeholder.error("Password must be at least 6 characters.")
                        elif "rate limit" in err.lower():
                            error_placeholder.error("Too many signup attempts. Supabase requires you to wait an hour.")
                        else:
                            error_placeholder.error(f"Signup failed: {err}")

            st.markdown(
                "<div class='auth-footer'>Already have an account? "
                "<a href='#'>Sign in →</a></div>",
                unsafe_allow_html=True
            )

        st.markdown("</div>", unsafe_allow_html=True)


def require_auth():
    """Call at the top of every restricted page. Halts if not authenticated."""
    init_session_state()
    user = st.session_state.get("user")
    if user is None:
        render_auth_page()
        st.stop()
    # If user exists but profile wasn't loaded (e.g. page refresh), load it now
    if st.session_state.get("user_profile") is None:
        st.session_state["user_profile"] = load_user_profile(user)


def check_password():
    return st.session_state.get("user") is not None


def logout_button():
    init_session_state()
    if st.session_state.get("user") is not None:
        profile = st.session_state.get("user_profile")
        if profile and getattr(profile, 'get', None):
            name = profile.get("full_name", "User")
            role = profile.get("role", "")
            st.sidebar.markdown(f"**{name}**<br/><small>{role}</small>", unsafe_allow_html=True)
        if st.sidebar.button("Logout", type="primary", use_container_width=True):
            try:
                get_supabase_client().auth.sign_out()
            except Exception:
                pass
            st.session_state["user"] = None
            st.session_state["user_profile"] = None
            st.rerun()
