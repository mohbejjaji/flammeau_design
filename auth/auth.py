
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
/* Masquer les éléments par défaut de Streamlit */
header, footer, #MainMenu {display:none;}

/* Animation d'apparition en douceur */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Background de l'application */
.stApp {
    background: linear-gradient(135deg, #0d0d0d, #1a1a1a);
    font-family: system-ui, -apple-system, sans-serif;
}

/* 1. Centrage vertical sur le conteneur principal */
[data-testid="stAppViewBlockContainer"], .main .block-container {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    height: 100vh !important;
    padding: 0 !important;
    max-width: 100% !important;
}

/* 2. CENTRAGE HORIZONTAL ABSOLU : Marges automatiques pour la carte et les alertes */
[data-testid="stForm"], [data-testid="stAlert"] {
    margin-left: auto !important;
    margin-right: auto !important;
}

/* 3. Style et largeur des messages d'erreur (st.error, st.info) */
[data-testid="stAlert"] {
    max-width: 420px;
    width: 100%;
    margin-bottom: 20px !important;
    animation: fadeIn 0.5s ease-out forwards;
}

/* La carte de connexion (appliquée au formulaire natif) */
[data-testid="stForm"] {
    width: 100%;
    min-width: 320px;
    max-width: 420px;
    padding: 48px;
    border-radius: 18px;
    background: rgba(20, 20, 20, 0.92);
    border: 1px solid rgba(255, 160, 50, 0.25);
    box-shadow: 0 30px 80px rgba(0, 0, 0, 0.6), 0 0 30px rgba(255, 160, 50, 0.08);
    animation: fadeIn 0.6s ease-out forwards;
}

/* Textes à l'intérieur de la carte */
.login-title {
    font-size: 30px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 8px;
    text-align: center;
}

.login-sub {
    color: #cfcfcf;
    font-size: 14px;
    margin-bottom: 30px;
    text-align: center;
}

/* Labels des champs de saisie */
.stTextInput label {
    color: #FFA032 !important;
    font-weight: 600 !important;
}

/* Champs de saisie */
.stTextInput input {
    background: #1a1a1a !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 10px !important;
    padding: 14px !important;
    color: #ffffff !important;
    font-size: 15px !important;
}

.stTextInput input:focus {
    border-color: #FFA032 !important;
    box-shadow: 0 0 0 2px rgba(255, 160, 50, 0.3), 0 0 20px rgba(255, 160, 50, 0.15) !important;
}

/* Bouton de connexion */
.stFormSubmitButton button {
    background: linear-gradient(135deg, #FFA032, #E8841A) !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 14px !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    color: #0d0d0d !important;
    transition: 0.25s;
    width: 100%;
    margin-top: 10px;
}

.stFormSubmitButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(255, 160, 50, 0.4);
}
</style>
""",
        unsafe_allow_html=True,
    )

def login_page():
    # Charge le CSS et configure la page
    ui()

    # Vérification du verrouillage
    if is_locked():
        remaining = int(st.session_state.lock_until - time.time())
        st.error(f"Trop de tentatives. Réessayez dans {remaining} secondes.")
        return False

    # Création du formulaire (qui sert de carte grâce au CSS)
    with st.form("login_form", clear_on_submit=True):
        
        # En-têtes à l'intérieur du formulaire
        st.markdown('<div class="login-title">🔐 Connexion</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">Accédez à votre espace sécurisé</div>', unsafe_allow_html=True)

        # Champs de saisie
        username = st.text_input("Utilisateur")
        password = st.text_input("Mot de passe", type="password")
        
        # Bouton de soumission
        submitted = st.form_submit_button("Se connecter")

        # Logique de vérification
        if submitted:
            # Petit loader visuel
            loader = st.empty()
            with loader.container():
                st.info("Connexion en cours...")
                time.sleep(1) # Simule un temps de chargement / évite le bruteforce rapide
                loader.empty() # Efface le message "Connexion en cours..."

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

    return False


def check_authentication():
    init_session()

    if not st.session_state.authenticated:
        return login_page()

    # On retourne juste True sans rien dessiner dans la sidebar ici
    return True

# NOUVELLE FONCTION : À appeler à la fin de votre sidebar dans app.py
def render_user_profile():
    st.divider()
    st.success(st.session_state.user_name)
    st.caption(st.session_state.user_role)
    st.caption(st.session_state.login_time)
    
    if st.button("Déconnexion", use_container_width=True):
        logout()

