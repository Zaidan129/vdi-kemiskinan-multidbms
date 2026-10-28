-- DBMS 1: PostgreSQL (Neon / Supabase) -- tabel FAKTA
-- Menyimpan data transaksi/pengamatan utama: jumlah penduduk miskin per provinsi per periode survei.
CREATE TABLE IF NOT EXISTS kemiskinan_provinsi (
    id                  SERIAL PRIMARY KEY,
    kode_provinsi       SMALLINT      NOT NULL,
    tahun               SMALLINT      NOT NULL,
    periode             VARCHAR(10)   NOT NULL CHECK (periode IN ('Maret', 'September')),
    jumlah_miskin_ribu  NUMERIC(10,2) NOT NULL CHECK (jumlah_miskin_ribu >= 0),
    UNIQUE (kode_provinsi, tahun, periode)
);
CREATE INDEX IF NOT EXISTS idx_kemiskinan_periode ON kemiskinan_provinsi (tahun, periode);
