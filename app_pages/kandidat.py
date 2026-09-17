"""Halaman 4 — Kandidat & Pasar Tenaga Kerja.

Pertanyaan yang dijawab: siapa yang melamar, dari mana mereka dites, dan ciri apa
yang membedakan yang diterima?

Revamp 2026-09-16: tunduk pada filter global. Kolom asal kandidat (`kota_domisili`,
`kota_asal`, `sekolah_universitas`) tetap TIDAK dipakai karena dibagikan acak seragam
oleh generator (mockdb/ISSUES_SEBARAN.md). Peta memakai `lokasi_kota` tes offline.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import ui
from core import metrics, theme
from core.format import angka, desimal, persen

ui.judul_halaman("Kandidat")
f = ui.bar_filter()

ringkas = metrics.pelamar_ringkas(f)
if not ringkas["pelamar"]:
    ui.kosong()
    st.stop()

t = theme.token()
warna = theme.seri()
akun = metrics.akun_ringkas()
kelengkapan = metrics.kelengkapan_akun()

# ── Baris KPI ────────────────────────────────────────────────────────────────
ui.baris_kpi(
    [
        {"label": "Pelamar unik", "value": angka(ringkas["pelamar"])},
        {
            "label": "Lamaran per pelamar",
            "value": desimal(ringkas["lamaran"] / ringkas["pelamar"], 2),
        },
        {
            "label": "Melamar lebih dari setahun",
            "value": persen(100 * ringkas["berulang"] / ringkas["pelamar"]),
            "help": f"{angka(ringkas['berulang'])} pelamar mencoba lagi di tahun program berbeda.",
        },
        {
            "label": "Akun tanpa lamaran",
            "value": angka(akun["tidak_melamar"]),
            "help": "Membuat akun tapi belum pernah melamar. Seluruh akun, tidak terpengaruh filter.",
        },
        {
            "label": "Profil lengkap dan aktif",
            "value": angka(kelengkapan["lengkap_dan_aktif"]),
            "help": "Surel teraktivasi dan alamat domisili terisi. Seluruh akun, tidak terpengaruh filter.",
        },
    ]
)

# ── Peta & pelamar berulang ─────────────────────────────────────────────────
kiri, kanan = st.columns([3, 2], gap="medium")

with kiri:
    kota = metrics.kota_tes_geo(f)
    with ui.seksi(
        "Volume dan tingkat lulus per kota tes",
        "Tiap lingkaran satu kota tempat tes offline (Psikologi, Fisik & MCU, Wawancara). "
        "Besar lingkaran sebanding dengan jumlah tes, warna menunjukkan persentase peserta "
        "hadir yang lulus: makin gelap makin tinggi.\n\nKoordinat adalah titik tengah kota, "
        "bukan alamat lokasi tes.",
    ):
        if kota.empty:
            ui.kosong("Tidak ada tes offline untuk kombinasi filter ini.")
        else:
            teratas = kota.nlargest(6, "n")
            kota["teks"] = kota.apply(lambda b: f"{b.lokasi_kota}<br>{angka(b.n)} tes, lulus {persen(b.pct_lulus)}", axis=1)
            lo, hi = float(kota["pct_lulus"].min()), float(kota["pct_lulus"].max())
            skala_warna = [[i / (len(theme.RAMP) - 1), c] for i, c in enumerate(theme.RAMP)]
            peta = go.Figure()
            peta.add_trace(
                go.Scattergeo(
                    lat=kota["lat"],
                    lon=kota["lon"],
                    mode="markers",
                    marker=dict(
                        size=kota["n"],
                        sizemode="area",
                        sizeref=2.0 * kota["n"].max() / (38.0**2),
                        sizemin=4,
                        color=kota["pct_lulus"],
                        colorscale=skala_warna,
                        cmin=lo,
                        cmax=hi,
                        opacity=0.9,
                        line=dict(width=1, color=t["surface_card"]),
                        colorbar=dict(
                            title=dict(text="Lulus %", font=dict(size=11)),
                            thickness=10,
                            len=0.6,
                            x=1.0,
                            tickfont=dict(size=10),
                            outlinewidth=0,
                        ),
                    ),
                    text=kota["teks"],
                    hovertemplate="%{text}<extra></extra>",
                    showlegend=False,
                )
            )
            peta.add_trace(
                go.Scattergeo(
                    lat=teratas["lat"],
                    lon=teratas["lon"],
                    mode="text",
                    text=teratas["lokasi_kota"],
                    textposition="top center",
                    textfont=dict(size=11, color=t["text_primary"]),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )
            peta.update_geos(
                # fitbounds memusatkan & memperbesar peta ke kota yang ada, jadi tidak ada
                # ruang kosong di luar Indonesia saat filter mengurangi jumlah kota.
                fitbounds="locations",
                showframe=False,
                showland=True,
                landcolor=t["border"],
                showcountries=False,
                showcoastlines=False,
                showocean=True,
                oceancolor=t["surface_card"],
                showlakes=False,
                bgcolor="rgba(0,0,0,0)",
            )
            theme.plotly_layout(peta, height=330)
            st.plotly_chart(peta, width="stretch", config={"displayModeBar": False})

with kanan:
    ulang = metrics.peluang_per_tahun_melamar(f)
    with ui.seksi(
        "Peluang menurut lama mencoba",
        "Pelamar dikelompokkan menurut jumlah tahun program berbeda tempat mereka melamar. "
        "Tinggi batang adalah persentase yang akhirnya pernah diterima.\n\nAngka ini "
        "menggambarkan kegigihan, bukan sebab-akibat: pelamar yang mencoba lagi biasanya "
        "sudah lolos lebih jauh di percobaan sebelumnya.",
    ):
        if ulang.empty:
            ui.kosong()
        else:
            ulang["label"] = ulang["tahun"].map(lambda v: f"{v} tahun")
            ulang["teks_pct"] = ulang["pct"].map(lambda v: persen(v))
            ulang["teks_pelamar"] = ulang["pelamar"].map(angka)
            x = alt.X("label:N", title=None, sort=None, axis=alt.Axis(labelAngle=0))
            y = alt.Y("pct:Q", title="Pernah diterima (%)", scale=alt.Scale(domain=[0, max(float(ulang["pct"].max()) * 1.2, 5)]))
            batang = alt.Chart(ulang).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color=warna[0], width={"band": 0.6}).encode(
                x=x,
                y=y,
                tooltip=[
                    alt.Tooltip("label:N", title="Melamar"),
                    alt.Tooltip("teks_pelamar:N", title="Pelamar"),
                    alt.Tooltip("teks_pct:N", title="Pernah diterima"),
                ],
            )
            teks = alt.Chart(ulang).mark_text(dy=-9, fontSize=13, fontWeight=600, color=t["text_primary"]).encode(x=x, y=y, text="teks_pct:N")
            jumlah = alt.Chart(ulang).mark_text(dy=14, fontSize=10, color="#FFFFFF").encode(
                x=x, y=alt.value(0), text="teks_pelamar:N"
            )
            st.altair_chart((batang + teks).properties(height=318), width="stretch")

# ── Ciri yang membedakan ────────────────────────────────────────────────────
kiri, kanan = st.columns(2, gap="medium")

with kiri:
    ipk = metrics.peluang_per_ipk(f)
    with ui.seksi(
        "Peluang diterima menurut IPK",
        "Persentase pendaftaran yang diterima per rentang IPK 0,25 (pendidikan terakhir). "
        "Garis putus-putus menandai IPK 3,00, ambang minimum yang paling sering dipakai "
        "lowongan.\n\nRentang dengan kurang dari 30 pendaftaran tidak ditampilkan.",
    ):
        if ipk.empty:
            ui.kosong()
        else:
            ipk["teks_ipk"] = ipk["ipk"].map(lambda v: f"{desimal(v, 2)} sampai {desimal(v + 0.25, 2)}")
            ipk["teks_pct"] = ipk["pct"].map(lambda v: persen(v, 2))
            ipk["teks_n"] = ipk["pendaftaran"].map(angka)
            x = alt.X("ipk:Q", title="IPK", scale=alt.Scale(domain=[2.0, 4.0]), axis=alt.Axis(values=[2.0, 2.5, 3.0, 3.5, 4.0], format=".2f"))
            y = alt.Y("pct:Q", title="Diterima (%)")
            tooltip = [
                alt.Tooltip("teks_ipk:N", title="IPK"),
                alt.Tooltip("teks_n:N", title="Pendaftaran"),
                alt.Tooltip("teks_pct:N", title="Diterima"),
            ]
            area = alt.Chart(ipk).mark_area(color=warna[0], opacity=0.15, interpolate="step-after").encode(x=x, y=y)
            garis = alt.Chart(ipk).mark_line(color=warna[0], strokeWidth=2, interpolate="step-after").encode(x=x, y=y)
            titik = alt.Chart(ipk).mark_circle(color=warna[0], size=70, opacity=1).encode(x=x, y=y, tooltip=tooltip)
            ambang = alt.Chart(pd.DataFrame({"x": [3.0]})).mark_rule(strokeDash=[4, 3], color=t["text_secondary"]).encode(x="x:Q")
            st.altair_chart((area + garis + titik + ambang).properties(height=280), width="stretch")

with kanan:
    rumpun = metrics.rumpun_f(f)
    with ui.seksi(
        "Volume dan peluang per rumpun jurusan",
        "Tiap titik satu rumpun jurusan. Makin ke kanan makin banyak pendaftaran, makin ke "
        "atas makin besar peluang diterima. Garis putus-putus adalah rata-rata semua rumpun.",
    ):
        if rumpun.empty:
            ui.kosong()
        else:
            rata = 100 * rumpun["diterima"].sum() / rumpun["melamar"].sum()
            rumpun["teks_pct"] = rumpun["pct"].map(lambda v: persen(v, 2))
            rumpun["teks_n"] = rumpun["melamar"].map(angka)
            diberi_label = pd.concat([rumpun.nlargest(2, "melamar"), rumpun.nlargest(1, "pct"), rumpun.nsmallest(1, "pct")]).drop_duplicates("rumpun")
            # Label titik di sisi kanan chart dirata kanan supaya tidak terpotong tepi.
            kanan_chart = diberi_label["melamar"] > 0.6 * rumpun["melamar"].max()
            x = alt.X("melamar:Q", title="Pendaftaran", axis=alt.Axis(format="~s"))
            y = alt.Y("pct:Q", title="Diterima (%)", scale=alt.Scale(zero=False, padding=12))
            titik = alt.Chart(rumpun).mark_circle(color=warna[0], size=110, opacity=0.85, stroke=t["surface_card"], strokeWidth=1.5).encode(
                x=x,
                y=y,
                tooltip=[
                    alt.Tooltip("rumpun:N", title="Rumpun"),
                    alt.Tooltip("teks_n:N", title="Pendaftaran"),
                    alt.Tooltip("teks_pct:N", title="Diterima"),
                ],
            )
            teks = alt.Chart(diberi_label[~kanan_chart]).mark_text(
                align="left", dx=8, dy=-8, fontSize=11, color=t["text_secondary"]
            ).encode(x=x, y=y, text="rumpun:N") + alt.Chart(diberi_label[kanan_chart]).mark_text(
                align="right", dx=-8, dy=-8, fontSize=11, color=t["text_secondary"]
            ).encode(x=x, y=y, text="rumpun:N")
            garis_rata = alt.Chart(pd.DataFrame({"y": [rata]})).mark_rule(strokeDash=[4, 3], color=t["text_muted"]).encode(y="y:Q")
            st.altair_chart((garis_rata + titik + teks).properties(height=280), width="stretch")

# ── Profil & waktu ──────────────────────────────────────────────────────────
kiri, kanan = st.columns(2, gap="medium")

with kiri:
    piramida = metrics.umur_gender_f(f)
    with ui.seksi(
        "Umur dan gender pelamar",
        "Piramida umur saat membuat akun. Batang ke kiri pria, ke kanan wanita. Panjang batang "
        "adalah jumlah pelamar pada umur itu.",
    ):
        if piramida.empty:
            ui.kosong()
        else:
            piramida["gender"] = piramida["jenis_kelamin"].map({"P": "Pria", "W": "Wanita"})
            piramida["nilai"] = piramida["n"].where(piramida["jenis_kelamin"] == "W", -piramida["n"])
            piramida["teks"] = piramida["n"].map(angka)
            batas = int(piramida["n"].max() * 1.1)
            st.altair_chart(
                alt.Chart(piramida)
                .mark_bar(height=7, cornerRadius=2)
                .encode(
                    y=alt.Y("umur:O", sort="descending", title=None, axis=alt.Axis(values=list(range(20, 40, 2)), ticks=False, domain=False)),
                    x=alt.X("nilai:Q", title=None, scale=alt.Scale(domain=[-batas, batas]), axis=alt.Axis(labelExpr="format(abs(datum.value), '~s')")),
                    color=alt.Color(
                        "gender:N",
                        scale=alt.Scale(domain=["Pria", "Wanita"], range=warna[:2]),
                        legend=alt.Legend(title=None, orient="top"),
                    ),
                    tooltip=[
                        alt.Tooltip("umur:O", title="Umur"),
                        alt.Tooltip("gender:N", title="Gender"),
                        alt.Tooltip("teks:N", title="Pelamar"),
                    ],
                )
                .properties(height=280),
                width="stretch",
            )

with kanan:
    bulanan = metrics.pendaftar_per_bulan_f(f)
    bulanan["teks"] = bulanan["n"].map(angka)
    with ui.seksi(
        "Pendaftaran per bulan",
        "Jumlah lamaran masuk tiap bulan. Lonjakan bertepatan dengan pembukaan gelombang, "
        "diselingi bulan tanpa pendaftaran sama sekali.",
    ):
        st.altair_chart(
            alt.Chart(bulanan)
            .mark_area(color=warna[0], opacity=0.85, line=dict(color=warna[0], strokeWidth=1.5), interpolate="step-after")
            .encode(
                x=alt.X("bulan:T", title=None, axis=alt.Axis(format="%Y", tickCount="year")),
                y=alt.Y("n:Q", title=None, axis=alt.Axis(format="~s", tickCount=4)),
                tooltip=[alt.Tooltip("bulan:T", title="Bulan", format="%b %Y"), alt.Tooltip("teks:N", title="Pendaftaran")],
            )
            .properties(height=280),
            width="stretch",
        )

# ── Lapis analis ─────────────────────────────────────────────────────────────
if ui.mode_analis():
    ui.lapis_analis(rumpun, "rumpun_melamar_vs_diterima.csv", "Rumpun jurusan: melamar vs diterima")
