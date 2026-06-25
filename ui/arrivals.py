import streamlit as st
import pandas as pd
from services.arrival_service import (
    process_arrival, get_all_shipments, get_shipment_details,
    update_shipment_metadata, add_item_to_existing_shipment,
    update_existing_shipment_item, delete_item_from_existing_shipment,
    delete_entire_shipment
)
from data.product_catalog import get_all_references
from datetime import date
from config import USD_TO_MAD_RATE

def arrivals_page():
    st.header("📦 Gestion des Arrivages de Chine")
    
    st.info(f"💰 Taux de change: 1 USD = {USD_TO_MAD_RATE} MAD")
    
    # Onglets
    tab1, tab2 = st.tabs(["➕ Nouvel Arrivage", "📋 Arrivages Enregistrés"])
    
    # ==========================================
    # ONGLET 1 : NOUVEL ARRIVAGE
    # ==========================================
    with tab1:
        st.subheader("Enregistrer un nouvel arrivage")
        st.caption(f"ℹ️ Catalogue chargé : {len(get_all_references())} produits référencés")
        
        # Informations générales
        col1, col2 = st.columns(2)
        
        with col1:
            arrival_date = st.date_input("Date d'arrivage", value=date.today(), key="new_arrival_date")
        
        with col2:
            container_ref = st.text_input("Référence conteneur", placeholder="EX: CONT-2025-001", key="new_container_ref")
        
        col3, col4, col5 = st.columns(3)
        
        with col3:
            transport_cost_usd = st.number_input(
                "🚛 Transport (USD)", 
                min_value=0.0, 
                step=100.0,
                help="Frais de transport en dollars",
                key="new_transport_usd"
            )
            if transport_cost_usd > 0:
                st.caption(f"≈ {transport_cost_usd * USD_TO_MAD_RATE:,.0f} MAD")
        
        with col4:
            shipping_cost_usd = st.number_input(
                "🚢 Fret maritime (USD)", 
                min_value=0.0, 
                step=100.0,
                help="Fret en dollars",
                key="new_shipping_usd"
            )
            if shipping_cost_usd > 0:
                st.caption(f"≈ {shipping_cost_usd * USD_TO_MAD_RATE:,.0f} MAD")
        
        with col5:
            customs_cost_mad = st.number_input(
                "🏛️ Douane (MAD)", 
                min_value=0.0, 
                step=100.0,
                help="Frais de douane en dirhams",
                key="new_customs_mad"
            )
        
        note = st.text_area("📝 Note", placeholder="Fournisseur, conditions particulières...", key="new_note")
        
        st.markdown("---")
        st.subheader("📦 Ajouter des produits")
        
        # Récupérer toutes les références disponibles
        references = get_all_references()
        ref_options = {f"{r['ref']} - {r['name']} ({r['category']} - {r['subtype']})": r['ref'] for r in references}
        
        # Initialiser la liste des articles
        if 'arrival_items' not in st.session_state:
            st.session_state.arrival_items = []
        
        # Formulaire d'ajout
        col_a1, col_a2, col_a3, col_a4 = st.columns([3, 1, 1, 1])
        
        with col_a1:
            selected_ref = st.selectbox(
                "Référence produit",
                options=list(ref_options.keys()),
                key="arrival_ref"
            )
            reference = ref_options[selected_ref]
        
        with col_a2:
            quantity = st.number_input("Quantité", min_value=1, value=1, key="arrival_qty")
        
        with col_a3:
            purchase_price_usd = st.number_input(
                "Prix achat (USD)", 
                min_value=0.0, 
                step=10.0,
                key="arrival_price",
                help="Prix unitaire en dollars"
            )
        
        with col_a4:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("➕ Ajouter", use_container_width=True):
                if purchase_price_usd > 0:
                    price_mad = purchase_price_usd * USD_TO_MAD_RATE
                    st.session_state.arrival_items.append({
                        'reference': reference,
                        'display': selected_ref,
                        'quantity': quantity,
                        'purchase_price_usd': purchase_price_usd,
                        'purchase_price_mad': price_mad
                    })
                    st.rerun()
                else:
                    st.error("Veuillez saisir un prix valide")
        
        # Afficher le panier
        if st.session_state.arrival_items:
            st.markdown("---")
            st.subheader("📋 Liste des produits ajoutés")
            
            df = pd.DataFrame(st.session_state.arrival_items)
            df['total_usd'] = df['purchase_price_usd'] * df['quantity']
            df['total_mad'] = df['purchase_price_mad'] * df['quantity']
            
            df_display = df[['display', 'quantity', 'purchase_price_usd', 'purchase_price_mad', 'total_usd', 'total_mad']].copy()
            df_display.columns = ['Produit', 'Qté', 'Prix (USD)', 'Prix (MAD)', 'Total (USD)', 'Total (MAD)']
            
            df_display['Prix (USD)'] = df_display['Prix (USD)'].apply(lambda x: f"${x:,.2f}")
            df_display['Prix (MAD)'] = df_display['Prix (MAD)'].apply(lambda x: f"{x:,.0f} MAD")
            df_display['Total (USD)'] = df_display['Total (USD)'].apply(lambda x: f"${x:,.2f}")
            df_display['Total (MAD)'] = df_display['Total (MAD)'].apply(lambda x: f"{x:,.0f} MAD")
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # --- Section Modifier / Supprimer un article ---
            with st.container(border=True):
                st.markdown("🔧 **Modifier / Supprimer un article de la liste ci-dessus**")
                
                edit_options = [
                    f"{i+1}. {item['reference']} - Qté: {item['quantity']}, ${item['purchase_price_usd']:.2f}" 
                    for i, item in enumerate(st.session_state.arrival_items)
                ]
                
                col_sel, col_val, col_pr, col_actions = st.columns([2.5, 1, 1, 1.5], vertical_alignment="bottom")
                
                with col_sel:
                    selected_item_display = st.selectbox(
                        "Sélectionner l'article à modifier",
                        options=edit_options,
                        key="new_edit_select_item"
                    )
                
                if selected_item_display:
                    idx = int(selected_item_display.split(".")[0]) - 1
                    item = st.session_state.arrival_items[idx]
                    
                    with col_val:
                        new_qty = st.number_input(
                            "Qté", 
                            min_value=1, 
                            value=int(item['quantity']), 
                            key=f"new_edit_qty_{idx}"
                        )
                    with col_pr:
                        new_price = st.number_input(
                            "Prix ($)", 
                            min_value=0.0, 
                            value=float(item['purchase_price_usd']), 
                            key=f"new_edit_price_{idx}",
                            format="%.2f"
                        )
                    with col_actions:
                        sub_col1, sub_col2 = st.columns(2)
                        with sub_col1:
                            if st.button("💾", key=f"new_save_edit_{idx}", help="Enregistrer les modifications"):
                                st.session_state.arrival_items[idx]['quantity'] = new_qty
                                st.session_state.arrival_items[idx]['purchase_price_usd'] = new_price
                                st.session_state.arrival_items[idx]['purchase_price_mad'] = new_price * USD_TO_MAD_RATE
                                st.toast("Article mis à jour !")
                                st.rerun()
                        with sub_col2:
                            if st.button("🗑️", key=f"new_delete_edit_{idx}", help="Supprimer l'article de la liste"):
                                removed = st.session_state.arrival_items.pop(idx)
                                st.toast(f"Article {removed['reference']} supprimé !")
                                st.rerun()
            
            # Totaux
            total_usd = df['total_usd'].sum()
            total_mad = df['total_mad'].sum()
            
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1:
                st.metric("Total achat (USD)", f"${total_usd:,.2f}")
            with col_t2:
                st.metric("Total achat (MAD)", f"{total_mad:,.0f} MAD")
            with col_t3:
                frais_total_usd = transport_cost_usd + shipping_cost_usd
                frais_total_mad = frais_total_usd * USD_TO_MAD_RATE + customs_cost_mad
                st.metric("Frais totaux", f"{frais_total_mad:,.0f} MAD")
            
            total_invest_mad = total_mad + frais_total_mad
            st.metric("💰 Investissement total", f"{total_invest_mad:,.0f} MAD")
            
            if total_mad > 0:
                frais_percent = (frais_total_mad / total_mad) * 100
                st.progress(min(frais_percent/100, 1.0))
                st.caption(f"Frais représentant {frais_percent:.1f}% du prix d'achat")
            
            col_b1, col_b2 = st.columns(2)
            
            with col_b1:
                if st.button("🗑️ Vider tout", use_container_width=True, key="btn_clear_all"):
                    st.session_state.arrival_items = []
                    st.rerun()
            
            with col_b2:
                if st.button("✅ Valider l'arrivage", type="primary", use_container_width=True, key="btn_validate_arrival"):
                    try:
                        arrival_data = {
                            'date': arrival_date,
                            'transport_cost_usd': transport_cost_usd,
                            'shipping_cost_usd': shipping_cost_usd,
                            'customs_cost_mad': customs_cost_mad,
                            'note': f"{container_ref} - {note}" if container_ref else note,
                            'items': [
                                {
                                    'reference': item['reference'],
                                    'quantity': item['quantity'],
                                    'purchase_price_usd': item['purchase_price_usd']
                                }
                                for item in st.session_state.arrival_items
                            ]
                        }
                        
                        result = process_arrival(arrival_data)
                        
                        st.success(f"""
                        ✅ Arrivage #{result['shipment_id']} enregistré!
                        - {result['products_created']} nouveaux produits créés
                        - Total achat: ${result['total_usd']:,.2f} USD
                        - Total en MAD: {result['total_mad']:,.0f} MAD
                        - Frais: {result['total_frais_mad']:,.0f} MAD
                        - Investissement total: {result['total_cost_mad']:,.0f} MAD
                        """)
                        
                        st.balloons()
                        st.session_state.arrival_items = []
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Erreur: {e}")
        else:
            st.info("Ajoutez des produits à l'arrivage")
            
    # ==========================================
    # ONGLET 2 : ARRIVAGES ENREGISTRÉS
    # ==========================================
    with tab2:
        st.subheader("📋 Historique & Modification des Arrivages Enregistrés")
        
        shipments = get_all_shipments()
        
        if not shipments:
            st.info("Aucun arrivage enregistré en base de données.")
        else:
            # Sélectionner l'arrivage à modifier
            shipment_options = {
                f"Arrivage #{s['id']} ({s['date'].strftime('%d/%m/%Y')}) - {s['note'] or ''}": s['id']
                for s in shipments
            }
            selected_shipment_label = st.selectbox(
                "Sélectionner un arrivage", 
                list(shipment_options.keys()),
                key="select_existing_shipment"
            )
            selected_shipment_id = shipment_options[selected_shipment_label]
            
            # Charger les détails
            details = get_shipment_details(selected_shipment_id)
            
            if details:
                shipment_data = details['shipment']
                items_data = details['items']
                
                # Métriques de l'arrivage sélectionné
                total_purchase_mad = sum(it['quantity'] * it['unit_purchase_price_mad'] for it in items_data)
                total_purchase_usd = sum(it['quantity'] * it['unit_purchase_price_usd'] for it in items_data)
                
                frais_transport_mad = shipment_data['transport_cost_total'] or 0.0
                frais_customs_mad = shipment_data['customs_cost_total'] or 0.0
                frais_shipping_mad = shipment_data['shipping_cost_total'] or 0.0
                total_frais_mad = frais_transport_mad + frais_customs_mad + frais_shipping_mad
                total_invested_mad = total_purchase_mad + total_frais_mad
                
                st.markdown("##### 📊 Synthèse financière de l'arrivage")
                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                with col_stat1:
                    st.metric("Total Achat (USD)", f"${total_purchase_usd:,.2f}")
                with col_stat2:
                    st.metric("Total Achat (MAD)", f"{total_purchase_mad:,.0f} MAD")
                with col_stat3:
                    st.metric("Frais Totaux (MAD)", f"{total_frais_mad:,.0f} MAD")
                with col_stat4:
                    st.metric("Total Investi (MAD)", f"{total_invested_mad:,.0f} MAD")
                
                if shipment_data['note']:
                    st.markdown(f"**Note :** {shipment_data['note']}")
                    
                st.markdown("##### 📦 Produits inclus dans cet arrivage")
                if not items_data:
                    st.info("Aucun produit dans cet arrivage.")
                else:
                    df_existing = pd.DataFrame(items_data)
                    df_disp_exist = df_existing[['reference', 'name', 'quantity', 'qty_remaining', 'unit_purchase_price_usd', 'unit_purchase_price_mad', 'allocated_transport_cost', 'allocated_customs_cost']].copy()
                    
                    df_disp_exist.columns = ['Référence', 'Nom', 'Qté Origine', 'Qté Restante', 'Prix (USD)', 'Prix (MAD)', 'Part Transport', 'Part Douane']
                    df_disp_exist['Prix (USD)'] = df_disp_exist['Prix (USD)'].apply(lambda x: f"${x:,.2f}")
                    df_disp_exist['Prix (MAD)'] = df_disp_exist['Prix (MAD)'].apply(lambda x: f"{x:,.0f} MAD")
                    df_disp_exist['Part Transport'] = df_disp_exist['Part Transport'].apply(lambda x: f"{x:,.0f} MAD")
                    df_disp_exist['Part Douane'] = df_disp_exist['Part Douane'].apply(lambda x: f"{x:,.0f} MAD")
                    
                    st.dataframe(df_disp_exist, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                st.markdown("#### 🛠️ Actions de modification sur cet arrivage")
                
                # Option 1 : Modifier les métadonnées globales
                with st.expander("📝 Modifier les informations générales et frais"):
                    with st.form("edit_shipment_meta_form"):
                        col_m1, col_m2 = st.columns(2)
                        with col_m1:
                            new_date = st.date_input("Date d'arrivage", value=shipment_data['date'], key="edit_shipment_date")
                            new_note = st.text_area("Note / Référence conteneur", value=shipment_data['note'] or "", key="edit_shipment_note")
                        with col_m2:
                            new_trans_usd = st.number_input("Transport (USD)", min_value=0.0, value=float(frais_transport_mad / USD_TO_MAD_RATE), key="edit_shipment_trans_usd")
                            new_ship_usd = st.number_input("Fret maritime (USD)", min_value=0.0, value=float(frais_shipping_mad / USD_TO_MAD_RATE), key="edit_shipment_ship_usd")
                            new_customs_mad = st.number_input("Douane (MAD)", min_value=0.0, value=float(frais_customs_mad), key="edit_shipment_customs_mad")
                        
                        if st.form_submit_button("💾 Sauvegarder les informations", use_container_width=True):
                            try:
                                update_shipment_metadata(
                                    selected_shipment_id, 
                                    new_date, 
                                    new_trans_usd, 
                                    new_ship_usd, 
                                    new_customs_mad, 
                                    new_note
                                )
                                st.success("✅ Informations de l'arrivage mises à jour avec succès!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur: {e}")
                
                # Option 2 : Ajouter un produit à cet arrivage
                with st.expander("➕ Ajouter un nouveau produit à cet arrivage"):
                    with st.form("add_product_to_existing_form"):
                        col_add1, col_add2, col_add3 = st.columns([3, 1, 1])
                        
                        references = get_all_references()
                        exist_ref_options = {f"{r['ref']} - {r['name']} ({r['category']} - {r['subtype']})": r['ref'] for r in references}
                        
                        with col_add1:
                            add_selected_ref = st.selectbox("Référence produit", options=list(exist_ref_options.keys()), key="add_exist_ref")
                            add_reference = exist_ref_options[add_selected_ref]
                        with col_add2:
                            add_qty = st.number_input("Quantité", min_value=1, value=1, key="add_exist_qty")
                        with col_add3:
                            add_price_usd = st.number_input("Prix achat unitaire (USD)", min_value=0.0, step=10.0, key="add_exist_price_usd")
                        
                        if st.form_submit_button("➕ Valider l'ajout", use_container_width=True):
                            try:
                                if add_price_usd <= 0:
                                    st.error("Veuillez entrer un prix valide.")
                                else:
                                    add_item_to_existing_shipment(selected_shipment_id, add_reference, add_qty, add_price_usd)
                                    st.success(f"✅ Produit {add_reference} ajouté à l'arrivage!")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Erreur: {e}")
                
                # Option 3 : Modifier ou supprimer un produit de l'arrivage
                if items_data:
                    with st.expander("✏️ Modifier / Supprimer un produit de cet arrivage"):
                        item_options = {
                            f"{it['reference']} (Qté: {it['quantity']}, Restante: {it['qty_remaining']})": it
                            for it in items_data
                        }
                        selected_item_label = st.selectbox("Choisir le produit", list(item_options.keys()), key="select_item_to_edit")
                        selected_item = item_options[selected_item_label]
                        
                        qty_sold = selected_item['quantity'] - selected_item['qty_remaining']
                        
                        col_ed1, col_ed2 = st.columns(2)
                        with col_ed1:
                            edit_qty = st.number_input(
                                f"Nouvelle Quantité (Min: {qty_sold} vendues)", 
                                min_value=int(qty_sold), 
                                value=int(selected_item['quantity']), 
                                key="edit_existing_qty"
                            )
                        with col_ed2:
                            edit_price_usd = st.number_input(
                                "Nouveau Prix achat (USD)", 
                                min_value=0.0, 
                                value=float(selected_item['unit_purchase_price_usd']), 
                                key="edit_existing_price_usd"
                            )
                            
                        col_act_ed1, col_act_ed2 = st.columns(2)
                        with col_act_ed1:
                            if st.button("💾 Enregistrer modifications", key="btn_save_item_edit", use_container_width=True):
                                try:
                                    update_existing_shipment_item(
                                        selected_shipment_id, 
                                        selected_item['product_id'], 
                                        edit_qty, 
                                        edit_price_usd
                                    )
                                    st.success("✅ Produit mis à jour dans l'arrivage!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erreur: {e}")
                        with col_act_ed2:
                            if qty_sold > 0:
                                st.button("🗑️ Supprimer de l'arrivage", key="btn_delete_item_disabled", use_container_width=True, disabled=True, help="Impossible de supprimer car des unités ont déjà été vendues.")
                            else:
                                if st.button("🗑️ Supprimer de l'arrivage", key="btn_delete_item", use_container_width=True, type="secondary"):
                                    if st.checkbox("Confirmer la suppression définitive de cet article de l'arrivage ?", key="confirm_delete_item"):
                                        try:
                                            delete_item_from_existing_shipment(selected_shipment_id, selected_item['product_id'])
                                            st.success("✅ Produit supprimé de l'arrivage!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erreur: {e}")
                                            
                # Option 4 : Supprimer complètement l'arrivage
                with st.expander("🚨 Supprimer l'arrivage complet"):
                    st.warning("⚠️ La suppression d'un arrivage retirera tous les produits associés du stock. Cette action est irréversible et impossible si des produits ont déjà été vendus.")
                    confirm_shipment_delete = st.checkbox("Je confirme vouloir supprimer définitivement cet arrivage et tout son contenu", key="confirm_shipment_delete")
                    
                    if st.button("🗑️ Supprimer l'arrivage complet", type="secondary", use_container_width=True, disabled=not confirm_shipment_delete):
                        try:
                            delete_entire_shipment(selected_shipment_id)
                            st.success("✅ Arrivage supprimé définitivement!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur lors de la suppression : {e}")