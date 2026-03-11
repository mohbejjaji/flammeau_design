# 1. Modules natifs Python
import os
import base64
from datetime import datetime, timedelta

# 2. Bibliothèques tierces (installées via pip)
import streamlit as st
import pandas as pd
import plotly.express as px

# 3. Modules locaux (ton propre code)
from services.sales_history_service import (
    get_sales_history, 
    get_sale_details, 
    generate_ticket_pdf,
    get_sales_stats, 
    export_sales_to_excel
)


def sales_history_page():
    st.header("📜 Historique et Analyse des Ventes")
    
    # --- Onglets ---
    tab1, tab2, tab3 = st.tabs(["📋 Registre des ventes", "📊 Tableau de bord", "📤 Export Comptable"])
    
    # ==========================================
    # ONGLET 1 : REGISTRE DES VENTES
    # ==========================================
    with tab1:
        st.subheader("Filtres de recherche")
        
        # Filtres compacts
        col_f1, col_f2, col_f3 = st.columns([2, 1.5, 1.5], vertical_alignment="bottom")
        
        with col_f1:
            period = st.selectbox(
                "Période prédéfinie",
                ["Aujourd'hui", "Cette semaine", "Ce mois", "Ce trimestre", "Cette année", "Personnalisé"],
                label_visibility="collapsed"
            )
        
        # Calculer les dates selon la période
        today = datetime.now().date()
        
        if period == "Aujourd'hui":
            start_date, end_date = today, today
        elif period == "Cette semaine":
            start_date = today - timedelta(days=today.weekday())
            end_date = today
        elif period == "Ce mois":
            start_date = today.replace(day=1)
            end_date = today
        elif period == "Ce trimestre":
            quarter = (today.month - 1) // 3
            start_date = today.replace(month=quarter*3 + 1, day=1)
            end_date = today
        elif period == "Cette année":
            start_date = today.replace(month=1, day=1)
            end_date = today
        else: # Personnalisé
            with col_f2:
                start_date = st.date_input("Date début", today - timedelta(days=30))
            with col_f3:
                end_date = st.date_input("Date fin", today)
        
        st.markdown("---")
        
        # Récupérer les ventes
        sales = get_sales_history(start_date, end_date)
        
        if not sales:
            st.info("ℹ️ Aucune transaction trouvée pour cette période.")
        else:
            # --- Métriques rapides (KPIs) ---
            total_ca = sum(s['revenue'] for s in sales)
            total_profit = sum(s['profit'] for s in sales)
            total_ventes = len(sales)
            marge_moyenne = (total_profit / total_ca * 100) if total_ca > 0 else 0
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("Nombre de ventes", total_ventes)
            col_m2.metric("CA Total HT", f"{total_ca:,.2f} MAD")
            col_m3.metric("Bénéfice Total", f"{total_profit:,.2f} MAD")
            col_m4.metric("Marge Moyenne", f"{marge_moyenne:.1f} %")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- Liste des ventes (Expanders stylisés) ---
            for sale in sales:
                ca_ttc = sale['revenue'] * 1.20
                expander_title = f"💳 Vente #{sale['id']} | {sale['date']} | {sale['customer']} | **{ca_ttc:,.2f} MAD TTC**"
                
                with st.expander(expander_title):
                    st.write(f"**Vendeur :** {sale['seller']}  |  **Paiement :** {sale['payment']}  |  **Commission :** {sale['commission']:,.0f} MAD")
                    
                    # Détail des articles
                    details = get_sale_details(sale['id'])
                    
                    if details:
                        with st.container(border=True):
                            st.caption("DÉTAIL DES ARTICLES")
                            for item in details['items']:
                                st.markdown(f"- **{item['quantity']}x** {item['name']} : {item['total']:,.2f} MAD")
                            
                            st.divider()
                            
                            # Totaux financiers
                            c_ht, c_tva, c_ttc = st.columns(3)
                            c_ht.metric("Total HT", f"{details['total_revenue']:,.2f} MAD")
                            c_tva.metric("TVA (20%)", f"{details['total_revenue'] * 0.20:,.2f} MAD")
                            c_ttc.metric("Total TTC", f"{details['total_revenue'] * 1.20:,.2f} MAD")
                        
                        # --- Bouton de téléchargement natif Streamlit ---
                        pdf_path = generate_ticket_pdf(sale['id'])
                        if pdf_path and os.path.exists(pdf_path):
                            with open(pdf_path, "rb") as f:
                                st.download_button(
                                    label="📥 Télécharger le Ticket (PDF)",
                                    data=f,
                                    file_name=os.path.basename(pdf_path),
                                    mime="application/pdf",
                                    key=f"dl_ticket_{sale['id']}"
                                )

    # ==========================================
    # ONGLET 2 : TABLEAU DE BORD (Statistiques)
    # ==========================================
    with tab2:
        st.subheader("📊 Performances Globales")
        
        period_stats = st.radio(
            "Vue d'ensemble par :",
            ["Jour", "Semaine", "Mois", "Année"],
            horizontal=True
        )
        
        period_map = {"Jour": "day", "Semaine": "week", "Mois": "month", "Année": "year"}
        stats = get_sales_stats(period_map[period_stats])
        
        with st.container(border=True):
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            col_s1.metric("Transactions", stats['count'])
            col_s2.metric("Chiffre d'Affaires", f"{stats['revenue']:,.2f} MAD")
            col_s3.metric("Bénéfice Net", f"{stats['profit']:,.2f} MAD")
            col_s4.metric("Panier Moyen", f"{stats['avg_ticket']:,.2f} MAD")
        
        st.markdown("---")
        st.subheader("📈 Évolution sur les 30 derniers jours")
        
        end = datetime.now().date()
        start = end - timedelta(days=30)
        sales_30d = get_sales_history(start, end)
        
        if sales_30d:
            df = pd.DataFrame(sales_30d)
            df['date'] = pd.to_datetime(df['date'])
            df_daily = df.groupby(df['date'].dt.date).agg({
                'revenue': 'sum',
                'profit': 'sum'
            }).reset_index()
            
            # Utilisation d'un Area Chart pour un rendu plus moderne
            fig = px.area(
                df_daily,
                x='date',
                y=['revenue', 'profit'],
                labels={'value': 'Montant (MAD)', 'variable': 'Indicateur', 'date': 'Date'},
                color_discrete_map={'revenue': '#00adb5', 'profit': '#17c3b2'} # Couleurs harmonieuses
            )
            
            # Options visuelles pour le graphique
            fig.update_layout(
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Pas assez de données pour générer le graphique.")

    # ==========================================
    # ONGLET 3 : EXPORT COMPTABLE
    # ==========================================
    with tab3:
        st.subheader("📤 Exporter les données vers Excel")
        st.write("Générez un fichier complet pour votre comptabilité.")
        
        with st.container(border=True):
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                export_start = st.date_input("Date de début", today - timedelta(days=30), key="export_start")
            with col_e2:
                export_end = st.date_input("Date de fin", today, key="export_end")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- Bouton d'export généré dynamiquement ---
            filepath = export_sales_to_excel(export_start, export_end)
            
            if filepath and os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    st.download_button(
                        label="📥 Télécharger le fichier Excel",
                        data=f,
                        file_name=os.path.basename(filepath),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True
                    )
            else:
                st.error("Impossible de générer le fichier Excel actuellement.")
                
        st.caption("""
        **💡 Ce que contient l'export :**
        La liste complète des transactions sur la période, le détail article par article, 
        les montants HT et TTC, ainsi que la TVA et les marges calculées.
        """)