"""Format angka gaya Indonesia: ribuan titik, desimal koma."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd


def _kosong(nilai: Any) -> bool:
    if nilai is None:
        return True
    if isinstance(nilai, float) and math.isnan(nilai):
        return True
    return pd.isna(nilai)


def angka(nilai: Any) -> str:
    """1234567 -> '1.234.567'"""
    if _kosong(nilai):
        return "-"
    return f"{int(round(float(nilai))):,}".replace(",", ".")


def desimal(nilai: Any, digit: int = 1) -> str:
    """28.4 -> '28,4'"""
    if _kosong(nilai):
        return "-"
    return f"{float(nilai):,.{digit}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def persen(nilai: Any, digit: int = 1) -> str:
    """28.4 -> '28,4%'. Masukkan angka yang SUDAH dalam skala 0-100."""
    if _kosong(nilai):
        return "-"
    return f"{desimal(nilai, digit)}%"


# Label pendek tahap seleksi untuk sumbu & legenda. `tahap_ref.nama` terlalu panjang
# ("Tes Akademik (TKB) & Bahasa Inggris") untuk sumbu chart setengah lebar.
LABEL_TAHAP = {
    "administrasi": "Administrasi",
    "adaptif": "Adaptif",
    "akademik_inggris": "Akademik & Inggris",
    "psikologi": "Psikologi",
    "fisik_mcu": "Fisik & MCU",
    "wawancara": "Wawancara",
}
URUTAN_TAHAP = list(LABEL_TAHAP.values())


def rasio(nilai: Any) -> str:
    """28.4 -> '1 : 28'"""
    if _kosong(nilai):
        return "-"
    return f"1 : {int(round(float(nilai)))}"
