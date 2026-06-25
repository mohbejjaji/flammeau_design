import streamlit as st
from services.sales_service import (
    create_service_sale_with_deposit,
    pay_service_balance,
    get_pending_service_payments
)
from datetime import datetime


def sales_services_page():
    st.header("🔧 Vente de Prestations")
    
    # Onglets
    tab1, tab2 = st.tabs(["➕ Nouvelle prestation", "💰 Suivi des paiements"])
    
    with tab1:
        st.subheader("Nouvelle prestation")
        
        # Informations générales
        col1, col2 = st.columns(2)
        
        with col1:
            seller = st.selectbox(
                "Vendeur",
                ["Moi", "Employé 1", "Employé 2"],
                key="service_seller"
            )
            
            customer = st.text_input("Nom du client *", key="service_customer")
            customer_phone = st.text_input("Téléphone", key="service_phone")
            customer_email = st.text_input("Email", key="service_email")
        
        with col2:
            description = st.text_input("Description de la prestation *")
            quantity = st.number_input("Quantité", min_value=1, value=1)
            unit_price = st.number_input("Prix total TTC (MAD) *", min_value=0.0, step=100.0)
            unit_cost = st.number_input("Coût réel (MAD)", min_value=0.0, step=50.0)
        
        st.markdown("---")
        st.subheader("💰 Acompte")
        
        col_a1, col_a2 = st.columns(2)
        
        with col_a1:
            has_deposit = st.radio("Acompte ?", ["Oui", "Non"], horizontal=True)
            
            if has_deposit == "Oui":
                deposit_amount = st.number_input(
                    "Montant de l'acompte (MAD)",
                    min_value=0.0,
                    max_value=unit_price * quantity,
                    step=100.0,
                    value=min(unit_price * quantity * 0.3, 500.0)
                )
                deposit_method = st.selectbox(
                    "Mode de paiement de l'acompte",
                    ["Espèces", "Carte bancaire", "Virement", "Chèque"]
                )
            else:
                deposit_amount = 0
                deposit_method = "Espèces"
        
        with col_a2:
            total = unit_price * quantity
            if has_deposit == "Oui":
                remaining = total - deposit_amount
                st.info(f"""
                **Récapitulatif:**
                - Total: {total:,.0f} MAD
                - Acompte: {deposit_amount:,.0f} MAD
                - **Reste: {remaining:,.0f} MAD**
                """)
            else:
                st.info(f"**Total à payer:** {total:,.0f} MAD")
        
        if st.button("✅ Enregistrer la prestation", type="primary"):
            if not customer or not description or unit_price <= 0:
                st.error("Veuillez remplir tous les champs obligatoires (*)")
            else:
                try:
                    result = create_service_sale_with_deposit(
                        customer_name=customer,
                        description=description,
                        quantity=quantity,
                        unit_price=unit_price,
                        unit_cost=unit_cost,
                        deposit_amount=deposit_amount,
                        deposit_payment_method=deposit_method,
                        seller_name=seller,
                        customer_phone=customer_phone,
                        customer_email=customer_email
                    )
                    
                    st.success(f"✅ Prestation #{result['sale_id']} enregistrée!")
                    
                    if result['status'] == "payé":
                        st.success("💰 Prestation entièrement payée !")
                    elif result['deposit'] > 0:
                        st.info(f"💰 Acompte de {result['deposit']:,.0f} MAD enregistré. Solde: {result['remaining']:,.0f} MAD")
                    else:
                        st.warning(f"⏳ En attente de paiement - {result['remaining']:,.0f} MAD")
                    
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"Erreur: {e}")
    
    with tab2:
        st.subheader("💰 Suivi des paiements")
        
        # Récupérer les prestations en attente
        pending = get_pending_service_payments()
        
        if not pending:
            st.info("✅ Aucun paiement en attente")
        else:
            st.warning(f"⚠️ {len(pending)} prestations avec paiement en attente")
            
            for p in pending:
                with st.expander(f"📋 Prestation #{p['id']} - {p['customer']} - {p['date']}"):
                    col_p1, col_p2, col_p3 = st.columns(3)
                    
                    with col_p1:
                        st.write(f"**Description:** {p['description']}")
                        st.write(f"**Total:** {p['total']:,.0f} MAD")
                    
                    with col_p2:
                        st.write(f"**Acompte versé:** {p['deposit']:,.0f} MAD")
                        st.write(f"**Statut:** {p['status']}")
                    
                    with col_p3:
                        st.metric(
                            "💰 Solde restant",
                            f"{p['remaining']:,.0f} MAD",
                            delta=f"{p['remaining']/p['total']*100:.1f}%"
                        )
                    
                    if p['remaining'] > 0:
                        st.markdown("---")
                        with st.form(key=f"balance_form_{p['id']}"):
                            col_b1, col_b2 = st.columns(2)
                            
                            with col_b1:
                                balance_paid = st.number_input(
                                    "Montant du solde",
                                    min_value=0.0,
                                    max_value=p['remaining'],
                                    value=p['remaining'],
                                    step=100.0
                                )
                            
                            with col_b2:
                                balance_method = st.selectbox(
                                    "Mode de paiement",
                                    ["Espèces", "Carte bancaire", "Virement", "Chèque"]
                                )
                            
                            if st.form_submit_button("✅ Enregistrer le paiement"):
                                try:
                                    pay_service_balance(p['id'], balance_paid, balance_method)
                                    st.success("💰 Paiement enregistré!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erreur: {e}")