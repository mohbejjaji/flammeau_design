import streamlit as st
from datetime import datetime
from services.sales_service import create_product_sale
from services.product_service import get_products
from config import COMMISSION_RATE


def sales_products_page():

    st.header("🔥 Vente Cheminées")

    products = get_products()
    fireplaces = [p for p in products if p.category in ["electrique", "bioethanol"]]

    if not fireplaces:
        st.warning("Aucune cheminée en stock")
        return

    # Initialisation du panier
    if "cart" not in st.session_state:
        st.session_state.cart = []

    col1, col2, col3 = st.columns(3)

    with col1:
        customer = st.text_input("Client *")

    with col2:
        customer_phone = st.text_input("Téléphone")

    with col3:
        seller = st.selectbox("Vendeur", ["Moi","Kamal","Youssef"])

    search = st.text_input("🔎 Rechercher produit")

    filtered = fireplaces
    if search:
        filtered = [p for p in fireplaces if search.lower() in p.name.lower()]

    col_prod, col_panier = st.columns([1,1])

    with col_prod:
        st.subheader("Produits")
        for p in filtered:
            if p.stock_quantity > 0:
                with st.container(border=True):
                    col_a, col_b = st.columns([3,1])
                    with col_a:
                        st.markdown(f"**{p.name}**")
                        st.caption(f"{p.selling_price} MAD | Stock {p.stock_quantity}")
                    with col_b:
                        if st.button("Ajouter", key=f"add_{p.id}"):
                            existing = next(
                                (i for i in st.session_state.cart if i["product_id"] == p.id),
                                None
                            )
                            if existing:
                                existing["quantity"] += 1
                            else:
                                st.session_state.cart.append({
                                    "product_id": p.id,
                                    "name": p.name,
                                    "quantity": 1,
                                    "unit_price": p.selling_price,
                                    "discount": 0
                                })
                            st.rerun()

    with col_panier:
        st.subheader("🛒 Panier")
        
        if st.session_state.cart:
            total = 0
            
            # Interface pour chaque article
            for idx, item in enumerate(st.session_state.cart):
                with st.container(border=True):
                    st.markdown(f"**{item['name']}**")
                    
                    # Utiliser des colonnes pour l'organisation
                    col_qty, col_price, col_disc = st.columns(3)
                    
                    with col_qty:
                        new_qty = st.number_input(
                            "Qté",
                            min_value=1,
                            value=item["quantity"],
                            key=f"qty_{idx}"
                        )
                        if new_qty != item["quantity"]:
                            item["quantity"] = new_qty
                            st.rerun()
                    
                    with col_price:
                        st.write(f"Prix: {item['unit_price']} MAD")
                    
                    with col_disc:
                        manual_disc = st.number_input(
                            "Remise manuelle",
                            min_value=0.0,
                            max_value=float(item["unit_price"]),
                            value=float(item["discount"]),
                            step=50.0
                            # ← pas de key= ici
                        )
                        if manual_disc != item["discount"]:
                            item["discount"] = manual_disc
                            st.rerun()

                    # Boutons de remise rapide dans une ligne séparée
                    col_b1, col_b2, col_b3, col_b4, col_b5, col_b6 = st.columns(6)

                    with col_b1:
                        if st.button("-100", key=f"btn100_{idx}"):
                            item["discount"] = min(item["discount"] + 100, item["unit_price"])
                            st.rerun()

                    with col_b2:
                        if st.button("-200", key=f"btn200_{idx}"):
                            item["discount"] = min(item["discount"] + 200, item["unit_price"])
                            st.rerun()

                    with col_b3:
                        if st.button("-500", key=f"btn500_{idx}"):
                            item["discount"] = min(item["discount"] + 500, item["unit_price"])
                            st.rerun()

                    with col_b4:
                        if st.button("-1000", key=f"btn1000_{idx}"):
                            item["discount"] = min(item["discount"] + 1000, item["unit_price"])
                            st.rerun()

                    with col_b5:
                        if st.button("Reset", key=f"reset_{idx}"):
                            item["discount"] = 0
                            st.rerun()

                    with col_b6:
                        if st.button("❌", key=f"del_{idx}"):
                            st.session_state.cart.pop(idx)
                            st.rerun()
                    
                    # Calculs avec les valeurs actuelles
                    final_price = item["unit_price"] - item["discount"]
                    line_total = final_price * item["quantity"]
                    total += line_total
                    
                    # Affichage des résultats
                    st.markdown(f"**Prix final: {final_price} MAD**")
                    st.markdown(f"**Total ligne: {line_total} MAD**")
                    
                    # Alerte si remise élevée
                    if item["discount"] > item["unit_price"] * 0.3:
                        st.warning("⚠️ Remise élevée (>30%)")
            
            # Total général
            st.divider()
            st.subheader(f"💰 Total: {total} MAD")
            
            # Commission
            commission = total * COMMISSION_RATE if seller != "Moi" else 0
            if commission:
                st.info(f"Commission {seller}: {commission:.0f} MAD")
            
            # Mode de paiement
            payment = st.selectbox(
                "Paiement",
                ["Espèces","Carte bancaire","Virement","Chèque"],
                key="payment_method"
            )
            
            # Bouton de finalisation
            if st.button("✅ Finaliser vente", use_container_width=True):
                if not customer:
                    st.error("Nom client requis")
                else:
                    try:
                        # Préparer les articles avec le prix final
                        items = []
                        for item in st.session_state.cart:
                            final_price = item["unit_price"] - item["discount"]
                            items.append({
                                "product_id": item["product_id"],
                                "quantity": item["quantity"],
                                "unit_price": final_price
                            })
                        
                        # Appel au service
                        create_product_sale(
                            customer_name=customer,
                            items=items,
                            seller_name=seller,
                            commission=commission,
                            payment_method=payment,
                            customer_phone=customer_phone
                        )
                        
                        # Succès
                        st.success("✅ Vente enregistrée")
                        
                        # Ticket
                        with st.expander("🧾 Ticket", expanded=True):
                            st.markdown(f"""
                            **FLAMMEAU DESIGN**
                            {datetime.now().strftime('%d/%m/%Y %H:%M')}
                            Client: {customer}
                            Téléphone: {customer_phone}
                            Vendeur: {seller}
                            ---
                            """)
                            
                            for item in st.session_state.cart:
                                final = item["unit_price"] - item["discount"]
                                line = final * item["quantity"]
                                st.write(f"{item['name']} x{item['quantity']} = {line} MAD")
                            
                            st.markdown(f"### Total {total} MAD")
                        
                        st.balloons()
                        
                        # Vider le panier
                        st.session_state.cart = []
                        st.rerun()
                        
                    except Exception as e:
                        st.error(str(e))
        
        else:
            st.info("Panier vide")