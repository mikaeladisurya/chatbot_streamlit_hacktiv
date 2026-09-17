"""Primitif tata letak yang dipakai semua halaman.

Revamp 2026-09-16: halaman jadi dashboard penuh (filter global, banyak seksi chart,
bentuk chart beragam). Doktrin D1 (judul = kalimat temuan) dan D5 (maksimal 4 blok)
dicabut; yang bertahan adalah penjelasan on-demand (sekarang lewat tombol (?) per
seksi), tanpa emoji, tanpa gradien, tanpa caption permanen. Lihat
docs/design_system.md §11.

Prinsip: native dulu (`st.metric`, `st.popover`, `st.pills`), CSS kustom hanya untuk
yang tidak punya padanan di config.toml.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import pandas as pd
import streamlit as st

from core import metrics
from core.filters import Filter

LABEL_JENIS = {
    "REGULER": "Reguler",
    "DIASPORA": "Diaspora",
    "AFIRMASI": "Afirmasi",
    "RBB": "RBB",
    "BIDANG": "Bidang",
    "CAMPUS": "Campus hiring",
    "S2": "S2",
}


def gaya_global() -> None:
    """CSS kecil yang tidak punya padanan di config.toml. Dipanggil sekali dari
    streamlit_app.py. Warna tidak diatur di sini; semua warna tetap dari tema.

    - Angka tabular: digit KPI tidak bergoyang saat filter berubah (design_system §6).
    - Judul seksi: jarak rapat antara judul dan chart di bawahnya.
    """
    st.html(
        """
        <style>
          [data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; }
          [data-testid="stMetricValue"] > div { font-weight: 700; letter-spacing: -0.01em; }
          /* Nav atas melayang di atas isi: padding 2.2rem menyembunyikan baris
             pertama halaman di belakang bar navigasi. */
          .block-container { padding-top: 4.5rem; }
          [class*="st-key-seksi_"] h4 { padding: 0; margin: 0; }
        </style>
        """
    )


def judul_halaman(judul: str) -> None:
    """Judul halaman polos: tanpa spanduk gradien, tanpa subjudul permanen."""
    st.title(judul)


def bar_filter() -> Filter:
    """Bar filter global: tahun program, jenis program, jenjang.

    Pilihan bertahan lintas halaman lewat `persist_state="session"`. Pilihan kosong
    berarti "semua". Dipanggil tepat di bawah judul halaman yang datanya bisa disaring.
    """
    opsi = metrics.opsi_filter()
    with st.container(horizontal=True, vertical_alignment="bottom", gap="medium", key="bar_filter"):
        tahun = st.pills(
            "Tahun program",
            opsi["tahun"],
            selection_mode="multi",
            key="f_tahun",
            persist_state="session",
        )
        jenis = st.multiselect(
            "Jenis program",
            opsi["jenis"],
            format_func=lambda v: LABEL_JENIS.get(v, v),
            placeholder="Semua jenis",
            key="f_jenis",
            persist_state="session",
            width=260,
        )
        jenjang = st.pills(
            "Jenjang",
            opsi["jenjang"],
            selection_mode="multi",
            key="f_jenjang",
            persist_state="session",
        )
    return Filter(tahun=tuple(sorted(tahun)), jenis=tuple(sorted(jenis)), jenjang=tuple(sorted(jenjang)))


@contextmanager
def seksi(judul: str, bantuan: str | None = None, key: str | None = None) -> Iterator[None]:
    """Satu kelompok chart: judul benda (bukan kalimat temuan) + tombol (?) di tepi kanan.

    `bantuan` berisi cara membaca chart dan catatan data, dibuka on-demand lewat
    popover, tidak pernah jadi caption permanen di bawah chart.
    """
    kunci = key or "seksi_" + "".join(c if c.isalnum() else "_" for c in judul.lower())
    with st.container(border=True, key=kunci):
        with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
            st.markdown(f"#### {judul}")
            if bantuan:
                with st.popover(
                    "",
                    icon=":material/help:",
                    type="tertiary",
                    help="Cara membaca",
                ):
                    st.markdown(bantuan)
        yield


def kosong(pesan: str = "Tidak ada data untuk kombinasi filter ini.", saran: bool = True) -> None:
    """Keadaan kosong di dalam seksi: sebab + tindakan, bukan sekadar 'No data'.

    `saran=False` bila kosongnya memang sifat data (bukan filter yang terlalu sempit),
    supaya pengguna tidak disuruh melonggarkan filter yang tidak akan mengubah apa pun.
    """
    teks = f"{pesan} Longgarkan filter di atas untuk melihat datanya." if saran else pesan
    st.info(teks, icon=":material/filter_alt_off:")


def legenda(pasangan: list[tuple[str, str]]) -> None:
    """Legenda mendatar untuk chart yang tidak bisa menggambar legendanya sendiri.

    Treemap Plotly tidak punya legenda, jadi kunci warnanya harus ikut dirender di
    sebelah chart — legenda bagian dari chart, bukan isi popover bantuan.
    """
    titik = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:.35rem;margin-right:1rem;'
        f'white-space:nowrap"><span style="width:.65rem;height:.65rem;border-radius:2px;'
        f'background:{w}"></span>{nama}</span>'
        for nama, w in pasangan
    )
    st.markdown(
        f'<div style="display:flex;flex-wrap:wrap;font-size:.82rem;opacity:.85;'
        f'margin:.1rem 0 .4rem">{titik}</div>',
        unsafe_allow_html=True,
    )


def baris_kpi(items: list[dict[str, Any]]) -> None:
    """Baris KPI native: tanpa badge tertulis, konteks di tooltip `help=`.

    Tiap item: {"label": str, "value": str, "help": str (opsional),
    "chart_data": list (opsional, sparkline), "chart_type": "bar"|"line" (opsional)}.
    """
    with st.container(horizontal=True):
        for item in items:
            st.metric(
                item["label"],
                item["value"],
                help=item.get("help"),
                border=True,
                chart_data=item.get("chart_data"),
                chart_type=item.get("chart_type", "bar"),
                delta_color="off",
            )


def spanduk_dimodelkan(teks: str) -> None:
    """Peringatan permanen, HANYA untuk halaman yang seluruh isinya dimodelkan.

    Native st.warning: ikon + warna status bawaan tema, tanpa HTML kustom.
    """
    st.warning(f"**Seluruh halaman ini dimodelkan.** {teks}", icon=":material/science:")


def mode_analis() -> bool:
    """Status sakelar lapis analis. Berlaku lintas halaman."""
    st.session_state.setdefault("mode_analis", False)
    return st.session_state["mode_analis"]


def sakelar_mode_analis() -> None:
    st.session_state.setdefault("mode_analis", False)
    st.toggle(
        "Mode analis",
        key="mode_analis",
        help="Menampilkan tabel rinci dan tombol unduh CSV di bawah tiap halaman.",
    )


def lapis_analis(df: pd.DataFrame, nama_berkas: str, label_tabel: str = "Data rinci") -> None:
    """Tabel + unduh CSV, dipanggil di dalam `if ui.mode_analis():` pada tiap halaman."""
    st.markdown(f"**{label_tabel}**")
    st.dataframe(df, hide_index=True, width="stretch")
    st.download_button(
        "Unduh CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=nama_berkas,
        mime="text/csv",
        icon=":material/download:",
    )
