# Wireframe — Dashboard Rekrutmen PLN v2

**Revisi 2026-08-19** — ditulis ulang di bawah doktrin keterbacaan D1–D6
(`design_system.md` §11) setelah review halaman 1: *"terlalu AI — info di mana-mana,
banyak caption kecil."* Angka yang tertulis adalah **angka nyata** dari `metrik.md`.

## Yang berubah dari versi sebelumnya

| Pola lama | Pola baru |
|---|---|
| Judul chart = nama kategori ("Tren pendaftaran") | Judul chart = kalimat temuan (D1) |
| Kartu insight 💡 di bawah tiap chart | Maksimal 1 kalimat temuan per **halaman**, jadi judul chart utama (D3) |
| Badge `⟨NYATA⟩` di tiap KPI | Tanpa badge; konteks di `help=` tooltip. Spanduk hanya kalau seluruh halaman `DIMODELKAN` (D4) |
| Spanduk hero gradien tiap halaman | Judul halaman polos (`st.title`); tanggal potong sekali di baris global (D6) |
| 6–8 blok per halaman | Maksimal 4 blok: KPI + 1 chart jangkar + ≤2 pendukung (D5) |
| Emoji (💡 ⚠ ✓) | Ikon Material atau teks polos (D6) |
| Halaman 4: asal per provinsi + almamater + peta asal | **Dikeluarkan** — data cacat, lihat `mockdb/ISSUES_SEBARAN.md` |

**Pola dua lapis** tetap: `LAPIS EKSEKUTIF` (4 blok di atas) selalu tampil ·
`LAPIS ANALIS` (filter + tabel + unduh) muncul lewat toggle global di baris atas.

---

## Kerangka global

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Ringkasan  Perencanaan  Tahapan seleksi  Pasca-OJT  Penempatan  Kandidat   │
│ Kualitas data  RecruitMan                                                  │
├────────────────────────────────────────────────────────────────────────────┤
│                      Data per 15 Sep 2026 …   [Mode analis ◯]              │
│                                                                            │
│                              ISI HALAMAN                                   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

Navigasi memakai `st.navigation(position="top")`: urutannya mengikuti alur proses
(rencana, seleksi, prajabatan, penempatan), dengan Kandidat sesudahnya sebagai halaman
profil pelamar, bukan tahap proses. Sidebar tidak dipakai; toggle Mode Analis dan tanggal
potong data ada di baris kanan tepat di bawah bar navigasi — satu tempat, bukan diulang
tiap halaman.

---

## Halaman 1 — Ringkasan

Judul halaman: **"Ringkasan"** (polos, tanpa subjudul gradien).

```
┌───────────┬───────────┬───────────┬───────────┐
│Pendaftaran│Diterima   │Rasio      │Sudah ber-SK│  st.metric native
│218.928    │7.711      │1 : 28     │5.711       │  konteks di help=
│▁▃▂▅▂▇▆    │▂▁▁▃▄▃▅    │           │+2.000 OJT  │  sparkline bawaan
└───────────┴───────────┴───────────┴───────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ Tes Adaptif menggugurkan lebih banyak orang daripada administrasi      │  <- judul = temuan (D1)
│ (batang per tahap, satu hue, urutan funnel)                            │
│ Administrasi  ████████████████████████████ 213.648                     │
│ Adaptif       ██████████████████ 143.831                               │
│ Akademik+Ing  ███████ 53.907                                           │
│ Psikologi     ███ 24.699                                               │
│ Fisik/MCU     ██ 15.980                                                │
│ Wawancara     █ 12.623                                                 │
│ Diterima      ▌7.711                                                   │
└────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┬───────────────────────────────────────┐
│ Pendaftaran per tahun            │ 2.000 orang kohort 2025 sedang OJT     │  <- judul = temuan
│ (batang, warna=jalur, D1: sudah  │ (batang horizontal, status warna)      │
│ terbaca tanpa caption karena     │ Diterima      ████████ 7.711           │
│ warna jalur langsung terlihat)   │ Kontrak       ████████ 7.711           │
│ 66rb 54rb 39rb 55rb (mandiri)    │ Pembidangan   ████████ 7.711           │
│ ○455 ○179 ○4.646 (rbb, ditandai) │ Sedang OJT    ██ 2.000 (status:peringatan)│
└──────────────────────────────────┴───────────────────────────────────────┘
```

**Tidak ada** kartu tautan ke halaman lain (blok ke-5 di versi lama) — melanggar batas 4
blok (D5). Navigasi atas sudah cukup untuk berpindah halaman.

**Satu kalimat temuan halaman ini** (D3, dipakai sebagai judul chart jangkar): *"Tes Adaptif
menggugurkan lebih banyak orang daripada administrasi."* Detail angka (95.204 vs 69.817,
52,1% karena tidak hadir) ada di tooltip `help=` pada chart itu, bukan caption terpisah.

**Lapis analis:** tabel ringkas 7 kohort (tahun, jalur, pendaftaran, diterima, kuota,
% pemenuhan) + unduh CSV.

---

## Halaman 2 — Perencanaan Kebutuhan

Spanduk `DIMODELKAN` tetap ada — ini **satu-satunya** halaman yang memakainya, karena
seluruh isinya memang hasil pemodelan (D4 mengizinkan spanduk per-halaman untuk kasus ini):

```
[!] Seluruh halaman ini dimodelkan. Tidak ada satu pun angka kuota per posisi di
    sistem PLN manapun — halaman ini memperagakan insight yang bisa muncul kalau
    data itu dikumpulkan. Satu-satunya bahan nyata: kolom FTK & realisasi.

┌───────────────┬───────────────┬───────────────┬───────────────┐
│Gap FTK 2026   │Kekosongan '26│Usulan 2025    │Pagu disetujui │
│701            │919            │1.238          │84,8%          │
└───────────────┴───────────────┴───────────────┴───────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ Persetujuan pagu naik dari 13% (2020) jadi 85% (2025)                  │  <- judul = temuan
│ (batang per tahun, satu seri: % disetujui)                             │
│ 2020 ██ 13%   2021 ███ 30%   2023 ███████ 70%   2025 ████████ 85%      │
└────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┬───────────────────────────────────────┐
│ Pensiun mendominasi kekosongan   │ Gap FTK terbesar: UID Jawa Barat       │  <- judul = temuan
│ (batang bertumpuk, 2019–2026)    │ (batang horizontal, top 10)            │
│ 2019 ████████████████ 2.357      │ UID Jabar   ████████ 59                │
│ 2022 ██████████ 1.290            │ Kantor Pusat███████ 55                 │
│ 2026 ███████ 919 (85% pensiun)   │ P3B Sumatera██████ 50                  │
│ ■pensiun ■APS ■meninggal ■PHK    │ (UID Jateng&DIY dikeluarkan, lihat     │
│                                  │  halaman Kualitas data — anomali)      │
└──────────────────────────────────┴───────────────────────────────────────┘
```

Ini sudah 4 blok (KPI + chart jangkar + 2 pendukung) — heatmap unit × sub-bidang dari
rencana lama **dipindah ke lapis analis** supaya tidak melanggar D5.

**Lapis analis:** heatmap unit × sub-bidang; filter tahun/unit/sub-bidang/grade; tabel
`usulan_kebutuhan` per posisi (34.006 baris, paginasi); unduh CSV.

---

## Halaman 3 — Tahapan Seleksi

```
┌───────────────┬───────────────┬───────────────┬───────────────┐
│Pendaftaran    │Diterima       │No-show        │Konversi       │
│218.928        │7.711          │35,2%          │3,5%           │
└───────────────┴───────────────┴───────────────┴───────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ Dari pendaftar sampai diterima: enam gerbang, satu jalan keluar         │  <- jangkar Plotly
│ (SANKEY — simpul berlabel jumlah langsung, tanpa legenda terpisah)      │
│                                                                          │
│  Administrasi ══╗                                                       │
│  213.648        ╠══► Adaptif ══╗                                        │
│                 ║    143.831   ╠══► Akademik ══► Psikologi ══► ...      │
│                 ╚══► gugur     ║    53.907                              │
│                     69.817     ╚══► gugur 90.204 (52,1% tidak hadir)   │
└────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┬───────────────────────────────────────┐
│ Tes online kehilangan separuh    │ Jalur RBB nyaris tak berjejak di PLN  │  <- judul = temuan
│ pesertanya, tes offline tidak    │ (batang: FHCI vs tercatat PLN, per    │
│ (batang: no-show % per tahap,    │  tahun; ⟨AGREGAT⟩ ditandai di judul)  │
│  warna=mode online/offline)      │                                       │
│ Adaptif(online)   ████████ 52,1% │ 2024  FHCI 237.045 ██████████████████ │
│ Akademik(online)  ███ 17,7%      │       PLN 4.646    ▌                 │
│ Psikologi(offline)██ 8,3%        │       (1,96% terlihat)               │
│ Fisik(offline)    █ 7,2%         │                                       │
└──────────────────────────────────┴───────────────────────────────────────┘
```

**Satu kalimat temuan halaman** (judul Sankey): *"Dari pendaftar sampai diterima: enam
gerbang, satu jalan keluar."* Detail (95.204 gugur di adaptif, 52,1% karena tidak hadir)
ada di tooltip Sankey per simpul dan di expander "Tentang halaman ini".

**Lapis analis:** filter tahun/jalur/jenjang/kota/profesi; tabel pendaftaran teragregasi
(tanpa PII); unduh CSV.

---

## Halaman 4 — Kandidat & Pasar Tenaga Kerja

> **Revisi 2026-08-19.** Rencana semula (sebaran asal per provinsi, analisis almamater, peta
> asal vs kota tes) **dibatalkan** — tiga-tiganya bersandar pada `kota_domisili` /
> `kota_asal` / `sekolah_universitas`, yang diketahui dibagikan acak seragam oleh generator
> (`mockdb/ISSUES_SEBARAN.md`). Diganti dengan data yang sebarannya sudah diverifikasi
> berpola benar.

```
┌───────────────┬───────────────┬───────────────┬───────────────┐
│Akun           │Pelamar unik   │Lamaran/akun   │Tidak melamar  │
│368.912        │172.389        │1,27           │196.523        │
└───────────────┴───────────────┴───────────────┴───────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ Kota dengan volume tes terbanyak                                       │  <- jangkar Plotly
│ (PETA scatter_geo — ukuran titik = jumlah tes, label kota langsung     │
│  pada 8 titik terbesar tanpa perlu legenda terpisah)                   │
│         ●Makassar(5.162)  ●Surabaya(5.160)  ●Palembang(5.115)          │
│         ●Balikpapan(5.083)  ●Jakarta(4.950)  ●Medan(4.912)             │
└────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┬───────────────────────────────────────┐
│ S1/D-IV mendominasi pelamar      │ Proporsi pria berayun 62–74% per tahun │  <- judul = temuan
│ (batang horizontal, jenjang)     │ (batang per tahun, satu seri: % pria)  │
│ S1/D-IV ████████████ 245.553     │ 2020 ████████ 74%                     │
│ D-III   █████ 98.161             │ 2021 ██████ 62%                       │
│ SMK     █ 11.696                 │ 2019 ███████ 63%                      │
│ S2      █ 11.631                 │ (tidak pernah satu angka tetap)        │
└──────────────────────────────────┴───────────────────────────────────────┘
```

**Lapis analis:** filter jenjang/prodi/rumpun/tahun; tabel rumpun jurusan melamar vs
diterima (program_studi berpola benar, aman dipakai); unduh CSV. **PII tidak pernah
ditampilkan** — grep otomatis di `tests/uji_disiplin.py`.

---

## Halaman 5 — Pasca-Seleksi & OJT

```
┌───────────────┬───────────────┬───────────────┬───────────────┐
│Diterima       │Sudah ber-SK   │Sedang OJT     │UPDL aktif     │
│7.711          │5.711          │2.000          │11             │
└───────────────┴───────────────┴───────────────┴───────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ 2.000 orang kohort 2025 sedang OJT, SK menyusul                        │  <- judul = temuan
│ (batang rantai 7 tahap, status warna: selesai vs berjalan)             │
│ Pengumuman █████████ 7.711(selesai)                                    │
│ Kontrak    █████████ 7.711(selesai)                                    │
│ SAMAPTA    █████████ 7.711(selesai)                                    │
│ Pembidangan█████████ 7.711(selesai)                                    │
│ OJT        ██ 2.000(berjalan) ███████ 5.711(selesai)                   │
│ Ujian OJT  ███████ 5.711(selesai)                                      │
│ SK         ███████ 5.711(selesai)                                      │
└────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┬───────────────────────────────────────┐
│ Timeline kohort 2019–2025        │ Distribusi menyerap paling banyak     │  <- judul = temuan
│ (Gantt, penanda "hari ini")      │ (batang horizontal, pembidangan)      │
│ 2019 ▬▬▬▬▬(selesai)              │ Distribusi    ████████ 1.499          │
│ 2023 ▬▬▬▬▬(selesai)              │ SDM           ████████ 1.464          │
│ 2025 ▬▬▬▬░░ OJT→SK 9 Nov 2026    │ Pembangkitan  █████ 871                │
│      ▲hari ini                   │ Niaga         ████ 820                │
└──────────────────────────────────┴───────────────────────────────────────┘
```

Catatan durasi konstan (400 hari, tidak ada analisis SLA) dan titik rawan integrasi
Pusdiklat pindah ke expander "Tentang halaman ini" (D2) — bukan spanduk permanen.

**Lapis analis:** sebaran per UPDL (11 lokasi); filter tahun/bidang/UPDL; tabel; unduh CSV.

---

## Halaman 6 — Penempatan & Pemenuhan

```
┌───────────────┬───────────────┬───────────────┬───────────────┐
│Ditempatkan    │Induk          │Subholding     │Grade G2       │
│7.711          │5.171 (67%)    │2.540 (33%)    │5.423 (70%)    │
└───────────────┴───────────────┴───────────────┴───────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ Kantor Pusat menyerap penempatan terbanyak                             │  <- jangkar Plotly
│ (TREEMAP unit × bidang — label unit & angka langsung di tiap sel,      │
│  tanpa legenda terpisah)                                                │
│  ┌──────────┬───────┬─────┐                                            │
│  │Kantor    │UID    │UIW  │                                            │
│  │Pusat(447)│Jabar  │Maluku│                                           │
│  │          │(236)  │(225) │                                           │
│  └──────────┴───────┴─────┘                                            │
└────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┬───────────────────────────────────────┐
│ Rencana vs realisasi: mandiri    │ Grade masuk sesuai jenjang pendidikan │  <- judul = temuan
│ selalu 100%, RBB bervariasi      │ (batang horizontal)                   │
│ (slope chart per tahun, jalur    │ G2 ████████████ 5.423 (S1/D4)         │
│  RBB ditandai warna berbeda)     │ G1 ████ 2.020 (SMK/D3)                │
│ 2019 1.353→1.353(100%)           │ G3 █ 268 (S2)                         │
│ 2020 325→125(38,5%, RBB)         │                                       │
│ 2025 2.000→2.000(100%)           │                                       │
└──────────────────────────────────┴───────────────────────────────────────┘
```

Penjelasan kenapa tahun RBB dikeluarkan dari rata-rata pemenuhan pindah ke expander
"Tentang halaman ini", bukan spanduk permanen di bawah chart.

**Lapis analis:** tabel per unit induk (kuota, realisasi, %); filter bidang/grade/tahun/
jenis penempatan; unduh CSV.

---

## Halaman 7 — Kualitas Data & Sumber Sistem

Satu-satunya halaman lain yang boleh melebihi pola 4-blok standar, karena isinya sendiri
adalah katalog teknis (metadata tentang dashboard ini), bukan analisis bisnis berlapis.

```
┌────────────────────────────────────────────────────────────────────────┐
│ Empat sistem, satu perjalanan orang — tidak satu pun bisa berdiri      │  <- judul = temuan
│ sendiri menjawab "berapa orang sedang OJT"                             │
│ (diagram alur: FHCI → rekrutmen.pln → seleksi.pln → Pusdiklat → HTD,   │
│  label volume baris langsung di tiap panah)                            │
│  [FHCI]──►[rekrutmen.pln 370.102]──►[seleksi.pln 53.907]──►[Pusdiklat] │
│  agregat, 1,96% terlihat            +40.679 upload vendor    ──►[HTD]  │
└────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┬───────────────────────────────────────┐
│ Kelengkapan data membaik tiap    │ Dua angka rencana tak pernah          │  <- judul = temuan
│ tahun (ramp ordinal 3 langkah)   │ didamaikan, selisih melebar ke 950    │
│         blok fisik  domisili     │ (batang selisih per tahun)            │
│ RENDAH    0,0%       90,0%       │ 2020  0        2023  ████ +520        │
│ SEDANG   33,1%       97,3%       │ 2019  ██+260   2025  ████████ +950    │
│ BAIK     70,6%       99,6%       │                                       │
└──────────────────────────────────┴───────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ Kolom dimodelkan & anomali yang diketahui (tabel, bukan chart)         │
│ kuota per posisi    │ domain HST, tidak ada di HTD          │ F-017    │
│ passing grade       │ tidak ada di perdir 0056/0050/0048    │ F-028    │
│ skor tes mentah     │ sistem asli hanya simpan lulus/gagal  │ F-017    │
│ ---                                                                     │
│ UID Jateng&DIY: jumlah_pegawai 4 vs ftk_2025 144 -> gagal match DAPEG   │
│ realisasi_apr_2026 hanya 1/48 unit -> semua gap pakai Mar-2026          │
│ 5 bidang kandidat acak seragam -> mockdb/ISSUES_SEBARAN.md              │
└────────────────────────────────────────────────────────────────────────┘
```

Tabel di blok terakhir bukan pelanggaran D5 — ini referensi teknis, bukan chart tambahan.
Halaman ini **tidak punya lapis analis**; isinya sudah sepenuhnya level teknis.

---

## Halaman 8 — Chatbot

```
┌────────────────────────────────────────────┬─────────────────────────────┐
│  Percakapan                                 │ Profil LLM  [pilih]         │
│  ┌──────────────────────────────────────┐  │ status: terhubung            │
│  │ Berapa yang diterima tahun 2023?     │  │                             │
│  │ 1.797 orang dari 38.538 pendaftar    │  │ Pertanyaan contoh:          │
│  │ (4,7%).                              │  │ - Tahap mana yang paling    │
│  │  > SQL yang dijalankan   [lihat]     │  │   banyak menggugurkan?      │
│  │  [chart otomatis]        [unduh CSV] │  │ - Unit mana gap FTK terbesar│
│  └──────────────────────────────────────┘  │ - Berapa yang sedang OJT?   │
│  [ketik pertanyaan...                  ➤]  │                             │
└────────────────────────────────────────────┴─────────────────────────────┘
```

Port dari v1: tool `run_sql_query` + `render_chart`, guard SELECT-only, riwayat tersimpan,
ekspor CSV. Beda v2: koneksi DuckDB read-only ke file (bukan DataFrame di memori); prompt
skema dibangun dari katalog + `docs/metrik.md` dimuat saat runtime (bukan disalin) — setiap
metrik baru otomatis diketahui chatbot tanpa perubahan kode.

---

## Catatan implementasi lintas halaman

| Hal | Aturan |
|---|---|
| Urutan blok | KPI (native `st.metric`) → chart jangkar (judul=temuan) → ≤2 chart pendukung (judul=temuan) |
| Batas blok | Maksimal 4 per halaman (D5), kecuali halaman 7 (katalog teknis) |
| Lebar | KPI 4 kolom `st.container(horizontal=True)`; chart jangkar lebar penuh; pendukung 2 kolom |
| Penjelasan | `help=` di KPI, expander "Tentang halaman ini" per halaman — tidak pernah caption permanen (D2) |
| Kosong | Tiap chart punya keadaan "tidak ada data pada filter ini" |
| Muat | Query berat di-cache (`@st.cache_data`), bukan dijalankan tiap rerun |
| Emoji | Tidak dipakai (D6); ikon Material seperlunya untuk status/navigasi |
