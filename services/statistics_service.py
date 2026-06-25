from core.database import SessionLocal
from core.models import Sale, SaleItem, Product, Expense, VariableExpense  # ✅ Ajout des modèles de charges
from sqlalchemy import func, extract
from datetime import datetime, timedelta
import pandas as pd


def get_monthly_stats(year=None, month=None):
    """Statistiques mensuelles détaillées"""
    db = SessionLocal()
    
    if not year:
        year = datetime.now().year
    if not month:
        month = datetime.now().month
    
    # Ventes du mois
    sales = db.query(Sale).filter(
        extract('year', Sale.date) == year,
        extract('month', Sale.date) == month
    ).all()
    
    total_revenue = sum(s.total_revenue for s in sales)
    total_cost = sum(s.total_cost for s in sales)
    total_commission = sum(s.commission_amount for s in sales)
    gross_profit = total_revenue - total_cost
    
    # ✅ Récupérer les charges fixes et variables du mois
    fixed_expenses = db.query(Expense).filter(
        extract('year', Expense.date) == year,
        extract('month', Expense.date) == month
    ).all()
    
    variable_expenses = db.query(VariableExpense).filter(
        extract('year', VariableExpense.date) == year,
        extract('month', VariableExpense.date) == month
    ).all()
    
    total_fixed_charges = sum(e.amount for e in fixed_expenses)
    total_variable_charges = sum(e.amount for e in variable_expenses)
    
    # Bénéfice net après toutes les charges
    net_profit = gross_profit - total_fixed_charges - total_variable_charges - total_commission
    
    # Top produits vendus
    product_sales = db.query(
        Product.name,
        func.sum(SaleItem.quantity).label('total_quantity'),
        func.sum(SaleItem.quantity * SaleItem.unit_price).label('total_revenue')
    ).join(SaleItem).join(Sale).filter(
        extract('year', Sale.date) == year,
        extract('month', Sale.date) == month
    ).group_by(Product.id).order_by(func.sum(SaleItem.quantity).desc()).limit(10).all()
    
    db.close()
    
    return {
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "gross_profit": gross_profit,
        "total_commission": total_commission,
        "fixed_charges": total_fixed_charges,
        "variable_charges": total_variable_charges,
        "net_profit": net_profit,
        "sales_count": len(sales),
        "top_products": product_sales
    }


def get_breakeven_point():
    """Calcul du seuil de rentabilité"""
    db = SessionLocal()
    
    # Moyenne des 3 derniers mois
    three_months_ago = datetime.now() - timedelta(days=90)
    
    sales = db.query(Sale).filter(Sale.date >= three_months_ago).all()
    
    # ✅ Moyenne des charges fixes sur 3 mois
    fixed_expenses = db.query(Expense).filter(Expense.date >= three_months_ago).all()
    avg_monthly_fixed = sum(e.amount for e in fixed_expenses) / 3 if fixed_expenses else 0
    
    avg_monthly_revenue = sum(s.total_revenue for s in sales) / 3 if sales else 0
    avg_monthly_cost = sum(s.total_cost for s in sales) / 3 if sales else 0
    avg_margin = (avg_monthly_revenue - avg_monthly_cost) / avg_monthly_revenue if avg_monthly_revenue > 0 else 0
    
    if avg_margin > 0:
        breakeven = avg_monthly_fixed / avg_margin
    else:
        breakeven = 0
    
    db.close()
    
    return {
        "breakeven_point": breakeven,
        "avg_monthly_revenue": avg_monthly_revenue,
        "avg_monthly_cost": avg_monthly_cost,
        "avg_margin": avg_margin * 100,
        "monthly_fixed": avg_monthly_fixed
    }