
import streamlit as st
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path


MAX_LOGIN_ATTEMPTS = 3
LOCK_TIME_SECONDS = 60


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def load_users():
    users_file = Path(__file__).parent / "users.json"
    if users_file.exists():
        with open(users_file, "r") as f:
            return json.load(f)
    return {}


def init_session():

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "login_attempts" not in st.session_state:
        st.session_state.login_attempts = 0

    if "lock_until" not in st.session_state:
        st.session_state.lock_until = 0


def is_locked():
    return time.time() < st.session_state.lock_until


def register_failed_attempt():

    st.session_state.login_attempts += 1

    if st.session_state.login_attempts >= MAX_LOGIN_ATTEMPTS:
        st.session_state.lock_until = time.time() + LOCK_TIME_SECONDS
        st.session_state.login_attempts = 0


def login_success(user, user_data):

    st.session_state.authenticated = True
    st.session_state.user = user
    st.session_state.user_name = user_data["name"]
    st.session_state.user_role = user_data["role"]
    st.session_state.login_time = datetime.now().strftime("%d/%m/%Y %H:%M")

    st.rerun()


def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def ui():

    st.set_page_config(layout="wide")

    st.markdown(
        """
<style>

header, footer, #MainMenu {display:none}

/* Background */

.stApp{
background:linear-gradient(135deg,#0d0d0d,#1a1a1a);
font-family:system-ui;
}

/* Center layout */

section.main > div.block-container{

height:100vh;

display:flex;

align-items:center;

justify-content:center;

max-width:100% !important;

padding:0 !important;

}

/* Login card */

.login-card{

width:100%;

max-width:420px;

padding:48px;

border-radius:18px;

background:rgba(20,20,20,.92);

border:1px solid rgba(255,160,50,.25);

box-shadow:
0 30px 80px rgba(0,0,0,.6),
0 0 30px rgba(255,160,50,.08);

}

/* Title */

.login-title{

font-size:30px;

font-weight:700;

color:#ffffff;

margin-bottom:8px;

}

.login-sub{

color:#cfcfcf;

font-size:14px;

margin-bottom:30px;

}

/* Labels */

.stTextInput label{

color:#FFA032 !important;

font-weight:600 !important;

}

/* Inputs */

.stTextInput input{

background:#1a1a1a !important;

border:1px solid rgba(255,255,255,.15) !important;

border-radius:10px !important;

padding:14px !important;

color:#ffffff !important;

font-size:15px !important;

}

.stTextInput input:focus{

border-color:#FFA032 !important;

box-shadow:
0 0 0 2px rgba(255,160,50,.3),
0 0 20px rgba(255,160,50,.15);

}

/* Button */

.stFormSubmitButton button{

background:linear-gradient(135deg,#FFA032,#E8841A) !important;

border:none !important;

border-radius:10px !important;

padding:14px !important;

font-weight:700 !important;

letter-spacing:1px !important;

color:#0d0d0d !important;

transition:.25s;

}

.stFormSubmitButton button:hover{

transform:translateY(-2px);

box-shadow:0 10px 30px rgba(255,160,50,.4);

}

</style>
""",
        unsafe_allow_html=True,
    )


def login_page():

    ui()

    st.markdown('<div class="login-card">', unsafe_allow_html=True)

    st.markdown('<div class="login-title">🔐 Connexion</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-sub">Accédez à votre espace sécurisé</div>', unsafe_allow_html=True)

    if is_locked():

        remaining = int(st.session_state.lock_until - time.time())

        st.error(f"Trop de tentatives. Réessayez dans {remaining} secondes.")

        st.markdown("</div>", unsafe_allow_html=True)

        return False

    with st.form("login_form"):

        username = st.text_input("Utilisateur")

        password = st.text_input("Mot de passe", type="password")

        submitted = st.form_submit_button("Se connecter")

        if submitted:

            loader = st.empty()

            with loader.container():

                st.info("Connexion en cours...")
                time.sleep(1)

            users = load_users()

            if username in users:

                if users[username]["password_hash"] == hash_password(password):

                    login_success(username, users[username])

                else:

                    register_failed_attempt()
                    st.error("Mot de passe incorrect")

            else:

                register_failed_attempt()
                st.error("Utilisateur introuvable")

    st.markdown("</div>", unsafe_allow_html=True)

    return False


def check_authentication():

    init_session()

    if not st.session_state.authenticated:
        return login_page()

    with st.sidebar:

        st.success(st.session_state.user_name)

        st.caption(st.session_state.user_role)

        st.caption(st.session_state.login_time)

        st.divider()

        if st.button("Déconnexion"):
            logout()

    return True

