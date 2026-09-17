"""Implementasi kamus metrik — SATU definisi untuk seluruh aplikasi.

Aturan arsitektur: **halaman tidak boleh menulis SQL agregat sendiri.** Semua angka
yang tampil di dashboard (dan yang dirujuk chatbot) berasal dari modul ini, supaya
halaman 1, halaman 6, dan jawaban chatbot tidak pernah berbeda.

Kode metrik (M01, M08, …) merujuk ke `docs/metrik.md`. Kalau butuh angka baru,
tambahkan metriknya di dokumen itu dulu, baru di sini.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.db import TANGGAL_POTONG, query, skalar
from core.filters import SEMUA, Filter

_KOORDINAT_PATH = Path(__file__).resolve().parents[1] / "data" / "koordinat.csv"

# ──────────────────────────────────────────────────────────────────────────────
# A. Ringkasan (halaman 1)
# ──────────────────────────────────────────────────────────────────────────────


def opsi_filter() -> dict[str, list]:
    """Nilai yang tersedia untuk bar filter global, diurutkan menurut volume pendaftaran."""
    df = query(
        """
        SELECT pr.tahun_program, pr.jenis_program, pr.jenjang, count(*) AS n
        FROM pendaftaran p JOIN profesi pr USING (profesi_id)
        GROUP BY 1, 2, 3
        """
    )
    return {
        "tahun": sorted(df["tahun_program"].unique().tolist()),
        "jenis": df.groupby("jenis_program")["n"].sum().sort_values(ascending=False).index.tolist(),
        "jenjang": ["D-III", "S1/D-IV", "S2"],
    }


def ringkasan() -> dict[str, float]:
    """M01–M07 sekaligus — dipakai baris KPI halaman 1."""
    return {
        "pendaftaran": skalar("SELECT count(*) FROM pendaftaran"),
        "pelamar": skalar("SELECT count(DISTINCT kandidat_id) FROM pendaftaran"),
        "akun": skalar("SELECT count(*) FROM kandidat"),
        "diterima": skalar(
            "SELECT count(*) FROM pendaftaran WHERE hasil_akhir = 'DITERIMA'"
        ),
        "rasio": skalar(
            "SELECT round(count(*)*1.0 / nullif(sum(CASE WHEN hasil_akhir='DITERIMA' "
            "THEN 1 END), 0), 1) FROM pendaftaran"
        ),
        "sudah_sk": skalar(
            "SELECT count(*) FROM penempatan WHERE status_sk = 'SUDAH'"
        ),
        "sedang_ojt": skalar(
            "SELECT count(*) FROM pasca_tahap "
            "WHERE tahap_kode = 'ojt' AND status = 'BERJALAN'"
        ),
    }


def tren_tahunan() -> pd.DataFrame:
    """M11 — pendaftaran & diterima per tahun program, dipisah jalur."""
    return query(
        """
        SELECT g.tahun_program AS tahun,
               g.sumber_rekrutmen AS jalur,
               count(*) AS pendaftaran,
               sum(CASE WHEN p.hasil_akhir = 'DITERIMA' THEN 1 ELSE 0 END) AS diterima
        FROM pendaftaran p
        JOIN gelombang g USING (gelombang_id)
        GROUP BY 1, 2
        ORDER BY 1
        """
    )


# ──────────────────────────────────────────────────────────────────────────────
# B. Tahapan seleksi (halaman 3)
# ──────────────────────────────────────────────────────────────────────────────


def funnel_seleksi(f: Filter = SEMUA) -> pd.DataFrame:
    """M08 — enam tahap seleksi PLN dengan konversi & no-show.

    Catatan: tahap `administrasi` tidak punya kehadiran (seleksi dokumen), jadi
    `pct_no_show`-nya NULL — bukan 0. Jangan diisi nol saat menampilkan.
    """
    klausa, params = f.klausa_profesi("t.profesi_id")
    return query(
        f"""
        SELECT r.urutan,
               r.tahap_kode,
               r.nama,
               count(*) AS masuk,
               sum(CASE WHEN t.status_hadir = 'HADIR' THEN 1 ELSE 0 END) AS hadir,
               sum(CASE WHEN t.hasil = 'LULUS' THEN 1 ELSE 0 END) AS lulus,
               round(100.0 * sum(CASE WHEN t.hasil = 'LULUS' THEN 1 ELSE 0 END)
                     / count(*), 1) AS pct_lulus,
               round(100.0 * sum(CASE WHEN t.status_hadir = 'TIDAK_HADIR' THEN 1 ELSE 0 END)
                     / nullif(sum(CASE WHEN t.status_hadir IS NOT NULL THEN 1 END), 0),
                     1) AS pct_no_show
        FROM seleksi_tahap t
        JOIN tahap_ref r USING (tahap_kode)
        WHERE {klausa}
        GROUP BY 1, 2, 3
        ORDER BY 1
        """,
        params,
    )


def gugur_per_tahap() -> pd.DataFrame:
    """M10 — di tahap mana pendaftaran berhenti."""
    return query(
        """
        SELECT tahap_gugur, count(*) AS gugur
        FROM pendaftaran
        WHERE hasil_akhir = 'GAGAL'
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )


def no_show_keseluruhan() -> float:
    """M09 — persentase tidak hadir di seluruh tahap yang punya kehadiran."""
    return skalar(
        """
        SELECT round(100.0 * sum(CASE WHEN status_hadir = 'TIDAK_HADIR' THEN 1 ELSE 0 END)
               / nullif(count(status_hadir), 0), 1)
        FROM seleksi_tahap
        """
    )


def no_show_per_tahap_mode() -> pd.DataFrame:
    """M32 — no-show per tahap x mode online/offline.

    Jangkar temuan halaman Tahapan Seleksi: tes online kehilangan jauh lebih banyak
    peserta daripada offline. Menggantikan hipotesis jarak tempat tinggal, yang gugur
    setelah diuji (kota_domisili dibagikan acak seragam — lihat ISSUES_SEBARAN.md).
    """
    return query(
        """
        SELECT tahap_kode, mode,
               round(100.0 * sum(CASE WHEN status_hadir = 'TIDAK_HADIR' THEN 1 ELSE 0 END)
                     / count(*), 1) AS pct_no_show
        FROM seleksi_tahap
        WHERE status_hadir IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 3 DESC
        """
    )


def funnel_fhci() -> pd.DataFrame:
    """M12 — corong FHCI (jalur RBB, sebelum masuk sistem PLN). AGREGAT, tanpa kandidat_id."""
    return query(
        """
        SELECT tahun_program, urutan, nama, jumlah_masuk, jumlah_lulus,
               round(100.0 * jumlah_lulus / jumlah_masuk, 1) AS pct_lulus
        FROM seleksi_tahap_agregat
        ORDER BY tahun_program, urutan
        """
    )


def jejak_rbb() -> pd.DataFrame:
    """M29 — berapa persen pelamar FHCI yang berjejak di sistem PLN.

    WAJIB pakai CTE, JANGAN JOIN langsung seleksi_tahap_agregat ke pendaftaran —
    tabel agregat punya 3 baris per tahun, join langsung menggandakan hasil 3x.
    """
    return query(
        """
        WITH fhci AS (
            SELECT tahun_program, max(CASE WHEN urutan = -3 THEN jumlah_masuk END) AS pelamar_fhci
            FROM seleksi_tahap_agregat GROUP BY 1
        ), pln AS (
            SELECT g.tahun_program, count(*) AS masuk_pln
            FROM pendaftaran p JOIN gelombang g USING (gelombang_id) GROUP BY 1
        )
        SELECT f.tahun_program AS tahun, f.pelamar_fhci, p.masuk_pln,
               round(100.0 * p.masuk_pln / f.pelamar_fhci, 2) AS pct_terlihat
        FROM fhci f LEFT JOIN pln p USING (tahun_program)
        ORDER BY 1
        """
    )


def hasil_seleksi(f: Filter = SEMUA) -> dict[str, float]:
    """M01 + M05 + M07 dalam cakupan filter — baris KPI halaman Tahapan Seleksi."""
    klausa, params = f.klausa_profesi()
    df = query(
        f"""
        SELECT count(*) AS pendaftaran,
               sum(CASE WHEN hasil_akhir = 'DITERIMA' THEN 1 ELSE 0 END) AS diterima,
               sum(CASE WHEN titik_masuk = 'akademik_inggris' THEN 1 ELSE 0 END) AS masuk_rbb
        FROM pendaftaran
        WHERE {klausa}
        """,
        params,
    )
    return df.iloc[0].fillna(0).to_dict()


def lulus_tahap_tahun(f: Filter = SEMUA) -> pd.DataFrame:
    """M45 — persentase lulus per tahap x tahun program (heatmap Tahapan Seleksi).

    Pola yang dicari: kohort 2023 & 2025 menggugurkan separuh peserta wawancara
    (~48%, tahun lain ~80%) sementara lulus psikologinya justru naik.
    """
    klausa, params = f.klausa_profesi("t.profesi_id")
    return query(
        f"""
        SELECT pr.tahun_program AS tahun, r.urutan, r.tahap_kode, count(*) AS masuk,
               round(100.0 * sum(CASE WHEN t.hasil = 'LULUS' THEN 1 ELSE 0 END)
                     / count(*), 1) AS pct_lulus
        FROM seleksi_tahap t
        JOIN tahap_ref r USING (tahap_kode)
        JOIN profesi pr ON pr.profesi_id = t.profesi_id
        WHERE {klausa}
        GROUP BY 1, 2, 3
        ORDER BY 1, 2
        """,
        params,
    )


def no_show_tahun_mode(f: Filter = SEMUA) -> pd.DataFrame:
    """M46 — persentase tidak hadir per tahun program x mode tes (online/offline)."""
    klausa, params = f.klausa_profesi("t.profesi_id")
    return query(
        f"""
        SELECT pr.tahun_program AS tahun, t.mode, count(*) AS terjadwal,
               round(100.0 * sum(CASE WHEN t.status_hadir = 'TIDAK_HADIR' THEN 1 ELSE 0 END)
                     / count(*), 1) AS pct_no_show
        FROM seleksi_tahap t
        JOIN profesi pr ON pr.profesi_id = t.profesi_id
        WHERE t.status_hadir IS NOT NULL AND {klausa}
        GROUP BY 1, 2
        ORDER BY 1, 2
        """,
        params,
    )


def sebaran_skor(f: Filter = SEMUA) -> pd.DataFrame:
    """M47 — sebaran skor tes Adaptif & Akademik per pita 5 poin, dipisah hasil.

    Skor DIMODELKAN (`sumber_skor`) — sistem asli hanya menyimpan lulus/gagal. Batas
    lulus di data ini tajam di 60: seluruh skor >= 60 lulus, seluruh skor < 60 gugur.
    """
    klausa, params = f.klausa_profesi()
    return query(
        f"""
        SELECT t.tahap_kode, t.hasil,
               least(floor(t.skor_total / 5) * 5, 95) AS pita,
               count(*) AS n
        FROM seleksi_tahap t
        WHERE t.tahap_kode IN ('adaptif', 'akademik_inggris')
          AND t.skor_total IS NOT NULL AND {klausa}
        GROUP BY 1, 2, 3
        ORDER BY 1, 3
        """,
        params,
    )


def durasi_tahap(f: Filter = SEMUA) -> pd.DataFrame:
    """M48 — hari sejak melamar sampai tiap tahap dijadwalkan (p10, median, p90)."""
    klausa, params = f.klausa_profesi("t.profesi_id")
    return query(
        f"""
        SELECT r.urutan, r.tahap_kode,
               quantile_cont(date_diff('day', p.tanggal_lamar, t.tanggal_tahap), 0.1) AS p10,
               median(date_diff('day', p.tanggal_lamar, t.tanggal_tahap)) AS median,
               quantile_cont(date_diff('day', p.tanggal_lamar, t.tanggal_tahap), 0.9) AS p90
        FROM seleksi_tahap t
        JOIN pendaftaran p USING (pendaftaran_id)
        JOIN tahap_ref r ON r.tahap_kode = t.tahap_kode
        WHERE {klausa}
        GROUP BY 1, 2
        ORDER BY 1
        """,
        params,
    )


def lulus_per_vendor(f: Filter = SEMUA) -> pd.DataFrame:
    """M49 — persentase lulus per vendor tes psikologi & fisik/MCU (peserta hadir saja).

    Label SENGAJA kode vendor + kota basis, bukan `vendor.nama`: nama di tabel itu nama
    lembaga sungguhan, sementara penunjukan & hasilnya DIMODELKAN. Menempelkan tingkat
    lulus rekaan ke nama lembaga nyata akan terbaca sebagai klaim kinerja mereka.
    """
    klausa, params = f.klausa_profesi("t.profesi_id")
    return query(
        f"""
        SELECT t.tahap_kode, t.vendor_id || ' ' || coalesce(v.kota_basis, '') AS vendor,
               count(*) AS peserta,
               round(100.0 * sum(CASE WHEN t.hasil = 'LULUS' THEN 1 ELSE 0 END)
                     / count(*), 1) AS pct_lulus
        FROM seleksi_tahap t
        JOIN tahap_ref r USING (tahap_kode)
        LEFT JOIN vendor v ON v.vendor_id = t.vendor_id
        WHERE t.vendor_id IS NOT NULL AND t.status_hadir = 'HADIR' AND {klausa}
        GROUP BY 1, 2
        ORDER BY 1, 4 DESC
        """,
        params,
    )


def alasan_gugur_administrasi(f: Filter = SEMUA) -> pd.DataFrame:
    """M50 — alasan gugur di seleksi administrasi.

    Satu pendaftaran bisa punya beberapa alasan (dipisah `;`), jadi totalnya adalah
    jumlah penyebutan, lebih besar dari jumlah orang yang gugur.
    """
    klausa, params = f.klausa_profesi()
    return query(
        f"""
        SELECT alasan, count(*) AS n
        FROM (
            SELECT unnest(string_split(alasan_gagal, ';')) AS alasan
            FROM pendaftaran
            WHERE tahap_gugur = 'administrasi' AND alasan_gagal IS NOT NULL AND {klausa}
        )
        GROUP BY 1
        ORDER BY 2 DESC
        """,
        params,
    )


# ──────────────────────────────────────────────────────────────────────────────
# C. Perencanaan (halaman 2)
# ──────────────────────────────────────────────────────────────────────────────


def gap_ftk() -> dict[str, float]:
    """M13 — formasi vs realisasi.

    WAJIB memakai `realisasi_mar_2026`: kolom `realisasi_apr_2026` hanya terisi di
    1 dari 48 unit dan menghasilkan gap palsu 33.934.
    """
    df = query(
        """
        SELECT sum(ftk_2025) AS ftk,
               sum(realisasi_mar_2026) AS realisasi,
               sum(ftk_2025) - sum(realisasi_mar_2026) AS gap
        FROM unit_induk
        """
    )
    return df.iloc[0].to_dict()


def pagu_vs_usulan() -> pd.DataFrame:
    """M16 — berapa persen usulan unit yang disetujui jadi pagu. DIMODELKAN."""
    return query(
        """
        SELECT p.tahun_program AS tahun,
               sum(p.jumlah) AS pagu,
               round(u.usulan) AS usulan,
               round(100.0 * sum(p.jumlah) / u.usulan, 1) AS pct_disetujui
        FROM pagu_rekrutmen p
        JOIN (
            SELECT tahun_program, sum(usulan) AS usulan
            FROM usulan_kebutuhan GROUP BY 1
        ) u USING (tahun_program)
        GROUP BY 1, u.usulan
        ORDER BY 1
        """
    )


def gap_ftk_per_unit(minimal_pegawai: int = 50) -> pd.DataFrame:
    """M14 — gap FTK per unit induk.

    `unit_induk` punya baris duplikat/gagal-match untuk "UID Jawa Tengah & DIY"
    (jumlah_pegawai=4, ftk_2025=144 — lihat mockdb/ISSUES_MASTER_DATA.md). Filter
    `jumlah_pegawai > 50` menyingkirkannya tanpa perlu tahu penyebabnya lebih dulu.
    """
    return query(
        """
        SELECT nama_pendek, jenis_unit, ftk_2025, realisasi_mar_2026,
               ftk_2025 - realisasi_mar_2026 AS gap
        FROM unit_induk
        WHERE jumlah_pegawai > ?
        ORDER BY gap DESC
        """,
        [minimal_pegawai],
    )


def proyeksi_per_sebab() -> pd.DataFrame:
    """M17 — proyeksi kekosongan per sebab per tahun. DIMODELKAN.

    2019–2026 saja tabel ini yang punya tahun 2026 — isi "fase perencanaan".
    """
    return query(
        """
        SELECT tahun,
               round(sum(pensiun)) AS pensiun,
               round(sum(mengundurkan_diri)) AS aps,
               round(sum(meninggal_dunia)) AS meninggal,
               round(sum(phk)) AS phk,
               round(sum(kekosongan)) AS total
        FROM proyeksi_kekosongan
        GROUP BY 1
        ORDER BY 1
        """
    )


def heatmap_kebutuhan(tahun: int = 2025) -> pd.DataFrame:
    """M31 — usulan kebutuhan per unit induk × sub-bidang. DIMODELKAN. Lapis analis."""
    return query(
        """
        SELECT unit_induk, sub_bidang, round(sum(usulan)) AS usulan
        FROM usulan_kebutuhan
        WHERE tahun_program = ?
        GROUP BY 1, 2
        ORDER BY 3 DESC
        """,
        [tahun],
    )


# ──────────────────────────────────────────────────────────────────────────────
# D bis. Kandidat & pasar tenaga kerja (halaman 4)
# ──────────────────────────────────────────────────────────────────────────────
#
# Tiga metrik yang DIBATALKAN karena kolom sumbernya dibagikan acak seragam oleh
# generator (lihat mockdb/ISSUES_SEBARAN.md): sebaran asal per provinsi, peta asal
# vs kota tes, konversi per almamater. Tidak diimplementasikan di sini — halaman 4
# memakai volume_tes_per_kota() sebagai pengganti peta.


def akun_ringkas() -> dict[str, float]:
    """Bagian dari M03/M21 — baris KPI halaman Kandidat."""
    return {
        "akun": skalar("SELECT count(*) FROM kandidat"),
        "pelamar": skalar("SELECT count(DISTINCT kandidat_id) FROM pendaftaran"),
        "lamaran_per_akun": skalar(
            "SELECT count(*) * 1.0 / count(DISTINCT kandidat_id) FROM pendaftaran"
        ),
        "tidak_melamar": skalar(
            "SELECT count(*) FROM kandidat WHERE NOT pernah_melamar"
        ),
    }


def kelengkapan_akun() -> dict[str, float]:
    """M42 — kelengkapan biodata & aktivasi akun kandidat.

    `ukuran_baju`/`body_height`/`visus_*` SENGAJA tidak dipakai sebagai sinyal
    "belum lengkap" — NULL besar (220-258 ribu) di kolom itu bukan biodata akun,
    tapi data tes fisik/MCU yang memang cuma terisi kalau kandidat sampai ke
    tahap itu.
    """
    return {
        "email_belum_aktif": skalar(
            "SELECT count(*) FROM kandidat WHERE NOT email_teraktivasi"
        ),
        "biodata_belum_lengkap": skalar(
            "SELECT count(*) FROM kandidat WHERE alamat_domisili IS NULL"
        ),
        "lengkap_dan_aktif": skalar(
            "SELECT count(*) FROM kandidat "
            "WHERE email_teraktivasi AND alamat_domisili IS NOT NULL"
        ),
    }


def jenjang_pendidikan() -> pd.DataFrame:
    """M18 — jenjang pendidikan terakhir pelamar.

    Filter `pendidikan_terakhir` WAJIB — tanpa itu baris SD/SMP/SMA (±4 baris/kandidat)
    ikut terhitung.
    """
    return query(
        """
        SELECT degree, count(*) AS n
        FROM kandidat_pendidikan
        WHERE pendidikan_terakhir
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )


def akun_baru(hari: int = 30) -> dict[str, Any]:
    """M43 — akun baru dalam `hari` terakhir, dihitung dari TANGGAL_POTONG.

    Dashboard ini alat monitoring HARIAN: "baru" berarti baru relatif hari ini
    (TANGGAL_POTONG), BUKAN relatif bulan terakhir yang kebetulan ada isinya.
    Kalau hasilnya 0, itu jawaban yang benar — artinya memang tidak ada
    pendaftaran masuk belakangan, dan itu justru yang perlu terlihat.

    `hari_sejak_gelombang_tutup` dibawa serta supaya angka 0 punya konteks:
    0 karena sepi sementara, atau 0 karena tidak ada gelombang dibuka sama sekali.
    """
    return {
        "hari": hari,
        "n": skalar(
            "SELECT count(*) FROM kandidat WHERE tanggal_daftar_akun > ? - ?",
            [TANGGAL_POTONG, hari],
        ),
        "lamaran": skalar(
            "SELECT count(*) FROM pendaftaran WHERE tanggal_lamar > ? - ?",
            [TANGGAL_POTONG, hari],
        ),
        "gelombang_aktif": skalar(
            "SELECT count(*) FROM gelombang WHERE tgl_buka <= ? AND tgl_tutup >= ?",
            [TANGGAL_POTONG, TANGGAL_POTONG],
        ),
        "hari_sejak_gelombang_tutup": skalar(
            "SELECT date_diff('day', max(tgl_tutup), ?) FROM gelombang "
            "WHERE tgl_tutup <= ?",
            [TANGGAL_POTONG, TANGGAL_POTONG],
        ),
    }


def pendaftar_per_bulan() -> pd.DataFrame:
    """M44 — jumlah pendaftaran per bulan, bulan kosong diisi 0 (bukan dilompati).

    Polanya SENGAJA bergelombang, bukan mengalir rata — lonjakan bertepatan
    pembukaan gelombang rekrutmen, diselingi bulan-bulan nol panjang di antaranya.
    """
    return query(
        """
        WITH bulan_semua AS (
            SELECT unnest(generate_series(
                (SELECT date_trunc('month', min(tanggal_lamar)) FROM pendaftaran),
                (SELECT date_trunc('month', max(tanggal_lamar)) FROM pendaftaran),
                INTERVAL 1 MONTH
            )) AS bulan
        )
        SELECT b.bulan::DATE AS bulan, count(p.tanggal_lamar) AS n
        FROM bulan_semua b
        LEFT JOIN pendaftaran p ON date_trunc('month', p.tanggal_lamar) = b.bulan
        GROUP BY 1
        ORDER BY 1
        """
    )


def gender_per_kohort() -> pd.DataFrame:
    """M19 — proporsi pria per tahun kohort.

    Kode gender adalah P=Pria, W=Wanita — BUKAN L/P. Salah baca membalik chart.
    """
    return query(
        """
        SELECT tahun_kohort AS tahun, count(*) AS n,
               round(100.0 * sum(CASE WHEN jenis_kelamin = 'P' THEN 1 ELSE 0 END)
                     / count(*), 1) AS pct_pria
        FROM kandidat
        WHERE pernah_melamar
        GROUP BY 1
        ORDER BY 1
        """
    )


def umur_pelamar() -> pd.DataFrame:
    """M33 — sebaran umur pelamar saat mendaftar akun."""
    return query(
        """
        SELECT date_diff('year', tanggal_lahir, tanggal_daftar_akun) AS umur, count(*) AS n
        FROM kandidat
        WHERE pernah_melamar AND tanggal_lahir IS NOT NULL
        GROUP BY 1
        ORDER BY 1
        """
    )


def umur_gender() -> pd.DataFrame:
    """M41 — sebaran umur (per tahun) x gender, untuk piramida penduduk.

    Kode gender adalah P=Pria, W=Wanita — BUKAN L/P. Salah baca membalik chart.
    """
    return query(
        """
        SELECT date_diff('year', tanggal_lahir, tanggal_daftar_akun) AS umur,
               jenis_kelamin, count(*) AS n
        FROM kandidat
        WHERE pernah_melamar AND tanggal_lahir IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 1
        """
    )


def rumpun_melamar_vs_diterima() -> pd.DataFrame:
    """M34 — rumpun jurusan: melamar vs diterima.

    Join lewat tabel master `program_studi` (kolom `rumpun`) — BUKAN `profesi_prodi`
    (tidak ada kolom rumpun) dan BUKAN `rumpun_jurusan` (agregat, tanpa kolom
    penghubung ke program_studi perorangan).
    """
    return query(
        """
        WITH t AS (
            SELECT ps.rumpun, count(*) AS melamar,
                   sum(CASE WHEN p.hasil_akhir = 'DITERIMA' THEN 1 ELSE 0 END) AS diterima
            FROM pendaftaran p
            JOIN kandidat_pendidikan kp
                ON kp.kandidat_id = p.kandidat_id AND kp.pendidikan_terakhir
            JOIN program_studi ps ON ps.program_studi = kp.program_studi
            GROUP BY 1
        )
        SELECT rumpun, melamar, diterima, round(100.0 * diterima / melamar, 2) AS pct
        FROM t
        ORDER BY melamar DESC
        """
    )


def volume_tes_per_kota() -> pd.DataFrame:
    """M35 — volume tes offline per kota. Jangkar peta halaman Kandidat.

    Menggantikan peta "asal vs kota tes" yang dibatalkan (kota_domisili cacat).
    `lokasi_kota` berpola benar (rasio top/bawah 37,7x), aman dipakai.
    """
    return query(
        """
        SELECT lokasi_kota, count(*) AS n
        FROM seleksi_tahap
        WHERE mode = 'offline'
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )


def volume_tes_per_kota_geo() -> pd.DataFrame:
    """M35 + koordinat statis (`data/koordinat.csv`) — jangkar peta halaman Kandidat.

    43 kota tes offline diketik tangan (lat/lon kota, bukan alamat lokasi tes persis)
    karena DuckDB tidak punya kolom geografis untuk `lokasi_kota`.
    """
    koordinat = pd.read_csv(_KOORDINAT_PATH)
    return volume_tes_per_kota().merge(
        koordinat, left_on="lokasi_kota", right_on="kota", how="inner"
    )


# ──────────────────────────────────────────────────────────────────────────────
# D. Pasca-seleksi & penempatan (halaman 5 & 6)
# ──────────────────────────────────────────────────────────────────────────────


def posisi_pipeline() -> pd.DataFrame:
    """M22 — berapa orang di tiap tahap pasca-seleksi pada tanggal potong."""
    return query(
        """
        SELECT p.tahap_kode,
               r.nama,
               min(p.urutan) AS urutan,
               sum(CASE WHEN p.status = 'SELESAI' THEN 1 ELSE 0 END) AS selesai,
               sum(CASE WHEN p.status = 'BERJALAN' THEN 1 ELSE 0 END) AS berjalan,
               count(*) AS total
        FROM pasca_tahap p
        JOIN tahap_ref r USING (tahap_kode)
        GROUP BY 1, 2
        ORDER BY 3
        """
    )


def penempatan_jenis() -> pd.DataFrame:
    """M24 — induk vs subholding."""
    return query(
        """
        SELECT jenis_penempatan, count(*) AS jumlah
        FROM penempatan
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )


def pembidangan() -> pd.DataFrame:
    """M23 — pembidangan hasil penempatan."""
    return query(
        """
        SELECT bidang_pembidangan, count(*) AS n
        FROM penempatan
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )


def sebaran_updl() -> pd.DataFrame:
    """M36 — sebaran penempatan per UPDL (11 lokasi)."""
    return query(
        """
        SELECT d.nama AS updl, count(*) AS n
        FROM penempatan p JOIN updl d ON p.updl_id = d.updl_id
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )


def timeline_kohort() -> pd.DataFrame:
    """M37 — rentang tanggal gelombang per tahun, untuk sumbu Gantt."""
    return query(
        """
        SELECT tahun_program AS tahun, min(tgl_buka) AS mulai, max(tgl_tutup) AS selesai,
               count(*) AS n_gelombang
        FROM gelombang
        GROUP BY 1
        ORDER BY 1
        """
    )


def treemap_penempatan() -> pd.DataFrame:
    """M38 — penempatan per unit induk x bidang pembidangan. Jangkar treemap halaman 6.

    Dijoin ke `unit_induk.nama_pendek` — `penempatan.unit_induk` sendiri berisi nama
    resmi panjang ("PT PLN (PERSERO) UNIT INDUK DISTRIBUSI JAWA BARAT"), tidak layak
    jadi label sel treemap.
    """
    return query(
        """
        SELECT coalesce(u.nama_pendek, p.unit_induk) AS unit_induk,
               p.bidang_pembidangan, count(*) AS n
        FROM penempatan p
        LEFT JOIN unit_induk u ON u.unit_induk = p.unit_induk
        WHERE p.unit_induk IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 3 DESC
        """
    )


def grade_masuk() -> pd.DataFrame:
    """M25 — grade masuk hasil penempatan (validasi aturan grade sesuai jenjang)."""
    return query(
        """
        SELECT kode_grade, count(*) AS n
        FROM penempatan
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )


def rencana_vs_realisasi() -> pd.DataFrame:
    """M26 — kuota profesi vs penempatan nyata per tahun.

    Tiga tahun RBB (2020, 2021, 2024) ditandai: kuotanya kohort penuh sementara yang
    tercatat di PLN hanya hasil serah-terima FHCI. Membacanya sebagai "gagal memenuhi
    target" itu keliru — kolom `jalur` disediakan supaya UI bisa memberi penanda.
    """
    return query(
        """
        SELECT k.tahun_program AS tahun,
               k.kuota,
               coalesce(r.realisasi, 0) AS realisasi,
               round(100.0 * coalesce(r.realisasi, 0) / k.kuota, 1) AS pct,
               j.jalur
        FROM (SELECT tahun_program, sum(kuota) AS kuota FROM profesi GROUP BY 1) k
        LEFT JOIN (
            SELECT tahun_program, count(*) AS realisasi FROM penempatan GROUP BY 1
        ) r USING (tahun_program)
        LEFT JOIN (
            SELECT tahun_program, max(sumber_rekrutmen) AS jalur
            FROM gelombang GROUP BY 1
        ) j USING (tahun_program)
        ORDER BY 1
        """
    )


# ──────────────────────────────────────────────────────────────────────────────
# G. Kualitas data & sumber sistem (halaman 7)
# ──────────────────────────────────────────────────────────────────────────────


def volume_per_sistem() -> pd.DataFrame:
    """M27/M39 — volume baris seleksi_tahap per sistem sumber."""
    return query(
        """
        SELECT sistem_sumber, count(*) AS n
        FROM seleksi_tahap
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )


def kelengkapan_per_kohort() -> pd.DataFrame:
    """M28 — kelengkapan kolom (blok fisik, domisili) per kualitas kohort."""
    return query(
        """
        SELECT kualitas_kohort, count(*) AS n,
               round(100.0 * count(body_height) / count(*), 1) AS pct_blok_fisik,
               round(100.0 * count(kota_domisili) / count(*), 1) AS pct_domisili
        FROM kandidat
        GROUP BY 1
        ORDER BY 1
        """
    )


def selisih_angka_rencana() -> pd.DataFrame:
    """M30 — selisih target gelombang vs pagu disetujui per tahun. DIMODELKAN."""
    return query(
        """
        SELECT g.tahun_program AS tahun, sum(g.diterima_target) AS target_gelombang, p.pagu,
               sum(g.diterima_target) - p.pagu AS selisih
        FROM gelombang g
        LEFT JOIN (SELECT tahun_program, sum(jumlah) AS pagu FROM pagu_rekrutmen GROUP BY 1) p
            USING (tahun_program)
        GROUP BY 1, p.pagu
        ORDER BY 1
        """
    )


# ──────────────────────────────────────────────────────────────────────────────
# H. Revamp 2026-09: metrik yang tunduk pada filter global
# ──────────────────────────────────────────────────────────────────────────────
#
# Fungsi lama di atas dibiarkan utuh (dirujuk tes jangkar & dokumen metrik). Fungsi
# di bagian ini menerima `Filter` dan dipakai halaman hasil revamp.
#
# "Kelompok rekrutmen" melipat 7 jenis program jadi 3 slot warna yang punya arti
# berbeda: RBB (sudah disaring FHCI), Afirmasi (khusus putra-putri daerah), dan
# Terbuka (Reguler, Diaspora, S2, Bidang, Campus). Tiga slot juga batas aman palet
# untuk scatter (docs/design_system.md §2).

_KELOMPOK_SQL = """CASE {kolom} WHEN 'RBB' THEN 'RBB' WHEN 'AFIRMASI' THEN 'Afirmasi'
                   ELSE 'Terbuka' END"""


def ringkasan_f(f: Filter = SEMUA) -> dict[str, float]:
    """M01, M02, M05, M06, M07 dalam cakupan filter — baris KPI halaman Ringkasan."""
    k_prof, p_prof = f.klausa_profesi()
    k_pend, p_pend = f.klausa_pendaftaran()
    df = query(
        f"""
        SELECT
            (SELECT count(*) FROM pendaftaran WHERE {k_prof}) AS pendaftaran,
            (SELECT count(DISTINCT kandidat_id) FROM pendaftaran WHERE {k_prof}) AS pelamar,
            (SELECT count(*) FROM pendaftaran WHERE hasil_akhir = 'DITERIMA' AND {k_prof}) AS diterima,
            (SELECT count(*) FROM penempatan WHERE status_sk = 'SUDAH' AND {k_pend}) AS sudah_sk,
            (SELECT count(*) FROM pasca_tahap
             WHERE tahap_kode = 'ojt' AND status = 'BERJALAN' AND {k_prof}) AS sedang_ojt
        """,
        p_prof * 3 + p_pend + p_prof,
    )
    return df.iloc[0].fillna(0).to_dict()


def tren_kelompok(f: Filter = SEMUA) -> pd.DataFrame:
    """M11 versi filter — pendaftaran & diterima per tahun x kelompok rekrutmen."""
    klausa, params = f.klausa_profesi("p.profesi_id")
    return query(
        f"""
        SELECT pr.tahun_program AS tahun,
               {_KELOMPOK_SQL.format(kolom="pr.jenis_program")} AS kelompok,
               count(*) AS pendaftaran,
               sum(CASE WHEN p.hasil_akhir = 'DITERIMA' THEN 1 ELSE 0 END) AS diterima
        FROM pendaftaran p JOIN profesi pr USING (profesi_id)
        WHERE {klausa}
        GROUP BY 1, 2
        ORDER BY 1, 2
        """,
        params,
    )


def kalender_gelombang(f: Filter = SEMUA) -> pd.DataFrame:
    """M51 — tiap gelombang: buka, tutup, tes terakhir, pendaftar, diterima.

    Gelombang tanpa pendaftar dalam cakupan filter (mis. Pro Hire) tidak ikut.
    """
    klausa, params = f.klausa_profesi("p.profesi_id")
    return query(
        f"""
        WITH pend AS (
            SELECT p.gelombang_id, count(*) AS pendaftaran,
                   sum(CASE WHEN p.hasil_akhir = 'DITERIMA' THEN 1 ELSE 0 END) AS diterima
            FROM pendaftaran p
            WHERE {klausa}
            GROUP BY 1
        ), tes AS (
            SELECT gelombang_id, max(tanggal_tahap) AS tes_terakhir
            FROM seleksi_tahap GROUP BY 1
        )
        SELECT g.gelombang_id, g.tahun_program AS tahun, g.nama_gelombang, g.jenis_program,
               {_KELOMPOK_SQL.format(kolom="g.jenis_program")} AS kelompok,
               g.tgl_buka, g.tgl_tutup, t.tes_terakhir,
               pend.pendaftaran, pend.diterima,
               round(100.0 * pend.diterima / pend.pendaftaran, 1) AS pct_diterima
        FROM gelombang g
        JOIN pend USING (gelombang_id)
        LEFT JOIN tes t USING (gelombang_id)
        ORDER BY g.tgl_buka
        """,
        params,
    )


def status_kohort(f: Filter = SEMUA) -> pd.DataFrame:
    """M52 — status diterima per tahun program pada tanggal potong: SK terbit / sedang OJT."""
    klausa, params = f.klausa_pendaftaran()
    return query(
        f"""
        SELECT tahun_program AS tahun,
               CASE status_sk WHEN 'SUDAH' THEN 'SK terbit' ELSE 'Sedang OJT' END AS status,
               count(*) AS n
        FROM penempatan
        WHERE {klausa}
        GROUP BY 1, 2
        ORDER BY 1
        """,
        params,
    )


def pelamar_ringkas(f: Filter = SEMUA) -> dict[str, float]:
    """M02 + M21 dalam cakupan filter: pelamar unik, lamaran per pelamar, pelamar berulang.

    "Berulang" = melamar di lebih dari satu tahun program, bukan sekadar dua lamaran
    di gelombang yang sama.
    """
    klausa, params = f.klausa_profesi("p.profesi_id")
    df = query(
        f"""
        WITH k AS (
            SELECT p.kandidat_id, count(*) AS lamaran, count(DISTINCT pr.tahun_program) AS tahun
            FROM pendaftaran p JOIN profesi pr USING (profesi_id)
            WHERE {klausa}
            GROUP BY 1
        )
        SELECT count(*) AS pelamar, sum(lamaran) AS lamaran,
               sum(CASE WHEN tahun > 1 THEN 1 ELSE 0 END) AS berulang
        FROM k
        """,
        params,
    )
    return df.iloc[0].fillna(0).to_dict()


def kota_tes_geo(f: Filter = SEMUA) -> pd.DataFrame:
    """M35 versi filter + tingkat lulus peserta hadir per kota tes offline, dengan koordinat."""
    klausa, params = f.klausa_profesi()
    df = query(
        f"""
        SELECT lokasi_kota, count(*) AS n,
               round(100.0 * sum(CASE WHEN hasil = 'LULUS' THEN 1 ELSE 0 END)
                     / nullif(sum(CASE WHEN status_hadir = 'HADIR' THEN 1 ELSE 0 END), 0), 1) AS pct_lulus
        FROM seleksi_tahap
        WHERE mode = 'offline' AND {klausa}
        GROUP BY 1
        ORDER BY 2 DESC
        """,
        params,
    )
    koordinat = pd.read_csv(_KOORDINAT_PATH)
    return df.merge(koordinat, left_on="lokasi_kota", right_on="kota", how="inner")


def peluang_per_tahun_melamar(f: Filter = SEMUA) -> pd.DataFrame:
    """M53 — peluang seorang pelamar pernah diterima menurut berapa tahun ia melamar."""
    klausa, params = f.klausa_profesi("p.profesi_id")
    return query(
        f"""
        WITH k AS (
            SELECT p.kandidat_id, count(DISTINCT pr.tahun_program) AS tahun,
                   max(CASE WHEN p.hasil_akhir = 'DITERIMA' THEN 1 ELSE 0 END) AS diterima
            FROM pendaftaran p JOIN profesi pr USING (profesi_id)
            WHERE {klausa}
            GROUP BY 1
        )
        SELECT tahun, count(*) AS pelamar, sum(diterima) AS diterima,
               round(100.0 * sum(diterima) / count(*), 1) AS pct
        FROM k
        GROUP BY 1
        ORDER BY 1
        """,
        params,
    )


def peluang_per_ipk(f: Filter = SEMUA) -> pd.DataFrame:
    """M54 — peluang pendaftaran diterima per pita IPK 0,25 (pendidikan terakhir)."""
    klausa, params = f.klausa_profesi("p.profesi_id")
    return query(
        f"""
        SELECT floor(kp.skhu_ipk * 4) / 4 AS ipk, count(*) AS pendaftaran,
               round(100.0 * sum(CASE WHEN p.hasil_akhir = 'DITERIMA' THEN 1 ELSE 0 END)
                     / count(*), 2) AS pct
        FROM pendaftaran p
        JOIN kandidat_pendidikan kp ON kp.kandidat_id = p.kandidat_id AND kp.pendidikan_terakhir
        WHERE kp.skhu_ipk BETWEEN 2 AND 4 AND {klausa}
        GROUP BY 1
        HAVING count(*) >= 30
        ORDER BY 1
        """,
        params,
    )


def rumpun_f(f: Filter = SEMUA) -> pd.DataFrame:
    """M34 versi filter — rumpun jurusan: melamar vs diterima (join lewat program_studi)."""
    klausa, params = f.klausa_profesi("p.profesi_id")
    return query(
        f"""
        SELECT ps.rumpun, count(*) AS melamar,
               sum(CASE WHEN p.hasil_akhir = 'DITERIMA' THEN 1 ELSE 0 END) AS diterima,
               round(100.0 * sum(CASE WHEN p.hasil_akhir = 'DITERIMA' THEN 1 ELSE 0 END)
                     / count(*), 2) AS pct
        FROM pendaftaran p
        JOIN kandidat_pendidikan kp ON kp.kandidat_id = p.kandidat_id AND kp.pendidikan_terakhir
        JOIN program_studi ps ON ps.program_studi = kp.program_studi
        WHERE {klausa}
        GROUP BY 1
        ORDER BY 2 DESC
        """,
        params,
    )


def umur_gender_f(f: Filter = SEMUA) -> pd.DataFrame:
    """M41 versi filter — umur saat daftar akun x gender (P=Pria, W=Wanita, BUKAN L/P)."""
    klausa, params = f.klausa_kandidat()
    return query(
        f"""
        SELECT date_diff('year', tanggal_lahir, tanggal_daftar_akun) AS umur,
               jenis_kelamin, count(*) AS n
        FROM kandidat
        WHERE pernah_melamar AND tanggal_lahir IS NOT NULL AND {klausa}
        GROUP BY 1, 2
        ORDER BY 1
        """,
        params,
    )


def pendaftar_per_bulan_f(f: Filter = SEMUA) -> pd.DataFrame:
    """M44 versi filter — pendaftaran per bulan, bulan kosong diisi 0."""
    klausa, params = f.klausa_profesi("p.profesi_id")
    return query(
        f"""
        WITH bulan_semua AS (
            SELECT unnest(generate_series(
                (SELECT date_trunc('month', min(tanggal_lamar)) FROM pendaftaran),
                (SELECT date_trunc('month', max(tanggal_lamar)) FROM pendaftaran),
                INTERVAL 1 MONTH
            )) AS bulan
        ), pend AS (
            SELECT date_trunc('month', p.tanggal_lamar) AS bulan, count(*) AS n
            FROM pendaftaran p WHERE {klausa} GROUP BY 1
        )
        SELECT b.bulan::DATE AS bulan, coalesce(pend.n, 0) AS n
        FROM bulan_semua b LEFT JOIN pend USING (bulan)
        ORDER BY 1
        """,
        params,
    )


def pipeline_f(f: Filter = SEMUA) -> pd.DataFrame:
    """M22 versi filter — orang di tiap tahap pasca-seleksi pada tanggal potong."""
    klausa, params = f.klausa_profesi("p.profesi_id")
    return query(
        f"""
        SELECT p.tahap_kode, r.nama, min(p.urutan) AS urutan,
               sum(CASE WHEN p.status = 'SELESAI' THEN 1 ELSE 0 END) AS selesai,
               sum(CASE WHEN p.status = 'BERJALAN' THEN 1 ELSE 0 END) AS berjalan,
               count(*) AS total
        FROM pasca_tahap p JOIN tahap_ref r USING (tahap_kode)
        WHERE {klausa}
        GROUP BY 1, 2
        ORDER BY 3
        """,
        params,
    )


def tonggak_kohort(f: Filter = SEMUA) -> pd.DataFrame:
    """M55 — median tanggal tiga tonggak pasca-seleksi per tahun program."""
    klausa, params = f.klausa_profesi("p.profesi_id")
    return query(
        f"""
        SELECT pr.tahun_program AS tahun, p.tahap_kode,
               CAST(to_timestamp(median(epoch(p.tanggal_mulai))) AS DATE) AS tanggal,
               count(*) AS n
        FROM pasca_tahap p JOIN profesi pr USING (profesi_id)
        WHERE p.tahap_kode IN ('pengumuman_akhir', 'ojt', 'sk_penempatan') AND {klausa}
        GROUP BY 1, 2
        ORDER BY 1, 2
        """,
        params,
    )


def durasi_ojt(f: Filter = SEMUA) -> float:
    """Median hari OJT (tanggal_mulai ke tanggal_selesai) dalam cakupan filter."""
    klausa, params = f.klausa_profesi()
    return skalar(
        f"""
        SELECT median(date_diff('day', tanggal_mulai, tanggal_selesai))
        FROM pasca_tahap WHERE tahap_kode = 'ojt' AND {klausa}
        """,
        params,
    )


def updl_f(f: Filter = SEMUA) -> pd.DataFrame:
    """M36 versi filter — penempatan per UPDL (lokasi pendidikan & OJT)."""
    klausa, params = f.klausa_pendaftaran("p.pendaftaran_id")
    return query(
        f"""
        SELECT d.nama AS updl, count(*) AS n
        FROM penempatan p JOIN updl d ON p.updl_id = d.updl_id
        WHERE {klausa}
        GROUP BY 1
        ORDER BY 2 DESC
        """,
        params,
    )


def penempatan_ringkas(f: Filter = SEMUA) -> dict[str, float]:
    """M24 versi filter — total, induk, subholding, unit penerima."""
    klausa, params = f.klausa_pendaftaran()
    df = query(
        f"""
        SELECT count(*) AS ditempatkan,
               sum(CASE WHEN jenis_penempatan = 'INDUK' THEN 1 ELSE 0 END) AS induk,
               sum(CASE WHEN jenis_penempatan = 'SUBHOLDING' THEN 1 ELSE 0 END) AS subholding,
               count(DISTINCT unit_induk) AS unit
        FROM penempatan
        WHERE {klausa}
        """,
        params,
    )
    return df.iloc[0].fillna(0).to_dict()


def treemap_f(f: Filter = SEMUA) -> pd.DataFrame:
    """M38 versi filter — penempatan per unit induk (nama pendek) x bidang."""
    klausa, params = f.klausa_pendaftaran("p.pendaftaran_id")
    return query(
        f"""
        SELECT coalesce(u.nama_pendek, p.unit_induk) AS unit_induk,
               p.bidang_pembidangan, count(*) AS n
        FROM penempatan p
        -- Dedup nama pendek per unit: UID Jawa Tengah & DIY punya dua baris master,
        -- join langsung akan menggandakan penempatannya.
        LEFT JOIN (SELECT unit_induk, any_value(nama_pendek) AS nama_pendek FROM unit_induk GROUP BY 1) u
            ON u.unit_induk = p.unit_induk
        WHERE p.unit_induk IS NOT NULL AND {klausa}
        GROUP BY 1, 2
        ORDER BY 3 DESC
        """,
        params,
    )


def bidang_tahun(f: Filter = SEMUA) -> pd.DataFrame:
    """M56 — porsi bidang pembidangan per tahun program (persen dari penempatan tahun itu)."""
    klausa, params = f.klausa_pendaftaran()
    return query(
        f"""
        SELECT tahun_program AS tahun, bidang_pembidangan AS bidang, count(*) AS n,
               round(100.0 * count(*) / sum(count(*)) OVER (PARTITION BY tahun_program), 1) AS pct
        FROM penempatan
        WHERE {klausa}
        GROUP BY 1, 2
        ORDER BY 1, 3 DESC
        """,
        params,
    )


def perusahaan_tahun(f: Filter = SEMUA) -> pd.DataFrame:
    """M57 — penempatan per tahun: PLN induk vs tiap subholding (kode singkat)."""
    klausa, params = f.klausa_pendaftaran()
    return query(
        f"""
        SELECT tahun_program AS tahun,
               CASE WHEN jenis_penempatan = 'INDUK' THEN 'Induk' ELSE perusahaan_subholding END AS perusahaan,
               count(*) AS n
        FROM penempatan
        WHERE {klausa}
        GROUP BY 1, 2
        ORDER BY 1, 3 DESC
        """,
        params,
    )


def kuota_realisasi_f(f: Filter = SEMUA) -> pd.DataFrame:
    """M26 versi filter — kuota profesi vs penempatan nyata per tahun program."""
    k_prof, p_prof = f.klausa_profesi()
    k_pend, p_pend = f.klausa_pendaftaran()
    return query(
        f"""
        SELECT k.tahun_program AS tahun, k.kuota, coalesce(r.realisasi, 0) AS realisasi,
               round(100.0 * coalesce(r.realisasi, 0) / nullif(k.kuota, 0), 1) AS pct,
               k.rbb
        FROM (
            SELECT tahun_program, sum(kuota) AS kuota, bool_or(jenis_program = 'RBB') AS rbb
            FROM profesi WHERE {k_prof} GROUP BY 1
        ) k
        LEFT JOIN (
            SELECT tahun_program, count(*) AS realisasi FROM penempatan WHERE {k_pend} GROUP BY 1
        ) r USING (tahun_program)
        WHERE k.kuota > 0
        ORDER BY 1
        """,
        p_prof + p_pend,
    )


def usulan_unit_subbidang(tahun: int, top_unit: int = 20) -> pd.DataFrame:
    """M31 versi revamp — usulan per unit (nama pendek) x sub-bidang, dibatasi unit
    dengan usulan terbanyak supaya heatmap tetap terbaca. DIMODELKAN."""
    return query(
        """
        WITH u AS (
            SELECT x.nama_pendek AS unit, k.sub_bidang, sum(k.usulan) AS usulan
            FROM usulan_kebutuhan k
            JOIN unit_induk x ON x.unit_induk = k.unit_induk AND x.jumlah_pegawai > 50
            WHERE k.tahun_program = ?
            GROUP BY 1, 2
        ), atas AS (
            SELECT unit FROM u GROUP BY 1 ORDER BY sum(usulan) DESC LIMIT ?
        )
        SELECT unit, sub_bidang, round(usulan) AS usulan,
               sum(round(usulan)) OVER (PARTITION BY unit) AS total_unit
        FROM u WHERE unit IN (SELECT unit FROM atas)
        ORDER BY total_unit DESC, sub_bidang
        """,
        [tahun, top_unit],
    )


# ──────────────────────────────────────────────────────────────────────────────
# I. Rantai pemenuhan kebutuhan (revamp lanjutan 2026-09-16)
# ──────────────────────────────────────────────────────────────────────────────
#
# `usulan_kebutuhan` dan `penempatan` ternyata berbagi kosakata: 15 nilai `sub_bidang`
# ada di kedua tabel, dan 46 dari 47 `unit_induk` beririsan. Sebelumnya tidak pernah
# di-join, jadi pertanyaan "berapa kebutuhan yang benar-benar terisi" tidak terjawab
# di mana pun (temuan audit 2026-09-16, dua auditor independen).
#
# Batas yang harus selalu ikut ditampilkan:
# * `usulan_kebutuhan` DIMODELKAN; sistem PLN tidak menyimpan usulan per posisi.
# * `usulan_kebutuhan` tidak punya penanda jenis program, jadi rantai ini tidak bisa
#   dipilah RBB/Afirmasi/Terbuka. Karena itu ia tinggal di halaman Perencanaan yang
#   memang tidak berfilter, bukan di halaman yang berfilter.
# * Penempatan tahun berjalan belum ber-SK, sehingga `sub_bidang`-nya masih kosong;
#   tahun seperti itu tidak bisa masuk rincian per sub-bidang.


def rantai_pemenuhan() -> pd.DataFrame:
    """M59 — usulan, kuota, diterima, dan ditempatkan per tahun program.

    Empat titik rantai kebutuhan: apa yang diminta unit, apa yang dibuka sebagai
    kuota profesi, berapa yang lulus seleksi, berapa yang benar-benar ditempatkan.
    Kolom `usulan` DIMODELKAN.
    """
    return query(
        """
        WITH u AS (SELECT tahun_program, sum(usulan) AS usulan FROM usulan_kebutuhan GROUP BY 1),
             k AS (SELECT tahun_program, sum(kuota) AS kuota FROM profesi GROUP BY 1),
             d AS (
                 SELECT pr.tahun_program, count(*) AS diterima
                 FROM pendaftaran p JOIN profesi pr USING (profesi_id)
                 WHERE p.hasil_akhir = 'DITERIMA' GROUP BY 1
             ),
             t AS (SELECT tahun_program, count(*) AS ditempatkan FROM penempatan GROUP BY 1)
        SELECT u.tahun_program AS tahun, round(u.usulan) AS usulan,
               coalesce(k.kuota, 0) AS kuota, coalesce(d.diterima, 0) AS diterima,
               coalesce(t.ditempatkan, 0) AS ditempatkan
        FROM u
        LEFT JOIN k USING (tahun_program)
        LEFT JOIN d USING (tahun_program)
        LEFT JOIN t USING (tahun_program)
        ORDER BY 1
        """
    )


def pemenuhan_sub_bidang(tahun: int) -> pd.DataFrame:
    """M60 — usulan vs penempatan per sub-bidang untuk satu tahun program.

    FULL OUTER JOIN: satu sub-bidang bisa muncul hanya di salah satu sisi (diusulkan
    tapi tidak terisi, atau terisi tanpa pernah diusulkan), dan keduanya sama penting.
    """
    return query(
        """
        WITH u AS (
            SELECT sub_bidang, sum(usulan) AS usulan
            FROM usulan_kebutuhan WHERE tahun_program = ? GROUP BY 1
        ), r AS (
            SELECT sub_bidang, count(*) AS realisasi
            FROM penempatan WHERE tahun_program = ? AND sub_bidang IS NOT NULL GROUP BY 1
        )
        SELECT coalesce(u.sub_bidang, r.sub_bidang) AS sub_bidang,
               round(coalesce(u.usulan, 0)) AS usulan,
               coalesce(r.realisasi, 0) AS realisasi,
               round(100.0 * coalesce(r.realisasi, 0) / nullif(u.usulan, 0), 1) AS pct
        FROM u FULL OUTER JOIN r USING (sub_bidang)
        ORDER BY usulan DESC NULLS LAST
        """,
        [tahun, tahun],
    )


def jeda_pasca_tahap(f: Filter = SEMUA) -> pd.DataFrame:
    """M61 — median jeda hari dari tahap sebelumnya, untuk tiap tahap pasca-seleksi.

    Menggantikan "rantai tahap" lama yang menampilkan tujuh batang nyaris sama tinggi:
    semua yang diterima melewati semua tahap, jadi tingginya tidak membawa informasi.
    Yang membawa informasi adalah waktunya, karena jedanya berbeda jauh antar tahap.

    Durasi di sumber DIMODELKAN dan hampir konstan antar kohort, jadi angka ini
    menggambarkan jadwal baku satu kohort, bukan perbedaan antar kohort.
    """
    klausa, params = f.klausa_pendaftaran("x.pendaftaran_id")
    return query(
        f"""
        WITH x AS (
            SELECT pendaftaran_id, tahap_kode, tanggal_mulai,
                   lag(tanggal_mulai) OVER (PARTITION BY pendaftaran_id ORDER BY tanggal_mulai) AS sebelum
            FROM pasca_tahap
        )
        SELECT tahap_kode, count(*) AS n,
               median(date_diff('day', sebelum, tanggal_mulai)) AS jeda_hari,
               min(tanggal_mulai) AS paling_awal
        FROM x
        WHERE sebelum IS NOT NULL AND {klausa}
        GROUP BY 1
        ORDER BY 3 DESC
        """,
        params,
    )


def tahun_sub_bidang_tercatat() -> list[int]:
    """Tahun program yang penempatannya sudah punya sub-bidang (butuh SK terbit)."""
    df = query(
        "SELECT DISTINCT tahun_program FROM penempatan WHERE sub_bidang IS NOT NULL ORDER BY 1"
    )
    return df["tahun_program"].astype(int).tolist()


def realisasi_pegawai_bulanan() -> pd.DataFrame:
    """M58 — total realisasi pegawai & jumlah unit yang melapor per bulan.

    Bukti kualitas data: Sep-Okt 2025 tidak ada baris sama sekali, dan April 2026
    hanya 1 dari 48 unit melapor (alasan gap FTK wajib memakai Maret 2026).
    Kolom `realisasi` bertipe VARCHAR di sumber, jadi di-TRY_CAST.
    """
    return query(
        """
        SELECT strptime(bulan, '%Y-%m')::DATE AS bulan, count(*) AS unit_melapor,
               sum(try_cast(realisasi AS INTEGER)) AS realisasi
        FROM realisasi_bulanan
        GROUP BY 1
        ORDER BY 1
        """
    )
