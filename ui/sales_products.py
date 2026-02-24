import streamlit as st
import pandas as pd
from datetime import datetime
from services.sales_service import create_product_sale
from services.product_service import get_products
from core.database import SessionLocal
from core.models import Sale
from config import COMMISSION_RATE


def sales_products_page():
    st.header("🔥 Vente de Cheminées")
    
    # Filtrer pour n'avoir que les cheminées (électriques et bioéthanol)
    all_products = get_products()
    fireplaces = [p for p in all_products if p.category in ["electrique", "bioethanol"]]
    
    if not fireplaces:
        st.warning("Aucune cheminée en stock")
        return
    
    # Sélection du vendeur
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Nouvelle vente")
    
    with col2:
        seller = st.selectbox(
            "Vendeur",
            ["Moi", "Employé 1", "Employé 2"],
            key="seller"
        )
    
    # Informations client
    with st.expander("📋 Informations client", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            customer = st.text_input("Nom du client *")
        with col2:
            customer_phone = st.text_input("Téléphone")
        with col3:
            customer_email = st.text_input("Email")
    
    # Récupérer les produits
    products = get_products()
    
    if not products:
        st.warning("Aucun produit disponible. Veuillez d'abord ajouter des produits.")
        return
    
    # Filtres par catégorie
    st.subheader("🔍 Filtres")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        categories = ["Toutes"] + list(set(p.category for p in products))
        selected_category = st.selectbox("Catégorie", categories)
    
    # Filtrer les produits
    filtered_products = products
    if selected_category != "Toutes":
        filtered_products = [p for p in products if p.category == selected_category]
    
    # Création du panier
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    
    # Sélection des produits
    col_prod, col_panier = st.columns([1, 1])
    
    with col_prod:
        st.subheader("📦 Sélection produits")
        
        for p in filtered_products:
            if p.stock_quantity > 0:
                with st.container():
                    col_info, col_qty = st.columns([3, 1])
                    with col_info:
                        st.markdown(f"**{p.name}**")
                        st.caption(f"💰 {p.selling_price} MAD | Stock: {p.stock_quantity} | {p.subtype}")
                    
                    with col_qty:
                        qty = st.number_input(
                            "Qté",
                            min_value=0,
                            max_value=p.stock_quantity,
                            key=f"qty_{p.id}",
                            label_visibility="collapsed"
                        )
                        
                        if qty > 0 and st.button("➕", key=f"add_{p.id}"):
                            # Vérifier si déjà dans le panier
                            existing = next((item for item in st.session_state.cart 
                                           if item['product_id'] == p.id), None)
                            
                            if existing:
                                new_qty = existing['quantity'] + qty
                                if new_qty <= p.stock_quantity:
                                    existing['quantity'] = new_qty
                                    st.success(f"Quantité mise à jour")
                                else:
                                    st.error("Stock insuffisant")
                            else:
                                st.session_state.cart.append({
                                    'product_id': p.id,
                                    'name': p.name,
                                    'category': p.category,
                                    'subtype': p.subtype,
                                    'quantity': qty,
                                    'unit_price': p.selling_price
                                })
                                st.success(f"Ajouté au panier")
                            st.rerun()
    
    with col_panier:
        st.subheader("🛒 Panier")
        
        if st.session_state.cart:
            cart_total = 0
            for i, item in enumerate(st.session_state.cart):
                item_total = item['quantity'] * item['unit_price']
                cart_total += item_total
                
                col_a, col_b, col_c, col_d = st.columns([3, 1, 1.5, 0.5])
                with col_a:
                    st.write(f"**{item['name']}**")
                with col_b:
                    st.write(f"x{item['quantity']}")
                with col_c:
                    st.write(f"{item_total} MAD")
                with col_d:
                    if st.button("❌", key=f"del_{i}"):
                        st.session_state.cart.pop(i)
                        st.rerun()
            
            st.markdown("---")
            st.subheader(f"💰 Total: {cart_total} MAD")
            
            # Calcul de la commission
            commission = cart_total * COMMISSION_RATE if seller != "Moi" else 0
            
            if commission > 0:
                st.info(f"Commission {seller}: {commission} MAD")
            
            # Méthode de paiement
            payment_method = st.selectbox(
                "Mode de paiement",
                ["Espèces", "Carte bancaire", "Virement", "Chèque"]
            )
            
            if st.button("✅ Valider la vente", type="primary", use_container_width=True):
                if not customer:
                    st.error("Nom client obligatoire")
                else:
                    try:
                        # Préparer les items
                        items = []
                        for item in st.session_state.cart:
                            items.append({
                                "product_id": item['product_id'],
                                "quantity": item['quantity'],
                                "unit_price": item['unit_price']
                            })
                        
                        # Créer la vente avec commission
                        create_product_sale(
                            customer_name=customer,
                            items=items,
                            seller_name=seller,
                            commission=commission,
                            payment_method=payment_method,
                            customer_phone=customer_phone,
                            customer_email=customer_email
                        )
                        
                        # Afficher le récapitulatif
                        st.success("✅ Vente enregistrée!")
                        
                        with st.expander("🧾 Ticket de vente", expanded=True):
                            st.markdown(f"""
                            **FLAMMEAU DESIGN**  
                            Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}  
                            Client: {customer}  
                            Vendeur: {seller}  
                            
                            **Détails:**  
                            """)
                            
                            for item in st.session_state.cart:
                                st.markdown(f"- {item['name']} x{item['quantity']} = {item['quantity'] * item['unit_price']} MAD")
                            
                            st.markdown(f"**Total: {cart_total} MAD**")
                            if commission > 0:
                                st.markdown(f"*Commission: {commission} MAD*")
                            
                            st.markdown("🔥 Merci de votre confiance !")
                        
                        st.balloons()
                        st.session_state.cart = []
                        
                    except Exception as e:
                        st.error(f"Erreur: {e}")
        else:
            st.info("Panier vide")
    
    # Alertes stock
    low_stock = [p for p in products if p.stock_quantity < 5]
    if low_stock:
        with st.expander("⚠️ Alertes stock faible"):
            for p in low_stock:
                st.warning(f"{p.name} - Stock: {p.stock_quantity}")