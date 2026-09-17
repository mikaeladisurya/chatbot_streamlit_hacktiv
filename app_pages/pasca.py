"""Halaman 5 — Pasca-Seleksi & OJT.

Pertanyaan yang dijawab: setelah dinyatakan diterima, di mana orang-orang itu sekarang,
dan berapa lama jalan mereka sampai SK?

Revamp 2026-09-16: tunduk pada filter global. Durasi tiap tahap digenerate hampir
konstan (OJT 180 hari), jadi halaman ini menampilkan posisi & tonggak waktu, bukan
analisis SLA atau hambatan.
"""

from __future__ import annotations

import altair as alt
import streamlit as st

from components import ui
from core import metrics, theme
from core.db import TANGGAL_POTONG
from core.format import angka

LABEL_PASCA = {
    "pengumuman_akhir": "Pengumuman",
    "ttd_kontrak": "Kontrak",
    "samapta": "Samapta",
    "pembidangan": "Pembidangan",
    "ojt": "OJT",
    "ujian_ojt": "Ujian OJT",
    "sk_penempatan": "SK penempatan",
}

ui.judul_halaman("Pasca-seleksi dan OJT")
f = ui.bar_filter()

pipeline = metrics.pipeline_f(f)
if pipeline.empty:
    ui.kosong()
    st.stop()

t = theme.token()
warna = theme.seri()
p = pipeline.set_index("tahap_kode")
updl = metrics.updl_f(f)
hari_ojt = metrics.durasi_ojt(f)


def ambil(kode: str, kolom: str) -> int:
    return int(p.loc[kode, kolom]) if kode in p.index else 0


# ── Baris KPI ────────────────────────────────────────────────────────────────
ui.baris_kpi(
    [
        {"label": "Diterima", "value": angka(ambil("pengumuman_akhir", "total"))},
        {
            "label": "Sedang OJT",
            "value": angka(ambil("ojt", "berjalan")),
            "help": f"Masih menjalani OJT per {TANGGAL_POTONG.strftime('%d %B %Y')}.",
        },
        {"label": "SK terbit", "value": angka(ambil("sk_penempatan", "selesai"))},
        {"label": "UPDL dipakai", "value": angka(len(updl)), "help": "Unit pendidikan dan pelatihan tempat OJT."},
        {"label": "Lama OJT", "value": f"{angka(hari_ojt)} hari", "help": "Median hari dari mulai sampai selesai OJT."},
    ]
)

# ── Jeda antar tahap ────────────────────────────────────────────────────────
# Menggantikan "rantai tahap" lama (tujuh batang nyaris sama tinggi): semua yang
# diterima melewati semua tahap, jadi jumlah orang per tahap tidak membedakan apa pun.
# Yang berbeda adalah lama jedanya. Temuan audit 2026-09-16.
jeda = metrics.jeda_pasca_tahap(f)

with ui.seksi(
    "Jeda antar tahap setelah diterima",
    "Median jumlah hari dari tahap sebelumnya sampai tahap itu dimulai, diurutkan dari "
    "yang paling lama. Jumlahkan seluruh batang untuk mendapat lama perjalanan dari "
    "pengumuman diterima sampai SK penempatan.\n\nYang diukur adalah jarak ke tanggal MULAI "
    "tahap, jadi lamanya OJT sendiri muncul sebagai jeda sebelum Ujian OJT, bukan pada batang "
    "OJT.\n\nJadwal tahap **dimodelkan** dan hampir "
    "sama untuk semua kohort, jadi grafik ini menggambarkan jadwal baku satu kohort, bukan "
    "perbedaan antar kohort atau keterlambatan.",
):
    if jeda.empty:
        ui.kosong()
    else:
        jeda["tahap"] = jeda["tahap_kode"].map(LABEL_PASCA)
        jeda["teks"] = jeda["jeda_hari"].map(lambda v: f"{angka(v)} hari")
        y = alt.Y("tahap:N", sort="-x", title=None, axis=alt.Axis(ticks=False, domain=False))
        x = alt.X(
            "jeda_hari:Q",
            title="Hari",
            scale=alt.Scale(domain=[0, float(jeda["jeda_hari"].max()) * 1.18]),
            axis=alt.Axis(tickCount=5),
        )
        batang = alt.Chart(jeda).mark_bar(color=warna[0], height=22, cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
            y=y,
            x=x,
            tooltip=[
                alt.Tooltip("tahap:N", title="Tahap"),
                alt.Tooltip("teks:N", title="Jeda dari tahap sebelumnya"),
                alt.Tooltip("n:Q", title="Orang", format=",.0f"),
            ],
        )
        label = alt.Chart(jeda).mark_text(align="left", dx=6, fontSize=12, color=t["text_secondary"]).encode(
            y=y, x=x, text="teks:N"
        )
        st.altair_chart((batang + label).properties(height=32 * len(jeda) + 40), width="stretch")

# ── Tonggak waktu & UPDL ────────────────────────────────────────────────────
kiri, kanan = st.columns([3, 2], gap="medium")

with kiri:
    tonggak = metrics.tonggak_kohort(f)
    with ui.seksi(
        "Tonggak waktu per kohort",
        "Tiap baris satu tahun program. Tiga titik adalah median tanggal pengumuman diterima, "
        "mulai OJT, dan SK penempatan. Panjang garis adalah lama perjalanan dari pengumuman "
        "sampai SK.\n\nKohort yang belum punya titik SK masih menjalani OJT.",
    ):
        if tonggak.empty:
            ui.kosong()
        else:
            nama_tonggak = {"pengumuman_akhir": "Pengumuman", "ojt": "Mulai OJT", "sk_penempatan": "SK penempatan"}
            tonggak["tonggak"] = tonggak["tahap_kode"].map(nama_tonggak)
            jarak = tonggak.groupby("tahun")["tanggal"].agg(["min", "max"]).reset_index()
            y = alt.Y("tahun:O", title=None, axis=alt.Axis(ticks=False, domain=False))
            garis = alt.Chart(jarak).mark_rule(color=t["netral"], strokeWidth=3).encode(
                y=y, x=alt.X("min:T", title=None, axis=alt.Axis(format="%Y", tickCount="year")), x2="max:T"
            )
            titik = alt.Chart(tonggak).mark_circle(size=140, opacity=1, stroke=t["surface_card"], strokeWidth=2).encode(
                y=y,
                x="tanggal:T",
                color=alt.Color(
                    "tonggak:N",
                    scale=alt.Scale(domain=list(nama_tonggak.values()), range=warna[:3]),
                    legend=alt.Legend(title=None, orient="top"),
                ),
                tooltip=[
                    alt.Tooltip("tahun:O", title="Tahun program"),
                    alt.Tooltip("tonggak:N", title="Tonggak"),
                    alt.Tooltip("tanggal:T", title="Median tanggal", format="%d %b %Y"),
                ],
            )
            st.altair_chart((garis + titik).properties(height=max(40 * tonggak["tahun"].nunique(), 140)), width="stretch")

with kanan:
    with ui.seksi(
        "Peserta per UPDL",
        "Jumlah orang yang ditempatkan untuk pendidikan dan OJT di tiap Unit Pelaksana "
        "Pendidikan dan Latihan (UPDL).",
    ):
        if updl.empty:
            ui.kosong()
        else:
            updl["label"] = updl["updl"].str.replace("UPDL ", "", regex=False)
            updl["teks"] = updl["n"].map(angka)
            y = alt.Y("label:N", sort="-x", title=None, axis=alt.Axis(ticks=False, domain=False))
            x = alt.X("n:Q", title=None, axis=None, scale=alt.Scale(domain=[0, float(updl["n"].max()) * 1.18]))
            batang = alt.Chart(updl).mark_bar(color=warna[0], height=3).encode(y=y, x=x)
            ujung = alt.Chart(updl).mark_circle(color=warna[0], size=90, opacity=1).encode(
                y=y, x=x, tooltip=[alt.Tooltip("updl:N", title="UPDL"), alt.Tooltip("teks:N", title="Orang")]
            )
            teks = alt.Chart(updl).mark_text(align="left", dx=9, fontSize=11, color=t["text_secondary"]).encode(y=y, x=x, text="teks:N")
            st.altair_chart((batang + ujung + teks).properties(height=max(26 * len(updl), 140)), width="stretch")

# ── Lapis analis ─────────────────────────────────────────────────────────────
if ui.mode_analis():
    ui.lapis_analis(updl[["updl", "n"]], "sebaran_updl.csv", "Sebaran penempatan per UPDL")
