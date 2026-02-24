import streamlit as st
import pandas as pd
from services.product_service import create_product, get_products, update_product
from services.pricing_service import (
    calculate_product_price, get_margin_from_price,
    suggest_prices_for_category
)
from data.product_catalog import (
    get_categories, get_subtypes, 
    get_products_by_subtype, get_all_products_list
)


def products_page():
    st.header("🛒 Gestion des Produits")
    
    # Onglets
    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Ajouter", "📋 Catalogue", "📦 Stock", "💰 Tarification"
    ])
    
    with tab1:
        st.subheader("Ajouter un nouveau produit")
        
        # Sélection de la catégorie
        categories = get_categories()
        category_names = {
            "electrique": "Cheminée électrique",
            "bioethanol": "Cheminée bioéthanol",
            "accessoire": "Accessoires"
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            category = st.selectbox(
                "Catégorie *",
                options=categories,
                format_func=lambda x: category_names.get(x, x)
            )
        
        # Sélection de la sous-catégorie
        subtypes = get_subtypes(category)
        subtype_names = {
            "encastre": "Encastré",
            "mural": "Mural",
            "mobile": "Mobile",
            "bruleur": "Brûleur",
            "galets": "Galets",
            "buches": "Bûches",
            "ethanol": "Éthanol"
        }
        
        with col2:
            if subtypes:
                subtype = st.selectbox(
                    "Sous-catégorie *",
                    options=subtypes,
                    format_func=lambda x: subtype_names.get(x, x)
                )
            else:
                st.error("Aucune sous-catégorie disponible")
                subtype = None
        
        # Sélection du produit
        if category and subtype:
            products_list = get_products_by_subtype(category, subtype)
            
            if products_list:
                product_options = {p["name"]: p["ref"] for p in products_list}
                
                col3, col4 = st.columns(2)
                
                with col3:
                    selected_product = st.selectbox(
                        "Référence produit *",
                        options=list(product_options.keys())
                    )
                    product_ref = product_options[selected_product]
                
                with col4:
                    purchase_price = st.number_input(
                        "Prix d'achat Chine (MAD) *",
                        min_value=0.0,
                        step=50.0,
                        format="%.2f",
                        help="Prix d'achat unitaire en Chine"
                    )
                
                # Paramètres de marge
                st.subheader("💰 Paramètres de tarification")
                
                col_m1, col_m2 = st.columns(2)
                
                with col_m1:
                    default_margin = st.number_input(
                        "Marge souhaitée (%)",
                        min_value=0.0,
                        max_value=200.0,
                        value=30.0,
                        step=5.0,
                        help="Marge brute souhaitée (hors frais)"
                    )
                
                # Calcul du prix suggéré
                if purchase_price > 0:
                    from services.pricing_service import calculate_price_from_cost
                    
                    suggested_price_ht = calculate_price_from_cost(
                        purchase_price, default_margin, tva_included=False
                    )
                    suggested_price_ttc = suggested_price_ht * 1.20
                    
                    st.info(f"""
                    **Prix suggéré:** 
                    - HT: {suggested_price_ht:.0f} MAD
                    - TTC: {suggested_price_ttc:.0f} MAD
                    """)
                    
                    # Option pour utiliser le prix suggéré
                    use_suggested = st.checkbox("Utiliser le prix suggéré")
                    
                    if use_suggested:
                        selling_price = suggested_price_ttc
                    else:
                        selling_price = st.number_input(
                            "Prix de vente TTC (MAD) *",
                            min_value=0.0,
                            value=suggested_price_ttc,
                            step=100.0,
                            format="%.2f"
                        )
                else:
                    selling_price = st.number_input(
                        "Prix de vente TTC (MAD) *",
                        min_value=0.0,
                        step=100.0,
                        format="%.2f"
                    )
                
                # Stock initial
                initial_stock = st.number_input(
                    "Stock initial",
                    min_value=0,
                    value=0,
                    step=1
                )
                
                # Description
                description = st.text_area(
                    "Description",
                    placeholder="Description du produit..."
                )
                
                # Bouton d'ajout
                if st.button("✅ Ajouter le produit", type="primary", use_container_width=True):
                    if purchase_price <= 0:
                        st.error("Le prix d'achat doit être supérieur à 0")
                    elif selling_price <= 0:
                        st.error("Le prix de vente doit être supérieur à 0")
                    else:
                        try:
                            product = create_product(
                                name=selected_product,
                                reference=product_ref,
                                category=category,
                                subtype=subtype,
                                selling_price=selling_price,
                                purchase_price=purchase_price,
                                default_margin=default_margin,
                                description=description,
                                initial_stock=initial_stock
                            )
                            st.success(f"✅ Produit {selected_product} ajouté avec succès!")
                            
                        except Exception as e:
                            st.error(f"Erreur: {e}")
            else:
                st.warning("Aucun produit trouvé pour cette catégorie")
    
    with tab4:  # Nouvel onglet Tarification
        st.subheader("💰 Analyse des prix et marges")
        
        products = get_products()
        
        if not products:
            st.info("Aucun produit disponible")
        else:
            # Filtre par catégorie
            categories = ["Toutes"] + list(set(p.category for p in products))
            selected_cat = st.selectbox("Filtrer par catégorie", categories)
            
            filtered_products = products
            if selected_cat != "Toutes":
                filtered_products = [p for p in products if p.category == selected_cat]
            
            # Analyse des prix
            price_data = []
            for p in filtered_products:
                # Calculer le coût moyen
                if p.stock_lots:
                    total_value = sum(lot.unit_cost * lot.quantity_remaining for lot in p.stock_lots)
                    total_qty = sum(lot.quantity_remaining for lot in p.stock_lots)
                    avg_cost = total_value / total_qty if total_qty > 0 else 0
                else:
                    avg_cost = p.purchase_price
                
                # Calculer la marge actuelle
                if avg_cost > 0:
                    current_margin = ((p.selling_price - avg_cost) / avg_cost) * 100
                else:
                    current_margin = 0
                
                price_data.append({
                    "Produit": p.name,
                    "Catégorie": p.category,
                    "Prix achat": f"{p.purchase_price:.0f}",
                    "Coût moyen": f"{avg_cost:.0f}",
                    "Prix vente": f"{p.selling_price:.0f}",
                    "Marge actuelle": f"{current_margin:.1f}%",
                    "Statut": "✅ Optimal" if 25 <= current_margin <= 40 else "⚠️ À revoir"
                })
            
            df = pd.DataFrame(price_data)
            
            # Colorer les lignes selon la marge
            def color_margin(val):
                if "Optimal" in val:
                    return 'background-color: #d4edda'
                elif "À revoir" in val:
                    return 'background-color: #fff3cd'
                return ''
            
            styled_df = df.style.applymap(color_margin, subset=['Statut'])
            
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Produit": "Produit",
                    "Catégorie": "Catégorie",
                    "Prix achat": "Achat",
                    "Coût moyen": "Coût réel",
                    "Prix vente": "Vente",
                    "Marge actuelle": "Marge",
                    "Statut": "Statut"
                }
            )
            
            # Outil de simulation de prix
            st.subheader("📊 Simulateur de prix")
            
            col_s1, col_s2 = st.columns(2)
            
            with col_s1:
                sim_product = st.selectbox(
                    "Choisir un produit",
                    options=[p.name for p in products]
                )
            
            with col_s2:
                target_margin = st.slider(
                    "Marge cible (%)",
                    min_value=0,
                    max_value=100,
                    value=30,
                    step=5
                )
            
            # Trouver le produit sélectionné
            selected = next((p for p in products if p.name == sim_product), None)
            
            if selected:
                from services.pricing_service import calculate_price_from_cost
                
                # Coût de référence
                cost_ref = selected.average_cost if selected.average_cost > 0 else selected.purchase_price
                
                if cost_ref > 0:
                    col_r1, col_r2, col_r3 = st.columns(3)
                    
                    with col_r1:
                        st.metric("Coût de revient", f"{cost_ref:.0f} MAD")
                    
                    with col_r2:
                        suggested_ht = calculate_price_from_cost(cost_ref, target_margin, False)
                        st.metric("Prix HT suggéré", f"{suggested_ht:.0f} MAD")
                    
                    with col_r3:
                        suggested_ttc = suggested_ht * 1.20
                        st.metric("Prix TTC suggéré", f"{suggested_ttc:.0f} MAD")
                    
                    # Comparaison avec prix actuel
                    current_margin = ((selected.selling_price - cost_ref) / cost_ref) * 100
                    
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        st.metric("Prix actuel", f"{selected.selling_price:.0f} MAD")
                    with col_c2:
                        st.metric("Marge actuelle", f"{current_margin:.1f}%")
                    
                    # Recommandation
                    if abs(current_margin - target_margin) > 5:
                        if current_margin < target_margin:
                            st.warning(f"⚠️ Augmentez votre prix de {target_margin - current_margin:.1f}% pour atteindre la marge cible")
                        else:
                            st.success(f"✅ Vous pouvez baisser votre prix pour rester compétitif")
                else:
                    st.warning("Pas de données de coût pour ce produit")