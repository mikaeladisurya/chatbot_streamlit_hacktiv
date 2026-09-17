"""Halaman 3 — Tahapan Seleksi.

Pertanyaan yang dijawab: di tahap mana kandidat berguguran, kenapa, dan apakah
polanya berubah antar kohort?

Revamp 2026-09-16: satu halaman dashboard penuh yang tunduk pada filter global.
Urutan seksi mengikuti alur baca manajemen: berapa yang lolos (KPI), lewat mana
mereka keluar (Sankey), kapan pola itu berubah (heatmap + kehadiran), lalu apa
yang menggerakkannya (skor, waktu, vendor, alasan administrasi).
"""

from __future__ import annotations

import altair as alt
import plotly.graph_objects as go
import streamlit as st

from components import ui
from core import metrics, theme
from core.format import LABEL_TAHAP, URUTAN_TAHAP, angka, persen, rasio

ui.judul_halaman("Tahapan seleksi")
f = ui.bar_filter()

hasil = metrics.hasil_seleksi(f)
funnel = metrics.funnel_seleksi(f)

if not hasil["pendaftaran"]:
    ui.kosong()
    st.stop()

warna = theme.seri()
t = theme.token()
no_show_mode = metrics.no_show_tahun_mode(f)
durasi = metrics.durasi_tahap(f)

# ── Baris KPI ────────────────────────────────────────────────────────────────
terjadwal_online = no_show_mode.loc[no_show_mode["mode"] == "online"]
pct_online = (
    (terjadwal_online["pct_no_show"] * terjadwal_online["terjadwal"]).sum()
    / terjadwal_online["terjadwal"].sum()
    if not terjadwal_online.empty
    else None
)
hari_wawancara = durasi.loc[durasi["tahap_kode"] == "wawancara", "median"]

ui.baris_kpi(
    [
        {
            "label": "Pendaftaran",
            "value": angka(hasil["pendaftaran"]),
            "help": f"{angka(hasil['masuk_rbb'])} di antaranya jalur RBB, masuk langsung di tahap Akademik.",
        },
        {"label": "Diterima", "value": angka(hasil["diterima"])},
        {
            "label": "Peluang diterima",
            "value": rasio(hasil["pendaftaran"] / hasil["diterima"]) if hasil["diterima"] else "-",
            "help": f"{persen(100 * hasil['diterima'] / hasil['pendaftaran'], 1)} pendaftaran berujung diterima.",
        },
        {
            "label": "Tidak hadir tes online",
            "value": persen(pct_online),
            "help": "Porsi peserta terjadwal yang tidak hadir di tes online (Adaptif dan Akademik).",
        },
        {
            "label": "Melamar sampai wawancara",
            "value": f"{angka(hari_wawancara.iloc[0])} hari" if not hari_wawancara.empty else "-",
            "help": "Median hari dari tanggal melamar sampai jadwal wawancara.",
        },
    ]
)

# ── Sankey alur gugur ───────────────────────────────────────────────────────
# Tiap tahap punya node gugur SENDIRI, sejajar dengan tahap berikutnya, dipecah dua
# sebab: "Gugur X" (hadir tapi tidak lulus) dan "Tidak hadir X". Administrasi hanya
# punya "Gugur" karena seleksi dokumen tanpa kehadiran. Jalur RBB masuk langsung di
# Akademik & Inggris. Filter bisa menghilangkan tahap, jadi node & kolom dibangun dari
# data, bukan daftar tetap.
fu = funnel.set_index("tahap_kode")


def nilai(kode: str, kolom: str) -> int:
    return int(fu.loc[kode, kolom]) if kode in fu.index else 0


URUTAN_KODE = list(LABEL_TAHAP)
alur: list[tuple[str, str, int, str]] = []  # (asal, tujuan, nilai, jenis)
if "administrasi" in fu.index:
    alur.append(("Pendaftaran", "Administrasi", nilai("administrasi", "masuk"), "lulus"))
masuk_rbb = int(hasil["masuk_rbb"])
if masuk_rbb:
    alur.append(("Pendaftaran", "Akademik & Inggris", masuk_rbb, "lulus"))

for i, kode in enumerate(URUTAN_KODE):
    if kode not in fu.index:
        continue
    nama = LABEL_TAHAP[kode]
    berikut = LABEL_TAHAP[URUTAN_KODE[i + 1]] if i + 1 < len(URUTAN_KODE) else "Diterima"
    alur.append((nama, berikut, nilai(kode, "lulus"), "lulus"))
    if kode == "administrasi":
        alur.append((nama, f"Gugur {nama}", nilai(kode, "masuk") - nilai(kode, "lulus"), "gugur"))
    else:
        alur.append((nama, f"Gugur {nama}", nilai(kode, "hadir") - nilai(kode, "lulus"), "gugur"))
        alur.append((nama, f"Tidak hadir {nama}", nilai(kode, "masuk") - nilai(kode, "hadir"), "absen"))
alur = [a for a in alur if a[2] > 0]

# Kolom tiap node: tahap utama menurut urutannya, node gugur sejajar tahap berikutnya.
kolom_utama = {"Pendaftaran": 0, **{LABEL_TAHAP[k]: i + 1 for i, k in enumerate(URUTAN_KODE)}, "Diterima": 7}
node_nama: list[str] = []
for asal, tujuan, _v, _j in alur:
    for n in (asal, tujuan):
        if n not in node_nama:
            node_nama.append(n)


def kolom_node(n: str) -> int:
    if n in kolom_utama:
        return kolom_utama[n]
    induk = n.removeprefix("Gugur ").removeprefix("Tidak hadir ")
    return kolom_utama[induk] + 1


def jenis_node(n: str) -> str:
    if n.startswith("Gugur "):
        return "gugur"
    if n.startswith("Tidak hadir "):
        return "absen"
    return "lulus"


# Rapatkan kolom yang terpakai supaya filter RBB tidak menyisakan celah kosong di kiri.
# Celah kolom terakhir dilebarkan: Plotly menaruh label kolom paling kanan di sisi KIRI
# node, jadi tanpa ruang ekstra label "Diterima" menabrak label "Wawancara".
kolom_terpakai = sorted({kolom_node(n) for n in node_nama})
langkah = [1.0] * (len(kolom_terpakai) - 1)
if langkah:
    langkah[-1] = 1.5
kumulatif = [0.0]
for l in langkah:
    kumulatif.append(kumulatif[-1] + l)
posisi_kolom = {k: kumulatif[i] / max(kumulatif[-1], 1) for i, k in enumerate(kolom_terpakai)}
volume_node = {
    n: max(
        sum(v for a, _t, v, _j in alur if a == n),
        sum(v for _a, tj, v, _j in alur if tj == n),
    )
    for n in node_nama
}
warna_jenis = {"lulus": warna[0], "gugur": theme.STATUS["kritis"], "absen": theme.STATUS["peringatan"]}
alpha_jenis = {"lulus": 0.32, "gugur": 0.3, "absen": 0.38}
idx = {n: i for i, n in enumerate(node_nama)}

sankey = go.Figure(
    go.Sankey(
        arrangement="fixed",
        node=dict(
            # Node gugur & tidak hadir cukup berlabel angka: warnanya sudah menyebut
            # sebabnya, kolomnya sudah menyebut tahapnya, nama lengkap ada di hover.
            label=[
                f"{n}<br>{angka(volume_node[n])}" if jenis_node(n) == "lulus" else angka(volume_node[n])
                for n in node_nama
            ],
            customdata=node_nama,
            color=[warna_jenis[jenis_node(n)] for n in node_nama],
            x=[0.001 + 0.998 * posisi_kolom[kolom_node(n)] for n in node_nama],
            y=[{"lulus": 0.06, "gugur": 0.5, "absen": 0.9}[jenis_node(n)] for n in node_nama],
            pad=24,
            thickness=14,
            line=dict(width=0),
            hovertemplate="%{customdata}<br>%{value:,} orang<extra></extra>",
        ),
        link=dict(
            source=[idx[a] for a, _t, _v, _j in alur],
            target=[idx[tj] for _a, tj, _v, _j in alur],
            value=[v for _a, _t, v, _j in alur],
            color=[theme.rgba(warna_jenis[j], alpha_jenis[j]) for _a, _t, _v, j in alur],
            customdata=[f"{a} ke {tj}" for a, tj, _v, _j in alur],
            hovertemplate="%{customdata}<br>%{value:,} orang<extra></extra>",
        ),
        textfont=dict(size=12, color=t["text_primary"]),
    )
)
theme.plotly_layout(sankey, height=440)

with ui.seksi(
    "Alur pendaftar per tahap",
    "Pita biru adalah pendaftar yang lolos ke tahap berikutnya. Pita merah gugur karena "
    "tidak lulus tes, pita kuning gugur karena tidak hadir. Tebal pita sebanding dengan "
    "jumlah orang.\n\nPita biru yang langsung menuju **Akademik & Inggris** adalah jalur RBB: "
    "kandidat sudah disaring FHCI sehingga melewati Administrasi dan Adaptif.",
):
    st.plotly_chart(sankey, width="stretch", config={"displayModeBar": False})

# ── Pola antar kohort ───────────────────────────────────────────────────────
kiri, kanan = st.columns([3, 2], gap="medium")

with kiri:
    heat = metrics.lulus_tahap_tahun(f)
    # Label sumbu dipendekkan: enam kolom di chart 3/5 lebar tidak muat nama penuh,
    # dan Vega diam-diam menyembunyikan label yang bertabrakan.
    label_pendek = {**LABEL_TAHAP, "administrasi": "Admin", "akademik_inggris": "Akademik", "fisik_mcu": "Fisik"}
    heat["tahap"] = heat["tahap_kode"].map(label_pendek)
    urutan_pendek = [label_pendek[k] for k in LABEL_TAHAP]
    with ui.seksi(
        "Tingkat lulus per tahap dan tahun",
        "Tiap sel adalah persentase peserta yang lulus di tahap itu pada tahun program itu. "
        "Makin gelap makin banyak yang lulus. Baca per kolom untuk melihat tahun yang "
        "menyimpang dari biasanya.\n\nTahun RBB (2020, 2021, 2024) tidak punya kolom "
        "Administrasi dan Adaptif karena kandidatnya masuk di Akademik.",
    ):
        if heat.empty:
            ui.kosong()
        else:
            n_tahun = heat["tahun"].nunique()
            dasar = alt.Chart(heat).encode(
                x=alt.X("tahap:N", sort=urutan_pendek, title=None, axis=alt.Axis(labelAngle=0, orient="top", labelOverlap=False, ticks=False, domain=False)),
                y=alt.Y("tahun:O", title=None),
            )
            sel = dasar.mark_rect(cornerRadius=3, stroke=t["surface_card"], strokeWidth=2).encode(
                color=alt.Color(
                    "pct_lulus:Q",
                    scale=alt.Scale(domain=[0, 100], range=theme.RAMP),
                    legend=None,
                ),
                tooltip=[
                    alt.Tooltip("tahun:O", title="Tahun"),
                    alt.Tooltip("tahap:N", title="Tahap"),
                    alt.Tooltip("masuk:Q", title="Peserta", format=","),
                    alt.Tooltip("pct_lulus:Q", title="Lulus (%)", format=".1f"),
                ],
            )
            label = dasar.mark_text(fontSize=12, fontWeight=600).encode(
                text=alt.Text("pct_lulus:Q", format=".0f"),
                color=alt.condition(alt.datum.pct_lulus > 55, alt.value("#FFFFFF"), alt.value("#103A5D")),
            )
            st.altair_chart((sel + label).properties(height=max(44 * n_tahun, 120)), width="stretch")

with kanan:
    with ui.seksi(
        "Ketidakhadiran tes per tahun",
        "Titik biru adalah persentase peserta tes **online** yang tidak hadir, titik oranye "
        "tes **offline**. Garis abu menunjukkan jarak keduanya.\n\nTes online adalah "
        "Adaptif dan Akademik; tes offline adalah Psikologi, Fisik & MCU, dan Wawancara.",
    ):
        if no_show_mode.empty:
            ui.kosong()
        else:
            jarak = no_show_mode.groupby("tahun")["pct_no_show"].agg(["min", "max"]).reset_index()
            garis = alt.Chart(jarak).mark_rule(color=t["netral"], strokeWidth=2).encode(
                y=alt.Y("tahun:O", title=None),
                x=alt.X("min:Q", title="Tidak hadir (%)", scale=alt.Scale(domain=[0, 60])),
                x2="max:Q",
            )
            titik = alt.Chart(no_show_mode).mark_circle(size=130, opacity=1, stroke=t["surface_card"], strokeWidth=2).encode(
                y=alt.Y("tahun:O", title=None),
                x=alt.X("pct_no_show:Q"),
                color=alt.Color(
                    "mode:N",
                    scale=alt.Scale(domain=["online", "offline"], range=warna[:2]),
                    legend=alt.Legend(title=None, orient="top"),
                ),
                tooltip=[
                    alt.Tooltip("tahun:O", title="Tahun"),
                    alt.Tooltip("mode:N", title="Mode"),
                    alt.Tooltip("terjadwal:Q", title="Terjadwal", format=","),
                    alt.Tooltip("pct_no_show:Q", title="Tidak hadir (%)", format=".1f"),
                ],
            )
            n_tahun = no_show_mode["tahun"].nunique()
            st.altair_chart((garis + titik).properties(height=max(44 * n_tahun, 120)), width="stretch")

# ── Penggerak gugur ─────────────────────────────────────────────────────────
kiri, kanan = st.columns(2, gap="medium")

# Chart "Sebaran skor tes online" dihapus 2026-09-16. Skornya dibangkitkan acak (sistem
# asli hanya menyimpan lulus/gagal), sehingga histogramnya rata dan garis batas lulus 60
# menyiratkan temuan yang tidak ada di data. Tingkat lulus per tahap tetap ada di heatmap
# di atas, dan itu angka yang nyata.
with kiri:
    vendor = metrics.lulus_per_vendor(f)
    with ui.seksi(
        "Tingkat lulus per vendor tes",
        "Tiap titik adalah satu vendor, besar titik sebanding dengan jumlah peserta yang "
        "hadir. Posisi horizontal adalah persentase lulus.\n\nVendor ditampilkan dengan kode "
        "dan kota basis. Penunjukan vendor dan hasilnya **dimodelkan**, bukan kinerja lembaga "
        "sebenarnya.",
    ):
        if vendor.empty:
            ui.kosong()
        else:
            vendor["tahap"] = vendor["tahap_kode"].map(LABEL_TAHAP)
            panel = []
            for nama_tahap in [x for x in URUTAN_TAHAP if x in set(vendor["tahap"])]:
                data = vendor[vendor["tahap"] == nama_tahap]
                panel.append(
                    alt.Chart(data)
                    .mark_circle(color=warna[0], opacity=0.85, stroke=t["surface_card"], strokeWidth=1)
                    .encode(
                        y=alt.Y("vendor:N", sort="-x", title=None),
                        x=alt.X("pct_lulus:Q", title=None, scale=alt.Scale(domain=[40, 100])),
                        size=alt.Size("peserta:Q", legend=None, scale=alt.Scale(range=[60, 420])),
                        tooltip=[
                            alt.Tooltip("vendor:N", title="Vendor"),
                            alt.Tooltip("peserta:Q", title="Peserta hadir", format=","),
                            alt.Tooltip("pct_lulus:Q", title="Lulus (%)", format=".1f"),
                        ],
                    )
                    .properties(height=26 * len(data), title=alt.TitleParams(nama_tahap, anchor="start", fontSize=12, fontWeight=600))
                )
            st.altair_chart(alt.vconcat(*panel, spacing=14), width="stretch")

with kanan:
    with ui.seksi(
        "Hari sejak melamar",
        "Batang menunjukkan rentang hari dari tanggal melamar sampai tahap dijadwalkan, "
        "untuk 80% peserta di tengah (persentil 10 sampai 90). Garis tegak adalah median.",
    ):
        if durasi.empty:
            ui.kosong()
        else:
            durasi["tahap"] = durasi["tahap_kode"].map(LABEL_TAHAP)
            durasi["label"] = durasi["median"].map(lambda v: f"{angka(v)} hari")
            y = alt.Y("tahap:N", sort=URUTAN_TAHAP, title=None, axis=alt.Axis(labelLimit=150))
            rentang = alt.Chart(durasi).mark_bar(height=12, cornerRadius=6, color=warna[0], opacity=0.3).encode(
                y=y,
                x=alt.X("p10:Q", title="Hari"),
                x2="p90:Q",
                tooltip=[
                    alt.Tooltip("tahap:N", title="Tahap"),
                    alt.Tooltip("p10:Q", title="Persentil 10"),
                    alt.Tooltip("median:Q", title="Median"),
                    alt.Tooltip("p90:Q", title="Persentil 90"),
                ],
            )
            median = alt.Chart(durasi).mark_tick(thickness=3, size=20, color=warna[0]).encode(y=y, x="median:Q")
            label = alt.Chart(durasi).mark_text(align="left", dx=8, fontSize=12, color=t["text_secondary"]).encode(
                y=y, x="p90:Q", text="label:N"
            )
            st.altair_chart((rentang + median + label).properties(height=260), width="stretch")

# Selebar halaman: pasangannya di baris ini (histogram skor) dihapus, dan lima batang
# alasan justru lebih terbaca dengan label penuh.
with st.container():
    alasan = metrics.alasan_gugur_administrasi(f)
    label_alasan = {
        "ipk_di_bawah_minimum": "IPK di bawah minimum",
        "jurusan_tidak_sesuai": "Jurusan tidak sesuai",
        "berkas_tidak_lengkap": "Berkas tidak lengkap",
        "status_menikah": "Sudah menikah",
        "umur_melebihi_batas": "Umur melebihi batas",
    }
    with ui.seksi(
        "Alasan gugur administrasi",
        "Jumlah penyebutan tiap alasan pada pendaftaran yang gugur di seleksi administrasi. "
        "Satu pendaftaran bisa punya lebih dari satu alasan, jadi totalnya melebihi jumlah "
        "orang yang gugur.",
    ):
        if alasan.empty:
            ui.kosong("Tidak ada yang gugur di administrasi: jalur RBB masuk langsung di tahap Akademik.", saran=False)
        else:
            alasan["label"] = alasan["alasan"].map(label_alasan).fillna(alasan["alasan"])
            alasan["teks"] = alasan["n"].map(angka)  # format Indonesia: titik ribuan
            y = alt.Y("label:N", sort="-x", title=None, axis=alt.Axis(labelLimit=160))
            # Sumbu disembunyikan: tiap batang sudah berlabel angka langsung, dan ruang
            # 20% di kanan menampung label batang terpanjang tanpa terpotong.
            x = alt.X("n:Q", title=None, axis=None, scale=alt.Scale(domain=[0, alasan["n"].max() * 1.2]))
            batang = alt.Chart(alasan).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4, color=warna[0], height=22).encode(
                y=y,
                x=x,
                tooltip=[alt.Tooltip("label:N", title="Alasan"), alt.Tooltip("teks:N", title="Penyebutan")],
            )
            teks = alt.Chart(alasan).mark_text(align="left", dx=6, fontSize=12, color=t["text_secondary"]).encode(
                y=y, x=x, text="teks:N"
            )
            st.altair_chart((batang + teks).properties(height=260), width="stretch")

# ── Lapis analis ─────────────────────────────────────────────────────────────
if ui.mode_analis():
    ui.lapis_analis(
        funnel,
        "tahapan_seleksi_per_tahap.csv",
        "Konversi per tahap (masuk, hadir, lulus, tidak hadir)",
    )
