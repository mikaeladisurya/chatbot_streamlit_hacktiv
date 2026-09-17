# Audit UI/UX — Dashboard Rekrutmen PLN (Tower 2)

Tanggal audit: 16 September 2026
Metode: inspeksi antarmuka saja (browser, 1440px dan 390px, terang dan gelap). Tidak membaca kode, dokumen, atau basis data. Latar domain hanya dari `knowledge for auditor.txt`.
Data yang terlihat: "Data per 15 September 2026, gelombang 2019–2025, PLN Group".

---

## 1. Ringkasan eksekutif

**Vonis: ini produk analitik yang serius, bukan tumpukan chart — tapi ia berhenti satu langkah sebelum menjadi alat pengambilan keputusan.**

Yang membedakan dashboard ini dari rata-rata dashboard buatan AI: teks bantuannya benar-benar berisi. Hampir setiap popover `help` menjelaskan mekanisme data, bukan mengulang judul chart. Contoh: "Jalur RBB masuk langsung di Akademik & Inggris, sehingga batang Akademik bisa lebih lebar dari lulusan Adaptif" — itu tulisan orang yang paham datanya. Halaman "Kualitas data" yang mengaku terus terang soal lima sistem yang tidak tersambung adalah hal paling jujur yang pernah saya lihat di dashboard korporat. Filter global konsisten dan bertahan antar halaman. Palet warna menahan diri, tipografi rapi, mode gelap berfungsi.

Masalahnya ada di tempat lain: **dashboard ini tahu banyak, tapi tidak memutuskan apa yang paling penting.** Setiap halaman menyajikan 3–7 chart dengan berat visual yang hampir sama, disusun dalam grid kartu seragam. Angka yang paling penting bagi BPO — *apakah kebutuhan tenaga kerja terpenuhi?* — dikubur di chart paling bawah halaman keenam. Beberapa chart menempati ruang besar untuk menyampaikan nol informasi. Dan satu halaman (RecruitMan) dalam keadaan rusak sambil membocorkan potongan API key ke layar.

### Lima temuan terpenting

**T1 — Pertanyaan inti proses PLN tidak pernah dijawab di depan.**
Menurut logika proses PLN, seluruh rekrutmen ada untuk memenuhi kebutuhan tenaga kerja yang direncanakan. Rantai *pagu → diterima → ditempatkan → SK* adalah cerita utamanya. Chart yang menunjukkan itu, `"Kuota dan realisasi per tahun"`, ada di **paling bawah halaman "Penempatan"** — halaman keenam, slice kedua, di bawah lipatan. Halaman "Ringkasan" sama sekali tidak menyinggung pemenuhan kebutuhan; ia hanya bercerita tentang volume pelamar. Dashboard ini dimulai dari kandidat, persis yang menurut dokumen domain "sebaiknya tidak" dilakukan.

**T2 — Kartu KPI `"Kuota terpenuhi 100%"` di halaman "Penempatan" bertabrakan dengan chart di halaman yang sama.**
KPI besar bertuliskan `100%`. Empat ratus piksel di bawahnya, `"Kuota dan realisasi per tahun"` menampilkan 38% (2020), 7% (2021), 81% (2024). Satu halaman, dua jawaban berbeda untuk satu pertanyaan, tanpa penjelasan di KPI. Pembaca yang menyalin KPI itu ke rapat direksi akan salah.

**T3 — Beberapa chart besar menyampaikan nol informasi.**
`"Rantai tahap setelah diterima"` adalah tujuh batang, lima di antaranya persis 7.711 dan dua persis 5.711. Satu chart selebar halaman, tinggi ~300px, untuk menyampaikan dua angka yang sudah ada di kartu KPI di atasnya. Popover-nya bahkan mengakui bahwa penurunan itu bukan kejadian nyata. `"Jejak pelamar RBB di sistem PLN"` adalah tiga batang yang ketiganya 1,96%. `"Sebaran skor tes online"` adalah histogram yang rata sempurna karena skornya dimodelkan acak — tidak ada distribusi untuk dibaca.

**T4 — `"Penempatan per unit induk dan bidang"` (treemap) adalah elemen paling dekoratif dan paling sulit dibaca di seluruh aplikasi.**
Sekitar 40 warna kategorikal berputar tanpa makna — warna hanya menandai unit yang labelnya sudah tertulis di kotak. Belasan kotak terkecil punya label yang tidak terbaca (`UIP3B Kalimantan`, `PUSHARLIS`, `UIP Sulawesi` tercetak di dalam kotak 30×20px). Ini rainbow, dan tidak satu pun perbandingan bisa dilakukan dengan mata.

**T5 — Halaman "RecruitMan" rusak dan membocorkan kredensial.**
Di layar tertulis: `Error code: 401 - {'error': {'message': 'Authentication Error, Invalid proxy server token passed. Received API Key = sk-...FoqA, Key Hash (Token) =5ec`. Di sampingnya ada pemilih model `Qwen3.5 35B A3...`. Di bawahnya, riwayat percakapan pengembang masih terpampang, termasuk `"Hewan apa yang suka..."`. Ini kontrol internal dan sampah uji yang tidak boleh terlihat oleh pengguna manajemen, apalagi potongan API key.

---

## 2. Uji 60 detik — apa yang tertangkap tanpa bantuan

Satu kalimat per halaman, hanya dari yang terlihat, tanpa membuka popover.

| Halaman | Yang tertangkap dalam 60 detik |
|---|---|
| **Ringkasan** | "218.928 lamaran, 7.711 diterima, peluang 1:28, dan ada tiga kelompok rekrutmen yang peluangnya beda jauh" — tertangkap, dan `1 : 28` adalah cara menulis rasio yang sangat baik. |
| **Perencanaan kebutuhan** | "Ada kekurangan 701 pegawai di 41 dari 47 unit, dan hanya sebagian usulan disetujui" — tertangkap, tapi langsung terganggu banner kuning besar yang mengumumkan bahwa halaman ini dimodelkan dan filternya tidak berlaku. |
| **Corong seleksi** | "Dari 218.928 pendaftar tersisa 7.711; yang gugur sebagian karena tidak lulus, sebagian karena tidak hadir" — tertangkap dengan sangat baik. Sankey-nya adalah chart terbaik di aplikasi ini. |
| **Kandidat** | Tidak tertangkap. Saya melihat peta, piramida umur, dua scatter, dan sebuah grafik IPK — tapi tidak ada satu pun pernyataan tentang *siapa* kandidat PLN. Kartu `"Akun tanpa lamaran 196.523"` dan `"Profil lengkap dan aktif 340.561"` justru membingungkan karena angkanya lebih besar dari jumlah pelamar. |
| **Pasca-seleksi dan OJT** | "7.711 diterima, 5.711 sudah SK, 2.000 masih OJT" — tertangkap, tapi itu sudah saya baca di Ringkasan. Halaman ini tidak menambah apa-apa. |
| **Penempatan** | Mata langsung jatuh ke treemap pelangi dan berhenti di situ. Informasi yang berguna (`"Kuota dan realisasi per tahun"`) tidak terlihat dalam 60 detik. |
| **Kualitas data** | "Data rekrutmen melewati lima sistem dan tidak ada satu pun yang lengkap" — tertangkap sangat jelas. Halaman ini bekerja. |
| **RecruitMan** | "Rusak." |

---

## 3. Arsitektur informasi

### Urutan halaman saat ini
`Ringkasan → Perencanaan → Corong seleksi → Kandidat → Pasca-seleksi & OJT → Penempatan → Kualitas data → RecruitMan`

### Penilaian
Urutannya **hampir** mengikuti proses nyata (Perencanaan → Seleksi → Pasca-seleksi → Penempatan), dan itu keputusan yang benar. Tapi ada dua kesalahan urutan:

**3.1 "Kandidat" berada di tempat yang salah secara kronologis.**
Dalam proses PLN, kandidat mendaftar *sebelum* diseleksi. Menaruh "Kandidat" *setelah* "Corong seleksi" memutus alur cerita: pembaca sudah melihat hasil seleksi, lalu diminta mundur untuk melihat siapa yang mendaftar. Urutan yang benar: **Perencanaan → Kandidat → Corong seleksi → Pasca-seleksi → Penempatan**.

**3.2 "Kualitas data" ada di posisi 7, seharusnya posisi 2 atau sebagai panel permanen.**
Halaman ini menjelaskan *mengapa* angka-angka di enam halaman sebelumnya tidak bisa didamaikan. Pembaca yang menemukan kejanggalan di halaman 1 tidak punya petunjuk bahwa jawabannya ada di halaman 7. Minimal, chart yang angkanya terpengaruh (`"Selisih FTK dan realisasi per unit"`, `"Kuota dan realisasi per tahun"`) harus punya tautan langsung ke halaman ini, bukan hanya catatan di popover.

### Satu tugas per halaman
- **Ringkasan** — tugas: volume dan peluang. Tapi ia *tidak* meringkas seluruh dashboard; tidak ada satu pun angka perencanaan atau penempatan di sana. Ini "Ringkasan Pendaftaran", bukan "Ringkasan".
- **Perencanaan kebutuhan** — satu tugas, jelas. Tapi lihat 4.2: halamannya mengaku dirinya fiktif.
- **Corong seleksi** — satu tugas, dieksekusi paling baik.
- **Kandidat** — **tidak punya satu tugas.** Isinya campuran: demografi pelamar (piramida umur, rumpun jurusan, IPK), higiene akun (`"Akun tanpa lamaran"`, `"Profil lengkap dan aktif"`), dan **operasional tes** (`"Volume dan tingkat lulus per kota tes"`). Tiga topik berbeda dalam satu halaman.
- **Pasca-seleksi & OJT** — terlalu tipis. Tiga chart, dua di antaranya mengulang Ringkasan.
- **Penempatan** — satu tugas, tapi chart terpentingnya ditaruh terakhir.
- **Kualitas data** — satu tugas, jelas, bagus.

### Yang salah tempat

| Elemen | Ada di | Seharusnya di | Alasan |
|---|---|---|---|
| `"Volume dan tingkat lulus per kota tes"` (peta) | Kandidat | Corong seleksi | Ini tentang penyelenggaraan tes offline dan kinerja lokasi, bukan tentang siapa kandidatnya. Ia juga bersaudara langsung dengan `"Tingkat lulus per vendor tes"` yang ada di Corong seleksi. |
| KPI `"Akun tanpa lamaran 196.523"`, `"Profil lengkap dan aktif 340.561"` | Kandidat | Kualitas data | Ini metrik higiene basis data, bukan metrik rekrutmen. Kehadirannya di baris KPI Kandidat membuat pembaca mengira 340.561 orang melamar. |
| `"Pendaftaran per bulan"` | Kandidat | Ringkasan (atau dihapus) | Ia menunjukkan hal yang sama dengan `"Kalender gelombang rekrutmen"` di Ringkasan: rekrutmen PLN bersifat gelombang, bukan kontinu. |
| `"Kuota dan realisasi per tahun"` | Penempatan (paling bawah) | Ringkasan **dan** Perencanaan | Ini jawaban atas pertanyaan inti BPO. |

---

## 4. Penilaian per halaman

### 4.1 "Ringkasan"

**Hierarki visual.** Baik di baris KPI: enam kartu, angka besar, label kecil, tidak ada gradien atau ikon dekoratif. `1 : 28` untuk peluang diterima adalah pilihan yang sangat bagus — lebih mudah dicerna manajemen daripada "3,5%". Di bawah baris KPI, hierarki runtuh: lima chart dalam kartu berbingkai identik, tidak ada yang secara visual mengaku sebagai yang paling penting.

**Chart, satu per satu.**

1. `"Pendaftaran dan peluang per tahun"` — batang bertumpuk + panel garis terpisah di bawahnya. Bentuknya benar (menghindari sumbu ganda, panel terpisah adalah pilihan yang jauh lebih baik). Tapi panel garis punya masalah serius: garis biru "Terbuka" datar di ~2% dan garis hijau "RBB" di ~27,5% adalah **garis horizontal sempurna** — tidak ada perubahan antar tahun. Garis menyiratkan tren; di sini tidak ada tren. Lebih baik: batang kecil per kelompok, atau cukup satu anotasi teks "Peluang: Terbuka 2%, Afirmasi 19%, RBB 27%". Selain itu garis-garisnya terputus (RBB hanya 2020–2024, Afirmasi hanya 2023–2025) sehingga tampak seperti data hilang, bukan kelompok yang memang tidak ada di tahun itu.
2. `"Konversi tahap seleksi"` — corong (funnel). **Bentuk yang salah, dan berulang.** Data ini sudah disajikan sebagai Sankey di halaman "Corong seleksi" dengan angka yang sama persis (213.648 / 143.831 / 53.907 / 24.699 / 15.980 / 12.623 / 7.711), dan Sankey-nya lebih informatif karena memisahkan gugur-tidak-lulus dari gugur-tidak-hadir. Bentuk corong juga menipu: lebar batang proporsional, tapi sisi miringnya menciptakan luas yang tidak berarti apa-apa. Selain itu urutannya terbalik dari urutan baca: label di sumbu dibaca Administrasi→Diterima dari atas, tapi daftar teks (untuk pembaca layar) keluar Diterima→Administrasi.
3. `"Kalender gelombang rekrutmen"` — Gantt dengan titik ujung berukuran. Ini chart terbaik di halaman ini: ia menjawab "kapan, berapa lama, seberapa besar, seberapa sulit" dalam satu bentuk. Pertahankan.
4. `"Pendaftar dan peluang per gelombang"` — scatter log. **Redundan.** Tiga poin yang disampaikannya (RBB peluang tinggi volume kecil, Terbuka peluang rendah volume besar) sudah terbaca di chart 1 *dan* di chart 3. Hanya tiga dari 17 titik yang diberi label (`2024 RBB 1`, `2025 Afirmasi`, `2025 Reguler`); 14 sisanya anonim dan memaksa hover. Sumbu-x logaritmik tidak diberi tanda bahwa ia logaritmik.
5. `"Status diterima per tahun"` — batang bertumpuk SK terbit / Sedang OJT. Praktis tidak bertumpuk: 2019–2024 seluruhnya biru, 2025 seluruhnya kuning. Informasi sesungguhnya adalah "kohort 2025 belum SK" — satu kalimat, bukan satu chart.

**Beban kognitif.** Legenda `Terbuka / Afirmasi / RBB` muncul tiga kali di halaman ini dengan dua palet berbeda (pekat di chart 1 dan 4, pucat di chart 3). Pembaca harus membangun peta warna sendiri. Istilah "Terbuka", "Afirmasi", "RBB" tidak pernah didefinisikan di layar — hanya di dalam popover chart 1. Bagi pengguna baru, tiga kata itu adalah tiga teka-teki.

**Interaksi.** Filter jelas dan responsif. Tidak ada tombol "semua tahun"/reset yang terlihat.

---

### 4.2 "Perencanaan kebutuhan"

**Masalah struktural yang lebih besar dari semua chart di halaman ini:** banner kuning di paling atas berbunyi

> `"Seluruh halaman ini dimodelkan. Tidak ada angka kuota per posisi di sistem PLN mana pun; halaman ini memperagakan insight yang muncul kalau data itu dikumpulkan. Satu-satunya bahan nyata adalah FTK dan realisasi pegawai per unit. Filter tahun, jenis, dan jenjang tidak berlaku di halaman ini."`

Kejujurannya patut dihargai, tapi konsekuensinya berat: halaman ini adalah **titik awal seluruh proses rekrutmen PLN**, dan ia mengumumkan bahwa isinya tidak nyata. Lebih buruk lagi, filter global tetap **terlihat aktif di atas halaman** padahal tidak berfungsi — pengguna bisa mengklik `2023` dan tidak ada yang berubah, tanpa umpan balik. Filter yang tidak berlaku harus dinonaktifkan secara visual (redup + tooltip), bukan dibiarkan bisa diklik.

Kontradiksi tambahan: banner bilang filter tahun tidak berlaku, tapi `"Usulan kebutuhan per unit dan sub-bidang"` punya **tab tahun sendiri (2019–2025) di dalam kartunya**. Dua mekanisme tahun di satu halaman, satu mati satu hidup.

**Hierarki visual.** Baris KPI tidak koheren dalam kerangka waktu: `Kekurangan FTK 701` (saat ini), `Unit kekurangan 41 dari 47` (saat ini), `Proyeksi kekosongan 2026 919` (masa depan), `Usulan 2025 1.238` (tahun lalu), `Pagu disetujui 2025 84,8%` (tahun lalu). Lima kartu, tiga kerangka waktu, tidak ada yang menandai perbedaan itu. Selain itu satu kartu berisi persen dan empat berisi jumlah — tidak apa-apa, tapi `84,8%` tanpa penyebut membuat pembaca bertanya "84,8% dari apa".

**Chart, satu per satu.**

1. `"Usulan dan pagu per tahun"` — batang abu lebar dengan batang biru sempit di dalamnya (pola bullet). Bentuknya tepat untuk target-vs-realisasi. **Tapi tidak ada legenda sama sekali**: tidak ada di layar yang memberi tahu bahwa abu = usulan dan biru = pagu. Itu hanya ada di dalam popover. Persentase di atas batang juga tidak diberi keterangan (35%, 13%, 30%... porsi usulan yang disetujui) — angka telanjang di atas chart.
2. `"Proyeksi kekosongan per sebab"` — area bertumpuk, empat sebab. **Bentuk salah.** "Pensiun" menempati ~95% area; tiga kategori lain (Mengundurkan diri, Meninggal, PHK) adalah pita setebal beberapa piksel yang mustahil dibandingkan. Area bertumpuk juga menyiratkan kontinuitas antar tahun padahal ini angka tahunan diskrit. Ganti dengan: satu garis/batang untuk total, plus small multiple (4 panel kecil, sumbu-y masing-masing) untuk komposisi — atau cukup batang bertumpuk.
3. `"Usulan kebutuhan per unit dan sub-bidang"` — heatmap 20 unit × 15 sub-bidang. Skala biru sekuensial adalah pilihan benar. Masalahnya: **hampir semua sel warnanya sama** (biru sangat pucat), dengan 3–4 sel gelap terisolasi. Heatmap tanpa variasi = kanvas kosong yang mahal. Tidak ada legenda skala warna, tidak ada nilai di sel, jadi tidak ada cara membaca besaran tanpa hover. Label sumbu-x dimiringkan 45° dan satu terpotong (`Manajemen Konstruksi dan…`), label sumbu-y dipotong juga.
4. `"Selisih FTK dan realisasi per unit"` — batang divergen, 47 unit. **Ini chart paling salah tempatkan di aplikasi.** Ia berisi informasi paling berguna di halaman (unit mana yang kekurangan orang) tapi dijejalkan ke kolom setengah lebar sehingga tiap baris hanya ~9px dan sebagian besar nama unit hilang. Lebih parah: sumbu-x bertuliskan `Pegawai` dengan nilai `−100, −50, 0, 50` — unit yang **kelebihan** pegawai tampil sebagai angka **negatif**. Konvensi tanda itu terbalik dari intuisi dan tidak dijelaskan di sumbu. Ganti label sumbu menjadi eksplisit: `← Lebih | Kurang →`. Chart ini layak lebar penuh.

---

### 4.3 "Corong seleksi"

Halaman terkuat. Tugasnya satu dan jelas.

**Hierarki visual.** Sangat baik: Sankey lebar penuh mendominasi, sisanya mendukung. Persis seperti seharusnya.

**Chart, satu per satu.**

1. `"Alur pendaftar per tahap"` (Sankey) — **bentuk yang tepat dan eksekusi bagus.** Ia memisahkan tiga takdir (lanjut / gugur tidak lulus / gugur tidak hadir) yang tidak bisa dilakukan corong. Jalur RBB yang melompat ke Akademik terlihat jelas. Kritik: (a) **tidak ada legenda warna di chart** — biru/merah/kuning hanya dijelaskan di popover, padahal ini informasi wajib; (b) sekitar 40% tinggi kartu adalah ruang kosong di bawah pita kuning; (c) tidak ada penanda visual di simpul "Akademik & Inggris" yang menjelaskan lonjakan masuk dari RBB, padahal itu anomali pertama yang akan ditanyakan pembaca.
2. `"Tingkat lulus per tahap dan tahun"` — heatmap angka. Baik, tapi: nilai ditulis `65`, `30`, `36` tanpa tanda `%`; sel kosong untuk tahun RBB terbaca sebagai "data hilang" bukan "tahap tidak dilalui" (butuh arsiran atau tanda `—`); popover menyuruh "baca per kolom" tapi tata letaknya (tahun di baris kiri) mengundang baca per baris. **Saat filter tahun tunggal diaktifkan chart ini menjadi satu baris** dan kehilangan seluruh maksudnya — tidak ada fallback.
3. `"Ketidakhadiran tes per tahun"` — dumbbell online vs offline. Bentuk tepat. Tapi 2019 dan 2021 hanya punya satu titik tanpa penjelasan, dan sumbu-x `Tidak hadir (%)` naik sampai 60 padahal data maksimum ~50 — ruang kosong. Temuan besar di sini (tidak hadir tes online 39–50%) pantas jadi judul, bukan sekadar garis.
4. `"Sebaran skor tes online"` — dua histogram. **Chart ini sebaiknya dihapus.** Histogramnya rata sempurna — setiap bin tingginya identik — karena, seperti diakui popover-nya, `"Skor ini dimodelkan: sistem asli hanya menyimpan lulus atau gagal, tanpa angka skor."` Menampilkan distribusi yang dibuat-buat dalam bentuk yang secara khusus dimaksudkan untuk membaca distribusi adalah kontradiksi. Menyisakannya mengundang pembaca menyimpulkan hal yang tidak ada.
5. `"Tingkat lulus per vendor tes"` — dua dot plot bertumpuk. Bentuknya bisa diterima, tapi: tidak ada judul sumbu-x di kedua panel (angka 40–100 tanpa satuan); tidak ada nilai di samping titik sehingga harus hover; nama vendor terpotong (`VEND06 Balikpa…`, `VEND05 Palemb…`); dua panel memakai rentang sumbu yang sama (40–100) padahal semua data Psikologi ada di 60–75 dan semua Fisik di 85–90 — 60% lebar chart kosong. Lollipop terurut dengan nilai tercetak akan lebih baik.
6. `"Hari sejak melamar"` — batang rentang persentil 10–90 dengan median. Bentuk tepat, label `17 hari … 131 hari` tercetak — bagus. Satu-satunya kritik: judulnya `"Hari sejak melamar"` tidak menyebut bahwa ia menunjukkan sebaran, bukan satu angka.
7. `"Alasan gugur administrasi"` — batang horizontal terurut dengan nilai tercetak. Sempurna untuk tugasnya. `IPK di bawah minimum 34.077` adalah temuan nyata. Pertahankan.

**Beban kognitif.** Kartu KPI `"Tidak hadir tes online 42,7%"` adalah angka paling mengkhawatirkan di seluruh dashboard — hampir separuh peserta tidak datang — dan ia diletakkan sebagai kartu keempat dari lima, ukuran sama dengan yang lain.

---

### 4.4 "Kandidat"

**Hierarki visual.** Tidak ada. Enam chart, enam bentuk berbeda, berat visual sama. Peta menempati posisi kiri-atas (posisi paling berharga) padahal isinya paling tidak relevan dengan judul halaman.

**Chart, satu per satu.**

1. `"Volume dan tingkat lulus per kota tes"` — peta gelembung, ukuran = jumlah tes, warna = % lulus. Salah halaman (lihat §3). Selain itu: skala warnanya membentang hanya dari ~63 ke ~77 sehingga dua biru yang berbeda 10 poin persen tampak identik; legenda hanya menandai `75`, `70`, `65`; label kota tumpang tindih dengan gelembung (`Jakarta`, `Palembang`, `Makassar` tertimpa); dan lebih dari separuh gelembung tidak diberi nama sama sekali. Peta adalah bentuk yang benar hanya kalau geografi itu sendiri yang jadi temuan — di sini yang jadi temuan adalah peringkat kota, yang lebih baik disajikan sebagai batang terurut.
2. `"Peluang menurut lama mencoba"` — batang 1/2/3/4 tahun, dengan nilai tercetak (3,5% → 17,3%). Bentuk tepat, nilai tercetak, monoton naik, jelas. Popover-nya bahkan memperingatkan bias seleksi. Salah satu chart terbaik di aplikasi. Judulnya agak rancu (`"lama mencoba"` terbaca "durasi", padahal maksudnya "jumlah tahun program yang diikuti").
3. `"Peluang diterima menurut IPK"` — grafik langkah dengan **area terisi**. **Bentuk salah.** Area di bawah kurva menyiratkan akumulasi/volume; di sini sumbu-y adalah *tingkat* (%), dan luas di bawahnya tidak berarti apa-apa. Selain itu sumbu-y (0–4,0 %) dan sumbu-x (IPK 2,00–4,00) dua-duanya berakhir di "4" dengan makna berbeda — sumber salah baca. Temuan sesungguhnya — lompatan tajam tepat di IPK 3,00 (dari ~1,9% ke ~3,7%) — tidak dianotasi sama sekali, padahal itu satu-satunya alasan chart ini ada. Ganti dengan garis langkah tanpa isian, plus label lompatan, plus batang volume pendaftar di belakangnya agar pembaca tahu bin mana yang tebal.
4. `"Volume dan peluang per rumpun jurusan"` — scatter, ~20 titik, **hanya 4 diberi label**. Enam belas titik anonim. Garis putus-putus rata-rata tidak diberi label nilainya. Ini memaksa hover untuk informasi dasar. Untuk 20 kategori, tabel terurut atau batang berpasangan jauh lebih terbaca.
5. `"Umur dan gender pelamar"` — piramida penduduk. Bentuk tepat untuk data ini. Tapi sumbu umur dipotong di 20 dan 34 tanpa penanda "≤20" / "≥34", dan baris paling bawah punya batang aneh yang jauh lebih panjang ke kiri — tampak seperti kelompok "20 dan di bawah" yang tidak dilabeli sebagai bucket. Warna biru/oranye untuk Pria/Wanita adalah pilihan konvensional yang bisa diterima.
6. `"Pendaftaran per bulan"` — batang bulanan. Mostly nol dengan beberapa paku. Duplikat maksud `"Kalender gelombang rekrutmen"`. Kalau dipertahankan, ia lebih berguna di Ringkasan sebagai bukti "rekrutmen PLN bersifat gelombang".

**Beban kognitif.** Kartu `"Profil lengkap dan aktif 340.561"` berdampingan dengan `"Pelamar unik 172.389"`. Pembaca harus menyimpulkan sendiri bahwa 340.561 adalah populasi akun, bukan pelamar. Itu pekerjaan yang seharusnya dilakukan desain.

---

### 4.5 "Pasca-seleksi dan OJT"

Halaman paling tipis. Tiga chart, dan chart terbesarnya kosong makna.

**Chart, satu per satu.**

1. `"Rantai tahap setelah diterima"` — batang bertumpuk, tujuh tahap. **Hapus atau ganti total.** Lima batang pertama bernilai identik (7.711), dua terakhir identik (5.711). Satu-satunya variasi adalah irisan kuning di OJT. Popover-nya sendiri menulis: `"Batang yang memendek setelah OJT bukan orang yang keluar, melainkan kohort terbaru yang belum sampai ke tahap berikutnya."` Artinya: chart ini menggambar sebuah penurunan yang tidak nyata, lalu memakai popover untuk membatalkannya. Kalau tujuh tahap itu tidak punya kebocoran, katakan saja dengan kalimat, dan pakai ruangnya untuk chart yang tidak ada (lihat §9).
2. `"Tonggak waktu per kohort"` — timeline titik per kohort (pengumuman / mulai OJT / SK). Bentuk tepat, terbaca, informatif. Pertahankan. Kekurangan: durasi tidak ditulis sebagai angka (harus diukur dengan mata di sumbu tahun), dan kohort 2025 yang berhenti di dua titik tidak diberi tanda "masih berjalan" di layar.
3. `"Peserta per UPDL"` — lollipop terurut dengan nilai tercetak. Baik. Untuk 11 kategori, batang biasa sama efektifnya dan lebih tenang, tapi ini bukan kesalahan.

**Apa yang hilang.** Halaman bernama "Pasca-seleksi dan OJT" tapi tidak memuat satu pun hasil evaluasi: tidak ada nilai pembidangan, tidak ada nilai ujian OJT, tidak ada rekomendasi unit, tidak ada yang tidak lulus OJT. Menurut dokumen domain, justru menghubungkan karakteristik kandidat saat direkrut dengan hasil setelah masuk PLN adalah nilai terbesar dari analitik ini. Itu kosong sepenuhnya.

---

### 4.6 "Penempatan"

**Hierarki visual.** Terbalik. Elemen paling besar, paling berwarna, paling menarik mata (treemap) adalah yang paling tidak bisa dibaca; elemen paling berguna (`"Kuota dan realisasi per tahun"`) ada di paling bawah dan monokrom.

**Chart, satu per satu.**

1. `"Penempatan per unit induk dan bidang"` — treemap bersarang, ~40 unit × beberapa bidang. **Masalah terbesar: warna kategorikal yang berputar tanpa membawa informasi.** Oranye, hijau, ungu, pink, coklat, teal, kuning tua, magenta — semuanya hanya menandai unit yang namanya sudah tercetak di kotaknya. Ini definisi rainbow palette. Masalah kedua: sekitar 25 dari 40 blok terlalu kecil untuk dibaca; teks di dalamnya tercetak 5–6px dan terpotong. Masalah ketiga: manusia tidak bisa membandingkan luas kotak, apalagi kotak dengan rasio aspek berbeda. Fungsi zoom (klik untuk memperbesar) ada dan disebut di popover, tapi tidak ada afordansi visual apa pun di chart yang memberi tahu bahwa ia bisa diklik.
2. `"Porsi bidang per tahun"` — heatmap 10 bidang × 7 tahun dengan angka. Bentuknya bisa diterima untuk komposisi, tapi: angka tanpa `%` padahal tiap kolom berjumlah 100; sel kosong ambigu (nol atau tidak ada data?); urutan baris tampaknya mengikuti 2019 saja, sehingga tren tidak terbaca. Untuk pertanyaan sebenarnya — "bidang apa yang porsinya naik/turun?" — slope chart atau small multiple garis jauh lebih baik.
3. `"PLN induk dan subholding per tahun"` — batang bertumpuk 100%. Bentuk tepat untuk komposisi antar waktu. Legenda `Induk / ICON / IP / NP / ND / ES / Lainnya` memakai singkatan yang hanya dijelaskan di popover — enam singkatan yang wajib dicari artinya. Tulis nama panjangnya di legenda, atau minimal di hover.
4. `"Kuota dan realisasi per tahun"` — batang bullet abu/biru dengan capaian tercetak. **Bentuk tepat, isi paling penting, posisi paling buruk.** Sama seperti chart 1 di halaman Perencanaan, tidak ada legenda di layar untuk abu vs biru. Angka 7% dan 38% untuk tahun RBB membutuhkan penjelasan langsung di chart (anotasi), bukan hanya di popover, karena angka itu terlihat seperti kegagalan katastrofik.

**Koherensi.** Sudah disebut di T2: `"Kuota terpenuhi 100%"` (KPI) vs 7%/38%/81% (chart). Harus didamaikan atau KPI-nya diberi kualifikasi eksplisit.

---

### 4.7 "Kualitas data"

Halaman terbaik dari sisi maksud, terlemah dari sisi eksekusi bentuk.

1. `"Perjalanan data antar sistem"` — lima kartu dengan panah. Ini bukan chart, dan itu keputusan yang benar: diagram alur adalah bentuk yang tepat. Tapi eksekusinya sembrono: teks terpotong di tengah URL (`rekrutmen.pln.co.i` / `d, 370.102 baris`), dan kelima kartu berukuran sama sehingga "Pusdiklat, titik rawan integrasi" — satu-satunya kartu yang membawa peringatan — tidak menonjol sama sekali.
2. `"Kelengkapan kolom per kualitas kohort"` — heatmap 3 baris × 2 kolom. **Heatmap untuk enam angka.** Bentuk berlebihan; tabel kecil atau batang berkelompok sudah cukup dan lebih terbaca. Juga tidak dijelaskan di layar mengapa hanya dua kolom (`Blok fisik`, `Domisili`) dari sekian banyak kolom yang ditampilkan.
3. `"Laporan realisasi pegawai per bulan"` — batang dengan warna kondisional (biru = 48 unit melapor, oranye = sebagian). Bentuk tepat, warna membawa makna. Celah bulan tanpa batang terlihat jelas. Bagus.
4. `"Dua angka rencana per tahun"` — dumbbell target-gelombang vs pagu. Bentuk tepat untuk "dua angka yang tidak pernah didamaikan". Tapi 2020, 2021, dan 2024 hanya punya satu titik tanpa keterangan apa pun di layar — pembaca tidak tahu angka mana yang hilang.
5. `"Jejak pelamar RBB di sistem PLN"` — tiga batang, ketiganya `1,96%`. **Hapus.** Nol variasi. Sumbu-x membentang ke 2,4 dengan gridline tiap 0,2 untuk menampung tiga nilai identik. Ini satu kalimat: "Hanya 1,96% pelamar FHCI jalur RBB tercatat di sistem PLN, sama di ketiga tahun."
6. `"Kolom dimodelkan dan anomali yang diketahui"` — tabel. Isinya berharga. **Tapi kolom `Rujukan` membocorkan artefak pengembang ke pengguna akhir:** `F-017`, `F-028`, `M13`, `M58`, `M49`, `ISSUES_MASTER_DATA.md`, `ISSUES_SEBARAN.md`. Popover-nya bahkan berbunyi `"berkas ISSUES ada di folder mockdb"` — pengguna manajemen tidak punya folder mockdb. Kolom terakhir juga terpotong di tepi tabel (`ditampilkan sebagai k…`).

---

### 4.8 "RecruitMan"

Sudah dirinci di T5. Tambahan dari sisi tata letak: rel kiri (tombol "Percakapan baru", pemilih model, blok error, dan daftar Riwayat) memakan sekitar sepertiga lebar layar dan menjulur jauh ke bawah, sementara area percakapan — alasan halaman ini ada — kosong. Prioritas ruang terbalik. Judul kartu `"Tanyakan apa saja tentang data rekrutmen PLN"` adalah janji berlebihan yang langsung dibantah oleh pesan `Gagal terhubung` di sebelahnya.

Empat contoh pertanyaan yang disediakan (`"Tahap mana yang paling banyak menggugurkan kandidat?"`, `"Sebutkan 5 unit induk dengan gap FTK terbesar"`, `"Berapa persen jalur RBB yang berjejak di sistem PLN?"`, `"Berapa orang yang sedang OJT sekarang?"`) justru bagus dan spesifik pada domain — bukan contoh generik. Sayangnya tiga dari empat jawabannya sudah ada di dashboard.

---

## 5. Katalog chart bermasalah

| Judul chart (verbatim) | Bentuk sekarang | Masalah | Bentuk yang diusulkan | Alasan |
|---|---|---|---|---|
| `"Penempatan per unit induk dan bidang"` | Treemap bersarang, ~40 warna | Warna kategorikal berputar tanpa makna (rainbow); 25+ blok tidak terbaca; luas tidak bisa dibandingkan mata; afordansi klik tidak terlihat | Batang horizontal terurut untuk 15 unit teratas + batang bertumpuk bidang; sisanya "Lainnya" | Peringkat dan besaran dibaca dari panjang, bukan luas; satu warna cukup |
| `"Rantai tahap setelah diterima"` | Batang bertumpuk 7 tahap | 5 batang identik, 2 batang identik; penurunan yang digambar diakui palsu oleh popover-nya sendiri | Hapus; ganti kalimat + satu chart "posisi kohort per tahap" per tahun program | Chart yang tidak punya variasi adalah tinta tanpa informasi |
| `"Konversi tahap seleksi"` | Corong (funnel) | Duplikat Sankey di halaman Corong seleksi dengan angka identik; sisi miring corong menciptakan luas tanpa makna | Batang horizontal terurut dengan % konversi tercetak, atau hapus dan tautkan ke Sankey | Menyatakan satu temuan dua kali dalam dua bentuk melemahkan keduanya |
| `"Sebaran skor tes online"` | Dua histogram | Distribusi rata sempurna karena skor dimodelkan acak; bentuk histogram khusus untuk membaca distribusi | Hapus | Menyajikan sebaran fiktif dalam bentuk pembaca-sebaran mengundang kesimpulan palsu |
| `"Jejak pelamar RBB di sistem PLN"` | Batang horizontal, 3 baris | Ketiga nilai persis 1,96%; sumbu membentang ke 2,4 | Satu kalimat teks / satu kartu KPI | Nol varians tidak butuh sumbu |
| `"Selisih FTK dan realisasi per unit"` | Batang divergen, 47 baris di kolom setengah | Baris ~9px, nama unit hilang; sumbu `Pegawai` memakai negatif untuk "kelebihan" tanpa penjelasan | Lebar penuh; sumbu berlabel `← Lebih \| Kurang →`; batasi ke 20 teratas + "sisanya" | Chart paling berguna di halaman pantas ruang penuh dan sumbu yang tidak menipu |
| `"Proyeksi kekosongan per sebab"` | Area bertumpuk | Pensiun ~95%, tiga kategori lain tidak terlihat; area menyiratkan kontinuitas pada data tahunan | Garis/batang total + small multiple 4 panel (sumbu-y sendiri) | Kategori kecil jadi terbaca; diskrit digambar diskrit |
| `"Peluang diterima menurut IPK"` | Garis langkah dengan area terisi | Area di bawah sebuah *tingkat* tidak bermakna; sumbu-x dan sumbu-y sama-sama berakhir di 4; lompatan di IPK 3,00 tidak dianotasi | Garis langkah tanpa isian + anotasi lompatan + batang volume pendaftar di belakang | Isian menyiratkan akumulasi; anotasi memindahkan kerja baca dari pembaca ke desain |
| `"Volume dan peluang per rumpun jurusan"` | Scatter, ~20 titik | Hanya 4 titik berlabel; 16 anonim; garis rata-rata tanpa nilai | Batang berpasangan terurut atau tabel dengan sparkline | 20 kategori bernama tidak cocok untuk scatter tanpa label |
| `"Pendaftar dan peluang per gelombang"` | Scatter log | Redundan dengan dua chart lain di halaman yang sama; 14 dari 17 titik anonim; skala log tidak ditandai | Hapus, atau jadikan tabel gelombang di Mode analis | Halaman Ringkasan tidak boleh menyatakan hal yang sama tiga kali |
| `"Status diterima per tahun"` | Batang bertumpuk | Praktis tidak bertumpuk (semua biru kecuali 2025 semua kuning) | Kalimat + penanda pada `"Tonggak waktu per kohort"` | Satu fakta biner tidak butuh chart |
| `"Volume dan tingkat lulus per kota tes"` | Peta gelembung | Rentang warna terlalu sempit untuk dibedakan; label kota tumpang tindih; >50% gelembung tanpa nama; salah halaman | Batang terurut per kota (volume) dengan tingkat lulus sebagai titik kedua | Temuannya peringkat, bukan geografi |
| `"Kelengkapan kolom per kualitas kohort"` | Heatmap 3×2 | Heatmap untuk enam angka; pilihan dua kolom tidak dijelaskan | Tabel kecil atau batang berkelompok | Bentuk harus sepadan dengan ukuran data |
| `"Tingkat lulus per vendor tes"` | Dua dot plot | Tidak ada judul sumbu; nilai tidak tercetak; nama vendor terpotong; 60% lebar kosong | Lollipop terurut dengan nilai tercetak, sumbu per panel | Menghilangkan kebutuhan hover |
| `"Pendaftaran dan peluang per tahun"` (panel garis) | Garis multi-seri | Ketiga garis datar sempurna; segmen terputus terbaca sebagai data hilang | Batang kecil per kelompok, atau anotasi teks | Garis menjanjikan tren yang tidak ada |
| `"Porsi bidang per tahun"` | Heatmap angka 10×7 | Tanpa `%`; sel kosong ambigu; tren tidak terbaca | Slope chart atau small multiple garis | Pertanyaannya "apa yang berubah", bukan "berapa nilainya" |

---

## 6. Interaksi dan filter

**Yang berfungsi baik:**
- Tiga filter (`Tahun program`, `Jenis program`, `Jenjang`) konsisten di semua halaman, posisinya sama, dan **bertahan saat berpindah halaman** — diverifikasi: memilih `2023` di Ringkasan, lalu pindah ke Corong seleksi, KPI tetap 38.538. Ini sering gagal di aplikasi Streamlit dan di sini benar.
- Semua chart merespons filter secara koheren; tidak ditemukan chart yang mengabaikan filter (kecuali seluruh halaman Perencanaan, yang diumumkan).
- Tooltip KPI luar biasa bagus dan spesifik: `"Masih menjalani on the job training per 15 September 2026. Selisih diterima dan SK terbit adalah kelompok ini, bukan data hilang."` — kalimat kedua itu mendahului pertanyaan pembaca. Ini standar yang harus ditiru di seluruh aplikasi.
- Popover `help` per chart berisi mekanisme, bukan basa-basi. Sebagian bahkan memuat peringatan metodologis (`"Angka ini menggambarkan kegigihan, bukan sebab-akibat"`). Ini kualitas tinggi.

**Yang bermasalah:**

1. **Tidak ada reset filter.** Untuk kembali ke "semua tahun" pengguna harus menebak bahwa mengklik ulang pil yang aktif akan membatalkannya. Tambahkan tombol "Semua" atau "Atur ulang".
2. **Status terpilih terlalu lemah.** Pil `2023` yang aktif hanya diberi garis tepi biru tipis; pada pandangan sekilas tidak terbaca bahwa dashboard sedang difilter. Isi latar penuh akan lebih aman, karena salah baca di sini berarti salah angka.
3. **Filter mati tapi tetap bisa diklik di halaman "Perencanaan kebutuhan".** Pengguna bisa mengklik dan tidak terjadi apa-apa. Harus dinonaktifkan secara visual.
4. **Terlalu banyak informasi penting bersembunyi di dalam popover.** Ini pola yang berulang dan merugikan: legenda warna `"Alur pendaftar per tahap"` (biru/merah/kuning), legenda `"Usulan dan pagu per tahun"` (abu/biru), legenda `"Kuota dan realisasi per tahun"` (abu/biru), definisi `Terbuka/Afirmasi/RBB`, dan kepanjangan `ICON/IP/NP/ND/ES` — semuanya hanya ada di balik klik. Legenda bukan bantuan; legenda adalah bagian chart.
5. **Chart tidak menyesuaikan diri saat difilter ke satu tahun.** `"Tingkat lulus per tahap dan tahun"` dan `"Ketidakhadiran tes per tahun"` menjadi satu baris dan kehilangan maksudnya. Seharusnya berganti bentuk, atau memberi konteks pembanding (tahun terpilih vs rata-rata seluruh tahun).
6. **Treemap bisa di-zoom tapi tidak ada yang memberi tahu.** Satu-satunya petunjuk `"Klik satu unit untuk memperbesar"` ada di dalam popover.
7. **Tombol mengambang `RecruitMan`** menutupi sudut kanan-bawah konten di setiap halaman, di desktop maupun ponsel. Di 390px ia menimpa legenda chart.
8. **`Mode analis`** berfungsi (menampilkan tabel rinci + `Unduh CSV` di bawah tiap halaman), tapi togglenya ada di kiri-atas sidebar sementara efeknya muncul ratusan piksel di bawah lipatan — pengguna yang mengaktifkannya tidak melihat apa pun berubah. Tooltipnya (`"Menampilkan tabel rinci dan tombol unduh CSV di bawah tiap halaman."`) jelas, tapi harus dibuka dulu. Tabelnya sendiri menampilkan nama kolom mentah (`nama_gelombang`, `jenis_program`, `tgl_buka`) dan timestamp `2019-07-15 00:00:00` — bahasa basis data, bukan bahasa pengguna.

---

## 7. Bahasa dan "AI slop"

Kabar baiknya: **dashboard ini relatif bersih dari AI slop.** Tidak ada "Comprehensive Overview", tidak ada "Key Insights at a Glance", tidak ada paragraf pembuka yang merestate judul, tidak ada emoji dekoratif, tidak ada kartu berisi kalimat motivasional. Judul-judul chart sebagian besar adalah frasa benda yang deskriptif dan spesifik pada domain. Itu prestasi.

Yang tersisa:

| Kutipan persis | Di mana | Masalah | Usulan pengganti |
|---|---|---|---|
| `"Tanyakan apa saja tentang data rekrutmen PLN"` | RecruitMan | Janji berlebihan, dan dibantah oleh `Gagal terhubung` tepat di sebelahnya | `"Tanya angka rekrutmen 2019–2025"` — atau, saat layanan mati, ganti seluruh blok dengan pesan status |
| `"Atau klik salah satu contoh di bawah untuk mengisi kotak tanya."` | RecruitMan | Kalimat instruksi yang menjelaskan hal yang sudah jelas dari bentuk tombol | Hapus |
| `"Rantai tahap setelah diterima"` | Pasca-seleksi | "Rantai" adalah metafora dekoratif untuk sesuatu yang bukan rantai (tidak ada yang putus) | `"Posisi kohort pada tiap tahap"` — atau hapus chartnya |
| `"Jejak pelamar RBB di sistem PLN"` | Kualitas data | Judul puitis untuk satu angka tunggal | `"1,96% pelamar RBB tercatat di sistem PLN"` sebagai kartu |
| `"Perjalanan data antar sistem"` | Kualitas data | "Perjalanan" adalah bahasa presentasi; yang digambar adalah alur integrasi | `"Alur data antar sistem"` |
| `"Peluang menurut lama mencoba"` | Kandidat | `"lama mencoba"` terbaca sebagai durasi, padahal maksudnya jumlah tahun program yang diikuti | `"Peluang diterima menurut jumlah percobaan"` |
| `"Hari sejak melamar"` | Corong seleksi | Judul tidak menyatakan bahwa isinya sebaran, bukan satu angka | `"Sebaran hari dari melamar ke tiap tahap"` |
| `"Dua angka rencana per tahun"` | Kualitas data | Judul yang malu-malu; temuannya justru bahwa keduanya tidak pernah cocok | `"Target gelombang vs pagu disetujui: tidak pernah didamaikan"` |
| `F-017`, `F-028`, `M13`, `M49`, `M58`, `ISSUES_MASTER_DATA.md`, `ISSUES_SEBARAN.md` | Kualitas data, kolom `Rujukan` | Artefak pengembang bocor ke antarmuka pengguna manajemen | Hapus kolom, atau ganti dengan sumber yang bisa diakses pengguna |
| `"Daftar rujukan untuk analis. Kode F merujuk ke temuan riset lapangan; berkas ISSUES ada di folder mockdb."` | Popover Kualitas data | Menyuruh pengguna membuka folder yang tidak mereka miliki | Hapus kalimat kedua |
| `Error code: 401 - {'error': {'message': 'Authentication Error, Invalid proxy server token passed. Received API Key = sk-...FoqA, Key Hash (Token) =5ec` | RecruitMan | Stack trace mentah + potongan kredensial di layar pengguna | `"Asisten sedang tidak tersedia. Hubungi tim HC Analytics."` — dan catat error ke log, bukan ke layar |
| `Qwen3.5 35B A3...` (pemilih model) + `"Percakapan baru"` + daftar `Riwayat` berisi `"Hewan apa yang suka..."` | RecruitMan | Kontrol pengembang dan sampah uji di produk produksi | Sembunyikan pemilih model; bersihkan riwayat uji |
| `nama_gelombang`, `jenis_program`, `tgl_buka`, `tgl_tutup`, `2019-07-15 00:00:00` | Tabel Mode analis | Bahasa basis data di antarmuka | `Nama gelombang`, `Jenis`, `Buka`, `Tutup`, `15 Jul 2019` |

**Catatan tentang elemen dekoratif.** Hanya ada dua: palet pelangi treemap (§5) dan chevron `expand_more` yang menempel di setiap ikon `help` — dua ikon berdampingan untuk satu fungsi. Ikon `?` sudah cukup; chevron-nya menambah dua elemen visual per chart × 30+ chart tanpa tugas informasi.

**Catatan tentang grid kartu seragam.** Ini bentuk AI slop yang paling halus dan paling merusak di sini: setiap chart dibungkus kartu putih berbingkai dengan padding identik, sehingga chart yang menjawab pertanyaan strategis (`"Kuota dan realisasi per tahun"`) tampak setara dengan chart yang tidak mengatakan apa-apa (`"Jejak pelamar RBB di sistem PLN"`). Keseragaman ini meratakan hierarki. Biarkan chart utama tiap halaman lebih besar, tanpa bingkai, di posisi pertama; sisanya lebih kecil.

---

## 8. Responsif dan tema

**Mode gelap.** Berfungsi dengan benar melalui `prefers-color-scheme`. Latar, kartu, teks, dan sumbu chart semuanya beradaptasi — bukan hal sepele dengan chart Vega. Dua catatan kecil: (a) warna pucat di `"Kalender gelombang rekrutmen"` (tint Terbuka/Afirmasi/RBB) dirancang untuk latar terang dan tampak luntur di atas latar gelap; (b) teks putih `213.648 / 100%` di dalam batang biru muda pada `"Konversi tahap seleksi"` kontrasnya menurun. Tidak ditemukan kontrol tema di dalam aplikasi — hanya mengikuti sistem.

**Lebar 390px (ponsel).** Tata letak bertahan: kolom menumpuk, kartu KPI menjadi dua per baris, sidebar menjadi tombol. Tapi beberapa chart kehilangan fungsinya:
- `"Kalender gelombang rekrutmen"`: batang Gantt menyusut jadi serpihan beberapa piksel; sumbu waktu tinggal empat label; label persen terpotong di tepi kanan (`18,8'`).
- Tombol mengambang `RecruitMan` menutupi sudut kanan-bawah; pada beberapa posisi gulir ia menimpa judul dan legenda chart berikutnya.
- Heatmap (`"Usulan kebutuhan per unit dan sub-bidang"`, `"Porsi bidang per tahun"`) menjadi tidak terbaca sepenuhnya di lebar ini.
- Ukuran font di dalam chart tidak diperbesar untuk layar kecil, sehingga label sumbu ~8px.

Penilaian: aplikasi ini **layak dibaca di ponsel untuk baris KPI dan chart batang sederhana, tidak layak untuk chart padat**. Kalau ponsel adalah kanal nyata bagi manajemen, chart padat sebaiknya diganti otomatis dengan ringkasan tabel di lebar sempit.

---

## 9. Usulan

### Prioritas tinggi

1. **Perbaiki atau matikan halaman "RecruitMan".** Hentikan tampilnya stack trace dan potongan API key. Sembunyikan pemilih model. Bersihkan riwayat percakapan uji. Kalau layanan tidak tersedia, tampilkan satu pesan status, bukan error mentah.
2. **Angkat `"Kuota dan realisasi per tahun"` ke halaman "Ringkasan"** sebagai chart pertama, dan tambahkan kartu KPI `Pemenuhan kebutuhan` di baris KPI Ringkasan. Ini pertanyaan utama BPO dan sekarang tersembunyi di posisi paling belakang.
3. **Damaikan `"Kuota terpenuhi 100%"` dengan chart di bawahnya.** Salah satu dari keduanya salah, atau keduanya mengukur hal berbeda dan harus diberi nama berbeda.
4. **Pindahkan legenda keluar dari popover ke dalam chart** untuk lima chart yang saat ini tidak punya legenda di layar (Sankey, dua chart bullet abu/biru, singkatan subholding, definisi kelompok rekrutmen).
5. **Hapus tiga chart nol-informasi:** `"Rantai tahap setelah diterima"`, `"Jejak pelamar RBB di sistem PLN"`, `"Sebaran skor tes online"`. Ruang yang dibebaskan dipakai untuk usulan di bawah.
6. **Ganti treemap `"Penempatan per unit induk dan bidang"`** dengan batang terurut. Satu warna.
7. **Bersihkan kolom `Rujukan`** dari kode internal pengembang.

### Prioritas sedang

8. **Tukar urutan "Kandidat" dan "Corong seleksi"** agar mengikuti kronologi proses (mendaftar dulu, baru diseleksi).
9. **Pindahkan `"Volume dan tingkat lulus per kota tes"` ke "Corong seleksi"**, berdampingan dengan `"Tingkat lulus per vendor tes"`; pindahkan `"Akun tanpa lamaran"` dan `"Profil lengkap dan aktif"` ke "Kualitas data".
10. **Lebarkan `"Selisih FTK dan realisasi per unit"` ke lebar penuh** dan ganti label sumbu dari angka negatif menjadi `← Lebih | Kurang →`.
11. **Isi halaman "Pasca-seleksi dan OJT" dengan chart hasil, bukan chart status.** Yang hilang dan bernilai tinggi: sebaran nilai ujian OJT, tingkat kelulusan OJT per UPDL, rekomendasi unit, dan — yang paling berharga — **hubungan antara profil kandidat saat direkrut (IPK, jenjang, rumpun jurusan, skor seleksi) dengan hasil OJT**. Itu satu-satunya cara dashboard ini bisa menjawab "apakah kriteria seleksi kita memprediksi kinerja".
12. **Buat filter tahun punya tombol "Semua"** dan perkuat status terpilih.
13. **Tambahkan chart `"Kebutuhan vs pemenuhan internal vs rekrutmen eksternal"` di halaman "Perencanaan kebutuhan".** Menurut proses PLN, tidak semua kekosongan dipenuhi lewat rekrutmen — sebagian lewat APS, rotasi, mutasi. Dashboard sekarang melompat langsung dari proyeksi kekosongan ke usulan pagu, tanpa menunjukkan pemilahan itu sama sekali. Ini konsep yang hilang, bukan sekadar chart yang hilang.
14. **Anotasi lompatan IPK 3,00** di `"Peluang diterima menurut IPK"`, dan hilangkan area terisinya.
15. **Buat `"Tidak hadir tes online 42,7%"` menjadi temuan utama halaman "Corong seleksi"**, bukan kartu keempat. Tambahkan chart pendamping: tidak hadir per gelombang dan per tahap, agar terlihat di mana kebocorannya.

### Prioritas rendah

16. Hapus chevron `expand_more` dari ikon `help`.
17. Perbaiki teks terpotong: `"Manajemen Konstruksi dan…"`, `"VEND06 Balikpa…"`, `rekrutmen.pln.co.i / d`, `"ditampilkan sebagai k…"`.
18. Beri label nilai pada garis rata-rata di `"Volume dan peluang per rumpun jurusan"` dan beri nama semua titiknya, atau ubah bentuknya.
19. Label bucket umur `≤20` dan `≥34` di piramida.
20. Terjemahkan nama kolom dan format tanggal di tabel `Mode analis`.
21. Pindahkan toggle `Mode analis` ke dekat lokasi efeknya, atau tampilkan konfirmasi singkat saat diaktifkan.
22. Pindahkan tombol mengambang `RecruitMan` agar tidak menutupi konten di 390px.

### Insight yang bisa disajikan tapi belum ada

- **Waktu-ke-penempatan dibandingkan target.** Data `"Tonggak waktu per kohort"` sudah ada; yang belum ada adalah garis target/SLA untuk membandingkannya.
- **Biaya per kandidat diterima** (kalau data vendor memungkinkan) — pertanyaan wajar manajemen yang tidak muncul di mana pun.
- **Unit mana yang kebutuhannya paling sering tidak terpenuhi** — menyilangkan `"Selisih FTK"` dengan `"Kuota dan realisasi"`. Sekarang keduanya ada di halaman berbeda dan tidak pernah bertemu.
- **Kebocoran terbesar dalam corong dinyatakan sebagai pernyataan, bukan sebagai bentuk.** Dashboard punya semua bahannya (`Adaptif` menggugurkan 74.935 orang karena tidak hadir — angka terbesar di seluruh Sankey) tapi tidak pernah menyatakannya.

---

## 10. Apa yang sudah bagus dan jangan diubah

1. **Teks popover `help`.** Ini aset terbesar dashboard ini. Ia menjelaskan mekanisme (`"Jalur RBB masuk langsung di Akademik & Inggris"`), mengakui keterbatasan (`"Skor ini dimodelkan"`), dan mencegah salah tafsir (`"Itu bukan kegagalan target"`). Jangan diringkas, jangan digenerikkan. Yang perlu berubah hanyalah: legenda harus keluar dari sini ke layar.
2. **Tooltip kartu KPI.** Khususnya `"Selisih diterima dan SK terbit adalah kelompok ini, bukan data hilang."` — kalimat yang mendahului pertanyaan pembaca. Standar ini harus jadi patokan.
3. **`"Alur pendaftar per tahap"` (Sankey).** Bentuk yang tepat, dieksekusi dengan baik, dan memisahkan tiga takdir kandidat yang tidak bisa ditunjukkan corong.
4. **`"Kalender gelombang rekrutmen"`.** Menjawab empat pertanyaan sekaligus dalam satu bentuk, dan menangkap karakter paling khas rekrutmen PLN: bergelombang, bukan kontinu.
5. **`"Alasan gugur administrasi"`.** Batang terurut, nilai tercetak, satu warna. Tidak ada yang bisa diperbaiki.
6. **Keberadaan halaman "Kualitas data".** Sebagian besar dashboard korporat menyembunyikan keterbatasan datanya. Yang ini mendedikasikan satu halaman untuknya dan menyebut titik rawan integrasi dengan nama. Pertahankan, naikkan posisinya.
7. **`1 : 28` sebagai format peluang diterima.** Lebih mudah dicerna daripada persentase. Pilihan cerdas.
8. **Filter global yang bertahan antar halaman.** Konsisten, koheren, tidak ada chart yang menyimpang.
9. **Kejujuran banner "Seluruh halaman ini dimodelkan"** di halaman Perencanaan. Tidak nyaman, tapi benar. Yang perlu diperbaiki hanya filter mati yang dibiarkan bisa diklik.
10. **Disiplin palet dan tipografi secara umum.** Biru sebagai warna utama, oranye/hijau sebagai aksen bermakna, tidak ada gradien, tidak ada bayangan berlebihan, angka berformat Indonesia (`218.928`, `84,8%`). Satu-satunya pelanggaran adalah treemap.

---

## Yang tidak bisa saya pahami dari antarmuka saja

Dicatat sebagai kegagalan antarmuka menjelaskan dirinya, bukan sebagai pertanyaan:

- Apa beda `Pendaftaran` (218.928) dan `Pelamar unik` (172.389) dengan `Profil lengkap dan aktif` (340.561) — tiga populasi berbeda di dua halaman, tidak pernah dihubungkan.
- Mengapa `"Kuota terpenuhi 100%"` sementara chart di bawahnya menunjukkan 7% dan 38%.
- Apa arti sel kosong di heatmap: nol, tidak berlaku, atau data hilang.
- Mengapa `"Kelengkapan kolom per kualitas kohort"` hanya menampilkan `Blok fisik` dan `Domisili`.
- Apa dasar pengelompokan kohort menjadi `Rendah / Sedang / Baik`.
- Apa arti tanda negatif di sumbu `"Selisih FTK dan realisasi per unit"` sebelum saya membuka popover.
- Mengapa `2019` dan `2021` hanya punya satu titik di `"Ketidakhadiran tes per tahun"`, dan `2020/2021/2024` hanya satu titik di `"Dua angka rencana per tahun"`.
- Apa yang dilakukan `Mode analis` sebelum saya mengaktifkannya dan menggulir ke dasar halaman.
- Bahwa treemap bisa diklik.
