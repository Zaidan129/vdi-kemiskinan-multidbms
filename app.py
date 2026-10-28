"""Dashboard Kemiskinan Provinsi di Indonesia — Multi-DBMS (PostgreSQL + SQLite) dengan Streamlit."""
import inspect

import pandas as pd
import plotly.express as px
import streamlit as st

import pipeline
from pipeline import SQL_FAKTA, SQL_REF, load_dataset

st.set_page_config(page_title="Kemiskinan Provinsi Indonesia", page_icon="📊", layout="wide")

# ---------- Data ----------
try:
    df, meta = load_dataset()
except Exception as exc:
    st.error("Gagal terhubung ke database. Periksa DATABASE_URL (secrets) dan jalankan seed script.")
    st.exception(exc)
    st.stop()

periode_urut = list(df.drop_duplicates("tanggal").sort_values("tanggal")["label_periode"])
palet = px.colors.qualitative.Safe

# ---------- Header ----------
st.title("📊 Penduduk Miskin per Provinsi di Indonesia")
st.caption("Maret 2022 – Maret 2024 · Data fakta dari PostgreSQL + referensi wilayah dari SQLite, digabung di Pandas")
if meta["demo_mode"]:
    st.warning("Mode demo: DATABASE_URL belum di-set, sehingga tabel fakta dibaca dari SQLite lokal. "
               "Set DATABASE_URL untuk memakai PostgreSQL (DBMS 1) yang sesungguhnya.", icon="⚠️")
if meta["unmatched"]:
    st.warning(f"{meta['unmatched']} baris fakta tidak menemukan pasangan di tabel referensi.")

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Filter")
    periode = st.select_slider("Periode survei", options=periode_urut, value=periode_urut[-1])
    pulau_semua = sorted(df["kelompok_pulau"].unique())
    pulau = st.multiselect("Kelompok pulau", pulau_semua, default=pulau_semua)
    top_n = st.slider("Tampilkan N provinsi teratas", 5, 20, 10)
    st.divider()
    st.caption("Catatan: pemekaran Papua (2022) membuat angka Papua & Papua Barat pada 2024 "
               "tidak sebanding dengan periode sebelumnya.")

if not pulau:
    st.info("Pilih minimal satu kelompok pulau.")
    st.stop()

d_all = df[df["kelompok_pulau"].isin(pulau)]
d_sel = d_all[d_all["label_periode"] == periode]
idx = periode_urut.index(periode)
total_now = d_sel["jumlah_miskin_juta"].sum()
delta_txt = None
if idx > 0:
    prev = d_all[d_all["label_periode"] == periode_urut[idx - 1]]["jumlah_miskin_juta"].sum()
    delta_txt = f"{total_now - prev:+.2f} juta vs {periode_urut[idx - 1]}"
top = d_sel.sort_values("jumlah_miskin_ribu", ascending=False).iloc[0]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total penduduk miskin", f"{total_now:.2f} juta jiwa", delta_txt, delta_color="inverse")
k2.metric("Provinsi tertinggi", top["nama_provinsi"], f"{top['jumlah_miskin_juta']:.2f} juta jiwa", delta_color="off")
k3.metric("Jumlah provinsi", len(d_sel))
k4.metric("Rata-rata per provinsi", f"{d_sel['jumlah_miskin_ribu'].mean():.0f} ribu jiwa")

tab_peta, tab_tren, tab_banding, tab_data, tab_arsitektur = st.tabs(
    ["🗺️ Peta & Peringkat", "📈 Tren", "⚖️ Perbandingan", "🧾 Data hasil join", "🏗️ Arsitektur"])

# ---------- Tab 1: Peta & peringkat ----------
with tab_peta:
    c1, c2 = st.columns([3, 2])
    with c1:
        st.subheader(f"Sebaran — {periode}")
        fig = px.scatter_map(
            d_sel, lat="lat", lon="lon", size="jumlah_miskin_ribu", size_max=48, color="kelompok_pulau",
            hover_name="nama_provinsi", hover_data={"jumlah_miskin_ribu": ":.2f", "ibu_kota": True, "lat": False, "lon": False},
            labels={"jumlah_miskin_ribu": "Ribu jiwa", "kelompok_pulau": "Kelompok pulau", "ibu_kota": "Ibu kota"},
            zoom=3.1, center={"lat": -2.5, "lon": 118}, map_style="open-street-map", height=520,
            color_discrete_sequence=palet)
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), legend=dict(orientation="h", y=-0.05))
        st.plotly_chart(fig, width="stretch")
    with c2:
        st.subheader(f"{top_n} provinsi teratas")
        t = d_sel.nlargest(top_n, "jumlah_miskin_ribu").sort_values("jumlah_miskin_ribu")
        fig = px.bar(t, x="jumlah_miskin_ribu", y="nama_provinsi", color="kelompok_pulau", orientation="h",
                     labels={"jumlah_miskin_ribu": "Ribu jiwa", "nama_provinsi": "", "kelompok_pulau": "Pulau"},
                     color_discrete_sequence=palet, height=520)
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), legend=dict(orientation="h", y=-0.12))
        st.plotly_chart(fig, width="stretch")

# ---------- Tab 2: Tren ----------
with tab_tren:
    st.subheader("Total per kelompok pulau")
    agg = d_all.groupby(["label_periode", "kelompok_pulau"], as_index=False)["jumlah_miskin_juta"].sum()
    fig = px.bar(agg, x="label_periode", y="jumlah_miskin_juta", color="kelompok_pulau", barmode="stack",
                 category_orders={"label_periode": periode_urut}, color_discrete_sequence=palet,
                 labels={"label_periode": "Periode", "jumlah_miskin_juta": "Juta jiwa", "kelompok_pulau": "Pulau"})
    st.plotly_chart(fig, width="stretch")

    st.subheader("Tren per provinsi")
    opsi = sorted(d_all["nama_provinsi"].unique())
    default = list(d_all[d_all["label_periode"] == periode_urut[0]].nlargest(5, "jumlah_miskin_ribu")["nama_provinsi"])
    pilih = st.multiselect("Provinsi", opsi, default=default)
    if pilih:
        fig = px.line(d_all[d_all["nama_provinsi"].isin(pilih)], x="label_periode", y="jumlah_miskin_ribu",
                      color="nama_provinsi", markers=True, category_orders={"label_periode": periode_urut},
                      labels={"label_periode": "Periode", "jumlah_miskin_ribu": "Ribu jiwa", "nama_provinsi": "Provinsi"},
                      color_discrete_sequence=palet)
        st.plotly_chart(fig, width="stretch")

# ---------- Tab 3: Perbandingan ----------
with tab_banding:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader(f"Komposisi — {periode}")
        fig = px.treemap(d_sel, path=[px.Constant("Indonesia"), "kelompok_pulau", "nama_provinsi"],
                         values="jumlah_miskin_ribu", color="kelompok_pulau", color_discrete_sequence=palet, height=480)
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, width="stretch")
    with c2:
        st.subheader("Perubahan Maret 2022 → Maret 2024")
        a = d_all[d_all["label_periode"] == "Maret 2022"].set_index("kode_provinsi")
        b = d_all[d_all["label_periode"] == "Maret 2024"].set_index("kode_provinsi")
        ch = a[["nama_provinsi", "jumlah_miskin_ribu", "terdampak_pemekaran"]].join(
            b[["jumlah_miskin_ribu"]], lsuffix="_2022", rsuffix="_2024", how="inner")
        ch = ch[ch["terdampak_pemekaran"] == 0]  # buang provinsi yang terdampak pemekaran Papua
        ch["perubahan_persen"] = (ch["jumlah_miskin_ribu_2024"] / ch["jumlah_miskin_ribu_2022"] - 1) * 100
        ch = ch.sort_values("perubahan_persen")
        fig = px.bar(ch, x="perubahan_persen", y="nama_provinsi", orientation="h", height=480,
                     color="perubahan_persen", color_continuous_scale="RdYlGn_r", color_continuous_midpoint=0,
                     labels={"perubahan_persen": "Perubahan (%)", "nama_provinsi": ""})
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False)
        st.plotly_chart(fig, width="stretch")
        st.caption("Provinsi terdampak pemekaran Papua dikecualikan agar perbandingan adil.")

    st.subheader("Heatmap provinsi × periode (ribu jiwa)")
    pv = d_all.pivot_table(index="nama_provinsi", columns="label_periode", values="jumlah_miskin_ribu")[periode_urut]
    pv = pv.loc[pv.max(axis=1).sort_values(ascending=False).index]
    fig = px.imshow(pv, aspect="auto", color_continuous_scale="Teal", height=max(420, 18 * len(pv)),
                    labels=dict(color="Ribu jiwa", x="Periode", y=""))
    st.plotly_chart(fig, width="stretch")

# ---------- Tab 4: Data ----------
with tab_data:
    st.subheader("Dataset hasil join (Pandas merge)")
    kolom = ["kode_provinsi", "nama_provinsi", "kelompok_pulau", "ibu_kota", "label_periode", "jumlah_miskin_ribu", "terdampak_pemekaran"]
    tampil = d_all[kolom].sort_values(["label_periode", "jumlah_miskin_ribu"], ascending=[True, False])
    cari = st.text_input("Cari provinsi")
    if cari:
        tampil = tampil[tampil["nama_provinsi"].str.contains(cari, case=False)]
    st.dataframe(tampil, width="stretch", hide_index=True)
    st.download_button("⬇️ Unduh CSV", tampil.to_csv(index=False).encode("utf-8"), "kemiskinan_provinsi_join.csv", "text/csv")

# ---------- Tab 5: Arsitektur ----------
with tab_arsitektur:
    st.subheader("Arsitektur & alur data")
    st.graphviz_chart("""
    digraph G {
      rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#E6F4F1", fontname="Helvetica"];
      csv  [label="CSV BPS\\n(OpenData Aceh)", fillcolor="#FFF4D6"];
      seed [label="seed_data.py"];
      pg   [label="DBMS 1: PostgreSQL\\nkemiskinan_provinsi (fakta)"];
      sq   [label="DBMS 2: SQLite\\nref_provinsi (referensi)"];
      pd   [label="Pandas\\nmerge(kode_provinsi)"];
      ui   [label="Streamlit + Plotly\\n(web live)", fillcolor="#DCEBFF"];
      csv -> seed; seed -> pg; seed -> sq; pg -> pd; sq -> pd; pd -> ui;
    }""")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("DBMS 1 (fakta)", meta["fact_engine"])
    m2.metric("Baris fakta", meta["rows_fakta"])
    m3.metric("DBMS 2 (referensi)", meta["ref_engine"])
    m4.metric("Baris referensi", meta["rows_ref"])
    st.caption(f"Hasil join: {meta['rows_join']} baris · baris tanpa pasangan: {meta['unmatched']}")
    st.markdown("**Query ke DBMS 1**")
    st.code(SQL_FAKTA, language="sql")
    st.markdown("**Query ke DBMS 2**")
    st.code(SQL_REF, language="sql")
    st.markdown("**Integrasi di Pandas**")
    st.code('fakta.merge(ref, on="kode_provinsi", how="left", validate="many_to_one", indicator=True)', language="python")
    st.markdown("**Sumber data**: [Jumlah Penduduk Miskin Menurut Provinsi di Indonesia — OpenData Aceh (BPS)]"
                "(https://data.acehprov.go.id/dataset/jumlah-penduduk-miskin/resource/79aa49bd-5691-46fa-85c8-1aad98bf6383) · lisensi CC BY")
