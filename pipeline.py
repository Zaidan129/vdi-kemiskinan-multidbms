"""Data pipeline: query DBMS 1 + query DBMS 2 -> merge di Pandas -> dataset siap visualisasi."""
import pandas as pd
import streamlit as st
from sqlalchemy import text

from db import get_fact_engine, get_ref_engine

SQL_FAKTA = "SELECT kode_provinsi, tahun, periode, jumlah_miskin_ribu FROM kemiskinan_provinsi"
SQL_REF = ("SELECT kode_provinsi, nama_provinsi, kelompok_pulau, ibu_kota, lat, lon, terdampak_pemekaran "
           "FROM ref_provinsi")
BULAN_KE_NOMOR = {"Maret": 3, "September": 9}


@st.cache_data(ttl=3600, show_spinner="Mengambil data dari kedua DBMS...")
def load_dataset():
    fact_engine, fact_name = get_fact_engine()
    ref_engine, ref_name = get_ref_engine()

    # 1) Extract dari masing-masing DBMS
    with fact_engine.connect() as c:
        fakta = pd.read_sql(text(SQL_FAKTA), c)
    with ref_engine.connect() as c:
        ref = pd.read_sql(text(SQL_REF), c)

    # 2) Transform / integrasi di tingkat aplikasi (federation via Pandas)
    fakta["kode_provinsi"] = fakta["kode_provinsi"].astype(int)
    fakta["jumlah_miskin_ribu"] = fakta["jumlah_miskin_ribu"].astype(float)
    df = fakta.merge(ref, on="kode_provinsi", how="left", validate="many_to_one", indicator=True)
    tak_cocok = int((df["_merge"] != "both").sum())
    df = df.drop(columns="_merge")

    df["label_periode"] = df["periode"] + " " + df["tahun"].astype(str)
    df["tanggal"] = pd.to_datetime(dict(year=df["tahun"], month=df["periode"].map(BULAN_KE_NOMOR), day=1))
    df["jumlah_miskin_juta"] = df["jumlah_miskin_ribu"] / 1000
    df = df.sort_values(["tanggal", "kode_provinsi"]).reset_index(drop=True)

    meta = {
        "fact_engine": fact_name, "ref_engine": ref_name,
        "rows_fakta": len(fakta), "rows_ref": len(ref), "rows_join": len(df),
        "unmatched": tak_cocok,
        "demo_mode": fact_name != "PostgreSQL",
    }
    return df, meta
