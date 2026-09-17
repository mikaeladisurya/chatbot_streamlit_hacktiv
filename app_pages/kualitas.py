"""Halaman 7 — Kualitas Data & Sumber Sistem.

Pertanyaan yang dijawab: data mana yang bisa dipercaya, dari sistem mana asalnya, dan
lubang apa yang masih perlu ditambal?

Revamp 2026-09-16: tampilan diseragamkan dengan halaman lain (seksi + bantuan (?)).
Filter global tidak berlaku: halaman ini tentang datanya sendiri, bukan kohort tertentu.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from components import grafik, ui
from core import metrics, theme
from core.format import angka, persen

ui.judul_halaman("Kualitas data")

t = theme.token()
warna = theme.seri()
sistem = metrics.volume_per_sistem().set_index("sistem_sumber")["n"]
kelengkapan = metrics.kelengkapan_per_kohort()
selisih = metrics.selisih_angka_rencana()
rbb = metrics.jejak_rbb()
bulanan = metrics.realisasi_pegawai_bulanan()

rekrutmen_n = int(sistem.get("rekrutmen.pln.co.id", 0))
seleksi_n = int(sistem.get("seleksi.pln.co.id", 0))
upload_n = int(sistem.get("rekrutmen.pln.co.id (hasil di-upload)", 0))
pct_terlihat = rbb.iloc[-1]["pct_terlihat"]

# ── Alur sistem ─────────────────────────────────────────────────────────────
with ui.seksi(
    "Perjalanan data antar sistem",
    "Satu kandidat melewati empat sampai lima sistem dari melamar sampai SK. Tidak satu pun "
    "sistem bisa sendirian menjawab pertanyaan seperti berapa orang yang sedang OJT.\n\n"
    "FHCI hanya mengirim angka agregat; Pusdiklat adalah titik rawan integrasi karena data "
    "OJT tidak tersambung otomatis ke HTD.\n\n"
    f"Hasil tes vendor masuk portal rekrutmen lewat unggahan manual: {angka(upload_n)} baris.",
):
    simpul = [
        ("FHCI", f"Agregat, {persen(pct_terlihat, 2)} terlihat di PLN"),
        ("Portal rekrutmen", f"rekrutmen.pln.co.id, {angka(rekrutmen_n)} baris"),
        ("Portal seleksi", f"seleksi.pln.co.id, {angka(seleksi_n)} baris"),
        ("Pusdiklat", "OJT, titik rawan integrasi"),
        ("HTD", "SK dan data pegawai"),
    ]
    # st.columns rasio tetap: lima simpul selalu satu baris (container horizontal membungkus
    # simpul terakhir ke baris baru), panah di kolom sempit di antaranya.
    kolom = st.columns([4, 1, 4, 1, 4, 1, 4, 1, 4], vertical_alignment="center", gap="small")
    for i, (nama, sub) in enumerate(simpul):
        with kolom[2 * i]:
            with st.container(border=True, height=130):
                st.markdown(f"**{nama}**")
                st.caption(sub)
        if i < len(simpul) - 1:
            with kolom[2 * i + 1]:
                st.markdown(":material/arrow_forward:", text_alignment="center")

# ── Kelengkapan & laporan bulanan ───────────────────────────────────────────
kiri, kanan = st.columns(2, gap="medium")

with kiri:
    lengkap = kelengkapan.melt(
        id_vars=["kualitas_kohort"], value_vars=["pct_blok_fisik", "pct_domisili"], var_name="kolom", value_name="pct"
    )
    lengkap["kolom"] = lengkap["kolom"].map({"pct_blok_fisik": "Blok fisik", "pct_domisili": "Domisili"})
    lengkap["kualitas_kohort"] = lengkap["kualitas_kohort"].str.capitalize()
    with ui.seksi(
        "Kelengkapan kolom per kualitas kohort",
        "Persentase kandidat yang kolomnya terisi, dikelompokkan menurut kualitas pencatatan "
        "kohortnya. Blok fisik adalah tinggi, berat, dan visus; hanya terisi bila kandidat "
        "sampai tes fisik.",
    ):
        st.altair_chart(
            grafik.heatmap(
                lengkap,
                "kolom",
                "kualitas_kohort",
                "pct",
                urutan_y=["Rendah", "Sedang", "Baik"],
                domain=(0, 100),
                tinggi_baris=56,
                tooltip=[
                    alt.Tooltip("kualitas_kohort:N", title="Kualitas kohort"),
                    alt.Tooltip("kolom:N", title="Kolom"),
                    alt.Tooltip("pct:Q", title="Terisi (%)", format=".1f"),
                ],
            ),
            width="stretch",
        )

with kanan:
    bulanan["status"] = bulanan["unit_melapor"].map(lambda n: "48 unit melapor" if n >= 48 else "Sebagian unit")
    bulanan["teks"] = bulanan.apply(lambda b: f"{angka(b.realisasi)} pegawai, {b.unit_melapor} unit", axis=1)
    with ui.seksi(
        "Laporan realisasi pegawai per bulan",
        "Total realisasi pegawai yang dilaporkan unit induk tiap bulan. Batang oranye berarti "
        "tidak semua 48 unit melapor. Celah tanpa batang adalah bulan yang sama sekali tidak "
        "punya laporan.\n\nIni alasan gap FTK memakai Maret 2026: April 2026 baru dilaporkan "
        "1 unit, dan September sampai Oktober 2025 kosong.",
    ):
        st.altair_chart(
            alt.Chart(bulanan)
            .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, width=14)
            .encode(
                x=alt.X("yearmonth(bulan):T", title=None, axis=alt.Axis(format="%b %y", labelAngle=0, tickCount=8)),
                y=alt.Y("realisasi:Q", title=None, axis=alt.Axis(format="~s", tickCount=4)),
                color=alt.Color(
                    "status:N",
                    scale=alt.Scale(domain=["48 unit melapor", "Sebagian unit"], range=[warna[0], warna[1]]),
                    legend=alt.Legend(title=None, orient="top"),
                ),
                tooltip=[alt.Tooltip("bulan:T", title="Bulan", format="%B %Y"), alt.Tooltip("teks:N", title="Laporan")],
            )
            .properties(height=196),
            width="stretch",
        )

# ── Rencana & jejak RBB ─────────────────────────────────────────────────────
kiri, kanan = st.columns(2, gap="medium")

with kiri:
    dua_angka = selisih.melt(id_vars=["tahun"], value_vars=["target_gelombang", "pagu"], var_name="sumber", value_name="n")
    dua_angka["sumber"] = dua_angka["sumber"].map({"target_gelombang": "Target gelombang", "pagu": "Pagu disetujui"})
    dua_angka["teks"] = dua_angka["n"].map(angka)
    with ui.seksi(
        "Dua angka rencana per tahun",
        "Target diterima yang tercatat di gelombang dan pagu yang disetujui untuk tahun yang "
        "sama. Garis abu menunjukkan selisihnya: kedua angka tidak pernah didamaikan. "
        "Keduanya **dimodelkan**.",
    ):
        jarak = selisih.assign(lo=selisih[["target_gelombang", "pagu"]].min(axis=1), hi=selisih[["target_gelombang", "pagu"]].max(axis=1))
        y = alt.Y("tahun:O", title=None, axis=alt.Axis(ticks=False, domain=False))
        garis = alt.Chart(jarak).mark_rule(color=t["netral"], strokeWidth=3).encode(y=y, x=alt.X("lo:Q", title=None, axis=alt.Axis(format="~s")), x2="hi:Q")
        titik = alt.Chart(dua_angka).mark_circle(size=130, opacity=1, stroke=t["surface_card"], strokeWidth=2).encode(
            y=y,
            x="n:Q",
            color=alt.Color(
                "sumber:N",
                scale=alt.Scale(domain=["Target gelombang", "Pagu disetujui"], range=warna[:2]),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=[alt.Tooltip("tahun:O", title="Tahun"), alt.Tooltip("sumber:N", title="Angka"), alt.Tooltip("teks:N", title="Orang")],
        )
        st.altair_chart((garis + titik).properties(height=260), width="stretch")

with kanan:
    # Dulu batang per tahun. Persentasenya praktis sama untuk semua tahun, sehingga
    # batangnya sama panjang dan tidak membawa informasi apa pun; tabel tiga baris
    # menyampaikan angka yang sama tanpa berpura-pura ada pola (temuan audit 2026-09-16).
    with ui.seksi(
        "Jejak pelamar RBB di sistem PLN",
        "Berapa dari pelamar FHCI jalur RBB yang berkasnya sampai tercatat di sistem PLN. "
        "FHCI menyaring pelamarnya lebih dulu dan hanya menyerahkan kandidat terpilih, jadi "
        "pendaftaran di dashboard ini **bukan** gambaran seluruh pasar kerja BUMN.",
    ):
        st.dataframe(
            rbb.assign(
                Tahun=rbb["tahun"].astype(str),
                **{
                    "Pelamar FHCI": rbb["pelamar_fhci"].map(angka),
                    "Tercatat di PLN": rbb["masuk_pln"].map(angka),
                    "Porsi tercatat": rbb["pct_terlihat"].map(lambda v: persen(v, 2)),
                },
            )[["Tahun", "Pelamar FHCI", "Tercatat di PLN", "Porsi tercatat"]],
            hide_index=True,
            width="stretch",
        )

# ── Katalog anomali ─────────────────────────────────────────────────────────
with ui.seksi(
    "Kolom dimodelkan dan anomali yang diketahui",
    "Daftar rujukan untuk analis. Kode F merujuk ke temuan riset lapangan; berkas ISSUES ada "
    "di proyek pembangkit data (mockdb).",
):
    referensi = pd.DataFrame(
        [
            {"Hal": "Kuota per posisi", "Keterangan": "Domain HST, tidak ada di HTD", "Rujukan": "F-017"},
            {"Hal": "Passing grade", "Keterangan": "Tidak ada di Perdir 0056/0050/0048", "Rujukan": "F-028"},
            {"Hal": "Skor tes mentah", "Keterangan": "Sistem asli hanya menyimpan lulus atau gagal", "Rujukan": "F-017"},
            {"Hal": "UID Jawa Tengah & DIY", "Keterangan": "Baris ganda: jumlah_pegawai 4 vs FTK 144, gagal cocok DAPEG", "Rujukan": "ISSUES_MASTER_DATA.md"},
            {"Hal": "realisasi_apr_2026", "Keterangan": "Hanya terisi 1 dari 48 unit, gap FTK memakai Maret 2026", "Rujukan": "M13"},
            {"Hal": "Laporan bulanan Sep sampai Okt 2025", "Keterangan": "Tidak ada baris; Jan sampai Agu 2025 hanya 47 unit", "Rujukan": "M58"},
            {"Hal": "5 kolom kandidat", "Keterangan": "Dibagikan acak seragam (kota_domisili, kota_asal, sekolah_universitas, dll)", "Rujukan": "ISSUES_SEBARAN.md"},
            {"Hal": "Nama vendor", "Keterangan": "Nama lembaga nyata, penunjukan dan hasil dimodelkan; ditampilkan sebagai kode", "Rujukan": "M49"},
        ]
    )
    st.dataframe(referensi, hide_index=True, width="stretch")
