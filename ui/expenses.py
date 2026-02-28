import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from services.expense_service import (
    get_fixed_expenses, add_fixed_expense, delete_fixed_expense,
    get_variable_expenses, add_variable_expense, delete_variable_expense,
    get_expense_stats, get_monthly_expense_report
)
from config import FIXED_CHARGES


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
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard Charges", "🏢 Charges Fixes", "🔄 Charges Variables"])
    
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
        st.subheader("🏢 Charges fixes")
        
        col_f1, col_f2 = st.columns([1, 1])
        
        with col_f1:
            st.write("**Charges fixes mensuelles prédéfinies:**")
            for charge, montant in FIXED_CHARGES.items():
                if charge != "total":
                    st.write(f"- {charge}: {montant} MAD")
        
        with col_f2:
            st.write("**Ajouter une charge fixe ponctuelle:**")
            with st.form("add_fixed_expense"):
                expense_date = st.date_input("Date", date.today())
                expense_type = st.text_input("Type de charge", placeholder="Ex: Loyer, Assurance...")
                expense_amount = st.number_input("Montant (MAD)", min_value=0.0, step=100.0)
                expense_desc = st.text_input("Description", placeholder="Détails...")
                
                if st.form_submit_button("✅ Ajouter"):
                    if expense_type and expense_amount > 0:
                        add_fixed_expense({
                            'date': expense_date,
                            'type': expense_type,
                            'amount': expense_amount,
                            'description': expense_desc
                        })
                        st.success("Charge ajoutée!")
                        st.rerun()
        
        # Liste des charges fixes
        st.subheader("Historique des charges fixes")
        
        year_fixed = st.selectbox("Année", [2024, 2025, 2026], key="fixed_year")
        month_fixed = st.selectbox("Mois", ["Tous"] + [f"{i:02d}" for i in range(1, 13)], 
                                  key="fixed_month")
        
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
            
            # Suppression
            if st.checkbox("Mode suppression - Charges fixes"):
                delete_id = st.number_input("ID de la charge à supprimer", min_value=1, step=1)
                if st.button("🗑️ Supprimer"):
                    delete_fixed_expense(delete_id)
                    st.success("Charge supprimée!")
                    st.rerun()
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
                    st.success("Charge variable ajoutée!")
                    st.rerun()
        
        # Filtres
        col_fv1, col_fv2, col_fv3 = st.columns(3)
        
        with col_fv1:
            var_year = st.selectbox("Année", [2024, 2025, 2026], key="var_year")
        with col_fv2:
            var_month = st.selectbox("Mois", ["Tous"] + [f"{i:02d}" for i in range(1, 13)], 
                                    key="var_month")
        with col_fv3:
            var_type_filter = st.selectbox(
                "Type",
                ["Tous"] + list(variable_types.keys()),
                format_func=lambda x: "Tous" if x == "Tous" else variable_types[x]
            )
        
        month_num_var = None if var_month == "Tous" else int(var_month)
        type_filter = None if var_type_filter == "Tous" else var_type_filter
        
        var_expenses = get_variable_expenses(var_year, month_num_var, type_filter)
        
        if var_expenses:
            # Statistiques de la période
            total_var = sum(e.amount for e in var_expenses)
            st.metric(f"Total charges variables ({len(var_expenses)} opérations)", 
                     f"{total_var:,.0f} MAD")
            
            # Tableau détaillé
            df_var = pd.DataFrame([
                {
                    'ID': e.id,
                    'Date': e.date,
                    'Type': variable_types.get(e.type, e.type),
                    'Montant': f"{e.amount:,.0f} MAD",
                    'Description': e.description or "-",
                    'Véhicule': e.vehicle or "-",
                    'Projet': e.project or "-",
                    'Fournisseur': e.supplier or "-",
                    'Paiement': e.payment_method
                }
                for e in var_expenses
            ])
            
            st.dataframe(df_var, use_container_width=True, hide_index=True)
            
            # Suppression
            if st.checkbox("Mode suppression - Charges variables"):
                delete_id = st.number_input("ID de la charge à supprimer", min_value=1, step=1,
                                           key="var_delete")
                if st.button("🗑️ Supprimer", key="delete_var"):
                    delete_variable_expense(delete_id)
                    st.success("Charge supprimée!")
                    st.rerun()
        else:
            st.info("Aucune charge variable pour cette période")