import streamlit as st
import pandas as pd
from services.accessory_service import create_accessory_sale, get_accessory_catalog
from datetime import datetime


def accessories_page():
    st.header("🪵 Vente d'Accessoires")
    
    # ✅ Initialisation du panier dans session_state
    if 'acc_cart' not in st.session_state:
        st.session_state.acc_cart = []
    
    # Types d'accessoires avec leurs spécificités
    accessory_types = {
        "galets": {
            "name": "Galets décoratifs",
            "unit": "kg",
            "default_price": 150,
            "description": "Galets pour cheminée électrique"
        },
        "buches": {
            "name": "Bûches décoratives",
            "unit": "pièce",
            "default_price": 200,
            "description": "Bûches effet réel"
        },
        "ethanol": {
            "name": "Bioéthanol",
            "unit": "litre",
            "default_price": 50,
            "description": "Carburant pour cheminée bioéthanol"
        }
    }
    
    # Onglets
    tab1, tab2 = st.tabs(["🛒 Vente", "📋 Catalogue"])
    
    with tab1:
        # ✅ Initialisation (à placer TOUT EN HAUT de l'onglet ou de la fonction)
        if 'acc_cart' not in st.session_state:
            st.session_state.acc_cart = []
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Informations client")
            customer = st.text_input("Nom du client *", key="acc_customer")
            customer_phone = st.text_input("Téléphone", key="acc_phone")
            payment_method = st.selectbox(
                "Mode de paiement",
                ["Espèces", "Carte bancaire", "Virement", "Chèque"],
                key="acc_payment"
            )
        
        with col2:
            st.subheader("Sélection des accessoires")
            
            # Récupérer les accessoires en stock
            accessories = get_accessory_catalog()
            in_stock = [a for a in accessories if a.stock_quantity > 0]
            
            if not in_stock:
                st.warning("Aucun accessoire en stock")
            else:
                # Interface de vente simplifiée
                for acc in in_stock:
                    with st.container():
                        col_a1, col_a2, col_a3, col_a4 = st.columns([3, 1, 1, 1])
                        
                        with col_a1:
                            st.write(f"**{acc.name}**")
                            st.caption(f"{acc.description if acc.description else ''}")
                        
                        with col_a2:
                            st.metric("Prix", f"{acc.selling_price} MAD")
                        
                        with col_a3:
                            st.metric("Stock", acc.stock_quantity)
                        
                        with col_a4:
                            qty = st.number_input(
                                "Qté",
                                min_value=0,
                                max_value=acc.stock_quantity,
                                key=f"acc_qty_{acc.id}",
                                label_visibility="collapsed"
                            )
                            
                            if qty > 0 and st.button("➕", key=f"acc_add_{acc.id}"):
                                # Ajouter au panier
                                existing = next(
                                    (item for item in st.session_state.acc_cart 
                                    if item['product_id'] == acc.id),
                                    None
                                )
                                
                                if existing:
                                    new_qty = existing['quantity'] + qty
                                    if new_qty <= acc.stock_quantity:
                                        existing['quantity'] = new_qty
                                        st.success(f"Quantité mise à jour")
                                else:
                                    st.session_state.acc_cart.append({
                                        'product_id': acc.id,
                                        'name': acc.name,
                                        'quantity': qty,
                                        'unit_price': acc.selling_price
                                    })
                                    st.success(f"Ajouté au panier")
                                st.rerun()
        
        # Panier (maintenant st.session_state.acc_cart existe toujours)
        if st.session_state.acc_cart:
            st.markdown("---")
            st.subheader("🛒 Panier")
            
            cart_total = 0
            for i, item in enumerate(st.session_state.acc_cart):
                item_total = item['quantity'] * item['unit_price']
                cart_total += item_total
                
                col_p1, col_p2, col_p3, col_p4 = st.columns([3, 1, 1.5, 0.5])
                with col_p1:
                    st.write(f"**{item['name']}**")
                with col_p2:
                    st.write(f"x{item['quantity']}")
                with col_p3:
                    st.write(f"{item_total} MAD")
                with col_p4:
                    if st.button("❌", key=f"acc_del_{i}"):
                        st.session_state.acc_cart.pop(i)
                        st.rerun()
            
            st.markdown("---")
            st.subheader(f"💰 Total: {cart_total} MAD")
            
            if st.button("✅ Valider la vente", type="primary", use_container_width=True):
                if not customer:
                    st.error("Nom client obligatoire")
                else:
                    try:
                        items = []
                        for item in st.session_state.acc_cart:
                            items.append({
                                "product_id": item['product_id'],
                                "quantity": item['quantity'],
                                "unit_price": item['unit_price']
                            })
                        
                        sale = create_accessory_sale(
                            customer_name=customer,
                            items=items,
                            seller_name="Moi",
                            payment_method=payment_method,
                            customer_phone=customer_phone
                        )
                        
                        st.success("✅ Vente d'accessoires enregistrée!")
                        
                        with st.expander("🧾 Ticket de vente"):
                            st.markdown(f"""
                            **FLAMMEAU DESIGN - Accessoires**  
                            Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}  
                            Client: {customer}  
                            
                            **Détails:**  
                            """)
                            
                            for item in st.session_state.acc_cart:
                                st.markdown(f"- {item['name']} x{item['quantity']} = {item['quantity'] * item['unit_price']} MAD")
                            
                            st.markdown(f"**Total: {cart_total} MAD**")
                            st.markdown("🔥 Merci de votre confiance !")
                        
                        st.balloons()
                        st.session_state.acc_cart = []
                        
                    except Exception as e:
                        st.error(f"Erreur: {e}")
    
    with tab2:
        st.subheader("📋 Catalogue des accessoires")
        
        accessories = get_accessory_catalog()
        
        if accessories:
            # Statistiques
            total_accessories = len(accessories)
            total_stock = sum(a.stock_quantity for a in accessories)
            total_value = sum(a.selling_price * a.stock_quantity for a in accessories)
            
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.metric("Types d'accessoires", total_accessories)
            with col_s2:
                st.metric("Stock total", total_stock)
            with col_s3:
                st.metric("Valeur stock", f"{total_value:,.0f} MAD")
            
            # Tableau des stocks
            stock_data = []
            for acc in accessories:
                stock_data.append({
                    "Accessoire": acc.name,
                    "Type": acc.subtype,
                    "Stock": acc.stock_quantity,
                    "Prix unitaire": f"{acc.selling_price} MAD",
                    "Valeur": f"{acc.selling_price * acc.stock_quantity} MAD",
                    "Statut": "✅ OK" if acc.stock_quantity > 10 else "⚠️ Faible" if acc.stock_quantity > 0 else "❌ Rupture"
                })
            
            df = pd.DataFrame(stock_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Aucun accessoire dans le catalogue")