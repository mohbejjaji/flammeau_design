import streamlit as st
import pandas as pd
from services.shipment_service import (
    create_shipment, get_shipment_history, 
    get_shipment_details, get_shipment_stats
)
from services.product_service import get_products
from datetime import datetime


def shipments_page():
    st.header("📦 Gestion des Arrivages")
    
    # Onglets
    tab1, tab2, tab3 = st.tabs(["➕ Nouvel Arrivage", "📋 Historique", "📊 Statistiques"])
    
    with tab1:
        st.subheader("Nouvel arrivage de Chine")
        
        # Récupérer les produits existants
        products = get_products()
        
        if not products:
            st.warning("Veuillez d'abord créer des produits dans la section 'Produits'")
            return
        
        # Informations générales
        col1, col2 = st.columns(2)
        
        with col1:
            transport_total = st.number_input(
                "🚛 Frais de transport (MAD)",
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )
        
        with col2:
            customs_total = st.number_input(
                "🏛️ Frais de douane (MAD)",
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )
        
        note = st.text_input("📝 Note", placeholder="Référence conteneur, fournisseur...")
        
        st.markdown("---")
        st.subheader("Produits reçus")
        
        # Initialiser le panier d'arrivage
        if 'shipment_items' not in st.session_state:
            st.session_state.shipment_items = []
        
        # Formulaire d'ajout de produit
        col_p1, col_p2, col_p3, col_p4 = st.columns([2, 1, 1, 1])
        
        with col_p1:
            # Sélection du produit
            product_options = {f"{p.name} (Stock actuel: {p.stock_quantity})": p for p in products}
            selected_product = st.selectbox(
                "Produit",
                options=list(product_options.keys()),
                key="shipment_product"
            )
            product = product_options[selected_product]
        
        with col_p2:
            quantity = st.number_input("Quantité", min_value=1, value=1, key="shipment_qty")
        
        with col_p3:
            unit_price = st.number_input(
                "Prix achat (MAD)",
                min_value=0.0,
                value=0.0,
                step=10.0,
                format="%.2f",
                key="shipment_price",
                help="Prix d'achat unitaire en Chine"
            )
        
        with col_p4:
            if st.button("➕ Ajouter", use_container_width=True):
                if quantity > 0 and unit_price > 0:
                    # Vérifier si le produit est déjà dans la liste
                    existing = next(
                        (item for item in st.session_state.shipment_items 
                         if item['product_id'] == product.id),
                        None
                    )
                    
                    if existing:
                        existing['quantity'] += quantity
                        st.success(f"Quantité mise à jour: {product.name} x{existing['quantity']}")
                    else:
                        st.session_state.shipment_items.append({
                            'product_id': product.id,
                            'name': product.name,
                            'quantity': quantity,
                            'unit_purchase_price': unit_price
                        })
                        st.success(f"Ajouté: {product.name} x{quantity}")
                    
                    st.rerun()
                else:
                    st.error("Veuillez saisir une quantité et un prix valides")
        
        # Afficher le panier
        if st.session_state.shipment_items:
            st.markdown("---")
            st.subheader("📦 Récapitulatif de l'arrivage")
            
            # Créer un DataFrame pour l'affichage
            df_items = pd.DataFrame(st.session_state.shipment_items)
            
            # Calculer les totaux
            df_items['total'] = df_items['quantity'] * df_items['unit_purchase_price']
            total_achat = df_items['total'].sum()
            
            # Afficher le tableau
            df_display = df_items[['name', 'quantity', 'unit_purchase_price', 'total']].copy()
            df_display.columns = ['Produit', 'Quantité', 'Prix unitaire', 'Total']
            df_display['Prix unitaire'] = df_display['Prix unitaire'].apply(lambda x: f"{x:,.2f} MAD")
            df_display['Total'] = df_display['Total'].apply(lambda x: f"{x:,.2f} MAD")
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Afficher les totaux
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1:
                st.metric("Total achat", f"{total_achat:,.2f} MAD")
            with col_t2:
                st.metric("Frais transport", f"{transport_total:,.2f} MAD")
            with col_t3:
                st.metric("Frais douane", f"{customs_total:,.2f} MAD")
            
            total_general = total_achat + transport_total + customs_total
            st.metric("💰 Investissement total", f"{total_general:,.2f} MAD", 
                     delta=f"{(total_general/total_achat-1)*100:.1f}% de frais")
            
            # Boutons d'action
            col_b1, col_b2 = st.columns(2)
            
            with col_b1:
                if st.button("🗑️ Vider le panier", use_container_width=True):
                    # ✅ Uniquement vider la session Streamlit, pas de DB
                    st.session_state.shipment_items = []
                    st.rerun()
            
            with col_b2:
                if st.button("✅ Valider l'arrivage", type="primary", use_container_width=True):
                    try:
                        # ✅ Utiliser le dictionnaire retourné, pas l'objet
                        shipment_data = create_shipment(
                            items=st.session_state.shipment_items,
                            transport_total=transport_total,
                            customs_total=customs_total,
                            note=note
                        )
                        
                        st.success(f"✅ Arrivage #{shipment_data['id']} enregistré avec succès!")
                        
                        # Afficher le résumé avec les données du dictionnaire
                        with st.expander("📋 Détail de l'arrivage", expanded=True):
                            st.write(f"**Date:** {shipment_data['date'].strftime('%d/%m/%Y')}")
                            st.write(f"**Total achat:** {total_achat:,.2f} MAD")
                            st.write(f"**Frais transport:** {transport_total:,.2f} MAD")
                            st.write(f"**Frais douane:** {customs_total:,.2f} MAD")
                            st.write(f"**Total investi:** {total_general:,.2f} MAD")
                            
                            if note:
                                st.write(f"**Note:** {note}")
                            
                            st.write("**Produits reçus:**")
                            for item in st.session_state.shipment_items:
                                st.write(f"  • {item['name']}: {item['quantity']} unités")
                        
                        st.balloons()
                        st.session_state.shipment_items = []
                        
                    except Exception as e:
                        st.error(f"Erreur: {e}")
    
    with tab2:
        st.subheader("📜 Historique des arrivages")
        
        shipments = get_shipment_history()
        
        if not shipments:
            st.info("Aucun arrivage enregistré")
        else:
            for shipment in shipments:
                with st.expander(f"📦 Arrivage #{shipment.id} - {shipment.date.strftime('%d/%m/%Y')}"):
                    # ✅ Utiliser la fonction qui retourne des dictionnaires
                    details = get_shipment_details(shipment.id)
                    
                    if details:
                        col_h1, col_h2, col_h3 = st.columns(3)
                        
                        with col_h1:
                            total_achat = sum(i['quantity'] * i['unit_purchase_price'] for i in details['items'])
                            st.metric("Total achat", f"{total_achat:,.0f} MAD")
                        
                        with col_h2:
                            st.metric("Frais transport", f"{details['shipment']['transport_cost_total']:,.0f} MAD")
                        
                        with col_h3:
                            st.metric("Frais douane", f"{details['shipment']['customs_cost_total']:,.0f} MAD")
                        
                        if details['shipment']['note']:
                            st.caption(f"Note: {details['shipment']['note']}")
                        
                        # Afficher les produits
                        st.write("**Produits reçus:**")
                        for item in details['items']:
                            st.write(f"  • {item['product_name']}: {item['quantity']} unités à {item['unit_purchase_price']:,.0f} MAD")
    
    with tab3:
        st.subheader("📊 Statistiques des arrivages")
        
        stats = get_shipment_stats()
        
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        
        with col_s1:
            st.metric("Nombre d'arrivages", stats['total_shipments'])
        
        with col_s2:
            st.metric("Total achats", f"{stats['total_spent']:,.0f} MAD")
        
        with col_s3:
            st.metric("Total frais", f"{stats['total_transport'] + stats['total_customs']:,.0f} MAD")
        
        with col_s4:
            if stats['last_shipment_date']:
                st.metric("Dernier arrivage", stats['last_shipment_date'].strftime('%d/%m/%Y'))
            else:
                st.metric("Dernier arrivage", "Aucun")
        
        # Ratio frais / achats
        if stats['total_spent'] > 0:
            frais_total = stats['total_transport'] + stats['total_customs']
            ratio_frais = (frais_total / stats['total_spent']) * 100
            
            st.subheader("📈 Analyse des coûts")
            st.metric("Ratio frais / achats", f"{ratio_frais:.1f}%")
            
            # Barre de progression
            st.progress(min(ratio_frais/100, 1.0))