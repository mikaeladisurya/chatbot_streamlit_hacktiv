"""Akses ke rekrutmen.duckdb — satu-satunya pintu masuk data.

Database dibuka **read-only** dan tidak pernah dimuat ke memori sebagai DataFrame:
isinya 4,22 juta baris. Yang di-cache adalah hasil query, bukan tabelnya.

Dua sumber data yang dipilih otomatis:

* **MotherDuck** — dipakai bila ada `motherduck_token` (env var atau st.secrets).
  Ini jalur untuk deployment di Streamlit Community Cloud, yang meng-clone repo
  tanpa berkas .duckdb 62 MB itu.
* **Berkas lokal** — bila tidak ada token. Ini jalur pengembangan sehari-hari:
  cepat, offline, tanpa kuota.

Dialek SQL sama persis di kedua mode, jadi tidak ada query yang perlu diubah.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Any, Sequence

import duckdb
import pandas as pd
import streamlit as st

# core/ -> akar repo. Berkas 62 MB ini di-gitignore; salin dari hasil build mockdb.
DB_PATH = Path(__file__).resolve().parents[1] / "data" / "rekrutmen.duckdb"

# Nama database di MotherDuck. Diunggah dari DB_PATH; lihat docs/DEPLOY.md.
MD_DATABASE = "rekrutmen"

# Tanggal potong data. Semua status ("sedang OJT", "belum SK") dihitung relatif ke sini.
TANGGAL_POTONG = date(2026, 9, 15)


def _motherduck_token() -> str | None:
    """Token MotherDuck dari env var, lalu st.secrets. None berarti mode lokal."""
    token = os.getenv("motherduck_token")
    if token:
        return token
    try:
        token = st.secrets.get("motherduck_token")
    except Exception:
        return None
    return str(token) if token else None


def koneksi_baru() -> duckdb.DuckDBPyConnection:
    """Koneksi baru yang berdiri sendiri — pemanggil wajib menutupnya.

    Dipakai chatbot, yang butuh koneksi lepas dari cache Streamlit.
    """
    token = _motherduck_token()
    if token:
        # duckdb membaca token dari env var ini saat membuka URL md:.
        os.environ["motherduck_token"] = token
        return duckdb.connect(f"md:{MD_DATABASE}")

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database tidak ditemukan di {DB_PATH}. "
            "Salin rekrutmen.duckdb ke folder data/, "
            "atau isi motherduck_token di .streamlit/secrets.toml."
        )
    return duckdb.connect(str(DB_PATH), read_only=True)


@st.cache_resource
def koneksi() -> duckdb.DuckDBPyConnection:
    """Satu koneksi dipakai bersama seluruh sesi."""
    return koneksi_baru()


@st.cache_data(ttl=3600, show_spinner=False)
def query(sql: str, params: Sequence[Any] | None = None) -> pd.DataFrame:
    """Jalankan SQL dan kembalikan DataFrame.

    Memakai `.cursor()` supaya tiap pemanggilan punya kursor sendiri — koneksi
    DuckDB dipakai bersama antar sesi Streamlit lewat cache_resource.
    """
    return koneksi().cursor().execute(sql, list(params or [])).df()


@st.cache_data(ttl=3600, show_spinner=False)
def skalar(sql: str, params: Sequence[Any] | None = None) -> Any:
    """Ambil satu nilai tunggal dari query."""
    hasil = koneksi().cursor().execute(sql, list(params or [])).fetchone()
    return hasil[0] if hasil else None


def daftar_tabel() -> list[str]:
    """Nama seluruh tabel — dipakai chatbot untuk membangun prompt skema."""
    df = query(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'main' ORDER BY 1"
    )
    return df["table_name"].tolist()
