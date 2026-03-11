from core.database import SessionLocal
from core.models import Expense, VariableExpense
from datetime import datetime, timedelta
import pandas as pd


# ========== CHARGES FIXES ==========

def get_fixed_expenses(year=None, month=None):
    """Récupère les charges fixes pour une période"""
    db = SessionLocal()
    
    query = db.query(Expense)
    
    if year:
        query = query.filter(Expense.date >= f"{year}-01-01")
        if month:
            query = query.filter(Expense.date >= f"{year}-{month:02d}-01")
            next_month = month + 1 if month < 12 else 1
            next_year = year if month < 12 else year + 1
            query = query.filter(Expense.date < f"{next_year}-{next_month:02d}-01")
    
    expenses = query.order_by(Expense.date.desc()).all()
    db.close()
    
    return expenses


def add_fixed_expense(expense_data):
    """Ajoute une charge fixe"""
    db = SessionLocal()
    
    expense = Expense(
        date=expense_data['date'],
        type=expense_data['type'],
        amount=expense_data['amount'],
        description=expense_data.get('description', '')
    )
    
    db.add(expense)
    db.commit()
    db.refresh(expense)
    db.close()
    
    return expense


def update_fixed_expense(expense_id, expense_data):
    """Met à jour une charge fixe existante"""
    db = SessionLocal()
    try:
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        
        if not expense:
            return None
        
        # Mettre à jour les champs
        expense.date = expense_data['date']
        expense.type = expense_data['type']
        expense.amount = expense_data['amount']
        expense.description = expense_data.get('description', '')
        
        db.commit()
        db.refresh(expense)
        return expense
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def delete_fixed_expense(expense_id):
    """Supprime une charge fixe"""
    db = SessionLocal()
    try:
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if expense:
            db.delete(expense)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_fixed_expense_by_id(expense_id):
    """Récupère une charge fixe par son ID"""
    db = SessionLocal()
    try:
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        return expense
    finally:
        db.close()


# ========== CHARGES VARIABLES ==========

def get_variable_expenses(year=None, month=None, expense_type=None):
    """Récupère les charges variables avec filtres"""
    db = SessionLocal()
    
    query = db.query(VariableExpense)
    
    if year:
        query = query.filter(VariableExpense.date >= f"{year}-01-01")
        if month:
            query = query.filter(VariableExpense.date >= f"{year}-{month:02d}-01")
            next_month = month + 1 if month < 12 else 1
            next_year = year if month < 12 else year + 1
            query = query.filter(VariableExpense.date < f"{next_year}-{next_month:02d}-01")
    
    if expense_type and expense_type != "Tous":
        query = query.filter(VariableExpense.type == expense_type)
    
    expenses = query.order_by(VariableExpense.date.desc()).all()
    db.close()
    
    return expenses


def add_variable_expense(expense_data):
    """Ajoute une charge variable"""
    db = SessionLocal()
    
    expense = VariableExpense(
        date=expense_data['date'],
        type=expense_data['type'],
        amount=expense_data['amount'],
        description=expense_data.get('description', ''),
        vehicle=expense_data.get('vehicle'),
        project=expense_data.get('project'),
        supplier=expense_data.get('supplier'),
        payment_method=expense_data.get('payment_method', 'Espèces')
    )
    
    db.add(expense)
    db.commit()
    db.refresh(expense)
    db.close()
    
    return expense


def update_variable_expense(expense_id, expense_data):
    """Met à jour une charge variable existante"""
    db = SessionLocal()
    try:
        expense = db.query(VariableExpense).filter(VariableExpense.id == expense_id).first()
        
        if not expense:
            return None
        
        expense.date = expense_data['date']
        expense.type = expense_data['type']
        expense.amount = expense_data['amount']
        expense.description = expense_data.get('description', '')
        expense.vehicle = expense_data.get('vehicle')
        expense.project = expense_data.get('project')
        expense.supplier = expense_data.get('supplier')
        expense.payment_method = expense_data.get('payment_method', 'Espèces')
        
        db.commit()
        db.refresh(expense)
        return expense
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def delete_variable_expense(expense_id):
    """Supprime une charge variable"""
    db = SessionLocal()
    try:
        expense = db.query(VariableExpense).filter(VariableExpense.id == expense_id).first()
        if expense:
            db.delete(expense)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_variable_expense_by_id(expense_id):
    """Récupère une charge variable par son ID"""
    db = SessionLocal()
    try:
        expense = db.query(VariableExpense).filter(VariableExpense.id == expense_id).first()
        return expense
    finally:
        db.close()


# ========== STATISTIQUES ==========

def get_expense_stats(year=None, month=None):
    """Statistiques des charges"""
    db = SessionLocal()
    
    # Charges fixes
    fixed_query = db.query(Expense)
    if year:
        fixed_query = fixed_query.filter(Expense.date >= f"{year}-01-01")
        if month:
            fixed_query = fixed_query.filter(Expense.date >= f"{year}-{month:02d}-01")
            next_month = month + 1 if month < 12 else 1
            next_year = year if month < 12 else year + 1
            fixed_query = fixed_query.filter(Expense.date < f"{next_year}-{next_month:02d}-01")
    
    fixed_expenses = fixed_query.all()
    total_fixed = sum(e.amount for e in fixed_expenses)
    
    # Charges variables
    var_query = db.query(VariableExpense)
    if year:
        var_query = var_query.filter(VariableExpense.date >= f"{year}-01-01")
        if month:
            var_query = var_query.filter(VariableExpense.date >= f"{year}-{month:02d}-01")
            next_month = month + 1 if month < 12 else 1
            next_year = year if month < 12 else year + 1
            var_query = var_query.filter(VariableExpense.date < f"{next_year}-{next_month:02d}-01")
    
    var_expenses = var_query.all()
    total_var = sum(e.amount for e in var_expenses)
    
    # Détail par type de charge variable
    var_by_type = {}
    for expense in var_expenses:
        if expense.type not in var_by_type:
            var_by_type[expense.type] = 0
        var_by_type[expense.type] += expense.amount
    
    db.close()
    
    return {
        'total_fixed': total_fixed,
        'total_variable': total_var,
        'total_all': total_fixed + total_var,
        'fixed_count': len(fixed_expenses),
        'variable_count': len(var_expenses),
        'variable_by_type': var_by_type
    }


def get_monthly_expense_report(year):
    """Rapport mensuel des charges"""
    report = []
    
    for month in range(1, 13):
        stats = get_expense_stats(year, month)
        report.append({
            'mois': month,
            'charges_fixes': stats['total_fixed'],
            'charges_variables': stats['total_variable'],
            'total': stats['total_all']
        })
    
    return report