"""Filter global dashboard — tahun program, jenis program, jenjang.

Ketiga dimensi diambil dari tabel `profesi`, bukan `gelombang`: `profesi.jenis_program`
lebih rinci (BIDANG dan CAMPUS adalah profesi di dalam gelombang REGULER, 6.829
pendaftaran), dan `profesi.tahun_program` sudah diverifikasi selalu sama dengan
`gelombang.tahun_program`.

Semua tabel transaksi (`pendaftaran`, `seleksi_tahap`, `pasca_tahap`) punya kolom
`profesi_id`, jadi satu subquery `profesi_id IN (...)` cukup untuk menyaring semuanya
tanpa JOIN tambahan yang berisiko menggandakan baris.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Filter:
    """Pilihan filter. Tuple kosong berarti "semua" untuk dimensi itu."""

    tahun: tuple[int, ...] = ()
    jenis: tuple[str, ...] = ()
    jenjang: tuple[str, ...] = ()

    @property
    def aktif(self) -> bool:
        return bool(self.tahun or self.jenis or self.jenjang)

    def klausa_profesi(self, kolom: str = "profesi_id") -> tuple[str, list]:
        """`<kolom> IN (SELECT profesi_id FROM profesi WHERE ...)` beserta parameternya.

        Tanpa filter aktif mengembalikan `TRUE`, supaya query bisa selalu menulis
        `WHERE {klausa}` tanpa cabang.
        """
        if not self.aktif:
            return "TRUE", []
        syarat: list[str] = []
        params: list = []
        for nama_kolom, nilai in (
            ("tahun_program", self.tahun),
            ("jenis_program", self.jenis),
            ("jenjang", self.jenjang),
        ):
            if nilai:
                syarat.append(f"{nama_kolom} IN ({', '.join('?' * len(nilai))})")
                params.extend(nilai)
        return (
            f"{kolom} IN (SELECT profesi_id FROM profesi WHERE {' AND '.join(syarat)})",
            params,
        )


    def klausa_pendaftaran(self, kolom: str = "pendaftaran_id") -> tuple[str, list]:
        """Untuk tabel tanpa `profesi_id` (mis. `penempatan`): saring lewat pendaftaran."""
        if not self.aktif:
            return "TRUE", []
        dalam, params = self.klausa_profesi()
        return f"{kolom} IN (SELECT pendaftaran_id FROM pendaftaran WHERE {dalam})", params

    def klausa_kandidat(self, kolom: str = "kandidat_id") -> tuple[str, list]:
        """Kandidat yang pernah melamar ke profesi dalam cakupan filter."""
        if not self.aktif:
            return "TRUE", []
        dalam, params = self.klausa_profesi()
        return f"{kolom} IN (SELECT kandidat_id FROM pendaftaran WHERE {dalam})", params


SEMUA = Filter()
