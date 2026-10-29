# Multi-DBMS Data Pipeline & Web Visualization — Kemiskinan Provinsi di Indonesia

Tugas Mandiri Terstruktur · Visualisasi Data dan Informasi · Informatika

| | |
|---|---|
| **Nama / NIM** | _Zaidan Riziq Hibatulwafi_ / _230660121088_ |
| **Live App** | _https://vdi-kemiskinan-multidbms.streamlit.app/_ |
| **Repositori** | _https://github.com/Zaidan129/vdi-kemiskinan-multidbms_ |

## Studi kasus

Dashboard interaktif jumlah penduduk miskin per provinsi (Maret 2022 – Maret 2024). Pemisahan dua DBMS dibuat
karena sifat datanya berbeda:

- **Data fakta** (hasil pengamatan per periode, bertambah tiap survei) → DBMS relasional server (PostgreSQL).
- **Data referensi/metadata** (nama, pulau, koordinat, penanda pemekaran; kecil, jarang berubah, hanya dibaca) → DBMS embedded (SQLite) yang ikut di repositori.

## Ringkasan arsitektur

| | Engine | Fungsi | Tabel |
|---|---|---|---|
| **DBMS 1** | PostgreSQL (Neon / Supabase) | Fakta pengamatan | `kemiskinan_provinsi` (140 baris) |
| **DBMS 2** | SQLite (`data/referensi_provinsi.sqlite`) | Referensi provinsi | `ref_provinsi` (38 baris) |

```
CSV BPS ──► seed_data.py ──┬──► PostgreSQL: kemiskinan_provinsi ──┐
                           └──► SQLite:     ref_provinsi ─────────┴─► Pandas merge(kode_provinsi) ─► Streamlit + Plotly
```

**Alur pipeline** (`pipeline.py`):
1. *Extract*: `SELECT` dari PostgreSQL dan dari SQLite lewat SQLAlchemy.
2. *Integrate*: `fakta.merge(ref, on="kode_provinsi", how="left", validate="many_to_one", indicator=True)`; baris tanpa pasangan dihitung dan ditampilkan sebagai peringatan.
3. *Transform*: label periode, tanggal, konversi ribu → juta jiwa.
4. *Serve*: hasil di-cache (`st.cache_data`, TTL 1 jam) lalu divisualisasikan.

**Pembersihan data saat seed** (`database/seed_data.py`):
- 4 provinsi baru (Papua Barat Daya, Papua Selatan, Papua Tengah, Papua Pegunungan) tidak punya kode di CSV sumber, sehingga diberi kode internal 96, 93, 97, 95.
- Spasi di akhir nama ("Papua Pegunungan ") dibuang; kode di CSV divalidasi terhadap tabel referensi.
- Kolom `terdampak_pemekaran` menandai 6 provinsi di Papua yang angkanya tidak sebanding antarperiode, dan dipakai agar grafik perubahan tidak menyesatkan.

## Fitur interaktif

- Slider periode survei, filter kelompok pulau, dan pengaturan jumlah provinsi teratas.
- KPI (total, perubahan vs periode sebelumnya, provinsi tertinggi, rata-rata).
- Peta bubble (hover untuk detail), bar peringkat, treemap komposisi, heatmap provinsi × periode.
- Tren total per pulau dan tren per provinsi (multi-pilih).
- Perubahan persen Maret 2022 → Maret 2024 (tanpa provinsi terdampak pemekaran).
- Tabel hasil join dengan pencarian dan unduh CSV; tab Arsitektur menampilkan status kedua DBMS, query, dan diagram.

## Sumber data

- **Data primer**: Jumlah Penduduk Miskin Menurut Provinsi di Indonesia (BPS, via OpenData Aceh), lisensi CC BY
  https://data.acehprov.go.id/dataset/jumlah-penduduk-miskin/resource/79aa49bd-5691-46fa-85c8-1aad98bf6383
  (berkas mentah: `data/raw/jumlah-penduduk-miskin-menurut-provinsi.csv`)
- **Metadata referensi**: nama provinsi mengikuti CSV di atas; koordinat ibu kota dan pengelompokan pulau disusun manual (pembulatan, hanya untuk penempatan titik pada peta).

## Referensi kode / inspirasi

- Streamlit — Connect to PostgreSQL: https://docs.streamlit.io/develop/tutorials/databases/postgresql
- Streamlit — Secrets management: https://docs.streamlit.io/develop/concepts/connections/secrets-management
- SQLAlchemy — Engine configuration: https://docs.sqlalchemy.org/en/20/core/engines.html
- pandas — `DataFrame.merge` (`validate`, `indicator`): https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.merge.html
- Plotly — Scatter plots on tile maps: https://plotly.com/python/tile-scatter-maps/


## Menjalankan secara lokal

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1) Siapkan PostgreSQL (mis. Neon), lalu:
export DATABASE_URL="postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require"

# 2) Seed kedua database
python database/seed_data.py --target all

# 3) Jalankan aplikasi
streamlit run app.py
```

Tanpa `DATABASE_URL`, aplikasi tetap jalan dalam **mode demo** (tabel fakta dibaca dari SQLite lokal dan ada banner peringatan).
Buat file demo dengan `python database/seed_data.py --target sqlite-demo`. Mode ini hanya untuk pengembangan; untuk pengumpulan, pastikan banner demo **tidak** muncul.

## Deploy (Streamlit Community Cloud)

1. Buat project di Neon, salin connection string, jalankan seed (langkah 2 di atas).
2. Push repositori ke GitHub (publik). `.env` dan `secrets.toml` sudah masuk `.gitignore`.
3. Di share.streamlit.io: *New app* → pilih repo, branch, file `app.py`.
4. *Advanced settings → Secrets*: isi `DATABASE_URL = "postgresql://..."` (lihat `.streamlit/secrets.toml.example`).
5. Deploy, lalu pastikan tab Arsitektur menampilkan DBMS 1 = **PostgreSQL**.

## Struktur repositori

```
app.py                  # UI Streamlit + visualisasi Plotly
pipeline.py             # extract dari 2 DBMS, merge Pandas
db.py                   # koneksi SQLAlchemy (kredensial dari env/secrets)
database/
  schema_postgres.sql          # DDL DBMS 1
  schema_sqlite_ref.sql        # DDL DBMS 2
  schema_sqlite_demo_fakta.sql # DDL mode demo
  seed_data.py                 # seed kedua DBMS
data/raw/…csv           # data mentah sumber
data/referensi_provinsi.sqlite
requirements.txt
```
