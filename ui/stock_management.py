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
    st.header("📊 Gestion et Analyse des Stocks")
    
    # Onglets pour différentes vues avec icônes
    tab1, tab2, tab3, tab4 = st.tabs([
        "📦 État du stock", 
        "📈 Analyse Financière", 
        "📜 Mouvements (E/S)",
        "⚠️ Centre d'Alertes"
    ])
    
    # ==========================================
    # ONGLET 1 : ÉTAT DU STOCK
    # ==========================================
    with tab1:
        stock_data = get_current_stock()
        
        if not stock_data:
            st.info("ℹ️ Aucun produit actuellement en stock dans la base de données.")
        else:
            # --- Filtres ---
            with st.container(border=True):
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    categories = ["Toutes"] + sorted(list(set(s['category'] for s in stock_data)))
                    selected_category = st.selectbox("Filtrer par catégorie", categories)
                with col_f2:
                    search = st.text_input("Rechercher un produit", placeholder="Nom ou référence...")
            
            # --- Filtrage des données ---
            filtered_data = stock_data
            if selected_category != "Toutes":
                filtered_data = [s for s in filtered_data if s['category'] == selected_category]
            
            if search:
                filtered_data = [
                    s for s in filtered_data 
                    if search.lower() in s['name'].lower() or search.lower() in s['reference'].lower()
                ]
            
            # --- KPIs (Métriques) ---
            total_products = len(filtered_data)
            total_quantity = sum(s['quantity'] for s in filtered_data)
            total_value = sum(s['stock_value'] for s in filtered_data)
            total_potential = sum(s['potential_revenue'] for s in filtered_data)
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("Références actives", total_products)
            col_m2.metric("Unités physiques", total_quantity)
            col_m3.metric("Valeur d'achat stock", f"{total_value:,.0f} MAD")
            col_m4.metric("CA Potentiel", f"{total_potential:,.0f} MAD")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- Tableau interactif ---
            df = pd.DataFrame(filtered_data)
            
            # Création d'une colonne statut visuelle
            df['Statut'] = df['quantity'].apply(lambda x: "🔴 Rupture" if x <= 0 else ("🟠 Faible" if x < 5 else "🟢 OK"))
            
            df_display = df[[
                'Statut', 'reference', 'name', 'category', 'subtype', 
                'quantity', 'avg_cost', 'selling_price', 'stock_value'
            ]]
            
            st.dataframe(
                df_display,
                column_config={
                    "Statut": st.column_config.TextColumn("Statut"),
                    "reference": st.column_config.TextColumn("Réf."),
                    "name": st.column_config.TextColumn("Produit"),
                    "category": st.column_config.TextColumn("Catégorie"),
                    "subtype": st.column_config.TextColumn("Type"),
                    "quantity": st.column_config.NumberColumn("Stock", format="%d"),
                    "avg_cost": st.column_config.NumberColumn("Coût unitaire", format="%.2f MAD"),
                    "selling_price": st.column_config.NumberColumn("Prix vente", format="%.2f MAD"),
                    "stock_value": st.column_config.NumberColumn("Valeur Totale", format="%.2f MAD")
                },
                use_container_width=True,
                hide_index=True,
                height=450
            )

    # ==========================================
    # ONGLET 2 : ANALYSE
    # ==========================================
    with tab2:
        st.subheader("Visualisation de la valeur du stock")
        
        if stock_data:
            df = pd.DataFrame(stock_data)
            
            with st.container(border=True):
                col_a1, col_a2 = st.columns(2)
                
                with col_a1:
                    # Graphique Camembert (Donut) plus esthétique
                    cat_stats = df.groupby('category')['stock_value'].sum().reset_index()
                    fig_pie = px.pie(
                        cat_stats, 
                        values='stock_value', 
                        names='category',
                        hole=0.4, # Transforme en donut
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig_pie.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.1))
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col_a2:
                    # Top produits
                    top_products = df.nlargest(8, 'stock_value')[['name', 'stock_value']]
                    fig_bar = px.bar(
                        top_products,
                        x='stock_value',
                        y='name',
                        orientation='h',
                        color='stock_value',
                        color_continuous_scale='Blues'
                    )
                    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_bar, use_container_width=True)
            
            # --- Indicateurs de rotation ---
            st.subheader("Indicateurs de Performance")
            with st.container(border=True):
                total_sales = 50000  # Note: Pense à remplacer par la vraie fonction (ex: get_total_sales())
                avg_stock = df['stock_value'].mean()
                
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    st.metric("Ventes de référence (Démonstration)", f"{total_sales:,.0f} MAD")
                    
                with col_r2:
                    if avg_stock > 0:
                        rotation = total_sales / avg_stock
                        st.metric("Taux de rotation", f"{rotation:.2f}x")
                        
                        if rotation < 2:
                            st.warning("⚠️ Rotation lente : Risque de sur-stockage sur certains produits.")
                        elif rotation < 4:
                            st.info("ℹ️ Rotation moyenne : Flux tendu correct.")
                        else:
                            st.success("✅ Bonne rotation : Vos produits se vendent rapidement.")
        else:
            st.info("Pas assez de données pour l'analyse.")

    # ==========================================
    # ONGLET 3 : MOUVEMENTS (Avec filtre E/S)
    # ==========================================
    with tab3:
        st.subheader("Traçabilité des Mouvements")
        
        with st.container(border=True):
            col_m1, col_m2, col_m3 = st.columns([2, 1, 1.5], vertical_alignment="bottom")
            
            with col_m1:
                products = get_products()
                product_options = {"Tous les produits": None}
                if products:
                    product_options.update({p.name: p.id for p in products})
                selected_prod = st.selectbox("Produit", options=list(product_options.keys()))
                product_id = product_options[selected_prod]
                
            with col_m2:
                days = st.number_input("Période (Jours)", min_value=1, max_value=365, value=30)
                
            with col_m3:
                mov_type = st.radio("Flux", ["Tous 🔄", "Entrées 📥", "Sorties 📤"], horizontal=True)

        movements = get_stock_movements(product_id, days)
        
        if movements:
            df_movements = pd.DataFrame(movements)
            
            # Filtrage selon Entrée ou Sortie
            if mov_type == "Entrées 📥":
                df_movements = df_movements[df_movements['quantity'] > 0]
            elif mov_type == "Sorties 📤":
                df_movements = df_movements[df_movements['quantity'] < 0]

            if df_movements.empty:
                st.info(f"Aucun mouvement correspondant au filtre '{mov_type}' trouvé.")
            else:
                # Création d'une colonne "Type" visuelle
                df_movements['Flux'] = df_movements['quantity'].apply(lambda x: "📥 Entrée" if x > 0 else "📤 Sortie")
                
                # 🛠️ CORRECTION ICI : Liste dynamique des colonnes
                cols_to_display = ['date', 'Flux', 'quantity']
                
                if 'reference' in df_movements.columns:
                    cols_to_display.append('reference')
                if 'reason' in df_movements.columns:
                    cols_to_display.append('reason')
                
                st.dataframe(
                    df_movements[cols_to_display],
                    column_config={
                        "date": st.column_config.DatetimeColumn("Date et Heure", format="DD/MM/YYYY HH:mm"),
                        "Flux": st.column_config.TextColumn("Flux"),
                        "quantity": st.column_config.NumberColumn("Quantité"),
                        "reference": st.column_config.TextColumn("Réf. Document / Facture"),
                        "reason": st.column_config.TextColumn("Motif")
                    },
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("Aucun mouvement enregistré sur cette période.")

    # ==========================================
    # ONGLET 4 : ALERTES
    # ==========================================
    with tab4:
        st.subheader("Centre d'Alertes")
        
        alerts = get_stock_alerts()
        low_stock = get_low_stock_products()
        
        col_al1, col_al2 = st.columns([2, 1])
        
        with col_al1:
            if alerts:
                for alert in alerts:
                    if alert.get('type') == 'danger':
                        st.error(f"🚨 **{alert['product']}** : {alert['message']}")
                    else:
                        st.warning(f"⚠️ **{alert['product']}** : {alert['message']}")
            else:
                st.success("✅ Félicitations, aucun problème de stock signalé.")
                
        with col_al2:
            with st.container(border=True):
                st.markdown("#### ⚡ Actions rapides")
                if low_stock:
                    st.caption("Produits nécessitant un réapprovisionnement imminent :")
                    for p in low_stock[:5]: # Afficher les 5 plus urgents
                        st.markdown(f"- {p.name} (*Reste: {p.stock_quantity}*)")
                    
                    st.divider()
                    if st.button("➕ Enregistrer un arrivage", type="primary", use_container_width=True):
                        st.switch_page("arrivals") # Assure-toi que cette page existe dans ton architecture
                else:
                    st.caption("Le stock est à des niveaux sains.")