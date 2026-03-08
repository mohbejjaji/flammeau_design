import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from services.quote_service import (
    create_quote, get_all_quotes, get_quote_by_id,
    update_quote_status, delete_quote, generate_quote_pdf,
    convert_quote_to_sale
)
from services.product_service import get_products
import base64
import os


def quotes_page():
    st.header("📄 Gestion des Devis")
    
    # Onglets pour l'organisation
    tab1, tab2, tab3 = st.tabs(["➕ Nouveau Devis", "📋 Liste des Devis", "📊 Statistiques"])
    
    with tab1:
        st.subheader("Créer un nouveau devis")
        
        # Initialiser le panier du devis
        if 'quote_items' not in st.session_state:
            st.session_state.quote_items = []
        
        # Informations client
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("Nom du client *", key="quote_customer")
            customer_phone = st.text_input("Téléphone", key="quote_phone")
        
        with col2:
            customer_email = st.text_input("Email", key="quote_email")
            valid_days = st.number_input("Validité (jours)", min_value=1, max_value=90, value=30)
        
        # Sélection des produits
        st.markdown("---")
        st.subheader("Ajouter des produits/services")
        
        col_prod1, col_prod2, col_prod3 = st.columns([2, 1, 1])
        
        with col_prod1:
            # Option 1: Sélectionner un produit existant
            products = get_products()
            product_options = {f"{p.name} - {p.selling_price} MAD": p for p in products}
            product_options["Prestation personnalisée"] = None
            
            selected_option = st.selectbox(
                "Choisir un produit ou prestation",
                options=list(product_options.keys())
            )
        
        with col_prod2:
            quantity = st.number_input("Quantité", min_value=1, value=1, key="quote_qty")
        
        with col_prod3:
            if product_options[selected_option]:
                # Produit existant
                default_price = product_options[selected_option].selling_price
                unit_price = st.number_input(
                    "Prix unitaire",
                    value=float(default_price),
                    key="quote_price"
                )
                description = selected_option.split(" - ")[0]
                product_id = product_options[selected_option].id
            else:
                # Prestation personnalisée
                unit_price = st.number_input("Prix unitaire", min_value=0.0, value=0.0, key="quote_price_custom")
                description = st.text_input("Description prestation", key="quote_desc_custom")
                product_id = None
        
        # Bouton d'ajout
        if st.button("➕ Ajouter au devis"):
            if description and unit_price > 0:
                st.session_state.quote_items.append({
                    "product_id": product_id,
                    "description": description,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total": quantity * unit_price
                })
                st.success(f"Ajouté: {description} x{quantity}")
                st.rerun()
            else:
                st.error("Veuillez remplir tous les champs")
        
        # Afficher le panier du devis
        if st.session_state.quote_items:
            st.markdown("---")
            st.subheader("📦 Articles du devis")
            
            # Afficher le tableau
            df_items = pd.DataFrame(st.session_state.quote_items)
            df_display = df_items[["description", "quantity", "unit_price", "total"]].copy()
            df_display.columns = ["Description", "Qté", "Prix unitaire", "Total"]
            df_display["Prix unitaire"] = df_display["Prix unitaire"].apply(lambda x: f"{x:,.2f} MAD")
            df_display["Total"] = df_display["Total"].apply(lambda x: f"{x:,.2f} MAD")
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Total du devis
            total_ht = sum(item["total"] for item in st.session_state.quote_items)
            total_ttc = total_ht * 1.20
            
            col_total1, col_total2, col_total3 = st.columns(3)
            with col_total1:
                st.metric("Total HT", f"{total_ht:,.2f} MAD")
            with col_total2:
                st.metric("TVA (20%)", f"{total_ht * 0.20:,.2f} MAD")
            with col_total3:
                st.metric("Total TTC", f"{total_ttc:,.2f} MAD")
            
            # Notes
            notes = st.text_area("Notes / Conditions particulières", height=100)
            
            # Boutons d'action
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            
            with col_btn1:
                if st.button("🗑️ Vider le panier"):
                    st.session_state.quote_items = []
                    st.rerun()
            
            with col_btn2:
                if st.button("💾 Sauvegarder le devis", type="primary"):
                    if not customer_name:
                        st.error("Le nom du client est obligatoire")
                    else:
                        try:
                            quote = create_quote(
                                customer_name=customer_name,
                                customer_phone=customer_phone,
                                customer_email=customer_email,
                                items=st.session_state.quote_items,
                                notes=notes
                            )
                            st.success(f"✅ Devis {quote.quote_number} créé avec succès!")
                            st.session_state.quote_items = []
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur: {e}")
            
            with col_btn3:
                if st.button("📄 Aperçu PDF"):
                    st.info("Fonctionnalité à venir")
    
    with tab2:
        st.subheader("Liste des devis")
        
        # Récupérer tous les devis
        quotes = get_all_quotes()
        
        if not quotes:
            st.info("Aucun devis créé pour le moment")
        else:
            # Filtres
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                status_filter = st.selectbox(
                    "Filtrer par statut",
                    ["Tous", "brouillon", "envoyé", "accepté", "refusé", "converti"]
                )
            
            with col_f2:
                search = st.text_input("Rechercher client", placeholder="Nom du client...")
            
            # Filtrer les devis
            filtered_quotes = quotes
            if status_filter != "Tous":
                filtered_quotes = [q for q in quotes if q.status == status_filter]
            
            if search:
                filtered_quotes = [q for q in filtered_quotes if search.lower() in q.customer_name.lower()]
            
            # ✅ La boucle for DOIT contenir TOUT l'affichage de chaque devis
            for quote in filtered_quotes:
                with st.expander(f"📄 {quote.quote_number} - {quote.customer_name} - {quote.date.strftime('%d/%m/%Y')} - {quote.status.upper()}"):
                    col_info1, col_info2, col_info3 = st.columns(3)
                    
                    with col_info1:
                        st.write(f"**Client:** {quote.customer_name}")
                        st.write(f"**Tél:** {quote.customer_phone or 'Non renseigné'}")
                    
                    with col_info2:
                        st.write(f"**Email:** {quote.customer_email or 'Non renseigné'}")
                        st.write(f"**Valable jusqu'au:** {quote.valid_until.strftime('%d/%m/%Y')}")
                    
                    with col_info3:
                        st.metric("Montant TTC", f"{quote.total_amount * 1.20:,.2f} MAD")
                    
                    # Articles
                    st.write("**Articles:**")
                    for item in quote.quote_items:
                        st.write(f"• {item.description} x{item.quantity} = {item.quantity * item.unit_price:,.2f} MAD")
                    
                    if quote.notes:
                        st.write(f"**Notes:** {quote.notes}")
                    
                    # ✅ Les boutons DOIVENT être à l'INTÉRIEUR de l'expander
                    col_act1, col_act2, col_act3, col_act4, col_act5 = st.columns(5)
                    
                    with col_act1:
                        if st.button("📥 PDF", key=f"pdf_{quote.id}"):
                            with st.spinner("Génération du PDF en cours..."):
                                pdf_path = generate_quote_pdf(quote.id)
                                if pdf_path and os.path.exists(pdf_path):
                                    with open(pdf_path, "rb") as f:
                                        pdf_bytes = f.read()
                                    
                                    st.download_button(
                                        label="📥 Télécharger le PDF",
                                        data=pdf_bytes,
                                        file_name=os.path.basename(pdf_path),
                                        mime="application/pdf",
                                        key=f"download_{quote.id}"
                                    )
                                    
                                    st.success("✅ PDF généré avec succès!")
                                else:
                                    st.error("❌ Erreur lors de la génération du PDF")
                    
                    with col_act2:
                        new_status = st.selectbox(
                            "Statut",
                            ["brouillon", "envoyé", "accepté", "refusé", "converti"],
                            index=["brouillon", "envoyé", "accepté", "refusé", "converti"].index(quote.status),
                            key=f"status_{quote.id}"
                        )
                        if new_status != quote.status:
                            update_quote_status(quote.id, new_status)
                            st.rerun()
                    
                    with col_act3:
                        if st.button("💰 Convertir en vente", key=f"convert_{quote.id}"):
                            with st.spinner("Conversion en cours..."):
                                success, message = convert_quote_to_sale(quote.id)
                                if success:
                                    st.success(f"✅ {message}")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                    
                    with col_act4:
                        if st.button("✉️ Envoyer par email", key=f"email_{quote.id}"):
                            st.info("Fonctionnalité d'envoi par email à venir")
                    
                    with col_act5:
                        if st.button("🗑️ Supprimer", key=f"del_{quote.id}"):
                            delete_quote(quote.id)
                            st.rerun()
    
    with tab3:
        st.subheader("📊 Statistiques des devis")
        
        quotes = get_all_quotes()
        
        if quotes:
            # Statistiques générales
            total_quotes = len(quotes)
            accepted_quotes = len([q for q in quotes if q.status == "accepté"])
            converted_quotes = len([q for q in quotes if q.status == "converti"])
            total_amount = sum(q.total_amount * 1.20 for q in quotes)
            
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            with col_s1:
                st.metric("Total devis", total_quotes)
            with col_s2:
                st.metric("Devis acceptés", accepted_quotes)
            with col_s3:
                st.metric("Taux conversion", f"{((accepted_quotes + converted_quotes)/total_quotes*100):.1f}%")
            with col_s4:
                st.metric("Montant total", f"{total_amount:,.0f} MAD")
            
            # Graphique d'évolution
            df_quotes = pd.DataFrame([
                {
                    "date": q.date,
                    "montant": q.total_amount * 1.20,
                    "statut": q.status
                }
                for q in quotes
            ])
            
            df_quotes['date'] = pd.to_datetime(df_quotes['date'])
            df_monthly = df_quotes.groupby(pd.Grouper(key='date', freq='M')).agg({
                'montant': 'sum',
                'statut': 'count'
            }).reset_index()
            
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                st.line_chart(df_monthly.set_index('date')['montant'])
            
            with col_g2:
                status_counts = df_quotes['statut'].value_counts()
                st.bar_chart(status_counts)
        else:
            st.info("Pas assez de données pour les statistiques")