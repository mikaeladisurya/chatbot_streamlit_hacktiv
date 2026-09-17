"""Lapis 3 — disiplin tampilan (docs/design_system.md §11, revisi revamp 2026-09),
ditegakkan mekanis supaya "terlalu AI" tidak diam-diam kembali. D1 (judul = temuan) dan
D5 (maks 4 blok) sudah dicabut, jadi tidak diuji lagi. Jalankan:
`pytest tests/uji_disiplin.py -v`.

Ini pemeriksaan tekstual atas kode sumber `app_pages/*.py`, bukan atas output
render — proxy yang murah, bukan bukti visual. Pemeriksaan mata (terang & gelap)
tetap wajib manual per halaman.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

APP_PAGES = Path(__file__).resolve().parents[1] / "app_pages"
HALAMAN = sorted(APP_PAGES.glob("*.py"))

# Halaman analisis inti (D2: penjelasan wajib on-demand — help=/expander, bukan
# st.caption permanen). kualitas.py dikecualikan (caption jadi label sub-node
# diagram, bagian dari chart itu sendiri) dan chatbot.py (caption = chrome UI,
# bukan penjelasan angka).
HALAMAN_ANALISIS = [p for p in HALAMAN if p.name not in {"kualitas.py", "chatbot.py"}]

# Rentang blok emoji umum (D6). Ikon Material (":material/nama:") BUKAN emoji —
# sengaja tidak match pola ini.
POLA_EMOJI = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "]"
)


def _baca(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("halaman", HALAMAN, ids=lambda p: p.name)
def test_tanpa_emoji(halaman: Path):
    isi = _baca(halaman)
    ditemukan = POLA_EMOJI.findall(isi)
    assert not ditemukan, f"{halaman.name}: emoji ditemukan {ditemukan} (D6)"


@pytest.mark.parametrize("halaman", HALAMAN_ANALISIS, ids=lambda p: p.name)
def test_tanpa_caption_permanen(halaman: Path):
    isi = _baca(halaman)
    assert "st.caption(" not in isi, (
        f"{halaman.name}: st.caption() ditemukan. Penjelasan harus lewat help= atau "
        "tombol (?) ui.seksi(), bukan caption permanen di bawah chart"
    )


@pytest.mark.parametrize("halaman", HALAMAN_ANALISIS, ids=lambda p: p.name)
def test_tiap_seksi_punya_bantuan(halaman: Path):
    """Revamp 2026-09: tiap seksi chart wajib punya teks (?) cara membaca. Pemanggilan
    ui.seksi() dengan satu argumen saja (judul tanpa bantuan) ditolak."""
    isi = _baca(halaman)
    panggilan = re.findall(r"ui\.seksi\(\s*\n?\s*(\"[^\"]*\")\s*\)", isi)
    assert not panggilan, f"{halaman.name}: seksi tanpa bantuan: {panggilan}"
    assert "ui.seksi(" in isi, f"{halaman.name}: tidak memakai ui.seksi()"


@pytest.mark.parametrize("halaman", HALAMAN, ids=lambda p: p.name)
def test_tanpa_em_dash_di_teks_tampil(halaman: Path):
    """Em dash & en dash dilarang di teks yang tampil (antislop R-02). Docstring dan
    komentar dikecualikan: yang diperiksa hanya literal string di luar docstring modul."""
    isi = _baca(halaman)
    tanpa_docstring = re.sub(r'^"""[\s\S]*?"""', "", isi, count=1)
    literal = re.findall(r'"(?:[^"\\\n]|\\.)*"', tanpa_docstring)
    ditemukan = [s for s in literal if "—" in s or "–" in s]
    assert not ditemukan, f"{halaman.name}: dash di teks tampil: {ditemukan[:3]}"


@pytest.mark.parametrize("halaman", HALAMAN, ids=lambda p: p.name)
def test_tanpa_sql_di_halaman(halaman: Path):
    """Halaman tidak boleh menulis SQL agregat sendiri — semua lewat core/metrics.py
    (aturan arsitektur "satu sumber kebenaran"). Batas kata (\\b) supaya kata biasa
    seperti "selected_profile" tidak ikut ketangkap."""
    isi = _baca(halaman)
    assert not re.search(r"\bSELECT\b", isi, re.IGNORECASE), (
        f"{halaman.name}: string SQL ditemukan di halaman"
    )


@pytest.mark.parametrize("halaman", HALAMAN, ids=lambda p: p.name)
def test_tanpa_kolom_pii(halaman: Path):
    kolom_pii = ["nama_lengkap", "nik", "no_hp", "nomor_hp", "email", "alamat_lengkap"]
    isi = _baca(halaman).lower()
    ditemukan = [k for k in kolom_pii if re.search(rf"\b{k}\b", isi)]
    assert not ditemukan, f"{halaman.name}: kemungkinan kolom PII dirujuk: {ditemukan}"


@pytest.mark.parametrize("halaman", HALAMAN, ids=lambda p: p.name)
def test_chart_warna_kategori_punya_skala_eksplisit(halaman: Path):
    """Tiap alt.Color(...) harus disertai scale=alt.Scale(...) dalam beberapa baris
    — palet tidak boleh dibiarkan default Vega yang tidak konsisten dengan tema."""
    baris = _baca(halaman).splitlines()
    for i, l in enumerate(baris):
        if "alt.Color(" in l:
            jendela = "\n".join(baris[i : i + 4])
            assert "scale=" in jendela, (
                f"{halaman.name}:{i + 1}: alt.Color(...) tanpa scale= eksplisit"
            )


@pytest.mark.parametrize("halaman", HALAMAN, ids=lambda p: p.name)
def test_tanpa_hero_gradien(halaman: Path):
    isi = _baca(halaman)
    assert "linear-gradient" not in isi, f"{halaman.name}: gradien ditemukan (D6)"
