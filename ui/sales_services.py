import streamlit as st
from services.sales_service import create_service_sale
from datetime import datetime


def sales_services_page():
    st.header("🔧 Vente de Prestations")
    
    # Sélection du vendeur
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Nouvelle prestation")
    
    with col2:
        seller = st.selectbox(
            "Vendeur",
            ["Moi", "Employé 1", "Employé 2"],
            key="service_seller"
        )
    
    # Informations client
    with st.expander("📋 Informations client", expanded=True):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            customer = st.text_input("Nom du client *", key="service_customer")
        with col_c2:
            customer_phone = st.text_input("Téléphone", key="service_phone")
        
        customer_email = st.text_input("Email", key="service_email")
    
    # Types de prestations prédéfinies
    service_types = {
        "installation": {
            "name": "Installation de cheminée",
            "default_price": 1500,
            "default_cost": 500,
            "description": "Installation complète avec mise en service"
        },
        "maintenance": {
            "name": "Maintenance / Nettoyage",
            "default_price": 800,
            "default_cost": 200,
            "description": "Nettoyage et vérification annuelle"
        },
        "depannage": {
            "name": "Dépannage",
            "default_price": 600,
            "default_cost": 150,
            "description": "Intervention de dépannage"
        },
        "livraison": {
            "name": "Livraison",
            "default_price": 300,
            "default_cost": 100,
            "description": "Frais de livraison"
        },
        "personnalise": {
            "name": "Prestation personnalisée",
            "default_price": 0,
            "default_cost": 0,
            "description": "À définir"
        }
    }
    
    # Sélection du type de prestation
    st.subheader("📋 Type de prestation")
    
    service_option = st.selectbox(
        "Choisir une prestation",
        options=list(service_types.keys()),
        format_func=lambda x: service_types[x]["name"]
    )
    
    selected_service = service_types[service_option]
    
    # Détails de la prestation
    st.subheader("📝 Détails")
    
    col_d1, col_d2 = st.columns(2)
    
    with col_d1:
        if service_option == "personnalise":
            description = st.text_input("Description de la prestation *")
        else:
            description = selected_service["name"]
            st.info(f"**Description:** {selected_service['description']}")
    
    with col_d2:
        quantity = st.number_input("Quantité", min_value=1, value=1, key="service_qty")
    
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        if service_option == "personnalise":
            unit_price = st.number_input(
                "Prix facturé (MAD) *",
                min_value=0.0,
                value=0.0,
                step=100.0,
                format="%.2f",
                key="service_price"
            )
        else:
            unit_price = st.number_input(
                "Prix facturé (MAD) *",
                min_value=0.0,
                value=float(selected_service["default_price"]),
                step=100.0,
                format="%.2f",
                key="service_price"
            )
    
    with col_p2:
        if service_option == "personnalise":
            unit_cost = st.number_input(
                "Coût réel (MAD)",
                min_value=0.0,
                value=0.0,
                step=50.0,
                format="%.2f",
                key="service_cost",
                help="Coût réel de la prestation (main d'œuvre, déplacement...)"
            )
        else:
            unit_cost = st.number_input(
                "Coût réel (MAD)",
                min_value=0.0,
                value=float(selected_service["default_cost"]),
                step=50.0,
                format="%.2f",
                key="service_cost",
                help="Coût réel de la prestation (main d'œuvre, déplacement...)"
            )
    
    # Méthode de paiement
    payment_method = st.selectbox(
        "Mode de paiement",
        ["Espèces", "Carte bancaire", "Virement", "Chèque"],
        key="service_payment"
    )
    
    # Calcul et aperçu
    if description and unit_price > 0:
        total_ht = unit_price * quantity
        total_ttc = total_ht * 1.20
        marge = (unit_price - unit_cost) * quantity
        
        st.markdown("---")
        st.subheader("💰 Aperçu")
        
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        
        with col_r1:
            st.metric("Total HT", f"{total_ht:,.0f} MAD")
        
        with col_r2:
            st.metric("TVA (20%)", f"{total_ht * 0.20:,.0f} MAD")
        
        with col_r3:
            st.metric("Total TTC", f"{total_ttc:,.0f} MAD")
        
        with col_r4:
            marge_pct = (marge / total_ht * 100) if total_ht > 0 else 0
            st.metric("Marge", f"{marge:,.0f} MAD", delta=f"{marge_pct:.1f}%")
        
        # Bouton de validation
        if st.button("✅ Valider la prestation", type="primary", use_container_width=True):
            if not customer:
                st.error("Le nom du client est obligatoire")
            elif not description:
                st.error("La description est obligatoire")
            else:
                try:
                    sale = create_service_sale(
                        customer_name=customer,
                        description=description,
                        quantity=quantity,
                        unit_price=unit_price,
                        unit_cost=unit_cost,
                        seller_name=seller,
                        payment_method=payment_method,
                        customer_phone=customer_phone,
                        customer_email=customer_email
                    )
                    
                    st.success("✅ Prestation enregistrée avec succès!")
                    
                    # Afficher le ticket
                    with st.expander("🧾 Ticket de prestation", expanded=True):
                        st.markdown(f"""
                        **FLAMMEAU DESIGN**  
                        Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}  
                        Client: {customer}  
                        Vendeur: {seller}  
                        Paiement: {payment_method}  
                        
                        **Prestation:**  
                        - {description} x{quantity}  
                        
                        **Total: {total_ttc:,.0f} MAD TTC**  
                        ({total_ht:,.0f} MAD HT + {total_ht * 0.20:,.0f} MAD TVA)
                        
                        🔥 Merci de votre confiance !
                        """)
                    
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"Erreur: {e}")
    else:
        st.warning("Veuillez remplir tous les champs obligatoires")
    
    # Informations complémentaires
    with st.expander("ℹ️ Types de prestations"):
        st.markdown("""
        **Installation de cheminée** : Installation complète, mise en service, test de fonctionnement  
        **Maintenance / Nettoyage** : Nettoyage annuel, vérification des brûleurs, contrôle de sécurité  
        **Dépannage** : Intervention en cas de panne ou dysfonctionnement  
        **Livraison** : Frais de livraison et installation simple  
        **Prestation personnalisée** : Pour toute autre prestation sur mesure
        """)