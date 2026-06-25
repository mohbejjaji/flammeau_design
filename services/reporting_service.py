import pandas as pd
from core.database import SessionLocal

def sales_dataframe():
    db = SessionLocal()
    df = pd.read_sql("SELECT * FROM sales", db.bind)
    db.close()
    return df

def kpi_summary():
    df = sales_dataframe()
    total_revenue = df["total_revenue"].sum() if not df.empty else 0
    net_profit = df["net_profit"].sum() if not df.empty else 0
    return total_revenue, net_profit

# ✅ Ajoutez cette fonction si besoin
def get_fixed_charges_summary():
    """Récupère le résumé des charges fixes"""
    from services.expense_service import get_expense_stats
    from datetime import datetime
    
    current_year = datetime.now().year
    current_month = datetime.now().month
    stats = get_expense_stats(current_year, current_month)
    
    return {
        'total': stats['total_fixed'],
        'count': stats['fixed_count']
    }