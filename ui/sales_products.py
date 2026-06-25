import streamlit as st
from datetime import datetime
from services.sales_service import create_product_sale
from services.product_service import get_products
from config import COMMISSION_RATE

def sales_products_page():
    st.header("🔥 Vente de Cheminées")

    products = get_products()
    fireplaces = [p for p in products if p.category in ["electrique", "bioethanol"]]

    if not fireplaces:
        st.warning("Aucune cheminée en stock.")
        return

    # Initialisation du panier
    if "cart" not in st.session_state:
        st.session_state.cart = []

    # --- 1. Informations Client et Vendeur (En-tête stylisé) ---
    with st.container(border=True):
        st.subheader("👤 Informations de la vente")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            customer = st.text_input("Nom du client *", placeholder="Ex: M. Dupont")
        with col_c2:
            customer_phone = st.text_input("Téléphone", placeholder="Ex: 06 00 00 00 00")
        with col_c3:
            seller = st.selectbox("Vendeur", ["Moi", "Kamal", "Youssef"])

    st.markdown("---")

    # --- 2. Disposition principale (Produits 60% / Panier 40%) ---
    col_prod, col_panier = st.columns([1.5, 1], gap="large")

    # ==========================================
    # COLONNE GAUCHE : CATALOGUE PRODUITS
    # ==========================================
    with col_prod:
        st.subheader("📦 Catalogue")
        search = st.text_input("🔎 Rechercher un modèle...", placeholder="Tapez le nom d'une cheminée...")
        
        filtered = fireplaces
        if search:
            filtered = [p for p in fireplaces if search.lower() in p.name.lower()]

        # Affichage des produits sous forme de "cartes" épurées
        for p in filtered:
            if p.stock_quantity > 0:
                with st.container(border=True):
                    col_info, col_btn = st.columns([3, 1], vertical_alignment="center")
                    
                    with col_info:
                        st.markdown(f"**{p.name}**")
                        st.caption(f"🏷️ Prix unitaire : **{p.selling_price:,.2f} MAD** | 📦 En stock : {p.stock_quantity}")
                    
                    with col_btn:
                        if st.button("➕ Ajouter", key=f"add_{p.id}", type="primary", use_container_width=True):
                            existing = next((i for i in st.session_state.cart if i["product_id"] == p.id), None)
                            if existing:
                                existing["quantity"] += 1
                            else:
                                st.session_state.cart.append({
                                    "product_id": p.id,
                                    "name": p.name,
                                    "quantity": 1,
                                    "unit_price": p.selling_price,
                                    "discount": 0.0
                                })
                            st.rerun()

    # ==========================================
    # COLONNE DROITE : PANIER & PAIEMENT
    # ==========================================
    with col_panier:
        st.subheader("🛒 Panier actuel")
        
        if not st.session_state.cart:
            st.info("Le panier est vide. Sélectionnez des produits à gauche.")
        else:
            total = 0
            
            # --- Liste des articles ---
            for idx, item in enumerate(st.session_state.cart):
                with st.container(border=True):
                    st.markdown(f"**{item['name']}**")
                    
                    # Mise en page compacte pour l'édition de la ligne
                    c_qty, c_disc, c_del = st.columns([2, 3, 1], vertical_alignment="bottom")
                    
                    with c_qty:
                        new_qty = st.number_input("Qté", min_value=1, value=item["quantity"], key=f"qty_{idx}")
                        if new_qty != item["quantity"]:
                            item["quantity"] = new_qty
                            st.rerun()
                            
                    with c_disc:
                        # Remplace les 6 boutons par un seul champ intelligent (step=100)
                        manual_disc = st.number_input(
                            "Remise (MAD)", 
                            min_value=0.0, 
                            max_value=float(item["unit_price"]), 
                            value=float(item["discount"]), 
                            step=100.0, 
                            key=f"disc_{idx}"
                        )
                        if manual_disc != item["discount"]:
                            item["discount"] = manual_disc
                            st.rerun()
                            
                    with c_del:
                        if st.button("🗑️", key=f"del_{idx}", help="Supprimer l'article"):
                            st.session_state.cart.pop(idx)
                            st.rerun()
                    
                    # Calculs de la ligne
                    final_price = item["unit_price"] - item["discount"]
                    line_total = final_price * item["quantity"]
                    total += line_total
                    
                    # Affichage des montants sous les champs
                    st.caption(f"Prix unitaire net: {final_price:,.2f} MAD | **Total ligne: {line_total:,.2f} MAD**")
                    
                    if item["discount"] > item["unit_price"] * 0.3:
                        st.error("⚠️ Remise exceptionnelle (>30%) appliquée.")

            # --- Récapitulatif et Paiement ---
            st.markdown("---")
            
            # Affichage du total en grand
            st.metric("Total à payer (MAD)", f"{total:,.2f} MAD")
            
            commission = total * COMMISSION_RATE if seller != "Moi" else 0
            if commission > 0:
                st.caption(f"💡 Commission estimée pour {seller} : {commission:,.0f} MAD")
            
            payment = st.selectbox("Mode de paiement", ["Espèces", "Carte bancaire", "Virement", "Chèque"], key="payment_method")
            
            # --- Bouton de validation ---
            if st.button("✅ Encaisser et Finaliser", type="primary", use_container_width=True):
                if not customer:
                    st.error("⚠️ Le nom du client est requis pour valider la vente.")
                else:
                    try:
                        items = []
                        for item in st.session_state.cart:
                            final_price = item["unit_price"] - item["discount"]
                            items.append({
                                "product_id": item["product_id"],
                                "quantity": item["quantity"],
                                "unit_price": final_price
                            })
                        
                        # Création de la vente
                        create_product_sale(
                            customer_name=customer,
                            items=items,
                            seller_name=seller,
                            commission=commission,
                            payment_method=payment,
                            customer_phone=customer_phone
                        )
                        
                        st.success("🎉 Vente enregistrée avec succès !")
                        st.balloons()
                        
                        # Beau ticket de caisse
                        with st.expander("🧾 Voir le reçu de la transaction", expanded=True):
                            st.markdown(f"""
                            ### 🔥 FLAMMEAU DESIGN
                            *Le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*
                            
                            **Client :** {customer}  
                            **Contact :** {customer_phone if customer_phone else 'Non renseigné'}  
                            **Vendeur :** {seller}  
                            **Paiement :** {payment}
                            
                            ---
                            """)
                            
                            for item in st.session_state.cart:
                                final = item["unit_price"] - item["discount"]
                                line = final * item["quantity"]
                                discount_text = f" *(Remise de {item['discount']} MAD)*" if item["discount"] > 0 else ""
                                st.write(f"- **{item['quantity']}x {item['name']}**{discount_text} : **{line:,.2f} MAD**")
                            
                            st.markdown("---")
                            st.markdown(f"## TOTAL : {total:,.2f} MAD")
                        
                        # Vider le panier (on garde l'état avec un petit bouton pour continuer)
                        st.session_state.cart = []
                        if st.button("🔄 Nouvelle vente"):
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"Erreur lors de la vente : {str(e)}")