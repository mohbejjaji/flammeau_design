import streamlit as st
from services.reporting_service import kpi_summary, sales_dataframe
from config import FIXED_CHARGES
from services.stock_service import get_current_stock, get_low_stock_products


def dashboard_page():
    st.header("Dashboard Stratégique")

    total_revenue, net_profit = kpi_summary()
    
    # Calculer le total des charges fixes
    total_fixed_charges = sum(FIXED_CHARGES.values())
    real_profit = net_profit - total_fixed_charges

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("CA Total", f"{total_revenue:.2f} MAD")
    col2.metric("Profit Brut", f"{net_profit:.2f} MAD")
    col3.metric("Profit Net Réel", f"{real_profit:.2f} MAD")
    col4.metric("Seuil rentabilité", "44 000 MAD")

    st.subheader("Évolution du CA")
    df = sales_dataframe()
    if not df.empty:
        df = df.sort_values("date")
        st.line_chart(df.set_index("date")["total_revenue"])
    else:
        st.info("Aucune vente enregistrée pour le moment.")
        
    # Optionnel : Afficher le détail des charges fixes
    with st.expander("Détail des charges fixes"):
        for charge, montant in FIXED_CHARGES.items():
            st.write(f"{charge}: {montant} MAD")
    
    st.subheader("📦 Aperçu du stock")
    
    stock = get_current_stock()
    
    if stock:
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        
        total_value = sum(s['stock_value'] for s in stock)
        total_quantity = sum(s['quantity'] for s in stock)
        low_stock = len(get_low_stock_products())
        
        with col_s1:
            st.metric("Valeur totale stock", f"{total_value:,.0f} MAD")
        with col_s2:
            st.metric("Unités en stock", total_quantity)
        with col_s3:
            st.metric("Produits différents", len(stock))
        with col_s4:
            st.metric("Alertes stock", low_stock, 
                     delta_color="inverse" if low_stock > 0 else "off")
    else:
        st.info("Aucun stock disponible")