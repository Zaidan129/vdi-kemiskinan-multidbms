"""Koneksi ke dua DBMS. Kredensial hanya dari environment variable / st.secrets."""
import os
from pathlib import Path

import streamlit as st
from sqlalchemy import create_engine

BASE = Path(__file__).parent
REF_DB_PATH = BASE / "data" / "referensi_provinsi.sqlite"
DEMO_FACT_DB_PATH = BASE / "data" / "fakta_demo.sqlite"


def get_secret(name: str):
    """Prioritas: environment variable, lalu st.secrets (Streamlit Community Cloud)."""
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets.get(name)
    except Exception:  # belum ada secrets.toml
        return None


@st.cache_resource(show_spinner=False)
def get_fact_engine():
    """DBMS 1 -> PostgreSQL (Neon/Supabase). Fallback demo ke SQLite bila DATABASE_URL kosong."""
    url = get_secret("DATABASE_URL")
    if url:
        url = url.replace("postgres://", "postgresql+psycopg2://", 1).replace("postgresql://", "postgresql+psycopg2://", 1)
        return create_engine(url, pool_pre_ping=True, pool_recycle=300), "PostgreSQL"
    return create_engine(f"sqlite:///{DEMO_FACT_DB_PATH}"), "SQLite (mode demo)"


@st.cache_resource(show_spinner=False)
def get_ref_engine():
    """DBMS 2 -> SQLite embedded (file ada di repositori)."""
    return create_engine(f"sqlite:///{REF_DB_PATH}"), "SQLite"
