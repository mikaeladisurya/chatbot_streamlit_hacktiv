"""Halaman 6 — Penempatan & Pemenuhan.

Pertanyaan yang dijawab: orang yang diterima mendarat di mana, di bidang apa, dan
seberapa jauh kuota terpenuhi?

Revamp 2026-09-16: tunduk pada filter global (lewat pendaftaran asal tiap penempatan).
Treemap unit x bidang dipertahankan karena pemilik menyukainya sebagai jangkar halaman.
"""

from __future__ import annotations

import altair as alt
import plotly.express as px
import streamlit as st

from components import grafik, ui
from core import metrics, theme
from core.format import angka, persen

ui.judul_halaman("Penempatan")
f = ui.bar_filter()

ringkas = metrics.penempatan_ringkas(f)
if not ringkas["ditempatkan"]:
    ui.kosong()
    st.stop()

t = theme.token()
warna = theme.seri()
kuota = metrics.kuota_realisasi_f(f)
non_rbb = kuota[~kuota["rbb"]]

# ── Baris KPI ────────────────────────────────────────────────────────────────
ditempatkan = ringkas["ditempatkan"]
ui.baris_kpi(
    [
        {"label": "Ditempatkan", "value": angka(ditempatkan)},
        {
            "label": "PLN induk",
            "value": persen(100 * ringkas["induk"] / ditempatkan, 0),
            "help": f"{angka(ringkas['induk'])} orang di unit induk PT PLN (Persero).",
        },
        {
            "label": "Subholding",
            "value": persen(100 * ringkas["subholding"] / ditempatkan, 0),
            "help": f"{angka(ringkas['subholding'])} orang di anak perusahaan PLN Group.",
        },
        {"label": "Unit penerima", "value": angka(ringkas["unit"]), "help": "Unit induk yang menerima minimal satu orang."},
        {
            # Cakupan ("non-RBB") ditulis di label, bukan cuma di tooltip: tanpa itu
            # angka KPI dan chart "Kuota dan realisasi per tahun" di bawahnya terbaca
            # saling bertentangan (temuan audit 2026-09-16).
            "label": "Kuota terpenuhi, non-RBB",
            "value": persen(100 * non_rbb["realisasi"].sum() / non_rbb["kuota"].sum(), 0) if not non_rbb.empty else "-",
            "help": "Realisasi dibanding kuota, di luar tahun RBB. Kuota RBB adalah kohort penuh FHCI, "
            "jadi rasionya tidak sebanding dengan tahun lain.",
        },
    ]
)

# ── Treemap ─────────────────────────────────────────────────────────────────
treemap_df = metrics.treemap_f(f)
with ui.seksi(
    "Penempatan per unit induk dan bidang",
    "Tiap kotak besar satu unit induk, kotak di dalamnya bidang pembidangan. Luas kotak "
    "sebanding dengan jumlah orang yang ditempatkan. Klik satu unit untuk memperbesar, klik "
    "judul di atas untuk kembali.\n\nWarna menandai bidang pembidangan, bukan unit: lima bidang "
    "terbesar punya warnanya sendiri, sisanya jadi Lainnya. Kotak yang terlalu kecil untuk memuat "
    "tulisan dibiarkan kosong, namanya tetap muncul saat kursor lewat.\n\nHanya penempatan yang "
    "tercatat unit induknya: penempatan subholding tidak punya unit induk, dan sebagian penempatan "
    "PLN induk kolom unitnya kosong.",
):
    if treemap_df.empty:
        ui.kosong()
    else:
        # Warna dipakai untuk BIDANG, bukan unit. Sebelumnya tiap unit dapat hue sendiri
        # (~40 hue berputar) padahal nama unit sudah tercetak di kotaknya — warna tidak
        # membawa informasi apa pun. Lima slot teratas + "Lainnya" = batas palet (6).
        besar = treemap_df.groupby("bidang_pembidangan")["n"].sum().nlargest(5).index.tolist()
        treemap_df = treemap_df.assign(
            bidang=treemap_df["bidang_pembidangan"].where(treemap_df["bidang_pembidangan"].isin(besar), "Lainnya")
        )
        peta_warna = {nama: warna[i] for i, nama in enumerate(besar)}
        peta_warna["Lainnya"] = t["netral"]
        # Simpul induk (baris unit) tidak punya nilai bidang; Plotly memberinya label "(?)".
        peta_warna["(?)"] = t["surface_card"]
        treemap = px.treemap(
            treemap_df,
            path=["unit_induk", "bidang_pembidangan"],
            values="n",
            color="bidang",
            color_discrete_map=peta_warna,
        )
        treemap.update_traces(
            textinfo="label+value",
            marker=dict(line=dict(width=2, color=t["surface_page"])),
            hovertemplate="%{label}<br>%{value:,} orang<extra></extra>",
            root_color=t["surface_page"],
        )
        theme.plotly_layout(treemap, height=460)
        # Label yang tidak muat dihilangkan, bukan dipaksa mengecil sampai tak terbaca.
        treemap.update_layout(separators=",.", uniformtext=dict(minsize=11, mode="hide"))
        ui.legenda([(nama, peta_warna[nama]) for nama in besar] + [("Lainnya", t["netral"])])
        st.plotly_chart(treemap, width="stretch", config={"displayModeBar": False})

# ── Pola per tahun ──────────────────────────────────────────────────────────
kiri, kanan = st.columns(2, gap="medium")

with kiri:
    bidang = metrics.bidang_tahun(f)
    with ui.seksi(
        "Porsi bidang per tahun",
        "Tiap sel adalah persentase penempatan satu tahun program yang jatuh ke bidang itu. "
        "Satu kolom berjumlah 100%. Makin gelap makin besar porsinya.",
    ):
        if bidang.empty:
            ui.kosong()
        else:
            urutan_bidang = bidang.groupby("bidang")["n"].sum().sort_values(ascending=False).index.tolist()
            bidang["tahun"] = bidang["tahun"].astype(str)
            st.altair_chart(
                grafik.heatmap(
                    bidang,
                    "tahun",
                    "bidang",
                    "pct",
                    urutan_y=urutan_bidang,
                    domain=(0, float(bidang["pct"].max())),
                    tinggi_baris=30,
                    tooltip=[
                        alt.Tooltip("tahun:N", title="Tahun"),
                        alt.Tooltip("bidang:N", title="Bidang"),
                        alt.Tooltip("n:Q", title="Orang", format=".0f"),
                        alt.Tooltip("pct:Q", title="Porsi (%)", format=".1f"),
                    ],
                ),
                width="stretch",
            )

with kanan:
    perusahaan = metrics.perusahaan_tahun(f)
    slot = ["Induk", "ICON", "IP", "NP", "ND", "ES"]
    with ui.seksi(
        "PLN induk dan subholding per tahun",
        "Komposisi penempatan tiap tahun program: PLN induk dan tiap subholding, dalam persen. "
        "Subholding kecil (EPI, BTM, HLY) digabung sebagai Lainnya.\n\nICON: PLN Icon Plus. "
        "IP: PLN Indonesia Power. NP: PLN Nusantara Power. ND: PLN Nusa Daya. ES: PLN "
        "Electricity Services.",
    ):
        if perusahaan.empty:
            ui.kosong()
        else:
            perusahaan["perusahaan"] = perusahaan["perusahaan"].where(perusahaan["perusahaan"].isin(slot), "Lainnya")
            perusahaan = perusahaan.groupby(["tahun", "perusahaan"], as_index=False)["n"].sum()
            perusahaan["teks"] = perusahaan["n"].map(angka)
            st.altair_chart(
                alt.Chart(perusahaan)
                .mark_bar(stroke=t["surface_card"], strokeWidth=1.5, height=20)
                .encode(
                    y=alt.Y("tahun:O", title=None, axis=alt.Axis(ticks=False, domain=False)),
                    x=alt.X("n:Q", stack="normalize", title=None, axis=alt.Axis(format="%", tickCount=5)),
                    color=alt.Color(
                        "perusahaan:N",
                        scale=alt.Scale(domain=slot + ["Lainnya"], range=warna + [t["netral"]]),
                        legend=alt.Legend(title=None, orient="top", columns=7, symbolSize=80),
                    ),
                    order=alt.Order("urut:Q"),
                    tooltip=[
                        alt.Tooltip("tahun:O", title="Tahun"),
                        alt.Tooltip("perusahaan:N", title="Perusahaan"),
                        alt.Tooltip("teks:N", title="Orang"),
                    ],
                )
                .transform_calculate(urut=f"indexof({slot + ['Lainnya']}, datum.perusahaan)")
                .properties(height=max(38 * perusahaan["tahun"].nunique(), 140)),
                width="stretch",
            )

# ── Kuota vs realisasi ──────────────────────────────────────────────────────
with ui.seksi(
    "Kuota dan realisasi per tahun",
    "Batang lebar abu adalah kuota profesi, batang sempit biru di dalamnya adalah orang yang "
    "benar-benar ditempatkan. Persen di atas batang adalah capaian.\n\nTahun bertanda RBB "
    "memakai dasar hitung yang berbeda: kuotanya kohort penuh FHCI, sedangkan realisasi hanya "
    "menghitung yang tercatat serah-terima di sistem PLN. Capaiannya tidak sebanding dengan "
    "tahun non-RBB dan tidak dijumlahkan ke KPI di atas.",
):
    if kuota.empty:
        ui.kosong()
    else:
        kuota["tahun"] = kuota.apply(lambda b: f"{b.tahun} RBB" if b.rbb else str(b.tahun), axis=1)
        st.altair_chart(
            grafik.bullet(kuota, "tahun", "kuota", "realisasi", label_target="Kuota", label_capaian="Realisasi", tinggi=240),
            width="stretch",
        )

# ── Lapis analis ─────────────────────────────────────────────────────────────
if ui.mode_analis():
    ui.lapis_analis(treemap_df, "penempatan_per_unit_bidang.csv", "Penempatan per unit induk x bidang")
