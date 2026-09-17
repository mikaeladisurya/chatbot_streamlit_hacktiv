"""Halaman 1 — Ringkasan.

Pertanyaan yang dijawab: seberapa besar mesin rekrutmen ini, seberapa selektif, dan
kapan tiap gelombang berjalan?

Revamp 2026-09-16: tunduk pada filter global. Jenis program dilipat jadi tiga
kelompok rekrutmen (Terbuka, Afirmasi, RBB) karena ketiganya punya peluang diterima
yang berbeda jauh: sekitar 2% untuk Terbuka, belasan persen untuk Afirmasi, dan
puluhan persen untuk RBB yang sudah disaring FHCI.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import grafik, ui
from core import metrics, theme
from core.db import TANGGAL_POTONG
from core.format import LABEL_TAHAP, angka, desimal, persen, rasio

ui.judul_halaman("Ringkasan")
f = ui.bar_filter()

r = metrics.ringkasan_f(f)
if not r["pendaftaran"]:
    ui.kosong()
    st.stop()

t = theme.token()
warna = theme.seri()
tren = metrics.tren_kelompok(f)

# ── Baris KPI ────────────────────────────────────────────────────────────────
ui.baris_kpi(
    [
        {
            "label": "Pendaftaran",
            "value": angka(r["pendaftaran"]),
            "help": "Jumlah lamaran masuk. Satu orang bisa melamar lebih dari sekali.",
        },
        {
            "label": "Pelamar unik",
            "value": angka(r["pelamar"]),
            "help": f"Rata-rata {desimal(r['pendaftaran'] / r['pelamar'], 2)} lamaran per orang.",
        },
        {
            "label": "Diterima",
            "value": angka(r["diterima"]),
            "help": "Lulus seluruh tahap seleksi.",
        },
        {
            "label": "Peluang diterima",
            "value": rasio(r["pendaftaran"] / r["diterima"]) if r["diterima"] else "-",
            "help": f"{persen(100 * r['diterima'] / r['pendaftaran'], 1)} pendaftaran berujung diterima.",
        },
        {
            "label": "SK terbit",
            "value": angka(r["sudah_sk"]),
            "help": "Diterima yang sudah menerima SK penempatan.",
        },
        {
            "label": "Sedang OJT",
            "value": angka(r["sedang_ojt"]),
            "help": (
                f"Masih menjalani on the job training per {TANGGAL_POTONG.strftime('%d %B %Y')}. "
                "Kelompok inilah selisih antara Diterima dan SK terbit."
            ),
        },
    ]
)

# ── Volume & konversi ───────────────────────────────────────────────────────
kiri, kanan = st.columns([3, 2], gap="medium")

with kiri:
    with ui.seksi(
        "Pendaftaran dan peluang per tahun",
        "Batang atas: jumlah pendaftaran per tahun program, ditumpuk menurut kelompok "
        "rekrutmen. Garis bawah: persentase pendaftaran yang diterima.\n\n"
        "**Terbuka** mencakup Reguler, Diaspora, S2, Bidang, dan Campus hiring. "
        "**Afirmasi** khusus putra-putri daerah. **RBB** adalah rekrutmen bersama BUMN yang "
        "kandidatnya sudah disaring FHCI sebelum masuk sistem PLN, sehingga peluangnya jauh "
        "lebih tinggi.",
    ):
        tren["peluang"] = (100 * tren["diterima"] / tren["pendaftaran"]).round(1)
        tren["teks_pendaftaran"] = tren["pendaftaran"].map(angka)
        x = alt.X("tahun:O", title=None, axis=alt.Axis(labelAngle=0))
        batang = (
            alt.Chart(tren)
            .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, stroke=t["surface_card"], strokeWidth=2)
            .encode(
                x=x,
                y=alt.Y("pendaftaran:Q", title=None, stack="zero", axis=alt.Axis(format="~s", tickCount=4)),
                color=grafik.warna_kelompok(),
                order=alt.Order("kelompok:N"),
                tooltip=[
                    alt.Tooltip("tahun:O", title="Tahun"),
                    alt.Tooltip("kelompok:N", title="Kelompok"),
                    alt.Tooltip("teks_pendaftaran:N", title="Pendaftaran"),
                ],
            )
            .properties(height=210)
        )
        garis = (
            alt.Chart(tren)
            .mark_line(point=alt.OverlayMarkDef(size=70, filled=True), strokeWidth=2)
            .encode(
                x=x,
                y=alt.Y("peluang:Q", title="Diterima (%)", axis=alt.Axis(tickCount=3)),
                color=grafik.warna_kelompok(legend=False),
                tooltip=[
                    alt.Tooltip("tahun:O", title="Tahun"),
                    alt.Tooltip("kelompok:N", title="Kelompok"),
                    alt.Tooltip("peluang:Q", title="Diterima (%)", format=".1f"),
                ],
            )
            .properties(height=110)
        )
        st.altair_chart(alt.vconcat(batang, garis, spacing=12).resolve_scale(x="shared"), width="stretch")

with kanan:
    funnel = metrics.funnel_seleksi(f).sort_values("urutan")
    tahap = [LABEL_TAHAP[k] for k in funnel["tahap_kode"]] + ["Diterima"]
    jumlah = funnel["masuk"].tolist() + [int(r["diterima"])]
    corong = go.Figure(
        go.Funnel(
            y=tahap,
            x=jumlah,
            texttemplate="%{value:,}<br>%{percentPrevious:.0%}",
            # Tahap kecil (< 12% tahap pertama) tak muat teks di dalam batang.
            textposition=["inside" if v >= 0.12 * jumlah[0] else "outside" for v in jumlah],
            insidetextfont=dict(size=12, color="#FFFFFF"),
            outsidetextfont=dict(size=11, color=t["text_secondary"]),
            marker=dict(color=[warna[0]] * (len(tahap) - 1) + [theme.STATUS["baik"]]),
            connector=dict(fillcolor=theme.rgba(warna[0], 0.12), line=dict(width=0)),
            hovertemplate="%{y}<br>%{value:,} orang<br>%{percentPrevious:.1%} dari tahap sebelumnya<extra></extra>",
        )
    )
    theme.plotly_layout(corong, height=344)
    corong.update_layout(separators=",.", yaxis=dict(tickfont=dict(size=12)))
    with ui.seksi(
        "Konversi tahap seleksi",
        "Lebar tiap batang adalah jumlah orang yang masuk tahap itu. Persen di dalam batang "
        "adalah porsi yang tersisa dari tahap sebelumnya.\n\nBatang hijau terakhir adalah "
        "yang diterima. Jalur RBB masuk langsung di Akademik & Inggris, sehingga batang "
        "Akademik bisa lebih lebar dari lulusan Adaptif.",
    ):
        st.plotly_chart(corong, width="stretch", config={"displayModeBar": False})

# ── Kalender gelombang ──────────────────────────────────────────────────────
kalender = metrics.kalender_gelombang(f)
kalender["jenis"] = kalender["jenis_program"].map(ui.LABEL_JENIS).fillna(kalender["jenis_program"])
kalender["urut"] = kalender.groupby(["tahun", "jenis_program"]).cumcount() + 1
kalender["jumlah_sejenis"] = kalender.groupby(["tahun", "jenis_program"])["gelombang_id"].transform("count")
kalender["label"] = kalender.apply(
    lambda b: f"{b.tahun} {b.jenis}" + (f" {b.urut}" if b.jumlah_sejenis > 1 else ""), axis=1
)
kalender["teks_pendaftaran"] = kalender["pendaftaran"].map(angka)
kalender["teks_diterima"] = kalender["diterima"].map(angka)
kalender["teks_peluang"] = kalender["pct_diterima"].map(lambda v: persen(v, 1))

with ui.seksi(
    "Kalender gelombang rekrutmen",
    "Tiap baris satu gelombang. Batang pekat adalah masa pendaftaran dibuka, batang pucat "
    "berlanjut sampai tes terakhir gelombang itu. Besar titik di ujung sebanding dengan "
    "jumlah yang diterima, angka di sebelahnya adalah peluang diterima.\n\nGaris putus-putus "
    "adalah tanggal potong data.",
):
    urutan = kalender["label"].tolist()
    y = alt.Y("label:N", sort=urutan, title=None, axis=alt.Axis(labelLimit=180, ticks=False, domain=False))
    tooltip = [
        alt.Tooltip("nama_gelombang:N", title="Gelombang"),
        alt.Tooltip("tgl_buka:T", title="Dibuka", format="%d %b %Y"),
        alt.Tooltip("tgl_tutup:T", title="Ditutup", format="%d %b %Y"),
        alt.Tooltip("tes_terakhir:T", title="Tes terakhir", format="%d %b %Y"),
        alt.Tooltip("teks_pendaftaran:N", title="Pendaftaran"),
        alt.Tooltip("teks_diterima:N", title="Diterima"),
        alt.Tooltip("teks_peluang:N", title="Peluang"),
    ]
    dasar = alt.Chart(kalender)
    proses = dasar.mark_bar(height=8, cornerRadius=4, opacity=0.3).encode(
        y=y,
        x=alt.X("tgl_buka:T", title=None, axis=alt.Axis(format="%Y", tickCount="year", grid=True)),
        x2="tes_terakhir:T",
        color=grafik.warna_kelompok(),
        tooltip=tooltip,
    )
    buka = dasar.mark_bar(height=8, cornerRadius=4).encode(
        y=y, x="tgl_buka:T", x2="tgl_tutup:T", color=grafik.warna_kelompok(legend=False), tooltip=tooltip
    )
    titik = dasar.mark_circle(opacity=1, stroke=t["surface_card"], strokeWidth=2).encode(
        y=y,
        x="tes_terakhir:T",
        size=alt.Size("diterima:Q", legend=None, scale=alt.Scale(range=[40, 500])),
        color=grafik.warna_kelompok(legend=False),
        tooltip=tooltip,
    )
    teks = dasar.mark_text(align="left", dx=14, fontSize=11, color=t["text_secondary"]).encode(
        y=y, x="tes_terakhir:T", text="teks_peluang:N"
    )
    hari_ini = (
        alt.Chart(pd.DataFrame({"tanggal": [pd.Timestamp(TANGGAL_POTONG)]}))
        .mark_rule(strokeDash=[4, 4], color=t["text_muted"])
        .encode(x="tanggal:T")
    )
    st.altair_chart(
        (proses + buka + titik + teks + hari_ini).properties(height=max(26 * len(kalender), 140)),
        width="stretch",
    )

# ── Peluang per gelombang & status kohort ───────────────────────────────────
kiri, kanan = st.columns(2, gap="medium")

with kiri:
    with ui.seksi(
        "Pendaftar dan peluang per gelombang",
        "Tiap titik satu gelombang. Makin ke kanan makin banyak pendaftar (skala logaritmik), "
        "makin ke atas makin besar peluang diterima. Besar titik sebanding dengan jumlah "
        "yang diterima.\n\nWarna titik menandai kelompok rekrutmennya, jadi posisi tiap "
        "kelompok pada kedua sumbu bisa dibandingkan langsung.",
    ):
        # Satu label per kelompok (gelombang dengan diterima terbanyak) supaya label tidak bertumpuk.
        label_titik = kalender.loc[kalender.groupby("kelompok")["diterima"].idxmax()]
        x = alt.X("pendaftaran:Q", title="Pendaftar", scale=alt.Scale(type="log"), axis=alt.Axis(format="~s"))
        y = alt.Y("pct_diterima:Q", title="Diterima (%)")
        sebar = (
            alt.Chart(kalender)
            .mark_circle(opacity=0.9, stroke=t["surface_card"], strokeWidth=1.5)
            .encode(
                x=x,
                y=y,
                size=alt.Size("diterima:Q", legend=None, scale=alt.Scale(range=[40, 600])),
                color=grafik.warna_kelompok(),
                tooltip=[
                    alt.Tooltip("nama_gelombang:N", title="Gelombang"),
                    alt.Tooltip("teks_pendaftaran:N", title="Pendaftaran"),
                    alt.Tooltip("teks_diterima:N", title="Diterima"),
                    alt.Tooltip("teks_peluang:N", title="Peluang"),
                ],
            )
        )
        teks = alt.Chart(label_titik).mark_text(align="left", dx=10, dy=-8, fontSize=11, color=t["text_secondary"]).encode(
            x=x, y=y, text="label:N"
        )
        st.altair_chart((sebar + teks).properties(height=300), width="stretch")

with kanan:
    status = metrics.status_kohort(f)
    status["teks"] = status["n"].map(angka)
    with ui.seksi(
        "Status diterima per tahun",
        "Jumlah yang diterima per tahun program dan posisinya pada tanggal potong: sudah "
        "menerima SK penempatan, atau masih menjalani OJT.",
    ):
        if status.empty:
            ui.kosong()
        else:
            st.altair_chart(
                alt.Chart(status)
                .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, stroke=t["surface_card"], strokeWidth=2)
                .encode(
                    x=alt.X("tahun:O", title=None, axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("n:Q", title=None, stack="zero", axis=alt.Axis(format="~s", tickCount=4)),
                    color=alt.Color(
                        "status:N",
                        scale=alt.Scale(domain=["SK terbit", "Sedang OJT"], range=[warna[0], theme.STATUS["peringatan"]]),
                        legend=alt.Legend(title=None, orient="top"),
                    ),
                    tooltip=[
                        alt.Tooltip("tahun:O", title="Tahun"),
                        alt.Tooltip("status:N", title="Status"),
                        alt.Tooltip("teks:N", title="Orang"),
                    ],
                )
                .properties(height=300),
                width="stretch",
            )

# ── Lapis analis ─────────────────────────────────────────────────────────────
if ui.mode_analis():
    ui.lapis_analis(
        kalender[["tahun", "nama_gelombang", "jenis_program", "tgl_buka", "tgl_tutup", "tes_terakhir", "pendaftaran", "diterima", "pct_diterima"]],
        "ringkasan_per_gelombang.csv",
        "Ringkasan per gelombang",
    )
