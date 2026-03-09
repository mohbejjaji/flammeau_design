import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from core.database import engine, Base
import core.models
from auth.auth import check_authentication  # ✅ Import de l'authentification

# Configuration de la page
st.set_page_config(
    page_title="Flammeau Design PRO",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ✅ Vérifier l'authentification AVANT tout le reste
if not check_authentication():
    st.stop()  # Arrête l'exécution si non authentifié

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

# Sidebar (visible seulement si authentifié)
with st.sidebar:
    try:
        st.image("assets/logo.PNG", width=200)
    except:
        st.markdown("# 🔥 Flammeau Design PRO")
    
    st.markdown("---")
    
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