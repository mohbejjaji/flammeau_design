import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from services.sales_history_service import (
    get_sales_history, get_sale_details, generate_ticket_pdf,
    get_sales_stats, export_sales_to_excel,
    get_commission_history, get_commission_summary_by_seller,
    get_daily_commission_summary, generate_commission_report_pdf
)
import base64
import os


# ==================== FONCTIONS UI ====================

def commissions_tab_ui():
    """Interface pour l'historique des commissions"""
    
    st.subheader("💰 Historique des Commissions par Vendeur")
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    
    today = datetime.now().date()
    first_day_of_month = today.replace(day=1)
    
    with col1:
        start_date = st.date_input("Date début", first_day_of_month, key="comm_start")
    with col2:
        end_date = st.date_input("Date fin", today, key="comm_end")
    with col3:
        # Récupérer la liste des vendeurs depuis les données
        df_all = get_commission_history()
        sellers = ["Tous"] + sorted(df_all['seller'].unique().tolist()) if not df_all.empty else ["Tous"]
        seller_filter = st.selectbox("Vendeur", sellers, key="comm_seller")
    
    # Récupérer les données filtrées
    df = get_commission_history(
        start_date=start_date,
        end_date=end_date,
        seller=None if seller_filter == "Tous" else seller_filter
    )
    
    if df.empty:
        st.info("📊 Aucune commission trouvée pour cette période")
        return
    
    # KPIs
    total_commissions = df['commission'].sum()
    total_ventes = df['total_ventes'].sum()
    nb_transactions = len(df)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Total commissions", f"{total_commissions:,.0f} MAD")
    with col2:
        st.metric("📦 Total ventes", f"{total_ventes:,.0f} MAD")
    with col3:
        st.metric("📊 Taux moyen", f"{(total_commissions/total_ventes*100):.1f}%" if total_ventes > 0 else "0%")
    with col4:
        st.metric("🔄 Nb transactions", nb_transactions)
    
    # Graphique d'évolution des commissions
    st.subheader("📈 Évolution des commissions")
    
    df_chart = df.copy()
    df_chart['date'] = pd.to_datetime(df_chart['date'], format='%d/%m/%Y')
    df_daily = df_chart.groupby('date').agg({
        'commission': 'sum',
        'total_ventes': 'sum'
    }).reset_index()
    
    fig = px.line(
        df_daily,
        x='date',
        y=['commission', 'total_ventes'],
        title="Évolution journalière",
        labels={'value': 'Montant (MAD)', 'date': '', 'variable': 'Métrique'},
        color_discrete_map={'commission': '#FFA032', 'total_ventes': '#00adb5'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Résumé par vendeur
    st.subheader("📊 Résumé par vendeur")
    
    summary = get_commission_summary_by_seller(start_date, end_date)
    
    if not summary.empty:
        # Bar chart des commissions par vendeur
        fig = px.bar(
            summary,
            x='Vendeur',
            y='Total Commissions',
            title="Commissions par vendeur",
            labels={'Total Commissions': 'MAD', 'Vendeur': ''},
            color='Vendeur',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Tableau récapitulatif
        st.dataframe(
            summary,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Vendeur": "Vendeur",
                "Total Commissions": st.column_config.NumberColumn("Commissions", format="%.0f MAD"),
                "Total Ventes": st.column_config.NumberColumn("Ventes", format="%.0f MAD"),
                "Nombre de ventes": st.column_config.NumberColumn("Nb ventes"),
                "Taux moyen": st.column_config.NumberColumn("Taux moy.", format="%.1f%%")
            }
        )
    
    # Détail des commissions
    st.subheader("📋 Détail des commissions")
    
    df_display = df.copy()
    df_display = df_display[['date', 'seller', 'customer', 'total_ventes', 'commission', 'taux_commission', 'nb_articles']]
    df_display.columns = ['Date', 'Vendeur', 'Client', 'Total ventes', 'Commission', 'Taux', 'Articles']
    
    df_display['Total ventes'] = df_display['Total ventes'].apply(lambda x: f"{x:,.0f} MAD")
    df_display['Commission'] = df_display['Commission'].apply(lambda x: f"{x:,.0f} MAD")
    df_display['Taux'] = df_display['Taux'].apply(lambda x: f"{x:.1f}%")
    
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )
    
    # Export PDF
    st.subheader("📥 Export")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 Générer rapport PDF", use_container_width=True):
            with st.spinner("Génération du rapport..."):
                pdf_path = generate_commission_report_pdf(start_date, end_date, seller_filter if seller_filter != "Tous" else None)
                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    b64 = base64.b64encode(pdf_bytes).decode()
                    href = f'<a href="data:application/pdf;base64,{b64}" download="{os.path.basename(pdf_path)}" style="display: inline-block; padding: 0.5rem 1rem; background-color: #00adb5; color: white; text-decoration: none; border-radius: 5px;">📥 Télécharger le PDF</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    st.success("✅ Rapport généré!")
                else:
                    st.error("❌ Erreur lors de la génération")
    
    with col2:
        if st.button("📊 Voir récapitulatif du jour", use_container_width=True):
            daily_summary = get_daily_commission_summary()
            if daily_summary:
                st.write("**Commissions du jour:**")
                for seller, data in daily_summary.items():
                    st.write(f"• {seller}: {data['commissions']:,.0f} MAD ({data['ventes']:,.0f} MAD de ventes, {data['nb_transactions']} transaction(s))")
            else:
                st.info("Aucune commission aujourd'hui")


def liste_ventes_ui():
    """Interface de la liste des ventes"""
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
        return
    
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


def stats_ventes_ui():
    """Interface des statistiques des ventes"""
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


def export_ventes_ui():
    """Interface d'export des ventes"""
    st.subheader("📤 Export des données")
    
    today = datetime.now().date()
    
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


# ==================== PAGE PRINCIPALE ====================

def sales_history_page():
    st.header("📜 Historique des ventes")
    
    # Ajout d'un 4ème onglet pour les commissions
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Liste des ventes", "📊 Statistiques", "📤 Export", "💰 Commissions"])
    
    with tab1:
        liste_ventes_ui()
    
    with tab2:
        stats_ventes_ui()
    
    with tab3:
        export_ventes_ui()
    
    with tab4:
        commissions_tab_ui()