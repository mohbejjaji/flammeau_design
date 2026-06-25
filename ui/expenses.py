import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from services.expense_service import (
    get_fixed_expenses, add_fixed_expense, delete_fixed_expense, update_fixed_expense, get_fixed_expense_by_id,
    get_variable_expenses, add_variable_expense, delete_variable_expense, update_variable_expense, get_variable_expense_by_id,
    get_expense_stats, get_monthly_expense_report
)


def expenses_page():
    st.header("💰 Gestion des Charges")
    
    # Types de charges variables prédéfinis
    variable_types = {
        "deplacement": "🚗 Déplacement",
        "gasoil": "⛽ Gasoil",
        "menuiserie": "🪚 Menuiserie",
        "soudure": "⚡ Soudure",
        "fourniture": "📦 Fournitures",
        "repas": "🍽️ Repas professionnels",
        "peage": "🛣️ Péage",
        "parking": "🅿️ Parking",
        "divers": "📌 Divers"
    }
    
    # Onglets
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard Charges", "🏢 Charges Fixes", "🔄 Charges Variables", "✏️ Gérer les charges"])
    
    with tab1:
        st.subheader("📊 Dashboard des charges")
        
        # Sélection de la période
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            year = st.selectbox("Année", [2024, 2025, 2026], index=2)
        with col_p2:
            month = st.selectbox("Mois", 
                               ["Tous"] + [f"{i:02d}" for i in range(1, 13)],
                               index=0)
        
        month_num = None if month == "Tous" else int(month)
        
        stats = get_expense_stats(year, month_num)
        
        # KPIs
        col_k1, col_k2, col_k3, col_k4 = st.columns(4)
        with col_k1:
            st.metric("Charges fixes", f"{stats['total_fixed']:,.0f} MAD")
        with col_k2:
            st.metric("Charges variables", f"{stats['total_variable']:,.0f} MAD")
        with col_k3:
            st.metric("Total charges", f"{stats['total_all']:,.0f} MAD")
        with col_k4:
            st.metric("Nombre d'opérations", stats['fixed_count'] + stats['variable_count'])
        
        # Graphiques
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            # Répartition fixe/variable
            fig = px.pie(
                values=[stats['total_fixed'], stats['total_variable']],
                names=['Charges fixes', 'Charges variables'],
                title="Répartition des charges",
                color_discrete_sequence=['#00adb5', '#ff5722']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col_g2:
            # Détail des charges variables
            if stats['variable_by_type']:
                df_var = pd.DataFrame([
                    {'type': variable_types.get(t, t), 'montant': m}
                    for t, m in stats['variable_by_type'].items()
                ])
                fig = px.bar(
                    df_var,
                    x='type',
                    y='montant',
                    title="Détail des charges variables",
                    labels={'montant': 'Montant (MAD)', 'type': ''}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Graphique d'évolution annuelle
        if month == "Tous":
            st.subheader("Évolution mensuelle")
            report = get_monthly_expense_report(year)
            df_report = pd.DataFrame(report)
            df_report['mois'] = df_report['mois'].apply(lambda x: f"Mois {x:02d}")
            
            fig = px.line(
                df_report,
                x='mois',
                y=['charges_fixes', 'charges_variables', 'total'],
                title="Évolution des charges",
                labels={'value': 'Montant (MAD)', 'variable': 'Type'},
                color_discrete_map={
                    'charges_fixes': '#00adb5',
                    'charges_variables': '#ff5722',
                    'total': '#393e46'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("🏢 Ajouter une charge fixe")
        
        # Formulaire d'ajout de charge fixe
        with st.form("add_fixed_expense", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                expense_date = st.date_input("📅 Date", date.today())
                expense_type = st.text_input("🏷️ Type de charge", placeholder="Ex: Loyer, Assurance, Electricité...")
            with col2:
                expense_amount = st.number_input("💰 Montant (MAD)", min_value=0.0, step=100.0)
                expense_desc = st.text_input("📝 Description", placeholder="Détails...")
            
            if st.form_submit_button("✅ Ajouter la charge fixe", use_container_width=True):
                if expense_type and expense_amount > 0:
                    add_fixed_expense({
                        'date': expense_date,
                        'type': expense_type,
                        'amount': expense_amount,
                        'description': expense_desc
                    })
                    st.success(f"✅ Charge fixe '{expense_type}' ajoutée!")
                    st.rerun()
                else:
                    st.error("❌ Le type et le montant sont obligatoires")
        
        # ✅ Afficher l'historique des charges fixes
        st.subheader("📋 Historique des charges fixes")
        
        year_fixed = st.selectbox("Année", [2024, 2025, 2026], key="fixed_year")
        month_fixed = st.selectbox("Mois", ["Tous"] + [f"{i:02d}" for i in range(1, 13)], key="fixed_month")
        
        month_num_fixed = None if month_fixed == "Tous" else int(month_fixed)
        fixed_expenses = get_fixed_expenses(year_fixed, month_num_fixed)
        
        if fixed_expenses:
            df_fixed = pd.DataFrame([
                {
                    'ID': e.id,
                    'Date': e.date,
                    'Type': e.type,
                    'Montant': f"{e.amount:,.0f} MAD",
                    'Description': e.description or "-"
                }
                for e in fixed_expenses
            ])
            st.dataframe(df_fixed, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune charge fixe pour cette période")
    
    with tab3:
        st.subheader("🔄 Charges variables")
        
        # Formulaire d'ajout
        with st.expander("➕ Ajouter une charge variable", expanded=True):
            col_v1, col_v2 = st.columns(2)
            
            with col_v1:
                var_date = st.date_input("Date", date.today(), key="var_date")
                var_type = st.selectbox(
                    "Type de charge",
                    options=list(variable_types.keys()),
                    format_func=lambda x: variable_types[x]
                )
                var_amount = st.number_input("Montant (MAD)", min_value=0.0, step=50.0, key="var_amount")
            
            with col_v2:
                if var_type == "gasoil":
                    var_vehicle = st.text_input("Véhicule", placeholder="Ex: Kangoo, Berlingo...")
                else:
                    var_vehicle = None
                
                if var_type in ["menuiserie", "soudure"]:
                    var_project = st.text_input("Projet", placeholder="Ex: Installation client X...")
                    var_supplier = st.text_input("Fournisseur", placeholder="Nom du prestataire")
                else:
                    var_project = None
                    var_supplier = None
                
                var_payment = st.selectbox(
                    "Mode de paiement",
                    ["Espèces", "Carte", "Virement", "Chèque"],
                    key="var_payment"
                )
            
            var_description = st.text_input("Description", placeholder="Détails...", key="var_desc")
            
            if st.button("✅ Ajouter la charge variable"):
                if var_amount > 0:
                    expense_data = {
                        'date': var_date,
                        'type': var_type,
                        'amount': var_amount,
                        'description': var_description,
                        'vehicle': var_vehicle,
                        'project': var_project,
                        'supplier': var_supplier,
                        'payment_method': var_payment
                    }
                    add_variable_expense(expense_data)
                    st.success("✅ Charge variable ajoutée!")
                    st.rerun()
    
    with tab4:
        st.subheader("✏️ Gérer les charges existantes")
        
        # Sous-onglets pour fixe/variable
        sub_tab1, sub_tab2 = st.tabs(["🏢 Charges Fixes", "🔄 Charges Variables"])
        
        with sub_tab1:
            st.write("### Modifier/Supprimer une charge fixe")
            
            # Filtres
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                year_fix = st.selectbox("Année", [2024, 2025, 2026], key="fix_year")
            with col_f2:
                month_fix = st.selectbox("Mois", ["Tous"] + [f"{i:02d}" for i in range(1, 13)], key="fix_month")
            
            month_num_fix = None if month_fix == "Tous" else int(month_fix)
            fixed_expenses = get_fixed_expenses(year_fix, month_num_fix)
            
            if fixed_expenses:
                # Créer un DataFrame pour l'affichage
                df_fixed = pd.DataFrame([
                    {
                        'ID': e.id,
                        'Date': e.date,
                        'Type': e.type,
                        'Montant': e.amount,
                        'Description': e.description or '-'
                    }
                    for e in fixed_expenses
                ])
                
                # Afficher le tableau
                st.dataframe(
                    df_fixed,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "ID": st.column_config.NumberColumn("ID", width=50),
                        "Date": st.column_config.DateColumn("Date"),
                        "Type": st.column_config.TextColumn("Type"),
                        "Montant": st.column_config.NumberColumn("Montant", format="%.0f MAD"),
                        "Description": st.column_config.TextColumn("Description")
                    }
                )
                
                # Sélection pour modification
                st.markdown("---")
                st.write("#### Sélectionner une charge à modifier")
                
                expense_options = {
                    f"#{e.id} - {e.date} - {e.type} - {e.amount:,.0f} MAD": e.id 
                    for e in fixed_expenses
                }
                
                selected = st.selectbox(
                    "Choisir une charge",
                    options=list(expense_options.keys()),
                    key="select_fixed"
                )
                
                if selected:
                    expense_id = expense_options[selected]
                    expense = get_fixed_expense_by_id(expense_id)
                    
                    if expense:
                        with st.form("edit_fixed_form"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                new_date = st.date_input("Date", value=expense.date)
                                new_type = st.text_input("Type", value=expense.type)
                            with col2:
                                new_amount = st.number_input(
                                    "Montant (MAD)",
                                    min_value=0.0,
                                    value=float(expense.amount),
                                    step=100.0
                                )
                                new_desc = st.text_input("Description", value=expense.description or "")
                            
                            col_b1, col_b2 = st.columns(2)
                            
                            with col_b1:
                                if st.form_submit_button("💾 Mettre à jour"):
                                    try:
                                        update_fixed_expense(expense_id, {
                                            'date': new_date,
                                            'type': new_type,
                                            'amount': new_amount,
                                            'description': new_desc
                                        })
                                        st.success("✅ Charge mise à jour!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Erreur: {e}")
                            
                            with col_b2:
                                if st.form_submit_button("🗑️ Supprimer", type="secondary"):
                                    if st.checkbox("Confirmer la suppression?"):
                                        try:
                                            delete_fixed_expense(expense_id)
                                            st.success("✅ Charge supprimée!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Erreur: {e}")
            else:
                st.info("Aucune charge fixe trouvée pour cette période")
        
        with sub_tab2:
            st.write("### Modifier/Supprimer une charge variable")
            
            # Filtres
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                year_var = st.selectbox("Année", [2024, 2025, 2026], key="var_year")
            with col_f2:
                month_var = st.selectbox("Mois", ["Tous"] + [f"{i:02d}" for i in range(1, 13)], key="var_month")
            with col_f3:
                type_var = st.selectbox(
                    "Type",
                    ["Tous"] + list(variable_types.keys()),
                    format_func=lambda x: "Tous" if x == "Tous" else variable_types[x],
                    key="var_type"
                )
            
            month_num_var = None if month_var == "Tous" else int(month_var)
            type_filter = None if type_var == "Tous" else type_var
            
            var_expenses = get_variable_expenses(year_var, month_num_var, type_filter)
            
            if var_expenses:
                # Afficher le tableau
                df_var = pd.DataFrame([
                    {
                        'ID': e.id,
                        'Date': e.date,
                        'Type': variable_types.get(e.type, e.type),
                        'Montant': e.amount,
                        'Description': e.description or '-',
                        'Véhicule': e.vehicle or '-',
                        'Projet': e.project or '-',
                        'Fournisseur': e.supplier or '-'
                    }
                    for e in var_expenses
                ])
                
                st.dataframe(
                    df_var,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "ID": st.column_config.NumberColumn("ID", width=50),
                        "Date": st.column_config.DateColumn("Date"),
                        "Type": st.column_config.TextColumn("Type"),
                        "Montant": st.column_config.NumberColumn("Montant", format="%.0f MAD"),
                        "Description": st.column_config.TextColumn("Description"),
                        "Véhicule": st.column_config.TextColumn("Véhicule"),
                        "Projet": st.column_config.TextColumn("Projet"),
                        "Fournisseur": st.column_config.TextColumn("Fournisseur")
                    }
                )
                
                # Sélection pour modification
                st.markdown("---")
                st.write("#### Sélectionner une charge à modifier")
                
                expense_options = {
                    f"#{e.id} - {e.date} - {variable_types.get(e.type, e.type)} - {e.amount:,.0f} MAD": e.id 
                    for e in var_expenses
                }
                
                selected = st.selectbox(
                    "Choisir une charge",
                    options=list(expense_options.keys()),
                    key="select_var"
                )
                
                if selected:
                    expense_id = expense_options[selected]
                    expense = get_variable_expense_by_id(expense_id)
                    
                    if expense:
                        with st.form("edit_var_form"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                new_date = st.date_input("Date", value=expense.date)
                                new_type = st.selectbox(
                                    "Type",
                                    options=list(variable_types.keys()),
                                    format_func=lambda x: variable_types[x],
                                    index=list(variable_types.keys()).index(expense.type) if expense.type in variable_types else 0
                                )
                                new_amount = st.number_input(
                                    "Montant (MAD)",
                                    min_value=0.0,
                                    value=float(expense.amount),
                                    step=50.0
                                )
                            
                            with col2:
                                if new_type == "gasoil":
                                    new_vehicle = st.text_input("Véhicule", value=expense.vehicle or "")
                                else:
                                    new_vehicle = None
                                
                                if new_type in ["menuiserie", "soudure"]:
                                    new_project = st.text_input("Projet", value=expense.project or "")
                                    new_supplier = st.text_input("Fournisseur", value=expense.supplier or "")
                                else:
                                    new_project = None
                                    new_supplier = None
                                
                                new_payment = st.selectbox(
                                    "Mode de paiement",
                                    ["Espèces", "Carte", "Virement", "Chèque"],
                                    index=["Espèces", "Carte", "Virement", "Chèque"].index(expense.payment_method) if expense.payment_method in ["Espèces", "Carte", "Virement", "Chèque"] else 0
                                )
                            
                            new_desc = st.text_input("Description", value=expense.description or "")
                            
                            col_b1, col_b2 = st.columns(2)
                            
                            with col_b1:
                                if st.form_submit_button("💾 Mettre à jour"):
                                    try:
                                        update_variable_expense(expense_id, {
                                            'date': new_date,
                                            'type': new_type,
                                            'amount': new_amount,
                                            'description': new_desc,
                                            'vehicle': new_vehicle,
                                            'project': new_project,
                                            'supplier': new_supplier,
                                            'payment_method': new_payment
                                        })
                                        st.success("✅ Charge mise à jour!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Erreur: {e}")
                            
                            with col_b2:
                                if st.form_submit_button("🗑️ Supprimer", type="secondary"):
                                    if st.checkbox("Confirmer la suppression?"):
                                        try:
                                            delete_variable_expense(expense_id)
                                            st.success("✅ Charge supprimée!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Erreur: {e}")
            else:
                st.info("Aucune charge variable trouvée pour cette période")