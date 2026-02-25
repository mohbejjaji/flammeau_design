import streamlit as st
import pandas as pd
import plotly.express as px
from services.stock_service import (
    get_current_stock, get_stock_by_category,
    get_low_stock_products, get_out_of_stock_products,
    get_stock_movements, get_stock_alerts
)
from services.product_service import get_products
from datetime import datetime, timedelta


def stock_management_page():
    st.header("📊 Gestion de Stock")
    
    # Onglets pour différentes vues
    tab1, tab2, tab3, tab4 = st.tabs([
        "📦 État du stock", 
        "📈 Analyse", 
        "📜 Mouvements",
        "⚠️ Alertes"
    ])
    
    with tab1:
        st.subheader("État actuel du stock")
        
        # Récupérer les données de stock
        stock_data = get_current_stock()
        
        if not stock_data:
            st.info("Aucun produit en stock")
        else:
            # Filtres
            col_f1, col_f2 = st.columns(2)
            
            with col_f1:
                categories = ["Toutes"] + list(set(s['category'] for s in stock_data))
                selected_category = st.selectbox("Catégorie", categories)
            
            with col_f2:
                search = st.text_input("Rechercher", placeholder="Nom ou référence...")
            
            # Filtrer les données
            filtered_data = stock_data
            if selected_category != "Toutes":
                filtered_data = [s for s in filtered_data if s['category'] == selected_category]
            
            if search:
                filtered_data = [
                    s for s in filtered_data 
                    if search.lower() in s['name'].lower() 
                    or search.lower() in s['reference'].lower()
                ]
            
            # Statistiques globales
            total_products = len(filtered_data)
            total_quantity = sum(s['quantity'] for s in filtered_data)
            total_value = sum(s['stock_value'] for s in filtered_data)
            total_potential = sum(s['potential_revenue'] for s in filtered_data)
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("Produits", total_products)
            with col_m2:
                st.metric("Unités en stock", total_quantity)
            with col_m3:
                st.metric("Valeur stock", f"{total_value:,.0f} MAD")
            with col_m4:
                st.metric("CA potentiel", f"{total_potential:,.0f} MAD")
            
            # Tableau détaillé
            df = pd.DataFrame(filtered_data)
            
            # Formater les colonnes
            df_display = df[[
                'reference', 'name', 'category', 'subtype', 
                'quantity', 'avg_cost', 'selling_price', 
                'stock_value', 'potential_profit'
            ]].copy()
            
            df_display.columns = [
                'Référence', 'Produit', 'Catégorie', 'Type',
                'Stock', 'Coût moy.', 'Prix vente', 'Valeur', 'Profit pot.'
            ]
            
            # Formatage des nombres
            df_display['Coût moy.'] = df_display['Coût moy.'].apply(lambda x: f"{x:,.0f} MAD")
            df_display['Prix vente'] = df_display['Prix vente'].apply(lambda x: f"{x:,.0f} MAD")
            df_display['Valeur'] = df_display['Valeur'].apply(lambda x: f"{x:,.0f} MAD")
            df_display['Profit pot.'] = df_display['Profit pot.'].apply(lambda x: f"{x:,.0f} MAD")
            
            # Colorer les lignes selon le stock
            def color_stock(val):
                try:
                    # Extraire le nombre de stock
                    if pd.isna(val) or 'MAD' in str(val):
                        return ''
                    stock_val = float(str(val).replace(' MAD', '').replace(',', ''))
                    if stock_val == 0:
                        return 'background-color: #ffcccc'
                    elif stock_val < 5:
                        return 'background-color: #fff3cd'
                    else:
                        return ''
                except:
                    return ''
            
            styled_df = df_display.style.applymap(color_stock, subset=['Stock'])
            
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
                height=500
            )
    
    with tab2:
        st.subheader("Analyse du stock")
        
        stock_data = get_current_stock()
        
        if stock_data:
            df = pd.DataFrame(stock_data)
            
            col_a1, col_a2 = st.columns(2)
            
            with col_a1:
                # Répartition par catégorie
                cat_stats = df.groupby('category').agg({
                    'quantity': 'sum',
                    'stock_value': 'sum'
                }).reset_index()
                
                fig = px.pie(
                    cat_stats, 
                    values='stock_value', 
                    names='category',
                    title="Valeur du stock par catégorie"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col_a2:
                # Top produits par valeur
                top_products = df.nlargest(10, 'stock_value')[['name', 'stock_value']]
                fig = px.bar(
                    top_products,
                    x='stock_value',
                    y='name',
                    orientation='h',
                    title="Top 10 produits par valeur",
                    labels={'stock_value': 'Valeur (MAD)', 'name': ''}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Rotation du stock (simplifiée)
            st.subheader("Indicateurs de rotation")
            
            total_sales = 50000  # À remplacer par vraies données
            avg_stock = df['stock_value'].mean()
            
            if avg_stock > 0:
                rotation = total_sales / avg_stock
                st.metric("Rotation du stock", f"{rotation:.2f}")
                
                # Interprétation
                if rotation < 2:
                    st.warning("⚠️ Rotation lente - stock peut-être trop important")
                elif rotation < 4:
                    st.info("ℹ️ Rotation moyenne")
                else:
                    st.success("✅ Bonne rotation du stock")
        else:
            st.info("Pas assez de données pour l'analyse")
    
    with tab3:
        st.subheader("Mouvements de stock récents")
        
        # Sélection du produit
        products = get_products()
        if products:
            product_options = {p.name: p.id for p in products}
            product_options["Tous les produits"] = None
            
            selected = st.selectbox(
                "Filtrer par produit",
                options=list(product_options.keys())
            )
            
            product_id = product_options[selected]
            
            # Période
            days = st.slider("Période (jours)", 7, 90, 30)
            
            # Récupérer les mouvements
            movements = get_stock_movements(product_id if product_id else None, days)
            
            if movements:
                df_movements = pd.DataFrame(movements)
                st.dataframe(df_movements, use_container_width=True, hide_index=True)
                
                # Graphique d'évolution
                if product_id:
                    # Calculer l'évolution du stock
                    df_movements['net'] = df_movements['quantity']
                    df_movements['cumulative'] = df_movements['net'].cumsum()
                    
                    fig = px.line(
                        df_movements.sort_values('date'),
                        x='date',
                        y='cumulative',
                        title="Évolution du stock"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Aucun mouvement sur cette période")
        else:
            st.info("Aucun produit dans la base")
    
    with tab4:
        st.subheader("⚠️ Alertes stock")
        
        alerts = get_stock_alerts()
        
        if alerts:
            for alert in alerts:
                if alert['type'] == 'danger':
                    st.error(f"**{alert['product']}** : {alert['message']}")
                else:
                    st.warning(f"**{alert['product']}** : {alert['message']}")
            
            # Actions rapides
            st.markdown("---")
            st.subheader("Actions recommandées")
            
            low_stock = get_low_stock_products()
            if low_stock:
                st.info("📦 Produits à réapprovisionner:")
                for p in low_stock[:5]:
                    st.markdown(f"- {p.name} (stock: {p.stock_quantity})")
                
                if st.button("➕ Créer un arrivage"):
                    st.switch_page("arrivals")  # Redirection vers la page d'arrivage
        else:
            st.success("✅ Aucune alerte stock")