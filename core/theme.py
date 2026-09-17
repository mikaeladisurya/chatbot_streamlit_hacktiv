"""Token warna — mencerminkan docs/design_system.md.

Nilai di sini dijaga selaras dengan `.streamlit/config.toml`. config.toml mengatur
tampilan bawaan Streamlit & chart; modul ini dipakai komponen HTML kustom yang
harus mewarnai dirinya sendiri (`st.context.theme` hanya memberi `.type`, bukan
warna yang sudah diresolusi).
"""

from __future__ import annotations

from typing import Any

import streamlit as st

# Palet kategori — urutan slot TETAP, tidak pernah diputar-ulang.
SERI_TERANG = ["#0077C8", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#4a3aa7"]
SERI_GELAP = ["#2E9BE0", "#d95926", "#199e70", "#c98500", "#d55181", "#9085e9"]

# Palet status — dipesan, tidak pernah jadi warna seri. Selalu dengan ikon + label.
STATUS = {
    "baik": "#0ca30c",
    "peringatan": "#fab219",
    "serius": "#ec835a",
    "kritis": "#d03b3b",
}

TOKEN_TERANG = {
    "surface_page": "#F7F9FC",
    "surface_card": "#FFFFFF",
    "border": "#E7ECF2",
    "text_primary": "#103A5D",
    "text_secondary": "#4A5A6B",
    "text_muted": "#8093A5",
    "brand_navy": "#103A5D",
    "brand_blue": "#0077C8",
    "brand_yellow": "#F9C642",
    "netral": "#B6C2CE",
    "shadow": "rgba(16, 58, 93, 0.06)",
}

TOKEN_GELAP = {
    "surface_page": "#0E1B29",
    "surface_card": "#132C42",
    "border": "#1E3A52",
    "text_primary": "#EAF4FF",
    "text_secondary": "#A8BDD0",
    "text_muted": "#6E8398",
    "brand_navy": "#0B2236",
    "brand_blue": "#2E9BE0",
    "brand_yellow": "#F9C642",
    "netral": "#48607A",
    "shadow": "rgba(0, 0, 0, 0.35)",
}


# Ramp sekuensial (docs/design_system.md §3) — satu hue, terang ke gelap. Dipakai
# heatmap. Label angka di sel gelap memakai tinta putih, lihat AMBANG_TINTA_PUTIH.
RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def mode_gelap() -> bool:
    return (st.context.theme.type or "light") == "dark"


def token() -> dict[str, str]:
    return TOKEN_GELAP if mode_gelap() else TOKEN_TERANG


def seri() -> list[str]:
    return SERI_GELAP if mode_gelap() else SERI_TERANG


def warna_seri(indeks: int) -> str:
    """Slot warna ke-n. Slot ke-7 dst tidak dibuat baru — lipat jadi 'Lainnya'."""
    palet = seri()
    if indeks >= len(palet):
        raise ValueError(
            f"Slot seri {indeks} melebihi palet ({len(palet)} slot). "
            "Lipat kategori berlebih jadi 'Lainnya' atau pecah jadi small multiples."
        )
    return palet[indeks]


def rgba(hex_warna: str, alpha: float) -> str:
    """'#0077C8', 0.35 -> 'rgba(0,119,200,0.35)' — untuk pita Sankey semi-transparan."""
    h = hex_warna.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def plotly_layout(fig: Any, height: int = 420) -> Any:
    """Terapkan ke chart eksotis (Sankey/treemap/peta).

    `st.plotly_chart` sudah otomatis membaca `chartCategoricalColors` dari
    config.toml lewat `theme="streamlit"` (default) untuk trace yang punya
    parameter `color=` (mis. px.treemap). Sankey/scatter_geo membangun warna
    node/marker secara eksplisit di go.Figure, jadi tetap perlu `seri()` manual
    di kode pemanggil — fungsi ini hanya menyeragamkan latar & font.
    """
    t = token()
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="'Plus Jakarta Sans', sans-serif", color=t["text_primary"]),
    )
    return fig
