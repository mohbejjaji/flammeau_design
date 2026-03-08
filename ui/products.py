import streamlit as st
import pandas as pd
from services.product_service import get_products, update_product_price
from config import USD_TO_MAD_RATE

def products_page():
    st.header("💰 Gestion des Prix")
    
    products = get_products()
    
    if not products:
        st.info("Aucun produit en stock. Commencez par enregistrer un arrivage!")
        return
    
    # Filtres
    categories = ["Tous"] + list(set(p.category for p in products))
    selected_cat = st.selectbox("Filtrer par catégorie", categories)
    
    filtered_products = products
    if selected_cat != "Tous":
        filtered_products = [p for p in products if p.category == selected_cat]
    
    st.subheader("Ajuster les prix de vente")
    
    for product in filtered_products:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
            
            with col1:
                st.write(f"**{product.name}**")
                st.caption(f"Réf: {product.reference}")
            
            with col2:
                st.metric("Stock", product.stock_quantity)
            
            with col3:
                # Prix d'achat en MAD
                st.metric("Achat (MAD)", f"{product.purchase_price:,.0f}")
                # Équivalent USD approximatif
                st.caption(f"≈ ${product.purchase_price / USD_TO_MAD_RATE:,.0f}")
            
            with col4:
                # Prix suggéré (coût réel + marge 50% + TVA)
                if hasattr(product, 'average_cost') and product.average_cost > 0:
                    cost = product.average_cost
                else:
                    cost = product.purchase_price
                
                suggested = cost * 1.5 * 1.2
                st.metric("Suggéré", f"{suggested:,.0f} MAD")
            
            with col5:
                new_price = st.number_input(
                    "Prix",
                    value=float(product.selling_price),
                    key=f"price_{product.id}",
                    label_visibility="collapsed",
                    step=100.0
                )
                if st.button("💾", key=f"save_{product.id}"):
                    update_product_price(product.id, new_price)
                    st.success("Prix mis à jour!")
                    st.rerun()
            
            st.markdown("---")