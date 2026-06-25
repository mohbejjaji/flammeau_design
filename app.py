import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from core.database import engine, Base
import core.models

# ✅ Import de la vérification ET de la nouvelle fonction d'affichage
from auth.auth import check_authentication, render_user_profile 

# Configuration de la page
st.set_page_config(
    page_title="Flammeau Design PRO",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ✅ 1. On vérifie l'accès en premier (bloque si non authentifié)
if not check_authentication():
    st.stop() 

# Initialisation de la base de données
Base.metadata.create_all(bind=engine)

# Import des pages (après authentification)
from ui.dashboard import dashboard_page
from ui.products import products_page
from ui.shipments import shipments_page
from ui.analytics import analytics_page
from ui.sales_products import sales_products_page
from ui.sales_services import sales_services_page
from ui.quotes import quotes_page
from ui.accessories import accessories_page
from ui.arrivals import arrivals_page
from ui.stock_management import stock_management_page
from ui.sales_history import sales_history_page
from ui.expenses import expenses_page

# CSS
try:
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# ✅ 2. Construction de la Sidebar dans le bon ordre
with st.sidebar:
    # Haut de la sidebar : Logo
    try:
        st.image("assets/logo.PNG", width=200)
    except:
        st.markdown("# 🔥 Flammeau Design PRO")
    
    st.markdown("---")
    
    # Milieu de la sidebar : Menu
    menu = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "💰 Charges",
            "📦 Arrivage Chine",
            "📊 Gestion Stock",
            "💰 Gestion des Prix",
            "🔥 Vente Cheminées",
            "🪵 Vente Accessoires",
            "🔧 Vente Prestations",
            "📜 Historique Ventes",
            "📄 Devis",
            "📈 Analytics"
        ]
    )
    
    # ASTUCE : Pour vraiment pousser les infos tout en bas, on peut ajouter un espacement flexible
    st.markdown('<div style="flex-grow: 1;"></div>', unsafe_allow_html=True)
    
    # Bas de la sidebar : Profil et bouton déconnexion
    render_user_profile()

# Routing (inchangé)
if menu == "📊 Dashboard":
    dashboard_page()
elif menu == "📦 Arrivage Chine":
    arrivals_page()
elif menu == "💰 Gestion des Prix":
    products_page()
elif menu == "🔥 Vente Cheminées":
    sales_products_page()
elif menu == "🪵 Vente Accessoires":
    accessories_page()
elif menu == "🔧 Vente Prestations":
    sales_services_page()
elif menu == "📈 Analytics":
    analytics_page()
elif menu == "📄 Devis":
    quotes_page()
elif menu == "📊 Gestion Stock":
    stock_management_page()
elif menu == "📜 Historique Ventes":
    sales_history_page()
elif menu == "💰 Charges":
    expenses_page()