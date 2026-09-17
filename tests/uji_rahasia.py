"""Lapis 4 — kerahasiaan pesan galat.

Penyedia OpenAI-compatible menggemakan kunci yang dipakai ke dalam pesan galat 401.
Pesan itu dulu tampil mentah di browser, jadi kunci asli terbaca pengguna (temuan
audit 2026-09-16). `pesan_aman()` adalah satu-satunya jalur galat menuju layar;
tes ini menjaga jalur itu tetap tertutup. Jalankan: `pytest tests/uji_rahasia.py -v`.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from chat.chatbot import pesan_aman

AKAR = Path(__file__).resolve().parents[1]

# Bentuk asli galat LiteLLM yang bocor di audit, kuncinya diganti nilai palsu.
GALAT_401 = (
    "Error code: 401 - {'error': {'message': 'Authentication Error, Invalid proxy "
    "server token passed. Received API Key = sk-nPalsuPalsuPalsu9ChTFoqA, "
    "Key Hash (Token) =5ec3a1b2, Route = /chat/completions', 'type': "
    "'auth_error', 'code': '401'}}"
)


def test_kunci_api_tidak_lolos():
    hasil = pesan_aman(GALAT_401)
    assert "sk-nPalsuPalsuPalsu9ChTFoqA" not in hasil
    assert "5ec3a1b2" not in hasil
    # Hanya kode status dan kepala pesan, bukan payload penyedia apa adanya.
    assert hasil == "401 - Authentication Error"


@pytest.mark.parametrize(
    "galat, harapan",
    [
        (
            "Error code: 429 - {'error': {'message': 'Rate limit exceeded, please retry in 20s', 'code': '429'}}",
            "429 - Rate limit exceeded",
        ),
        (
            'Error code: 404 - {"error": {"message": "The model `qwen9` does not exist", "code": "model_not_found"}}',
            "404 - The model `qwen9` does not exist",
        ),
        ("Error code: 500 - {'error': {'message': 'Internal server error'}}", "500 - Internal server error"),
        # Tanpa payload penyedia: dibiarkan apa adanya, jangan sampai hilang keterangannya.
        ("Connection error.", "Connection error."),
        ("Request timed out.", "Request timed out."),
    ],
)
def test_bentuk_ringkas(galat: str, harapan: str):
    assert pesan_aman(galat) == harapan


def test_kode_tanpa_pesan_tetap_menyebut_kode():
    assert pesan_aman("Error code: 503 - <html>Service Unavailable</html>").startswith("503 - ")


@pytest.mark.parametrize(
    "bocor",
    [
        "Received API Key = sk-abcdef1234567890",
        "api_key: sk-or-v1-0011223344556677",
        "Authorization: Bearer abcdef1234567890",
        "motherduck_token = eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6ImFAYi5jb20ifQ.c2lnbmF0dXJlXzEyMw",
        "Key Hash (Token) =5ec3a1b2",
    ],
)
def test_pola_rahasia_tersensor(bocor: str):
    hasil = pesan_aman(bocor)
    assert "[disensor]" in hasil
    # Bagian nilai setelah pemisah tidak boleh tersisa utuh.
    nilai = re.split(r"[:=]\s*", bocor)[-1]
    assert nilai not in hasil


def test_nilai_rahasia_terkonfigurasi_disensor_harfiah(monkeypatch):
    """Kunci penyedia lain bisa berbentuk apa pun, jadi nilai yang kita kirim
    sendiri dicocokkan apa adanya, bukan hanya lewat pola."""
    aneh = "KUNCI-BENTUK-ASING-tanpa-awalan-sk-9911"
    monkeypatch.setattr("chat.chatbot._nilai_rahasia", lambda: [aneh])
    assert aneh not in pesan_aman(f"Gagal: provider menolak {aneh} untuk model ini")


def test_pesan_dipotong_dan_dirapikan():
    panjang = pesan_aman("baris satu\n\n" + "x" * 900)
    assert len(panjang) <= 303
    assert "\n" not in panjang


def test_pesan_kosong_tetap_ada_isinya():
    assert pesan_aman(Exception()).strip()


def test_tidak_ada_galat_mentah_ke_layar():
    """Setiap galat yang jadi teks untuk pengguna wajib lewat `pesan_aman`.

    Menjaga jalur baru tidak lupa disensor: pemeriksaan tekstual, bukan bukti
    runtime, tapi cukup untuk menangkap `f"...{exc}"` yang ditambahkan nanti.
    """
    pola_mentah = re.compile(r"""f["'][^"']*\{exc[^"']*\}""")
    pelanggaran = []
    for berkas in sorted((AKAR / "chat").glob("*.py")) + sorted((AKAR / "app_pages").glob("*.py")):
        for nomor, baris in enumerate(berkas.read_text(encoding="utf-8").splitlines(), 1):
            if pola_mentah.search(baris) and "pesan_aman" not in baris:
                pelanggaran.append(f"{berkas.name}:{nomor}: {baris.strip()}")
    assert not pelanggaran, "galat mentah ditampilkan tanpa sensor:\n" + "\n".join(pelanggaran)
