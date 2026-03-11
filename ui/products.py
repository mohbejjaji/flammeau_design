import streamlit as st
import pandas as pd
import time
from services.product_service import get_products, update_product_price
from config import USD_TO_MAD_RATE

def products_page():
    st.header("💰 Gestion des Prix")
    
    products = get_products()
    
    if not products:
        st.info("Aucun produit en stock. Commencez par enregistrer un arrivage !")
        return
    
    # --- 1. Zone de Filtres et Actions Rapides ---
    col1, col2, _ = st.columns([2, 3, 2]) # Organisation de l'en-tête
    
    with col1:
        categories = ["Tous"] + sorted(list(set(p.category for p in products)))
        selected_cat = st.selectbox("Filtrer par catégorie", categories, label_visibility="collapsed")
    
    filtered_products = products
    if selected_cat != "Tous":
        filtered_products = [p for p in products if p.category == selected_cat]
        
    with col2:
        # Bouton "Magique" pour tout mettre à jour d'un coup
        if st.button("🪄 Appliquer les prix suggérés à la sélection", help="Remplace les prix de vente actuels par les prix suggérés pour tous les produits affichés ci-dessous."):
            
            # Affichage d'une barre de progression (très pro si beaucoup d'articles)
            progress_bar = st.progress(0, text="Mise à jour des prix en cours...")
            total_items = len(filtered_products)
            
            for i, p in enumerate(filtered_products):
                # Même calcul que pour l'affichage
                cost = p.average_cost if hasattr(p, 'average_cost') and p.average_cost > 0 else p.purchase_price
                suggested = cost * 1.5 * 1.2
                
                # Mise à jour en base de données
                update_product_price(p.id, suggested)
                
                # Fait avancer la barre de progression
                progress_bar.progress((i + 1) / total_items, text=f"Mise à jour : {p.name}...")
            
            time.sleep(0.5) # Petit délai agréable visuellement pour voir la barre à 100%
            st.rerun() # Recharge la page pour afficher les nouveaux prix dans le tableau
            
    st.markdown("---")
    st.subheader("Ajuster les prix de vente manuellement")
    st.caption("Double-cliquez sur une cellule de la colonne **Prix de Vente** pour la modifier.")

    # --- 2. Préparation des données pour le tableau ---
    data = []
    for p in filtered_products:
        cost = p.average_cost if hasattr(p, 'average_cost') and p.average_cost > 0 else p.purchase_price
        suggested = cost * 1.5 * 1.2
        
        data.append({
            "id": p.id,
            "Produit": p.name,
            "Référence": p.reference,
            "Stock": p.stock_quantity,
            "Achat (MAD)": float(p.purchase_price),
            "Achat (USD)": float(p.purchase_price / USD_TO_MAD_RATE),
            "Suggéré (MAD)": float(suggested),
            "Prix Vente (MAD)": float(p.selling_price)
        })
        
    df = pd.DataFrame(data)

    # --- 3. Affichage du tableau interactif ---
    with st.form("price_update_form"):
        edited_df = st.data_editor(
            df,
            column_config={
                "id": None, # Masqué
                "Produit": st.column_config.TextColumn("Produit", disabled=True),
                "Référence": st.column_config.TextColumn("Réf.", disabled=True),
                "Stock": st.column_config.NumberColumn("Stock", disabled=True),
                "Achat (MAD)": st.column_config.NumberColumn("Achat (MAD)", disabled=True, format="%.0f"),
                "Achat (USD)": st.column_config.NumberColumn("Achat (USD)", disabled=True, format="$%.0f"),
                "Suggéré (MAD)": st.column_config.NumberColumn("Suggéré (MAD)", disabled=True, format="%.0f"),
                "Prix Vente (MAD)": st.column_config.NumberColumn(
                    "Prix Vente (MAD) ✏️", 
                    required=True,
                    step=10.0,
                    format="%.0f",
                    help="Modifiez ce prix manuellement"
                ),
            },
            hide_index=True,
            use_container_width=True
        )
        
        # --- 4. Bouton de sauvegarde globale (pour les modifications manuelles) ---
        submit_button = st.form_submit_button("💾 Sauvegarder les modifications manuelles", type="primary")

    # --- 5. Logique de mise à jour manuelle ---
    if submit_button:
        changes_made = False
        
        for index, row in edited_df.iterrows():
            original_price = df.loc[index, "Prix Vente (MAD)"]
            new_price = row["Prix Vente (MAD)"]
            
            if new_price != original_price:
                product_id = row["id"]
                update_product_price(product_id, new_price)
                changes_made = True
                
        if changes_made:
            st.success("✅ Les prix modifiés manuellement ont été sauvegardés !")
            time.sleep(1)
            st.rerun()
        else:
            st.info("Aucune modification manuelle détectée.")