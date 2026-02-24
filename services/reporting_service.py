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