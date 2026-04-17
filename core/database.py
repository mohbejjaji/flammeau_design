import os
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Check Streamlit secrets first, then OS environment variables
try:
    DATABASE_URL = st.secrets.get("DATABASE_URL")
except Exception:
    DATABASE_URL = None

if not DATABASE_URL:
    DATABASE_URL = os.environ.get("DATABASE_URL")

# Fallback to local SQLite if neither is found
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///flammeau.db"

# Supprimer l'argument SQLite-spécifique si on utilise PostgreSQL
is_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()