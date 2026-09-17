# PRD — Dashboard Rekrutmen PLN v2

**Status:** draf untuk direview · **Tanggal:** 19 Agustus 2026
**Sumber data:** `mockdb/out/rekrutmen.duckdb` — 34 tabel, 4.224.925 baris
**Tanggal potong data:** 15 September 2026 (semua status dihitung relatif ke tanggal ini)

---

## 1. Kenapa dashboard ini dibuat

Proses rekrutmen PLN tersebar di **empat sistem** yang tidak saling bicara:
`rekrutmen.pln.co.id` (HTD), `seleksi.pln.co.id` (tes akademik), aplikasi Pusdiklat
(prajabatan & OJT), dan `rekrutmenbersama.fhcibumn.id` (jalur RBB). Tidak ada satu tempat
pun yang bisa menjawab pertanyaan sesederhana *"berapa orang sedang OJT sekarang dan kapan
mereka ber-SK?"*

Dashboard ini menjawabnya, sekaligus **menunjukkan apa yang belum bisa dijawab**. Sebagian
data yang dipakai tidak ada di sistem manapun dan sengaja dimodelkan (kuota per posisi,
passing grade, skor mentah). Itu bukan kelemahan yang disembunyikan — itu argumennya:
*inilah insight yang bisa didapat kalau data tersebut memang dikumpulkan.*

### Yang membedakan dari v1

| Hal | v1 | v2 |
|---|---|---|
| Data | mock lama, ±beberapa ribu baris | `rekrutmen.duckdb`, 4,22 juta baris berjangkar 49 temuan riset |
| Cakupan | seleksi & penempatan | + perencanaan kebutuhan, pasca-seleksi/OJT, kualitas data |
| Audiens | satu lapis | dua lapis dalam satu halaman (eksekutif & analis) |
| Kejujuran data | tidak dibedakan | badge `NYATA` / `DIMODELKAN` / `AGREGAT` di tiap angka |
| Angka | dihitung per halaman | satu sumber kebenaran di `core/metrics.py` |

---

## 2. Persona

### P1 — Manajemen / Direksi ("Bu Direktur")
Waktu baca 2–3 menit. Ingin tahu: apakah rekrutmen berjalan sesuai rencana, di mana
masalahnya, apa yang perlu diputuskan. **Tidak** mau mengatur filter.
→ Dilayani **lapis eksekutif**: KPI besar, satu chart utama, satu kalimat insight.

### P2 — Analis HTD ("Mas Analis")
Mencari jawaban spesifik: kenapa konversi 2023 turun, unit mana yang usulannya tidak
terpenuhi, profesi mana yang no-show-nya tinggi. Butuh filter, drill-down, dan ekspor.
→ Dilayani **lapis analis**: panel filter, tabel rinci, unduh CSV.

### P3 — Tim Data / IT ("Pak Arsitek")
Ingin tahu data mana yang nyata, mana yang dimodelkan, dan di mana titik rawan integrasi
antar sistem. → Dilayani **halaman 7** dan badge sumber data di seluruh aplikasi.

---

## 3. Prinsip desain

> **Revisi 2026-08-19** setelah review halaman 1: *"terlalu AI — info di mana-mana, banyak
> caption kecil, tandanya grafik sendiri tidak terbaca sekali lihat."* Dashboard ini dilihat
> **berulang tiap hari** sebagai alat monitoring — penjelasan yang berguna di lihatan pertama
> jadi kebisingan di lihatan ke-sepuluh. Prinsip §2 lama ("tiap chart punya kartu insight")
> diganti. Detail lengkap di `docs/design_system.md` §11 (aturan D1–D6).

1. **Satu halaman, satu pertanyaan.** Judul halaman adalah pertanyaannya; chart utama
   adalah jawabannya — judulnya sendiri kalimat temuan, bukan nama kategori (D1).
2. **Maksimal satu kalimat temuan per halaman**, bukan satu insight per chart (D3).
   Penjelasan tambahan bersifat on-demand: tooltip `help=` atau expander "Tentang halaman
   ini", tidak permanen di layar (D2).
3. **Jujur soal asal data, tapi tidak berulang.** Satu spanduk per halaman kalau seluruh
   halaman itu dimodelkan; bukan badge di tiap angka yang semuanya sama-sama nyata (D4).
4. **Satu definisi, satu tempat.** Halaman tidak menulis SQL agregat; semua lewat
   `core/metrics.py` — yang juga jadi rujukan chatbot.
5. **Eksekutif dulu, detail belakangan.** Lapis analis tersembunyi sampai diminta.
6. **Maksimal 4 blok per halaman**: 1 baris KPI + 1 chart jangkar perhatian + ≤2 pendukung
   (D5). Chart eksotis (Sankey, treemap, peta) dipertahankan sebagai jangkar itu — perannya
   menarik perhatian, bukan didampingi caption.

---

## 4. Halaman & pertanyaan yang dijawab

### Halaman 1 — Ringkasan Eksekutif
> *Sehat tidak mesin rekrutmen kita?*

- KPI: 218.928 pendaftaran · 7.711 diterima · rasio 1:28 · 5.711 sudah ber-SK
- Tren pendaftar vs diterima 2019–2025
- **Status pipeline hari ini**: 2.000 orang kohort 2025 sedang OJT, SK menyusul
- Ringkasan 3 baris: perencanaan, seleksi, penempatan — masing-masing tautan ke halamannya

### Halaman 2 — Perencanaan Kebutuhan
> *Berapa orang yang perlu direkrut, di posisi dan unit mana?*

Seluruh halaman ini **DIMODELKAN** dan diberi disclaimer permanen di bagian atas. Justru
inilah demonya: tidak ada satu pun angka kuota/kebutuhan per posisi di sistem PLN manapun
(F-017, F-027, F-043), jadi halaman ini memperagakan insight yang bisa muncul kalau data
itu dikumpulkan.

- Rantai perencanaan: proyeksi kekosongan → usulan unit → pagu disetujui (waterfall)
- Proyeksi kekosongan 2019–2026 per penyebab (pensiun / APS / meninggal / PHK)
- Gap FTK: 37.854 formasi vs 37.153 realisasi Mar-2026 → **gap 701** per unit induk
- Heatmap unit induk × sub-bidang: di mana kekosongan menumpuk
- Rasio pagu terhadap usulan — berapa persen usulan unit yang benar-benar disetujui

### Halaman 3 — Tahapan Seleksi
> *Di mana kandidat berguguran, dan kenapa?*

- Funnel 6 tahap: administrasi 213.648 → adaptif → akademik → psikologi → fisik/MCU →
  wawancara → 7.711 diterima, dengan % konversi dan % no-show per tahap
- **Temuan utama**: Tes Adaptif menggugurkan 95.204 orang — lebih besar dari administrasi
  (69.817), dan no-show-nya 52% (143.831 dipanggil, 68.896 hadir)
- Perbandingan jalur mandiri vs RBB berdampingan, termasuk titik serah-terima FHCI→PLN
- Corong FHCI (agregat, tanpa nama) ditampilkan terpisah dengan badge `AGREGAT`
- Lapis analis: Sankey alur gugur, filter tahun/jalur/jenjang/kota/profesi, tabel drill-down

### Halaman 4 — Kandidat & Pasar Tenaga Kerja
> *Siapa yang melamar ke PLN?*

⚠️ **Revisi 2026-08-19:** verifikasi menemukan `kota_domisili`, `kota_asal`, dan
`sekolah_universitas` dibagikan **acak seragam** oleh generator mockdb (rasio top/bawah
1,02–1,07 — lihat `mockdb/ISSUES_SEBARAN.md`). Sebaran asal per provinsi dan analisis
almamater **dikeluarkan** dari halaman ini sampai generator dibangun ulang — angkanya bukan
insight nyata, hanya artefak jumlah kota per provinsi di master data.

- Komposisi jenjang: S1/D-IV 245.553 · D-III 98.161 · SMK 11.696 · S2 11.631
- Gender per kohort (63–74% pria, berayun antar tahun) — slider tahun
- Peta **volume tes per kota** (`lokasi_kota`, berpola benar — rasio 37,7×) — jangkar
  perhatian halaman, menggantikan rencana "peta asal vs kota tes" yang datanya cacat
- Akun *lifetime*: 172.389 pelamar unik untuk 218.928 pendaftaran (rata-rata 1,27 lamaran)
- Rumpun jurusan & program studi yang paling banyak melamar vs yang paling banyak diterima
  (`program_studi` berpola benar — rasio 10,1×, aman dipakai)

### Halaman 5 — Pasca-Seleksi & OJT
> *Siapa yang sedang dalam perjalanan menuju SK?*

⚠️ Durasi antar tahap di data ini **konstan** (tutup gelombang → SK = 400 hari untuk semua
kohort), jadi halaman ini **tidak** menganalisis bottleneck durasi — tidak ada variasi untuk
dianalisis. Fokusnya posisi pipeline, bukan kecepatan.

- Rantai 7 tahap pasca: pengumuman → kontrak → SAMAPTA → pembidangan → OJT → ujian → SK
- Posisi tiap kohort per 15 Sep 2026: 5.711 SELESAI, **2.000 sedang OJT** (kohort 2025)
- Pembidangan: Distribusi 1.499 · SDM 1.464 · Pembangkitan 871 · Niaga 820 …
- Sebaran per UPDL (11 lokasi) dan kapasitas kelas
- Titik rawan integrasi: SAMAPTA→OJT dikelola Pusdiklat di aplikasi terpisah

### Halaman 6 — Penempatan & Pemenuhan
> *Rencana mendarat di mana, dan seberapa tepat?*

- 7.711 diterima → 5.171 induk, 2.540 subholding
- Grade: G2 5.423 · G1 2.020 · G3 268 — validasi aturan "grade sesuai jenjang"
- Rencana (`profesi.kuota`) vs realisasi (`penempatan`) per tahun & unit — slope chart
- Treemap unit induk × bidang; top unit: Kantor Pusat 447, UID Jawa Barat 236, UIW Maluku 225
- Lapis analis: tabel per unit induk dengan pemenuhan, filter bidang/grade/tahun

### Halaman 7 — Kualitas Data & Sumber Sistem
> *Mana yang kita punya, mana yang masih perlu dikumpulkan?*

Halaman penuh, bukan catatan kaki — ini nilai jual proyeknya.

- Peta serah-terima 4 sistem, dengan volume baris yang melewati tiap sistem
  (rekrutmen.pln.co.id 370.102 · seleksi.pln.co.id 53.907 · hasil vendor di-upload 40.679)
- **Jalur RBB nyaris tanpa jejak**: 2021 hanya menyisakan 179 baris di sistem PLN dari
  9.135 pelamar FHCI
- Kelengkapan kolom per kualitas kohort: blok fisik terisi 0% di kohort RENDAH, 33% SEDANG,
  71% BAIK — kelengkapan membaik tiap tahun
- Daftar seluruh kolom `DIMODELKAN` beserta alasannya
- **Ketidaksinkronan angka rencana** (lihat §6 no. 1) ditampilkan apa adanya di sini

### Halaman 8 — Chatbot
> *Tanya apa saja tentang data ini*

Port dari v1 apa adanya: agen text-to-SQL dengan tool `run_sql_query` + `render_chart`,
guard SELECT-only, multi-profil LLM, ringkasan percakapan bergulir, ekspor CSV.
Perbedaan: koneksi langsung ke file DuckDB read-only (bukan DataFrame di memori), dan
prompt skema dibangun dari katalog + kamus metrik.

---

## 5. Ruang lingkup

### Termasuk
- 8 halaman di atas, Bahasa Indonesia penuh
- Dua lapis (eksekutif / analis) via toggle per halaman, preferensi tersimpan di sesi
- Light & dark mode
- Ekspor CSV pada tabel di lapis analis
- Chatbot port dari v1

### Tidak termasuk (non-goals)
- **Autentikasi & hak akses** — ini demo, bukan aplikasi produksi
- **Tulis-balik ke database** — dashboard read-only, selamanya
- **Data real-time / refresh otomatis** — sumbernya file DuckDB statis
- **PII kandidat** — nama, NIK, email, HP tidak pernah ditampilkan meski ada di tabel
- **Analisis bottleneck durasi pasca-seleksi** — datanya konstan, tidak ada yang dianalisis
- **Level unit layanan (ULP)** — master DAPEG berhenti di unit pelaksana
- **Prediksi / ML** — tidak ada model prediktif di v2

---

## 6. Batasan data yang diketahui

Empat hal ini ditemukan saat verifikasi dan **ditangani eksplisit**, bukan disembunyikan:

1. **Dua angka rencana yang tidak sinkron.** `pagu_rekrutmen` per tahun (1.093 / 325 / 689 /
   689 / 1.277 / 1.098 / 1.050) tidak sama dengan `gelombang.diterima_target` (1.353 / 325 /
   689 / 1.109 / 1.797 / 1.578 / 2.000). Keputusan: **halaman 2 pakai `pagu_rekrutmen`**
   (sisi perencanaan), **halaman 6 pakai `profesi.kuota`** (sisi program), dan selisihnya
   ditampilkan sebagai temuan di halaman 7.
2. **Tahun RBB timpang.** 2020 target 325 → diterima 125; 2021 target 689 → diterima 49.
   Volume RBB di `gelombang` adalah kohort penuh, bukan volume yang diserahterimakan ke PLN.
   Halaman 3 & 6 **tidak** menampilkan ini sebagai "gagal 93%" — diberi penanda dan
   dikeluarkan dari perhitungan rasio pemenuhan sampai isunya diputuskan.
3. **Durasi pasca-seleksi konstan 400 hari** untuk semua kohort → tidak ada analisis durasi.
4. **`realisasi_apr_2026` hanya terisi 1 dari 48 unit** → semua perhitungan gap FTK memakai
   `realisasi_mar_2026` (lengkap 48/48).
5. **Lima bidang kandidat dibagikan acak seragam oleh generator**, bukan berpola realistis:
   `kota_domisili`, `kota_asal` (identik `kota_domisili` di seluruh baris — bug generator),
   `tempat_lahir`, `ukuran_baju`, `sekolah_universitas`. Rincian bukti & rencana perbaikan di
   `mockdb/ISSUES_SEBARAN.md`. **Konsekuensi ke v2:** sebaran asal per provinsi dan analisis
   almamater dikeluarkan dari halaman 4 (§4) sampai generator dibangun ulang — lihat B7 di
   `docs/backlog.md`.

---

## 7. Kriteria sukses

| # | Kriteria | Cara mengukur |
|---|---|---|
| K1 | Bu Direktur paham kondisi rekrutmen dalam 3 menit tanpa menyentuh filter | Uji baca halaman 1 |
| K2 | Setiap angka di dashboard bisa direproduksi dari `docs/metrik.md` | Skrip verifikasi metrik |
| K3 | Chatbot dan halaman memberi angka yang sama untuk pertanyaan yang sama | Uji 10 pertanyaan silang |
| K4 | Tidak ada satu pun PII kandidat yang tampil | Grep kolom terlarang di seluruh `pages/` |
| K5 | Halaman yang seluruhnya `DIMODELKAN` punya satu spanduk; tidak ada badge berulang di tiap KPI | Review manual per halaman |
| K6 | Halaman termuat < 2 detik pada beban penuh 4,22 juta baris | Ukur waktu render |
| K7 | Chart utama terbaca tanpa membaca judulnya dua kali; judulnya sendiri kalimat temuan | `tests/uji_disiplin.py` + review manual |
| K8 | Maksimal 1 kalimat temuan per halaman, tidak ada caption permanen di bawah tiap chart | `tests/uji_disiplin.py` |

---

## 8. Keputusan yang sudah dikunci

| Hal | Keputusan |
|---|---|
| Stack | Streamlit — native dulu (`st.metric`, dst), kustom hanya saat tidak ada padanan |
| Audiens | Campuran berlapis — toggle "Mode Analis" per halaman |
| Chatbot | Port persis dari v1, adaptasi koneksi DuckDB, dikerjakan awal |
| Bahasa | Indonesia penuh, termasuk label chart |
| Halaman 2 | Tetap halaman utama meski 100% dimodelkan |
| Halaman 7 | Halaman penuh, bukan panel |
| Warna | Basis PLN dari v1; palet kategori chart ditata ulang |
| Teks & tata letak | Doktrin D1–D6 (`design_system.md` §11) — temuan sebagai judul chart, bukan caption terpisah; maksimal 4 blok/halaman |
| Chart eksotis | Dipertahankan (Sankey, treemap, peta) sebagai jangkar perhatian per halaman, ditambah Plotly |
| Sebaran acak seragam di mockdb | Dicatat di `mockdb/ISSUES_SEBARAN.md`, diperbaiki saat generator dibangun ulang — bukan sekarang |

---

## 9. Urutan pengerjaan

| # | Tahap | Keluaran |
|---|---|---|
| 1 | PRD | dokumen ini |
| 2 | Kamus metrik | `metrik.md` — definisi + SQL tiap KPI |
| 3 | Wireframe | `wireframe.md` — susunan blok tiap halaman |
| 4 | Design system | `design_system.md` — token, komponen, aturan chart |
| 5 | Kerangka aplikasi | `app.py` + `core/` + `components/` + 1 halaman contoh |
| 6 | Halaman 1–7 | satu per satu, tiap halaman diverifikasi angkanya |
| 7 | Chatbot | port + prompt skema baru |
