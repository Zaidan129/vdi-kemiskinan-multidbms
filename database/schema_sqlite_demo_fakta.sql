-- HANYA UNTUK MODE DEMO LOKAL (tanpa PostgreSQL). Struktur identik dengan schema_postgres.sql.
CREATE TABLE IF NOT EXISTS kemiskinan_provinsi (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    kode_provinsi       INTEGER NOT NULL,
    tahun               INTEGER NOT NULL,
    periode             TEXT    NOT NULL CHECK (periode IN ('Maret', 'September')),
    jumlah_miskin_ribu  REAL    NOT NULL CHECK (jumlah_miskin_ribu >= 0),
    UNIQUE (kode_provinsi, tahun, periode)
);
