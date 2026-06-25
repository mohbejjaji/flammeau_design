import streamlit as st

def main_layout(title):
    st.set_page_config(page_title=title, layout="wide")
    st.image("assets/logo.png", width=220)
    st.sidebar.title("Flammeau Design")
    st.sidebar.markdown("---")