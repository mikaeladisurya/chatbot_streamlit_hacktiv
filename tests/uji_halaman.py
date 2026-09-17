"""Lapis 2 — perilaku halaman.

`streamlit.testing.v1.AppTest` dijalankan lewat titik masuk `streamlit_app.py`
(bukan tiap berkas halaman langsung — `st.page_link`/navigasi butuh konteks
`st.navigation`). Per halaman: tidak ada exception, sakelar mode analis
memunculkan tabel + tombol unduh (kecuali halaman 7 & 8 yang memang tidak punya
lapis analis). Jalankan: `pytest tests/uji_halaman.py -v`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

HALAMAN_DENGAN_LAPIS_ANALIS = [
    "app_pages/ringkasan.py",
    "app_pages/perencanaan.py",
    "app_pages/corong.py",
    "app_pages/kandidat.py",
    "app_pages/pasca.py",
    "app_pages/penempatan.py",
]

HALAMAN_TANPA_LAPIS_ANALIS = [
    "app_pages/kualitas.py",
]


def _muat(halaman: str) -> AppTest:
    at = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
    at.switch_page(halaman)
    at.run(timeout=30)
    return at


@pytest.mark.parametrize("halaman", HALAMAN_DENGAN_LAPIS_ANALIS + HALAMAN_TANPA_LAPIS_ANALIS)
def test_halaman_tanpa_exception(halaman: str):
    at = _muat(halaman)
    assert not at.exception, [str(e) for e in at.exception]


@pytest.mark.parametrize("halaman", HALAMAN_DENGAN_LAPIS_ANALIS)
def test_lapis_analis_memunculkan_tabel_dan_unduh(halaman: str):
    at = _muat(halaman)
    assert not at.exception
    at.toggle[0].set_value(True)
    at.run(timeout=30)
    assert not at.exception, [str(e) for e in at.exception]
    assert len(at.get("dataframe")) >= 1
    assert len(at.get("download_button")) >= 1


def test_ringkasan_adalah_halaman_default():
    at = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
    at.run(timeout=30)
    assert not at.exception
    assert len(at.get("metric")) == 6


def test_pindah_halaman_beruntun_tanpa_exception():
    """Simulasi klik navigasi sidebar berurutan — beberapa bug hanya muncul di
    transisi antar-halaman (cache lintas-halaman, session_state yang bocor)."""
    at = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
    at.run(timeout=30)
    for halaman in HALAMAN_DENGAN_LAPIS_ANALIS + HALAMAN_TANPA_LAPIS_ANALIS + ["app_pages/chatbot.py"]:
        at.switch_page(halaman)
        at.run(timeout=30)
        assert not at.exception, f"{halaman}: {[str(e) for e in at.exception]}"


HALAMAN_BERFILTER = [
    "app_pages/ringkasan.py",
    "app_pages/corong.py",
    "app_pages/kandidat.py",
    "app_pages/pasca.py",
    "app_pages/penempatan.py",
]

# Kombinasi filter yang pernah menjebak: satu tahun RBB saja (tanpa Administrasi &
# Adaptif), irisan sangat kecil (S2 RBB 2021, 1 orang diterima), dan irisan kosong.
KOMBINASI_FILTER = [
    {"tahun": [2023, 2025]},
    {"jenis": ["RBB"]},
    {"tahun": [2021], "jenis": ["RBB"], "jenjang": ["S2"]},
    {"tahun": [2019], "jenis": ["RBB"]},
]


@pytest.mark.parametrize("halaman", HALAMAN_BERFILTER)
@pytest.mark.parametrize("pilihan", KOMBINASI_FILTER, ids=lambda p: "-".join(f"{k}{v}" for k, v in p.items()))
def test_halaman_berfilter_tahan_kombinasi(halaman: str, pilihan: dict):
    at = _muat(halaman)
    at.button_group(key="f_tahun").set_value(pilihan.get("tahun", []))
    at.multiselect(key="f_jenis").set_value(pilihan.get("jenis", []))
    at.button_group(key="f_jenjang").set_value(pilihan.get("jenjang", []))
    at.run(timeout=30)
    assert not at.exception, [str(e.value) for e in at.exception]


def test_filter_bertahan_saat_pindah_halaman():
    at = _muat("app_pages/corong.py")
    at.button_group(key="f_tahun").set_value([2024])
    at.run(timeout=30)
    at.switch_page("app_pages/perencanaan.py")
    at.run(timeout=30)
    at.switch_page("app_pages/penempatan.py")
    at.run(timeout=30)
    assert at.button_group(key="f_tahun").value == [2024]


def test_chatbot_tanpa_exception():
    at = _muat("app_pages/chatbot.py")
    assert not at.exception, [str(e) for e in at.exception]
