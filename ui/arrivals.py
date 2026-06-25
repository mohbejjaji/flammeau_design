import streamlit as st
import pandas as pd
from services.arrival_service import process_arrival
from data.product_catalog import get_all_references
from datetime import date
from config import USD_TO_MAD_RATE

def arrivals_page():
    st.header("📦 Arrivage de Chine")
    
    st.info(f"💰 Taux de change: 1 USD = {USD_TO_MAD_RATE} MAD")
    
    # Informations générales
    col1, col2 = st.columns(2)
    
    with col1:
        arrival_date = st.date_input("Date d'arrivage", value=date.today())
    
    with col2:
        container_ref = st.text_input("Référence conteneur", placeholder="EX: CONT-2025-001")
    
    col3, col4, col5 = st.columns(3)
    
    with col3:
        transport_cost_usd = st.number_input(
            "🚛 Transport (USD)", 
            min_value=0.0, 
            step=100.0,
            help="Frais de transport en dollars"
        )
        if transport_cost_usd > 0:
            st.caption(f"≈ {transport_cost_usd * USD_TO_MAD_RATE:,.0f} MAD")
    
    with col4:
        shipping_cost_usd = st.number_input(
            "🚢 Fret maritime (USD)", 
            min_value=0.0, 
            step=100.0,
            help="Fret en dollars"
        )
        if shipping_cost_usd > 0:
            st.caption(f"≈ {shipping_cost_usd * USD_TO_MAD_RATE:,.0f} MAD")
    
    with col5:
        customs_cost_mad = st.number_input(
            "🏛️ Douane (MAD)", 
            min_value=0.0, 
            step=100.0,
            help="Frais de douane en dirhams"
        )
    
    note = st.text_area("📝 Note", placeholder="Fournisseur, conditions particulières...")
    
    st.markdown("---")
    st.subheader("📦 Produits reçus")
    
    # Récupérer toutes les références disponibles
    references = get_all_references()
    ref_options = {f"{r['ref']} - {r['name']} ({r['category']} - {r['subtype']})": r['ref'] for r in references}
    
    # Initialiser la liste des articles
    if 'arrival_items' not in st.session_state:
        st.session_state.arrival_items = []
    
    # Formulaire d'ajout
    col_a1, col_a2, col_a3, col_a4 = st.columns([3, 1, 1, 1])
    
    with col_a1:
        selected_ref = st.selectbox(
            "Référence produit",
            options=list(ref_options.keys()),
            key="arrival_ref"
        )
        reference = ref_options[selected_ref]
    
    with col_a2:
        quantity = st.number_input("Quantité", min_value=1, value=1, key="arrival_qty")
    
    with col_a3:
        purchase_price_usd = st.number_input(
            "Prix achat (USD)", 
            min_value=0.0, 
            step=10.0,
            key="arrival_price",
            help="Prix unitaire en dollars"
        )
    
    with col_a4:
        if st.button("➕ Ajouter", use_container_width=True):
            if purchase_price_usd > 0:
                # Calculer le prix en MAD
                price_mad = purchase_price_usd * USD_TO_MAD_RATE
                
                st.session_state.arrival_items.append({
                    'reference': reference,
                    'display': selected_ref,
                    'quantity': quantity,
                    'purchase_price_usd': purchase_price_usd,
                    'purchase_price_mad': price_mad
                })
                st.rerun()
            else:
                st.error("Veuillez saisir un prix valide")
    
    # Afficher le panier
    if st.session_state.arrival_items:
        st.markdown("---")
        st.subheader("📋 Récapitulatif")
        
        df = pd.DataFrame(st.session_state.arrival_items)
        df['total_usd'] = df['purchase_price_usd'] * df['quantity']
        df['total_mad'] = df['purchase_price_mad'] * df['quantity']
        
        df_display = df[['display', 'quantity', 'purchase_price_usd', 'purchase_price_mad', 'total_usd', 'total_mad']].copy()
        df_display.columns = ['Produit', 'Qté', 'Prix (USD)', 'Prix (MAD)', 'Total (USD)', 'Total (MAD)']
        
        # Formater les colonnes
        df_display['Prix (USD)'] = df_display['Prix (USD)'].apply(lambda x: f"${x:,.2f}")
        df_display['Prix (MAD)'] = df_display['Prix (MAD)'].apply(lambda x: f"{x:,.0f} MAD")
        df_display['Total (USD)'] = df_display['Total (USD)'].apply(lambda x: f"${x:,.2f}")
        df_display['Total (MAD)'] = df_display['Total (MAD)'].apply(lambda x: f"{x:,.0f} MAD")
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Totaux
        total_usd = df['total_usd'].sum()
        total_mad = df['total_mad'].sum()
        
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            st.metric("Total achat (USD)", f"${total_usd:,.2f}")
        with col_t2:
            st.metric("Total achat (MAD)", f"{total_mad:,.0f} MAD")
        with col_t3:
            frais_total_usd = transport_cost_usd + shipping_cost_usd
            frais_total_mad = frais_total_usd * USD_TO_MAD_RATE + customs_cost_mad
            st.metric("Frais totaux", f"{frais_total_mad:,.0f} MAD")
        
        total_invest_mad = total_mad + frais_total_mad
        st.metric("💰 Investissement total", f"{total_invest_mad:,.0f} MAD")
        
        # Taux de frais
        if total_mad > 0:
            frais_percent = (frais_total_mad / total_mad) * 100
            st.progress(min(frais_percent/100, 1.0))
            st.caption(f"Frais représentant {frais_percent:.1f}% du prix d'achat")
        
        col_b1, col_b2 = st.columns(2)
        
        with col_b1:
            if st.button("🗑️ Vider", use_container_width=True):
                st.session_state.arrival_items = []
                st.rerun()
        
        with col_b2:
            if st.button("✅ Valider l'arrivage", type="primary", use_container_width=True):
                try:
                    arrival_data = {
                        'date': arrival_date,
                        'transport_cost_usd': transport_cost_usd,
                        'shipping_cost_usd': shipping_cost_usd,
                        'customs_cost_mad': customs_cost_mad,
                        'note': f"{container_ref} - {note}" if container_ref else note,
                        'items': [
                            {
                                'reference': item['reference'],
                                'quantity': item['quantity'],
                                'purchase_price_usd': item['purchase_price_usd']
                            }
                            for item in st.session_state.arrival_items
                        ]
                    }
                    
                    result = process_arrival(arrival_data)
                    
                    st.success(f"""
                    ✅ Arrivage #{result['shipment_id']} enregistré!
                    - {result['products_created']} nouveaux produits créés
                    - Total achat: ${result['total_usd']:,.2f} USD
                    - Total en MAD: {result['total_mad']:,.0f} MAD
                    - Frais: {result['total_frais_mad']:,.0f} MAD
                    - Investissement total: {result['total_cost_mad']:,.0f} MAD
                    """)
                    
                    st.balloons()
                    st.session_state.arrival_items = []
                    
                except Exception as e:
                    st.error(f"Erreur: {e}")
    else:
        st.info("Ajoutez des produits à l'arrivage")