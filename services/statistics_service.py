from core.database import SessionLocal
from core.models import Sale, SaleItem, Product, Expense
from sqlalchemy import func, extract
from datetime import datetime, timedelta
import pandas as pd
from config import FIXED_CHARGES, COMMISSION_RATE

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
    
    # Bénéfice net après charges fixes
    monthly_fixed_charges = sum(FIXED_CHARGES.values())
    net_profit = gross_profit - monthly_fixed_charges - total_commission
    
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
        "net_profit": net_profit,
        "fixed_charges": monthly_fixed_charges,
        "sales_count": len(sales),
        "top_products": product_sales
    }

def get_category_stats():
    """Statistiques par catégorie de produit"""
    db = SessionLocal()
    
    stats = db.query(
        Product.category,
        func.count(Product.id).label('product_count'),
        func.sum(Product.stock_quantity).label('total_stock'),
        func.sum(Product.stock_quantity * Product.purchase_price).label('stock_value')
    ).group_by(Product.category).all()
    
    db.close()
    return stats

def get_profitability_analysis():
    """Analyse de rentabilité par produit"""
    db = SessionLocal()
    
    products = db.query(Product).all()
    analysis = []
    
    for p in products:
        # Ventes totales du produit
        sales_data = db.query(
            func.sum(SaleItem.quantity).label('total_sold'),
            func.sum(SaleItem.quantity * (SaleItem.unit_price - SaleItem.unit_cost_snapshot)).label('total_profit')
        ).filter(SaleItem.product_id == p.id).first()
        
        if sales_data.total_sold and sales_data.total_sold > 0:
            margin_per_unit = (p.selling_price - p.purchase_price) / p.selling_price * 100
            analysis.append({
                "product": p.name,
                "category": p.category,
                "subtype": p.subtype,
                "total_sold": sales_data.total_sold,
                "total_profit": sales_data.total_profit or 0,
                "margin_percentage": margin_per_unit,
                "stock": p.stock_quantity
            })
    
    db.close()
    return sorted(analysis, key=lambda x: x['total_profit'], reverse=True)

def get_breakeven_point():
    """Calcul du seuil de rentabilité"""
    db = SessionLocal()
    
    # Moyenne des 3 derniers mois
    three_months_ago = datetime.now() - timedelta(days=90)
    
    sales = db.query(Sale).filter(Sale.date >= three_months_ago).all()
    
    avg_monthly_revenue = sum(s.total_revenue for s in sales) / 3 if sales else 0
    avg_monthly_cost = sum(s.total_cost for s in sales) / 3 if sales else 0
    avg_margin = (avg_monthly_revenue - avg_monthly_cost) / avg_monthly_revenue if avg_monthly_revenue > 0 else 0
    
    monthly_fixed = sum(FIXED_CHARGES.values())
    
    if avg_margin > 0:
        breakeven = monthly_fixed / avg_margin
    else:
        breakeven = 0
    
    db.close()
    
    return {
        "breakeven_point": breakeven,
        "avg_monthly_revenue": avg_monthly_revenue,
        "avg_monthly_cost": avg_monthly_cost,
        "avg_margin": avg_margin * 100,
        "monthly_fixed": monthly_fixed
    }