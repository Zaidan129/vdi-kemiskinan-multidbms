"""
Seed script untuk kedua DBMS.

  python database/seed_data.py --target all          # PostgreSQL (DATABASE_URL) + SQLite referensi
  python database/seed_data.py --target postgres     # hanya DBMS 1
  python database/seed_data.py --target sqlite-ref   # hanya DBMS 2
  python database/seed_data.py --target sqlite-demo  # tabel fakta lokal (mode demo tanpa PostgreSQL)

Sumber data primer: BPS via OpenData Aceh (lihat README). Berkas CSV disalin di data/raw/.
Kredensial dibaca dari environment variable DATABASE_URL (tidak pernah di-hardcode).
"""
import argparse
import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "raw" / "jumlah-penduduk-miskin-menurut-provinsi.csv"
REF_DB = ROOT / "data" / "referensi_provinsi.sqlite"
DEMO_FACT_DB = ROOT / "data" / "fakta_demo.sqlite"

# (kode, nama, kelompok pulau, ibu kota, lat, lon, terdampak_pemekaran)
# Koordinat = titik ibu kota provinsi (pembulatan, disusun manual untuk keperluan peta).
# Kode 93/95/96/97 = kode internal untuk 4 provinsi baru yang kodenya kosong di CSV sumber.
REF_PROVINSI = [
    (11, "Aceh", "Sumatera", "Banda Aceh", 5.55, 95.32, 0),
    (12, "Sumatera Utara", "Sumatera", "Medan", 3.59, 98.67, 0),
    (13, "Sumatera Barat", "Sumatera", "Padang", -0.95, 100.35, 0),
    (14, "Riau", "Sumatera", "Pekanbaru", 0.51, 101.45, 0),
    (15, "Jambi", "Sumatera", "Jambi", -1.61, 103.61, 0),
    (16, "Sumatera Selatan", "Sumatera", "Palembang", -2.98, 104.77, 0),
    (17, "Bengkulu", "Sumatera", "Bengkulu", -3.80, 102.26, 0),
    (18, "Lampung", "Sumatera", "Bandar Lampung", -5.43, 105.26, 0),
    (19, "Kepulauan Bangka Belitung", "Sumatera", "Pangkal Pinang", -2.13, 106.11, 0),
    (21, "Kepulauan Riau", "Sumatera", "Tanjung Pinang", 0.92, 104.45, 0),
    (31, "DKI Jakarta", "Jawa", "Jakarta", -6.21, 106.85, 0),
    (32, "Jawa Barat", "Jawa", "Bandung", -6.91, 107.61, 0),
    (33, "Jawa Tengah", "Jawa", "Semarang", -6.97, 110.42, 0),
    (34, "DI Yogyakarta", "Jawa", "Yogyakarta", -7.80, 110.36, 0),
    (35, "Jawa Timur", "Jawa", "Surabaya", -7.25, 112.75, 0),
    (36, "Banten", "Jawa", "Serang", -6.12, 106.15, 0),
    (51, "Bali", "Bali & Nusa Tenggara", "Denpasar", -8.65, 115.22, 0),
    (52, "Nusa Tenggara Barat", "Bali & Nusa Tenggara", "Mataram", -8.58, 116.12, 0),
    (53, "Nusa Tenggara Timur", "Bali & Nusa Tenggara", "Kupang", -10.18, 123.58, 0),
    (61, "Kalimantan Barat", "Kalimantan", "Pontianak", -0.03, 109.33, 0),
    (62, "Kalimantan Tengah", "Kalimantan", "Palangka Raya", -2.21, 113.92, 0),
    (63, "Kalimantan Selatan", "Kalimantan", "Banjarmasin", -3.32, 114.59, 0),
    (64, "Kalimantan Timur", "Kalimantan", "Samarinda", -0.50, 117.15, 0),
    (65, "Kalimantan Utara", "Kalimantan", "Tanjung Selor", 2.84, 117.37, 0),
    (71, "Sulawesi Utara", "Sulawesi", "Manado", 1.47, 124.84, 0),
    (72, "Sulawesi Tengah", "Sulawesi", "Palu", -0.90, 119.87, 0),
    (73, "Sulawesi Selatan", "Sulawesi", "Makassar", -5.15, 119.43, 0),
    (74, "Sulawesi Tenggara", "Sulawesi", "Kendari", -3.97, 122.51, 0),
    (75, "Gorontalo", "Sulawesi", "Gorontalo", 0.54, 123.06, 0),
    (76, "Sulawesi Barat", "Sulawesi", "Mamuju", -2.68, 118.89, 0),
    (81, "Maluku", "Maluku & Papua", "Ambon", -3.70, 128.18, 0),
    (82, "Maluku Utara", "Maluku & Papua", "Sofifi", 0.74, 127.57, 0),
    (91, "Papua Barat", "Maluku & Papua", "Manokwari", -0.86, 134.06, 1),
    (94, "Papua", "Maluku & Papua", "Jayapura", -2.53, 140.72, 1),
    (93, "Papua Selatan", "Maluku & Papua", "Merauke", -8.50, 140.40, 1),
    (95, "Papua Pegunungan", "Maluku & Papua", "Wamena", -4.10, 138.94, 1),
    (96, "Papua Barat Daya", "Maluku & Papua", "Sorong", -0.88, 131.26, 1),
    (97, "Papua Tengah", "Maluku & Papua", "Nabire", -3.37, 135.48, 1),
]


def load_clean_csv() -> pd.DataFrame:
    """Baca CSV mentah (separator ';'), bersihkan, dan petakan kode provinsi."""
    raw = pd.read_csv(CSV_PATH, sep=";", dtype={"bps_kode_provinsi": "string"})
    raw["bps_nama_provinsi"] = raw["bps_nama_provinsi"].str.strip()
    name_to_code = {nama: kode for kode, nama, *_ in REF_PROVINSI}

    raw["kode_provinsi"] = raw["bps_nama_provinsi"].map(name_to_code)
    if raw["kode_provinsi"].isna().any():
        raise ValueError(f"Nama provinsi tak dikenal: {raw.loc[raw['kode_provinsi'].isna(), 'bps_nama_provinsi'].unique()}")

    # Integritas: kode asli dari CSV (bila ada) harus sama dengan kode referensi.
    punya_kode = raw[raw["bps_kode_provinsi"].notna()]
    mismatch = punya_kode[punya_kode["bps_kode_provinsi"].astype(int) != punya_kode["kode_provinsi"]]
    if not mismatch.empty:
        raise ValueError(f"Kode CSV tidak cocok dengan referensi:\n{mismatch}")

    df = raw.rename(columns={"periode_bulan": "periode", "jumlah_penduduk_miskin": "jumlah_miskin_ribu"})
    df["kode_provinsi"] = df["kode_provinsi"].astype(int)
    return df[["kode_provinsi", "tahun", "periode", "jumlah_miskin_ribu"]]


def run_ddl(conn, path: Path) -> None:
    for stmt in path.read_text(encoding="utf-8").split(";"):
        if stmt.strip():
            conn.execute(text(stmt))


def seed_postgres() -> None:
    url = os.getenv("DATABASE_URL")
    if not url:
        sys.exit("DATABASE_URL belum di-set. Contoh: postgresql+psycopg2://user:pass@host/db?sslmode=require")
    url = url.replace("postgres://", "postgresql+psycopg2://", 1).replace("postgresql://", "postgresql+psycopg2://", 1)
    engine = create_engine(url)
    df = load_clean_csv()
    with engine.begin() as conn:
        run_ddl(conn, ROOT / "database" / "schema_postgres.sql")
        conn.execute(text("DELETE FROM kemiskinan_provinsi"))
        df.to_sql("kemiskinan_provinsi", conn, if_exists="append", index=False, method="multi")
    print(f"[PostgreSQL] kemiskinan_provinsi: {len(df)} baris dimuat.")


def seed_sqlite_ref() -> None:
    engine = create_engine(f"sqlite:///{REF_DB}")
    ref = pd.DataFrame(REF_PROVINSI, columns=["kode_provinsi", "nama_provinsi", "kelompok_pulau", "ibu_kota", "lat", "lon", "terdampak_pemekaran"])
    with engine.begin() as conn:
        run_ddl(conn, ROOT / "database" / "schema_sqlite_ref.sql")
        conn.execute(text("DELETE FROM ref_provinsi"))
        ref.to_sql("ref_provinsi", conn, if_exists="append", index=False)
    print(f"[SQLite] ref_provinsi: {len(ref)} baris dimuat -> {REF_DB.name}")


def seed_sqlite_demo() -> None:
    engine = create_engine(f"sqlite:///{DEMO_FACT_DB}")
    df = load_clean_csv()
    with engine.begin() as conn:
        run_ddl(conn, ROOT / "database" / "schema_sqlite_demo_fakta.sql")
        conn.execute(text("DELETE FROM kemiskinan_provinsi"))
        df.to_sql("kemiskinan_provinsi", conn, if_exists="append", index=False)
    print(f"[SQLite demo] kemiskinan_provinsi: {len(df)} baris dimuat -> {DEMO_FACT_DB.name}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--target", choices=["all", "postgres", "sqlite-ref", "sqlite-demo"], default="all")
    t = p.parse_args().target
    if t in ("all", "postgres"):
        seed_postgres()
    if t in ("all", "sqlite-ref"):
        seed_sqlite_ref()
    if t == "sqlite-demo":
        seed_sqlite_demo()
