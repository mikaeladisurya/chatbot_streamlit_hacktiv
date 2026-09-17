"""Halaman 2 — Perencanaan Kebutuhan.

Pertanyaan yang dijawab: berapa orang yang perlu direkrut, kenapa kursinya kosong,
dan di unit mana kebutuhannya menumpuk?

Seluruh halaman DIMODELKAN kecuali FTK & realisasi di `unit_induk`. Filter global
tidak berlaku: tabel perencanaan tidak terhubung ke profesi atau gelombang.
"""

from __future__ import annotations

import altair as alt
import streamlit as st

from components import grafik, ui
from core import metrics, theme
from core.format import angka, persen

ui.judul_halaman("Perencanaan kebutuhan")

t = theme.token()
warna = theme.seri()
gap = metrics.gap_ftk()
proyeksi = metrics.proyeksi_per_sebab()
pagu = metrics.pagu_vs_usulan()
gap_unit = metrics.gap_ftk_per_unit()

tahun_akhir = int(pagu["tahun"].max())
baris_akhir = pagu.loc[pagu["tahun"] == tahun_akhir].iloc[0]
# Tahun proyeksi diambil dari data, bukan ditulis tetap: label ikut bergeser saat
# tabel proyeksi bertambah tahun.
tahun_proyeksi = int(proyeksi["tahun"].max()) if not proyeksi.empty else None
kekosongan = proyeksi.loc[proyeksi["tahun"] == tahun_proyeksi, "total"] if tahun_proyeksi else proyeksi["total"][:0]
unit_kurang = int((gap_unit["gap"] > 0).sum())

# ── Baris KPI ────────────────────────────────────────────────────────────────
ui.baris_kpi(
    [
        {
            "label": "Kekurangan FTK",
            "value": angka(gap["gap"]),
            "help": f"FTK 2025 {angka(gap['ftk'])} dikurangi realisasi Maret 2026 {angka(gap['realisasi'])}.",
        },
        {
            "label": "Unit kekurangan",
            "value": f"{unit_kurang} dari {len(gap_unit)}",
            "help": "Unit induk yang realisasinya di bawah FTK.",
        },
        {
            "label": f"Proyeksi kekosongan {tahun_proyeksi}" if tahun_proyeksi else "Proyeksi kekosongan",
            "value": angka(kekosongan.iloc[0]) if not kekosongan.empty else "-",
            "help": "Kursi yang diperkirakan kosong karena pensiun, mengundurkan diri, meninggal, dan PHK.",
        },
        {"label": f"Usulan {tahun_akhir}", "value": angka(baris_akhir["usulan"])},
        {
            "label": f"Pagu disetujui {tahun_akhir}",
            "value": persen(baris_akhir["pct_disetujui"]),
            "help": f"{angka(baris_akhir['pagu'])} dari {angka(baris_akhir['usulan'])} usulan unit.",
        },
    ]
)

# ── Rantai pemenuhan kebutuhan ──────────────────────────────────────────────
# Ditaruh paling atas: inilah pertanyaan pemilik proses (berapa kebutuhan yang
# benar-benar terisi), yang sebelumnya tidak terjawab di halaman mana pun.
rantai = metrics.rantai_pemenuhan()
TITIK = [("usulan", "Usulan unit"), ("kuota", "Kuota dibuka"), ("diterima", "Diterima"), ("ditempatkan", "Ditempatkan")]

with ui.seksi(
    "Kebutuhan sampai penempatan per tahun",
    "Empat titik rantai kebutuhan dalam satu garis per tahun: jumlah yang diusulkan unit, "
    "kuota yang dibuka di profesi, orang yang lulus seleksi, dan orang yang benar-benar "
    "ditempatkan. Makin panjang jarak antar titik, makin besar susutnya di tahap itu.\n\n"
    "Usulan **dimodelkan**. Usulan juga tidak menyimpan jenis program, jadi rantai ini tidak "
    "bisa dipilah per RBB, Afirmasi, atau Terbuka.\n\nKuota bernilai nol pada tahun yang "
    "profesinya tidak mencantumkan kuota, dan penempatan tahun berjalan masih bertambah.",
):
    if rantai.empty:
        ui.kosong(saran=False)
    else:
        panjang = rantai.melt(id_vars=["tahun"], value_vars=[k for k, _ in TITIK], var_name="titik", value_name="n")
        panjang["titik"] = panjang["titik"].map(dict(TITIK))
        panjang["teks"] = panjang["n"].map(angka)
        urutan_titik = [nama for _, nama in TITIK]
        # Tahap di sumbu Y dan tahun di sumbu X: dua tahap yang kebetulan bernilai sama
        # menghasilkan garis mendatar (benar), bukan dua titik yang saling menutupi dan
        # terbaca sebagai chart rusak. Facet per tahun dihindari karena spesifikasi
        # Vega-Lite ber-facet tidak bisa memakai lebar "container", jadi panelnya gepeng.
        x = alt.X("tahun:O", title=None, axis=alt.Axis(labelAngle=0, ticks=False, domain=False))
        y = alt.Y(
            "titik:N",
            sort=urutan_titik,
            title=None,
            axis=alt.Axis(ticks=False, domain=False, labelFontWeight=600, labelPadding=8),
        )
        dasar = alt.Chart(panjang).encode(
            x=x,
            y=y,
            tooltip=[
                alt.Tooltip("tahun:O", title="Tahun"),
                alt.Tooltip("titik:N", title="Titik"),
                alt.Tooltip("teks:N", title="Orang"),
            ],
        )
        # Garis vertikal per tahun menyatukan keempat tahap jadi satu rantai yang terbaca
        # dari atas ke bawah; ukuran titik membawa besarannya.
        tali = dasar.mark_line(color=t["netral"], strokeWidth=2, opacity=0.5).encode(detail="tahun:O")
        rantai_chart = (
            dasar.mark_circle(opacity=1, color=warna[0], stroke=t["surface_card"], strokeWidth=2).encode(
                size=alt.Size("n:Q", scale=alt.Scale(range=[60, 900]), legend=None),
            )
            + dasar.mark_text(dy=-16, fontSize=11, color=t["text_secondary"]).encode(text="teks:N")
        )
        # padding atas: label angka baris teratas digambar di luar area plot.
        st.altair_chart(
            (tali + rantai_chart).properties(height=190, padding={"top": 18, "left": 5, "right": 5, "bottom": 5}),
            width="stretch",
        )

# ── Pemenuhan per sub-bidang ────────────────────────────────────────────────
tahun_sub = metrics.tahun_sub_bidang_tercatat()
with ui.seksi(
    "Usulan dan penempatan per sub-bidang",
    "Batang lebar abu adalah kebutuhan yang diusulkan unit untuk sub-bidang itu, batang sempit "
    "biru di dalamnya adalah orang yang ditempatkan di sub-bidang yang sama pada tahun program "
    "yang sama. Persen di ujung adalah porsi usulan yang terisi.\n\nUsulan **dimodelkan**. "
    "Penempatan baru punya sub-bidang setelah SK terbit, jadi tahun yang kohortnya belum ber-SK "
    "tidak muncul di pilihan tahun.\n\nCapaian bisa melebihi 100% bila unit menempatkan orang di "
    "sub-bidang yang usulannya kecil atau tidak diusulkan sama sekali.",
):
    if not tahun_sub:
        ui.kosong("Belum ada penempatan yang sub-bidangnya tercatat.", saran=False)
    else:
        tahun_sb = st.segmented_control(
            "Tahun program",
            tahun_sub,
            default=tahun_sub[-1],
            key="tahun_sub_bidang",
            label_visibility="collapsed",
        ) or tahun_sub[-1]
        sub = metrics.pemenuhan_sub_bidang(int(tahun_sb))
        sub = sub[sub["usulan"] > 0]
        if sub.empty:
            ui.kosong("Tidak ada usulan tercatat untuk tahun ini.", saran=False)
        else:
            st.altair_chart(
                grafik.bullet(
                    sub,
                    "sub_bidang",
                    "usulan",
                    "realisasi",
                    label_target="Usulan",
                    label_capaian="Ditempatkan",
                    # 15 sub-bidang: nama panjang hanya terbaca kalau batangnya mendatar.
                    horizontal=True,
                    tinggi=30 * len(sub) + 60,
                ),
                width="stretch",
            )

# ── Usulan vs pagu & sebab kekosongan ───────────────────────────────────────
kiri, kanan = st.columns(2, gap="medium")

with kiri:
    with ui.seksi(
        "Usulan dan pagu per tahun",
        "Batang lebar abu adalah jumlah kebutuhan yang diusulkan unit. Batang sempit biru di "
        "dalamnya adalah pagu yang disetujui. Persen di atas batang adalah porsi usulan yang "
        "disetujui.",
    ):
        st.altair_chart(
            grafik.bullet(pagu, "tahun", "usulan", "pagu", label_target="Usulan", label_capaian="Pagu", tinggi=280),
            width="stretch",
        )

with kanan:
    label_sebab = {"pensiun": "Pensiun", "aps": "Mengundurkan diri", "meninggal": "Meninggal", "phk": "PHK"}
    area = proyeksi.melt(id_vars=["tahun"], value_vars=list(label_sebab), var_name="sebab", value_name="jumlah")
    area["sebab"] = area["sebab"].map(label_sebab)
    area["teks"] = area["jumlah"].map(angka)
    with ui.seksi(
        "Proyeksi kekosongan per sebab",
        "Jumlah kursi yang diperkirakan kosong tiap tahun, ditumpuk menurut sebabnya. Tebal "
        "lapisan menunjukkan besar tiap sebab.",
    ):
        st.altair_chart(
            alt.Chart(area)
            .mark_area(opacity=0.9, line=dict(color=t["surface_card"], strokeWidth=1.5))
            .encode(
                x=alt.X("tahun:O", title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("jumlah:Q", title=None, stack="zero", axis=alt.Axis(format="~s", tickCount=4)),
                color=alt.Color(
                    "sebab:N",
                    scale=alt.Scale(domain=list(label_sebab.values()), range=warna[:4]),
                    legend=alt.Legend(title=None, orient="top"),
                ),
                order=alt.Order("sebab:N"),
                tooltip=[
                    alt.Tooltip("tahun:O", title="Tahun"),
                    alt.Tooltip("sebab:N", title="Sebab"),
                    alt.Tooltip("teks:N", title="Kursi"),
                ],
            )
            .properties(height=280),
            width="stretch",
        )

# ── Sebaran per unit ────────────────────────────────────────────────────────
kiri, kanan = st.columns([3, 2], gap="medium")

with kiri:
    with ui.seksi(
        "Usulan kebutuhan per unit dan sub-bidang",
        "Tiap sel adalah jumlah kebutuhan yang diusulkan satu unit induk untuk satu sub-bidang. "
        "Makin gelap makin banyak. Hanya 20 unit dengan usulan terbanyak yang ditampilkan, "
        "diurutkan dari yang terbesar.",
    ):
        tahun_pilih = st.segmented_control(
            "Tahun usulan",
            sorted(pagu["tahun"].tolist()),
            default=tahun_akhir,
            key="tahun_usulan",
            label_visibility="collapsed",
        ) or tahun_akhir
        heat = metrics.usulan_unit_subbidang(int(tahun_pilih))
        if heat.empty:
            ui.kosong("Tidak ada usulan untuk tahun ini.", saran=False)
        else:
            urutan_unit = heat.drop_duplicates("unit")["unit"].tolist()
            st.altair_chart(
                grafik.heatmap(
                    heat,
                    "sub_bidang",
                    "unit",
                    "usulan",
                    urutan_y=urutan_unit,
                    tinggi_baris=26,
                    label=False,
                    sudut_label_x=-40,
                    tooltip=[
                        alt.Tooltip("unit:N", title="Unit"),
                        alt.Tooltip("sub_bidang:N", title="Sub-bidang"),
                        alt.Tooltip("usulan:Q", title="Usulan", format=".0f"),
                    ],
                ),
                width="stretch",
            )

with kanan:
    selisih = gap_unit.copy()
    selisih["arah"] = selisih["gap"].map(lambda v: "Kurang" if v > 0 else "Lebih")
    selisih["teks"] = selisih["gap"].map(lambda v: angka(abs(v)))
    with ui.seksi(
        "Selisih FTK dan realisasi per unit",
        "Batang ke kanan: unit kekurangan pegawai dibanding FTK 2025. Batang ke kiri: unit "
        "yang realisasinya melebihi FTK.\n\nRealisasi memakai Maret 2026 karena data April "
        "2026 baru terisi di 1 dari 48 unit. UID Jawa Tengah & DIY versi anomali "
        "(jumlah pegawai 4) dikeluarkan.",
    ):
        st.altair_chart(
            alt.Chart(selisih)
            .mark_bar(height=9, cornerRadius=3)
            .encode(
                y=alt.Y("nama_pendek:N", sort=alt.SortField("gap", order="descending"), title=None, axis=alt.Axis(labelLimit=160, ticks=False, domain=False, labelFontSize=10)),
                x=alt.X("gap:Q", title="Pegawai"),
                color=alt.Color(
                    "arah:N",
                    scale=alt.Scale(domain=["Kurang", "Lebih"], range=[warna[1], warna[0]]),
                    legend=alt.Legend(title=None, orient="top"),
                ),
                tooltip=[
                    alt.Tooltip("nama_pendek:N", title="Unit"),
                    alt.Tooltip("ftk_2025:Q", title="FTK 2025", format=".0f"),
                    alt.Tooltip("realisasi_mar_2026:Q", title="Realisasi Mar 2026", format=".0f"),
                    alt.Tooltip("arah:N", title="Arah"),
                    alt.Tooltip("teks:N", title="Selisih"),
                ],
            )
            .properties(height=14 * len(selisih)),
            width="stretch",
        )

# ── Lapis analis ─────────────────────────────────────────────────────────────
if ui.mode_analis():
    ui.lapis_analis(gap_unit, "gap_ftk_per_unit.csv", "Gap FTK per unit induk")

# Spanduk di kaki halaman: peringatan ini berlaku untuk seluruh isi, jadi ia catatan
# sumber data, bukan pembuka. Di atas ia mendorong KPI turun dan dibaca sebelum ada
# yang bisa dinilai.
ui.spanduk_dimodelkan(
    "Usulan dan pagu per posisi tidak tersimpan di sistem PLN mana pun, jadi angkanya di sini "
    "dimodelkan. Bahan yang nyata hanya FTK dan realisasi pegawai per unit. Filter tahun, jenis, "
    "dan jenjang tidak berlaku di halaman ini."
)
