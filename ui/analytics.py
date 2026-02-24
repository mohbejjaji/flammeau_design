import streamlit as st
import pandas as pd
from services.reporting_service import sales_dataframe

def analytics_page():
    st.header("Reporting & Analyse")

    df = sales_dataframe()
    if df.empty:
        st.info("Aucune donnée de vente disponible")
        return

    st.subheader("Ventes par catégorie")
    st.bar_chart(df["total_revenue"])

    st.subheader("Marge cumulée")
    st.line_chart(df["net_profit"])

    st.subheader("Top ventes")
    top_sales = df.sort_values("total_revenue", ascending=False).head(10)
    st.dataframe(top_sales[["customer_name", "total_revenue", "net_profit"]])