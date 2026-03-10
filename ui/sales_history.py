import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from services.sales_history_service import (
    get_sales_history, get_sale_details, generate_ticket_pdf,
    get_sales_stats, export_sales_to_excel
)
import base64
import os


def sales_history_page():
    st.header("📜 Historique des ventes")
    
    # Onglets
    tab1, tab2, tab3 = st.tabs(["📋 Liste des ventes", "📊 Statistiques", "📤 Export"])
    
    with tab1:
        # Filtres
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            period = st.selectbox(
                "Période",
                ["Aujourd'hui", "Cette semaine", "Ce mois", "Ce trimestre", "Cette année", "Personnalisé"]
            )
        
        # Calculer les dates selon la période
        today = datetime.now().date()
        
        if period == "Aujourd'hui":
            start_date = today
            end_date = today
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
        else:
            with col_f2:
                start_date = st.date_input("Date début", today - timedelta(days=30))
            with col_f3:
                end_date = st.date_input("Date fin", today)
        
        # Récupérer les ventes
        sales = get_sales_history(start_date, end_date)
        
        if not sales:
            st.info("Aucune vente sur cette période")
        else:
            # Métriques rapides
            total_ca = sum(s['revenue'] for s in sales)
            total_profit = sum(s['profit'] for s in sales)
            total_ventes = len(sales)
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("Nombre de ventes", total_ventes)
            with col_m2:
                st.metric("CA total", f"{total_ca:,.0f} MAD")
            with col_m3:
                st.metric("Bénéfice total", f"{total_profit:,.0f} MAD")
            with col_m4:
                marge_moyenne = (total_profit / total_ca * 100) if total_ca > 0 else 0
                st.metric("Marge moyenne", f"{marge_moyenne:.1f}%")
            
            # Liste des ventes
            for sale in sales:
                with st.expander(f"🪙 Vente #{sale['id']} - {sale['date']} - {sale['customer']} - {sale['revenue'] * 1.20:,.0f} MAD TTC"):
                    col_d1, col_d2, col_d3 = st.columns(3)
                    
                    with col_d1:
                        st.write(f"**Client:** {sale['customer']}")
                        st.write(f"**Vendeur:** {sale['seller']}")
                    
                    with col_d2:
                        st.write(f"**Date:** {sale['date']}")
                        st.write(f"**Paiement:** {sale['payment']}")
                    
                    with col_d3:
                        st.write(f"**Articles:** {sale['items_count']}")
                        st.write(f"**Commission:** {sale['commission']:,.0f} MAD")
                    
                    # Détail des articles
                    details = get_sale_details(sale['id'])
                    
                    if details:
                        st.write("**Articles vendus:**")
                        for item in details['items']:
                            st.write(f"  • {item['name']} x{item['quantity']} = {item['total']:,.0f} MAD")
                        
                        # Totaux
                        col_t1, col_t2, col_t3 = st.columns(3)
                        with col_t1:
                            st.info(f"**Total HT:** {details['total_revenue']:,.0f} MAD")
                        with col_t2:
                            st.info(f"**TVA:** {details['total_revenue'] * 0.20:,.0f} MAD")
                        with col_t3:
                            st.success(f"**Total TTC:** {details['total_revenue'] * 1.20:,.0f} MAD")
                        
                        # Bouton ticket
                        if st.button("🧾 Télécharger ticket", key=f"ticket_{sale['id']}"):
                            pdf_path = generate_ticket_pdf(sale['id'])
                            if pdf_path and os.path.exists(pdf_path):
                                with open(pdf_path, "rb") as f:
                                    pdf_bytes = f.read()
                                b64 = base64.b64encode(pdf_bytes).decode()
                                href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(pdf_path)}">📥 Cliquez pour télécharger le ticket</a>'
                                st.markdown(href, unsafe_allow_html=True)
                                st.success("Ticket généré!")
    
    with tab2:
        st.subheader("📊 Statistiques des ventes")
        
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            period_stats = st.radio(
                "Période",
                ["Jour", "Semaine", "Mois", "Année"],
                horizontal=True
            )
        
        period_map = {
            "Jour": "day",
            "Semaine": "week",
            "Mois": "month",
            "Année": "year"
        }
        
        stats = get_sales_stats(period_map[period_stats])
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("Ventes", stats['count'])
        with col_m2:
            st.metric("CA", f"{stats['revenue']:,.0f} MAD")
        with col_m3:
            st.metric("Bénéfice", f"{stats['profit']:,.0f} MAD")
        with col_m4:
            st.metric("Ticket moyen", f"{stats['avg_ticket']:,.0f} MAD")
        
        # Graphique d'évolution
        st.subheader("Évolution des ventes")
        
        # Récupérer les ventes des 30 derniers jours
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
            
            fig = px.line(
                df_daily,
                x='date',
                y=['revenue', 'profit'],
                title="CA et bénéfice journaliers",
                labels={'value': 'MAD', 'variable': 'Métrique'},
                color_discrete_map={'revenue': '#00adb5', 'profit': '#00ff00'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("📤 Export des données")
        
        col_e1, col_e2 = st.columns(2)
        
        with col_e1:
            export_start = st.date_input("Date début", today - timedelta(days=30), key="export_start")
        
        with col_e2:
            export_end = st.date_input("Date fin", today, key="export_end")
        
        if st.button("📥 Exporter en Excel", type="primary"):
            with st.spinner("Génération du fichier..."):
                filepath = export_sales_to_excel(export_start, export_end)
                
                if filepath and os.path.exists(filepath):
                    with open(filepath, "rb") as f:
                        excel_bytes = f.read()
                    b64 = base64.b64encode(excel_bytes).decode()
                    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{os.path.basename(filepath)}">📥 Cliquez pour télécharger le fichier Excel</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    st.success("Export terminé!")
        
        st.info("""
        **L'export Excel contient :**
        - Liste complète des ventes
        - Détails par transaction
        - Calculs automatiques (TVA, marges)
        - Filtrable par période
        """)