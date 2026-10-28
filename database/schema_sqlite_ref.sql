-- DBMS 2: SQLite (embedded, file data/referensi_provinsi.sqlite) -- tabel REFERENSI / METADATA
-- Menyimpan metadata provinsi: nama, pulau/region, koordinat ibu kota, penanda pemekaran.
CREATE TABLE IF NOT EXISTS ref_provinsi (
    kode_provinsi    INTEGER PRIMARY KEY,
    nama_provinsi    TEXT    NOT NULL UNIQUE,
    kelompok_pulau   TEXT    NOT NULL,
    ibu_kota         TEXT    NOT NULL,
    lat              REAL    NOT NULL,
    lon              REAL    NOT NULL,
    terdampak_pemekaran INTEGER NOT NULL DEFAULT 0 CHECK (terdampak_pemekaran IN (0, 1))
);
