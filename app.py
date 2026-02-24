import sys
import os
# Ajouter le chemin absolu du dossier courant au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from core.database import engine, Base
import core.models


# Page configuration
st.set_page_config(
    page_title="Flammeau Design PRO",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
Base.metadata.create_all(bind=engine)

# Import UI components
from ui.layout import main_layout
from ui.dashboard import dashboard_page
from ui.products import products_page
from ui.shipments import shipments_page
from ui.analytics import analytics_page
from ui.sales_products import sales_products_page
from ui.sales_services import sales_services_page
from ui.quotes import quotes_page
from ui.accessories import accessories_page

# Load custom CSS
try:
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("Style sheet not found. Using default styling.")

# Main layout
main_layout("Flammeau Design PRO")

# Sidebar navigation
with st.sidebar:
    try:
        st.image("assets/logo.PNG", width=200)  # Correction du chemin du logo
    except Exception as e:
        st.markdown("# 🔥 Flammeau Design PRO")
        st.error(f"Logo non trouvé: {e}")
    
    st.markdown("---")
    
    menu = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "🛒 Produits",
            "📦 Arrivages",
            "🔥 Vente Cheminées",        # Changé
            "🪵 Vente Accessoires",       # Nouveau
            "🔧 Vente Prestations",
            "📄 Devis",
            "📈 Analytics"
        ]
    )

# Page routing
if menu == "📊 Dashboard":
    dashboard_page()
elif menu == "🛒 Produits":
    products_page()
elif menu == "📦 Arrivages":
    shipments_page()
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