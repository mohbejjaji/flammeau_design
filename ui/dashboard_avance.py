import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from services.reporting_service import kpi_summary, sales_dataframe
from services.statistics_service import get_monthly_stats, get_breakeven_point, get_category_stats
from config import FIXED_CHARGES, COMMISSION_RATE

def dashboard_page():
    st.header("🔥 Flammeau Design - Tableau de Bord")
    
    # Sélection de la période
    col_period1, col_period2 = st.columns(2)
    with col_period1:
        period = st.selectbox(
            "Période",
            ["Aujourd'hui", "Cette semaine", "Ce mois", "Ce trimestre", "Cette année", "Personnalisé"]
        )
    
    with col_period2:
        if period == "Personnalisé":
            start_date = st.date_input("Date début", datetime.now() - timedelta(days=30))
            end_date = st.date_input("Date fin", datetime.now())
    
    # Statistiques mensuelles
    monthly_stats = get_monthly_stats()
    
    # KPIs principaux
    st.subheader("📊 Indicateurs clés")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Chiffre d'affaires mensuel",
            f"{monthly_stats['total_revenue']:,.0f} MAD",
            delta=f"{monthly_stats['total_revenue'] - monthly_stats['total_cost']:,.0f} MAD"
        )
    
    with col2:
        st.metric(
            "Bénéfice brut",
            f"{monthly_stats['gross_profit']:,.0f} MAD",
            delta=f"{monthly_stats['gross_profit']/monthly_stats['total_revenue']*100:.1f}%" if monthly_stats['total_revenue'] > 0 else "0%"
        )
    
    with col3:
        st.metric(
            "Bénéfice net",
            f"{monthly_stats['net_profit']:,.0f} MAD",
            delta=f"Charges: {monthly_stats['fixed_charges']:,.0f} MAD"
        )
    
    with col4:
        st.metric(
            "Ventes du mois",
            monthly_stats['sales_count'],
            delta=f"{monthly_stats['total_commission']:,.0f} MAD commissions"
        )
    
    # Graphiques
    st.subheader("📈 Analyse des ventes")
    
    col_graph1, col_graph2 = st.columns(2)
    
    with col_graph1:
        # Évolution des ventes
        df = sales_dataframe()
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df_monthly = df.resample('M', on='date').agg({
                'total_revenue': 'sum',
                'net_profit': 'sum'
            }).reset_index()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_monthly['date'],
                y=df_monthly['total_revenue'],
                name='CA',
                line=dict(color='#00adb5', width=3)
            ))
            fig.add_trace(go.Scatter(
                x=df_monthly['date'],
                y=df_monthly['net_profit'],
                name='Bénéfice',
                line=dict(color='#ff5722', width=3)
            ))
            
            fig.update_layout(
                title="Évolution mensuelle",
                xaxis_title="Mois",
                yaxis_title="MAD",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col_graph2:
        # Répartition par catégorie
        category_stats = get_category_stats()
        if category_stats:
            categories = [c[0] for c in category_stats]
            stocks = [c[2] for c in category_stats]
            values = [c[3] for c in category_stats]
            
            fig = px.pie(
                values=values,
                names=categories,
                title="Valeur du stock par catégorie"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Analyse de rentabilité
    st.subheader("💰 Analyse de rentabilité")
    
    # Seuil de rentabilité
    breakeven = get_breakeven_point()
    
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        st.metric(
            "Seuil de rentabilité",
            f"{breakeven['breakeven_point']:,.0f} MAD",
            help="Chiffre d'affaires minimum pour couvrir les charges"
        )
    with col_b2:
        st.metric(
            "Marge moyenne",
            f"{breakeven['avg_margin']:.1f}%"
        )
    with col_b3:
        st.metric(
            "Objectif mensuel",
            f"{breakeven['breakeven_point'] * 1.3:,.0f} MAD",
            help="Objectif +30% au-dessus du seuil"
        )
    
    # Top produits
    if monthly_stats['top_products']:
        st.subheader("🏆 Top 5 produits vendus")
        
        top_data = []
        for p in monthly_stats['top_products'][:5]:
            top_data.append({
                "Produit": p[0],
                "Quantité": p[1],
                "CA": f"{p[2]:,.0f} MAD"
            })
        
        st.dataframe(pd.DataFrame(top_data), use_container_width=True, hide_index=True)
    
    # Charges fixes
    with st.expander("📋 Détail des charges fixes"):
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            st.metric("Salaires", f"{FIXED_CHARGES['salaries']:,.0f} MAD")
        with col_c2:
            st.metric("CNSS", f"{FIXED_CHARGES['cnss']:,.0f} MAD")
        with col_c3:
            st.metric("Crédits voitures", f"{FIXED_CHARGES['credits_voitures']:,.0f} MAD")
        st.metric("Total charges fixes", f"{sum(FIXED_CHARGES.values()):,.0f} MAD")
    
    # Alertes et recommandations
    st.subheader("⚠️ Alertes et recommandations")
    
    # Vérifier les stocks
    from services.product_service import get_products
    products = get_products()
    low_stock = [p for p in products if p.stock_quantity < 5]
    
    if low_stock:
        st.warning(f"🔴 {len(low_stock)} produits en stock faible")
        for p in low_stock[:5]:
            st.caption(f"- {p.name}: {p.stock_quantity} restants")
    
    # Performance par rapport à l'objectif
    if monthly_stats['total_revenue'] < breakeven['breakeven_point']:
        st.error(f"⚠️ Vous êtes en dessous du seuil de rentabilité de {breakeven['breakeven_point'] - monthly_stats['total_revenue']:,.0f} MAD")
    else:
        st.success(f"✅ Objectif dépassé de {monthly_stats['total_revenue'] - breakeven['breakeven_point']:,.0f} MAD")