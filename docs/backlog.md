# Backlog Fitur — Dashboard Rekrutmen PLN v2

Daftar hidup. Ide baru ditambahkan di sini, bukan langsung ke PRD — PRD hanya memuat yang
sudah masuk cakupan kerja.

Tiap ide dinilai pada satu sumbu yang menentukan biayanya: **apakah datanya sudah ada?**

| Status | Arti |
|---|---|
| 🟢 SIAP | data sudah ada di `rekrutmen.duckdb`, tinggal dibuat halamannya |
| 🟡 PERLU TAMBAHAN KECIL | data inti ada, kurang satu tabel referensi kecil |
| 🔴 PERLU SUMBER DATA BARU | tidak ada di database manapun — butuh generator mock terpisah |

---

## Usulan user — 19 Agustus 2026

### B1 · Prediksi kebutuhan rekrutmen dari attrition & pensiun — 🟢 SIAP

**Kondisi data:** sudah sangat siap, lebih siap dari dugaan.
- `proyeksi_kekosongan` — 92.928 baris per unit × posisi × tahun **2019–2026**, dengan
  pensiun / APS / meninggal / PHK sudah terpisah kolom
- `profil_usia` — `bobot_risiko_pensiun` per grade (G1 0,0002 · G2 0,069 · G3 0,331 ·
  SPC 0,643 · SSP 1,000 · MA 1,000)
- Riset: attrition 2,7%/tahun (definisi luas), **didominasi pensiun** (F-036)

**Kekurangan:** horison berhenti di 2026. Untuk prediksi 2027–2030 perlu memperpanjang
generator langkah 04 — perhitungannya sudah ada, tinggal diteruskan majunya.

**Rencana:** perluas **halaman 2**, bukan halaman baru.
- Kurva proyeksi kebutuhan 2027–2031 dengan pita ketidakpastian
- Pemilih skenario: attrition baseline 2,7% · konservatif 2,0% · agresif 3,5%
- Tabel "unit paling terancam": mana yang >15% pegawainya pensiun dalam 5 tahun

> **Catatan metode:** ini proyeksi aktuarial (usia × grade × bobot pensiun), **bukan ML**.
> Di konteks HC itu justru lebih dipercaya karena asumsinya bisa ditunjuk satu per satu.
> Asumsi ditampilkan di layar, bisa diubah pengguna.

---

### B2 · Peta Indonesia — 🟡 PERLU TAMBAHAN KECIL

**Kondisi data:** 43 kota tes, 48 unit induk, 11 UPDL, `lokasi_kota` + `tanggal_tahap` di
464.688 baris seleksi, `propinsi_domisili` + `kota_domisili` kandidat. **Yang kurang hanya
koordinat lat/lon** — data referensi publik, kecil, mudah dibuat.

**Masalah dengan "kondisi realtime seleksi yang berlangsung":** pada tanggal potong
15 September 2026 **tidak ada seleksi yang sedang berjalan**. Aktivitas seleksi terakhir
Februari 2026 (1.507 event), puncaknya Oktober 2025 (57.715 event). Gelombang 2026 memang
sengaja tidak ada — 2026 adalah fase perencanaan.

**Tiga pilihan, dua di antaranya bagus:**

| Opsi | Isi | Data |
|---|---|---|
| **A. Peta putar-ulang** ⭐ | Animasi aktivitas seleksi per minggu 2019→2026: titik membesar saat kota menggelar tes. Puncak Okt 2025 akan terlihat dramatis | 100% ada |
| **B. Peta "yang benar-benar berjalan hari ini"** ⭐ | 2.000 orang sedang OJT tersebar di 11 UPDL + unit induk tujuan mereka | 100% ada |
| C. Bikin gelombang 2026 fiktif supaya ada "live" | — | ❌ melanggar keputusan mockdb, jangan |

**Rekomendasi:** A + B jadi satu halaman baru **"Peta Operasi"**. Opsi A memberi kesan
"realtime" yang dicari tanpa memalsukan data, dan justru lebih informatif karena
memperlihatkan pola musiman rekrutmen.

**Bonus yang direncanakan, sekarang ditunda:** garis penghubung kota domisili → kota tes.
⚠️ `kota_domisili` diketahui dibagikan acak seragam oleh generator (lihat
`mockdb/ISSUES_SEBARAN.md`), jadi "48.969 pendaftaran kota tes ≠ kota domisili" hanya
kebetulan statistik (1/43 kota), bukan pola nyata. Bonus ini menunggu generator diperbaiki,
sama seperti B7.

---

### B3 · Update tren & berita rekrutmen (vendor, tren dalam/luar negeri) — 🔴 SUMBER BARU

**Kondisi data:** tidak ada. Yang ada hanya `vendor` (10 baris: Prodia, Kimia Farma, LPT UI,
DDI, UPAC PLN, Bina Talenta) — itu vendor pelaksana tes, bukan tren pasar.

**Yang dibutuhkan:** tabel baru `tren_rekrutmen` (topik, kategori, tanggal, ringkasan,
sumber, relevansi) — dikurasi manual atau dibangkitkan sebagai mock.

⚠️ **Batas yang harus dijaga:** jangan membuat artikel berita palsu yang tampak asli
(judul + nama media + tanggal). Kalau keluar dari konteks demo, itu jadi misinformasi
sungguhan. Bentuk yang aman: **kartu ringkasan tren berlabel `CONTOH`** tanpa mengatasnamakan
media nyata, atau feed RSS asli kalau nanti diizinkan online.

**Prioritas:** rendah — nilai demonya paling kecil dibanding B4/B5, dan risikonya paling
tidak sebanding.

---

### B4 · Monitoring sentimen & traffic publik — 🔴 SUMBER BARU

**Kondisi data:** tidak ada sama sekali.

**Kenapa ini justru ide paling kuat dari ketiga yang butuh data baru:** volumenya bisa
**disandarkan ke tanggal nyata**. Kita punya `tgl_buka` dan `tgl_tutup` asli tiap gelombang.
Mock percakapan publik yang melonjak tepat di tanggal pembukaan gelombang, memuncak di
minggu penutupan, lalu turun — itu pola yang benar secara kausal, bukan angka acak.

**Bentuk yang diusulkan:**
- Deret waktu volume percakapan per platform, ditumpangkan pada penanda buka/tutup gelombang
- Sentimen positif / netral / negatif (pakai palet status, bukan palet seri)
- Topik yang paling banyak dibicarakan: pengumuman lambat, lokasi tes, biaya, hasil tes
- Korelasi: lonjakan pertanyaan "kapan pengumuman" vs jeda antar tahap yang nyata di data

**Kendala nyata yang perlu diakui:** crawling media sosial punya batasan ToS dan API
berbayar. Untuk demo, mock. Untuk produksi, ini butuh keputusan pengadaan tersendiri.

---

### B5 · Monitoring hoaks rekrutmen — 🔴 SUMBER BARU, tapi paling berdasar

**Kondisi data:** tidak ada. **Tapi masalahnya nyata dan tercatat di riset**: F-033 mencatat
FAQ resmi situs rekrutmen PLN memuat peringatan penipuan — artinya PLN sendiri mengakui ini
masalah berulang, bukan kekhawatiran karangan.

**Bentuk yang diusulkan:**
- Jumlah kasus terdeteksi per platform per bulan
- Kategori modus: calo/jaminan lulus · biaya pendaftaran · surat panggilan palsu ·
  akun/situs tiruan · grup berbayar
- Status penanganan: terdeteksi → diverifikasi → dibantah di kanal resmi → dilaporkan
- Waktu tanggap: berapa lama dari terdeteksi sampai ada bantahan resmi
- Kaitkan ke gelombang: hoaks memuncak saat gelombang buka — itu yang mau ditunjukkan

⚠️ **Batas keras:** dashboard hanya menyimpan **metadata** (platform, tanggal, kategori,
status). **Tidak boleh** membuat contoh konten hoaks yang realistis — surat panggilan palsu,
tangkapan layar palsu, nomor kontak. Membuat artefak seperti itu, bahkan untuk demo, sama
saja memproduksi bahan penipuan yang siap pakai.

**Prioritas:** tinggi di antara yang butuh data baru — masalahnya nyata, dan nilainya jelas
untuk tim rekrutmen (siapkan bantahan sebelum hoaks menyebar).

---

## Usulan tambahan — dari analisis data

Empat ide berikut muncul saat memverifikasi data, dan **semuanya 🟢 SIAP** — tidak butuh
satu baris data baru pun.

### B6 · Bedah no-show: kenapa lebih dari separuh tidak datang? — 🟢 SIAP (revisi 2026-08-19)

Temuan terbesar dashboard ini adalah Tes Adaptif kehilangan **74.935 orang karena tidak
hadir** — lebih besar dari yang gagal tes. Verifikasi ulang menunjukkan pemicunya **bukan
jarak**, melainkan **mode tes**:

| Uji | Hasil |
|---|---|
| No-show: kota tes = kota domisili vs beda kota | 7,26% vs 7,47% — **praktis sama** (dan sampelnya sendiri tidak andal, lihat catatan di bawah) |
| No-show per tahap × mode | Online: **52,1%** (adaptif) · 17,7% (akademik) — Offline: 8,3% (psikologi) · 7,2% (fisik/MCU) · 6,1% (wawancara) |

Hipotesis jarak **gugur**. Yang membedakan justru online vs offline — kandidat jauh lebih
mudah melewatkan tes yang tidak mengharuskan mereka hadir fisik. Ini satu batang sederhana
per tahap × mode, sudah terbaca sekali lihat tanpa perlu caption penjelas — persis yang
dicari doktrin D1 (`design_system.md` §11).

> Catatan: uji jarak di atas memakai `kota_domisili`, yang belakangan diketahui dibagikan
> acak seragam oleh generator (lihat `mockdb/ISSUES_SEBARAN.md`) — jadi hasil "praktis sama"
> ini sendiri tidak sepenuhnya bisa dipercaya sampai generator diperbaiki. Tapi pola
> online-vs-offline berdiri sendiri di `seleksi_tahap.mode`, kolom yang berpola benar, jadi
> insight utamanya tetap valid terlepas dari cacat itu.

### B7 · Kualitas sumber talenta — 🟡 MENUNGGU REBUILD GENERATOR (revisi 2026-08-19)

`kandidat_pendidikan.sekolah_universitas` **dibagikan acak seragam** oleh generator (rasio
top/bawah 1,02 dari 15 nilai yang muncul; konversi pelamar→diterima antar kampus 3,10%–3,76%
— rentang terlalu sempit untuk jadi insight). Ditemukan saat verifikasi data untuk halaman 4.
**Tidak dibangun sampai generator diperbaiki** — detail di `mockdb/ISSUES_SEBARAN.md`.

**Pendekatan yang dicatat untuk rebuild:** bukan sekadar mengacak lebih realistis, tapi
disusun dari struktur nyata yang sudah ada di repo — kampus mitra ikatan dinas/kelas
kerjasama (ITPLN, PENS, 18 PTN di `rules/ikatan_dinas.yaml`) dan akreditasi BAN-PT sebagai
kolom baru. Perilaku yang diusulkan: akreditasi lebih tinggi → peluang lulus tiap tahap naik,
**tapi** peluang no-show juga naik — kandidat kampus unggulan melamar ke banyak perusahaan
sekaligus dan PLN kerap jadi pilihan kedua/ketiga. Dua efek berlawanan dalam satu dimensi,
kandidat kuat untuk jangkar perhatian halaman 4 begitu datanya benar.

### B8 · Simulator "what-if" pagu — 🟢 SIAP

Murni kalkulasi dari laju funnel yang sudah diketahui: *"Kalau pagu 2027 adalah 1.500 orang,
berapa pelamar yang harus masuk?"* Geser tingkat kelulusan tiap tahap dan tingkat kehadiran →
lihat berapa pendaftar yang dibutuhkan. Menyambung langsung ke B1.

### B9 · Kapasitas UPDL vs gelombang masuk — 🟢 SIAP

2.000 orang sedang OJT, 11 UPDL, kelas prajabatan 30–60 orang. Apakah kapasitas cukup untuk
kohort berikutnya? Ini kendala operasional nyata yang tidak pernah terlihat di laporan
rekrutmen biasa.

---

## Rencana bertahap

| Fase | Isi | Prasyarat |
|---|---|---|
| **1** | 8 halaman inti sesuai PRD | — |
| **1,5** | B6, B8, B9 (🟢) + B2 peta versi volume-tes (butuh koordinat) + B1 proyeksi 2027–2031 (butuh perpanjang generator) | fase 1 jalan |
| **1,5-tunda** | B7 almamater + bonus garis domisili→tes di B2 — menunggu rebuild generator (`mockdb/ISSUES_SEBARAN.md`) | rebuild generator |
| **2** | B4 sentimen + B5 hoaks, satu paket sebagai halaman **"Radar Publik"** — sumbernya sama-sama sinyal eksternal, lebih efisien dibangun sekali | generator mock baru |
| **3** | B3 tren & berita | keputusan soal sumber (mock vs feed nyata) |

**Alasan urutan ini:** fase 1 dan 1,5 tidak butuh data baru sama sekali — jadi seluruh
tenaga bisa dipakai untuk membuat dashboardnya bagus. Fase 2 butuh generator mock baru yang
kira-kira sebesar `mockdb/build/08–09` — itu proyek tersendiri, dan lebih baik dikerjakan
setelah ada dashboard yang sudah kelihatan bentuknya.
