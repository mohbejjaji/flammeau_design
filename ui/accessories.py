import streamlit as st
import pandas as pd
from services.accessory_service import create_accessory_sale, get_accessory_catalog
from datetime import datetime

def accessories_page():
    st.header("🪵 Vente d'Accessoires")
    
    # ✅ Initialisation du panier dans session_state
    if 'acc_cart' not in st.session_state:
        st.session_state.acc_cart = []
    
    # Onglets
    tab1, tab2 = st.tabs(["🛒 Point de Vente", "📋 État du Stock"])
    
    # ==========================================
    # ONGLET 1 : POINT DE VENTE
    # ==========================================
    with tab1:
        # --- 1. Informations Client ---
        with st.container(border=True):
            st.subheader("👤 Informations de la vente")
            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1:
                customer = st.text_input("Nom du client *", key="acc_customer", placeholder="Ex: M. Dupont")
            with col_c2:
                customer_phone = st.text_input("Téléphone", key="acc_phone", placeholder="Ex: 06 00 00 00 00")
            with col_c3:
                payment_method = st.selectbox("Mode de paiement", ["Espèces", "Carte bancaire", "Virement", "Chèque"], key="acc_payment")
        
        st.markdown("---")

        # --- 2. Disposition principale (Catalogue 60% / Panier 40%) ---
        col_prod, col_panier = st.columns([1.5, 1], gap="large")
        
        # COLONNE GAUCHE : CATALOGUE
        with col_prod:
            st.subheader("📦 Catalogue Accessoires")
            
            accessories = get_accessory_catalog()
            in_stock = [a for a in accessories if a.stock_quantity > 0]
            
            if not in_stock:
                st.warning("⚠️ Aucun accessoire actuellement en stock.")
            else:
                # Affichage des accessoires sous forme de "cartes"
                for acc in in_stock:
                    with st.container(border=True):
                        # On centre verticalement les éléments de la ligne
                        c_info, c_price, c_qty, c_btn = st.columns([3, 1.5, 1.5, 1], vertical_alignment="center")
                        
                        with c_info:
                            st.markdown(f"**{acc.name}**")
                            if acc.description:
                                st.caption(acc.description)
                        
                        with c_price:
                            st.markdown(f"**{acc.selling_price:,.2f} MAD**")
                            st.caption(f"Stock: {acc.stock_quantity}")
                        
                        with c_qty:
                            qty = st.number_input(
                                "Qté",
                                min_value=0,
                                max_value=acc.stock_quantity,
                                value=0, # Par défaut à 0 pour éviter les ajouts accidentels
                                key=f"acc_qty_{acc.id}",
                                label_visibility="collapsed"
                            )
                        
                        with c_btn:
                            # Le bouton n'est cliquable que si la quantité > 0
                            if st.button("➕", key=f"acc_add_{acc.id}", type="primary", use_container_width=True, disabled=(qty == 0)):
                                existing = next((item for item in st.session_state.acc_cart if item['product_id'] == acc.id), None)
                                
                                if existing:
                                    new_qty = existing['quantity'] + qty
                                    if new_qty <= acc.stock_quantity:
                                        existing['quantity'] = new_qty
                                        st.toast(f"✅ Quantité mise à jour pour {acc.name}")
                                    else:
                                        st.error("Stock insuffisant !")
                                else:
                                    st.session_state.acc_cart.append({
                                        'product_id': acc.id,
                                        'name': acc.name,
                                        'quantity': qty,
                                        'unit_price': acc.selling_price
                                    })
                                    st.toast(f"✅ {acc.name} ajouté au panier")
                                st.rerun()

        # COLONNE DROITE : PANIER
        with col_panier:
            st.subheader("🛒 Panier actuel")
            
            if not st.session_state.acc_cart:
                st.info("Le panier est vide. Sélectionnez des quantités à gauche.")
            else:
                cart_total = 0
                
                # --- Liste des articles dans le panier ---
                for i, item in enumerate(st.session_state.acc_cart):
                    item_total = item['quantity'] * item['unit_price']
                    cart_total += item_total
                    
                    with st.container(border=True):
                        c_name, c_details, c_del = st.columns([3, 2, 1], vertical_alignment="center")
                        with c_name:
                            st.markdown(f"**{item['name']}**")
                        with c_details:
                            st.markdown(f"x{item['quantity']} = **{item_total:,.2f} MAD**")
                        with c_del:
                            if st.button("🗑️", key=f"acc_del_{i}"):
                                st.session_state.acc_cart.pop(i)
                                st.rerun()
                
                # --- Récapitulatif et Paiement ---
                st.markdown("---")
                st.metric("Total à payer (MAD)", f"{cart_total:,.2f} MAD")
                
                if st.button("✅ Encaisser et Finaliser", type="primary", use_container_width=True):
                    if not customer:
                        st.error("⚠️ Le nom du client est requis pour valider la vente.")
                    else:
                        try:
                            items = [{"product_id": it['product_id'], "quantity": it['quantity'], "unit_price": it['unit_price']} for it in st.session_state.acc_cart]
                            
                            sale = create_accessory_sale(
                                customer_name=customer,
                                items=items,
                                seller_name="Moi",
                                payment_method=payment_method,
                                customer_phone=customer_phone
                            )
                            
                            st.success("🎉 Vente d'accessoires enregistrée avec succès !")
                            st.balloons()
                            
                            # Beau ticket de caisse
                            with st.expander("🧾 Voir le reçu de la transaction", expanded=True):
                                st.markdown(f"""
                                ### 🔥 FLAMMEAU DESIGN - Accessoires
                                *Le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*
                                
                                **Client :** {customer}  
                                **Contact :** {customer_phone if customer_phone else 'Non renseigné'}  
                                **Paiement :** {payment_method}
                                
                                ---
                                """)
                                
                                for item in st.session_state.acc_cart:
                                    st.write(f"- **{item['quantity']}x {item['name']}** : {item['quantity'] * item['unit_price']:,.2f} MAD")
                                
                                st.markdown("---")
                                st.markdown(f"## TOTAL : {cart_total:,.2f} MAD")
                            
                            # Vider le panier
                            st.session_state.acc_cart = []
                            if st.button("🔄 Nouvelle vente d'accessoires"):
                                st.rerun()
                                
                        except Exception as e:
                            st.error(f"Erreur lors de la vente : {str(e)}")

    # ==========================================
    # ONGLET 2 : CATALOGUE ET STOCK
    # ==========================================
    with tab2:
        st.subheader("📋 État du Stock des Accessoires")
        
        accessories = get_accessory_catalog()
        
        if not accessories:
            st.info("Aucun accessoire référencé dans le catalogue.")
        else:
            # Statistiques (KPIs)
            total_accessories = len(accessories)
            total_stock = sum(a.stock_quantity for a in accessories)
            total_value = sum(a.selling_price * a.stock_quantity for a in accessories)
            
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.metric("📦 Références actives", total_accessories)
            with col_s2:
                st.metric("📊 Volume en stock (unités/kg/L)", f"{total_stock:,.0f}")
            with col_s3:
                st.metric("💰 Valeur marchande estimée", f"{total_value:,.2f} MAD")
            
            st.markdown("---")
            
            # Préparation des données pour le tableau
            stock_data = []
            for acc in accessories:
                # Logique de statut visuel
                if acc.stock_quantity > 10:
                    status = "🟢 OK"
                elif acc.stock_quantity > 0:
                    status = "🟠 Stock Faible"
                else:
                    status = "🔴 Rupture"
                    
                stock_data.append({
                    "Statut": status,
                    "Accessoire": acc.name,
                    "Catégorie": acc.subtype.capitalize() if acc.subtype else "-",
                    "Stock": acc.stock_quantity,
                    "Prix Unitaire": float(acc.selling_price),
                    "Valeur Totale": float(acc.selling_price * acc.stock_quantity)
                })
            
            df = pd.DataFrame(stock_data)
            
            # Utilisation de st.dataframe avec column_config pour un rendu parfait
            st.dataframe(
                df,
                column_config={
                    "Statut": st.column_config.TextColumn("Statut"),
                    "Accessoire": st.column_config.TextColumn("Accessoire"),
                    "Catégorie": st.column_config.TextColumn("Catégorie"),
                    "Stock": st.column_config.NumberColumn("En Stock", format="%d"),
                    "Prix Unitaire": st.column_config.NumberColumn("Prix (MAD)", format="%.2f MAD"),
                    "Valeur Totale": st.column_config.NumberColumn("Valeur (MAD)", format="%.2f MAD")
                },
                use_container_width=True,
                hide_index=True
            )