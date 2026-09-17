# Design System — Dashboard Rekrutmen PLN v2

Bukan dokumen selera. Setiap warna di sini **sudah dihitung** dengan validator
(`scripts/validate_palette.js` dari skill dataviz) terhadap lima cek: band kecerahan,
lantai chroma, keterpisahan buta warna (protan/deutan), lantai penglihatan normal, dan
kontras terhadap permukaan. Hasil validasi dicantumkan apa adanya.

---

## 1. Temuan validasi yang mengubah keputusan

Palet v1 dipakai apa adanya sebagai titik awal, lalu diuji. Dua warna brand **gagal**
sebagai warna data:

| Warna | Peran di v1 | Hasil uji | Keputusan |
|---|---|---|---|
| `#F9C642` PLN kuning | dipakai sebagai warna seri | **FAIL** band kecerahan (L 0,85 vs batas 0,77); kontras 1,59:1 | **Hanya warna UI** — garis aksen kartu insight, tidak pernah jadi warna seri |
| `#103A5D` PLN navy | dipakai sebagai warna seri | **FAIL** chroma 0,077 (di bawah lantai 0,10 → terbaca abu); L 0,339 di luar band | **Hanya warna UI** — judul, gradien hero, teks |
| `#0077C8` PLN biru | warna utama | **PASS** semua cek | **Slot seri 1** ✅ |

Ini alasan konkret kenapa palet chart v1 ditata ulang: dua dari tiga warna brand memang
tidak bisa jadi warna data, dan itu terukur — bukan pendapat.

---

## 2. Palet kategori (identitas seri)

Urutan slot **tetap, tidak pernah diputar-ulang**. Seri ke-7 tidak mendapat warna baru —
dilipat jadi "Lainnya" atau dipecah jadi small multiples.

| Slot | Hue | Terang | Gelap | Contoh pemakaian |
|---|---|---|---|---|
| 1 | PLN biru | `#0077C8` | `#2E9BE0` | seri utama, jalur mandiri |
| 2 | oranye | `#eb6834` | `#d95926` | pembanding, jalur RBB |
| 3 | aqua | `#1baf7a` | `#199e70` | seri ketiga |
| 4 | kuning | `#eda100` | `#c98500` | seri keempat |
| 5 | magenta | `#e87ba4` | `#d55181` | seri kelima |
| 6 | ungu | `#4a3aa7` | `#9085e9` | seri keenam |

**Hasil validator:**

```
Terang (permukaan #FFFFFF, 6 slot, pasangan bersebelahan)
  [PASS] Band kecerahan      6/6 dalam L 0,43–0,77
  [PASS] Lantai chroma       6/6 >= 0,10
  [PASS] Keterpisahan CVD    terburuk #eda100↔#1baf7a ΔE 9,1 (protan)
  [PASS] Penglihatan normal  terburuk #e87ba4↔#eda100 ΔE 19,6
  [WARN] Kontras permukaan   di bawah 3:1 — #1baf7a 2,82 · #eda100 2,17 · #e87ba4 2,69

Gelap (permukaan #132C42, 6 slot, pasangan bersebelahan)
  [PASS] semua lima cek — kontras 6/6 >= 3:1
```

⚠️ **Aturan kelegaan (relief) wajib di mode terang.** Tiga slot (aqua, kuning, magenta)
di bawah 3:1 terhadap latar putih. Konsekuensi mengikat: chart yang memakai ketiganya
**wajib** punya label langsung yang terlihat atau tampilan tabel. Ini bukan saran.

### Batas seri untuk scatter / peta / small multiples

Bentuk chart yang membandingkan **semua pasangan sekaligus** (bukan hanya yang
bersebelahan) hanya boleh memakai **3 slot pertama**:

```
Semua-pasangan, 3 slot
  Terang: CVD ΔE 9,2 · normal 23,0 — PASS
  Gelap:  CVD ΔE 9,4 · normal 17,5 — PASS
```

Lebih dari tiga kategori di scatter/peta → lipat jadi "Lainnya" atau pecah jadi facet.

---

## 3. Ramp sekuensial (besaran)

Satu hue, terang→gelap. Dipakai untuk heatmap unit × sub-bidang dan choropleth peta.

| step | 100 | 150 | 200 | 250 | 300 | 350 | 400 | 450 | 500 | 550 | 600 | 650 | 700 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hex | `#cde2fb` | `#b7d3f6` | `#9ec5f4` | `#86b6ef` | `#6da7ec` | `#5598e7` | `#3987e5` | `#2a78d6` | `#256abf` | `#1c5cab` | `#184f95` | `#104281` | `#0d366b` |

### Ramp ordinal (kategori berurutan & diskrit)

Untuk skala berjenjang seperti kualitas kohort. **Maksimal 4 langkah** — di luar itu jarak
kecerahan antar langkah turun di bawah 0,06 dan langkahnya tidak lagi terbaca (sudah diuji:
6 langkah selalu FAIL).

| Jumlah | Terang | Gelap |
|---|---|---|
| 3 langkah | `#86b6ef` `#2a78d6` `#104281` | `#cde2fb` `#5598e7` `#1c5cab` |
| 4 langkah | `#86b6ef` `#3987e5` `#256abf` `#104281` | `#cde2fb` `#86b6ef` `#3987e5` `#1c5cab` |

Keempatnya PASS penuh (monoton, ΔL ≥ 0,06, ujung terang ≥ 2:1, satu hue).

> **Funnel seleksi TIDAK memakai ramp ordinal.** Panjang batang sudah mengkodekan besaran;
> memberi warna berbeda per tahap hanya dekorasi. Funnel memakai **satu** hue biru PLN,
> dengan segmen gugur berwarna netral abu.

---

## 4. Palet status (dipesan — tidak pernah jadi warna seri)

| Peran | Hex | Makna di dashboard ini |
|---|---|---|
| baik | `#0ca30c` | lulus, terpenuhi, SELESAI |
| peringatan | `#fab219` | perlu perhatian, BERJALAN |
| serius | `#ec835a` | di bawah target |
| kritis | `#d03b3b` | gagal, tidak terpenuhi |

Selalu berpasangan dengan **ikon + label** — warna tidak pernah menanggung makna sendirian.
Di mode terang, `peringatan` dan `serius` memang di bawah 3:1; ikon+label itulah
mitigasinya.

---

## 5. Warna UI (bukan warna data)

| Token | Terang | Gelap | Guna |
|---|---|---|---|
| `--surface-page` | `#F7F9FC` | `#0E1B29` | latar halaman |
| `--surface-card` | `#FFFFFF` | `#132C42` | kartu, permukaan chart |
| `--border` | `#E7ECF2` | `#1E3A52` | garis kartu |
| `--text-primary` | `#103A5D` | `#EAF4FF` | judul |
| `--text-secondary` | `#4A5A6B` | `#A8BDD0` | label, sumbu |
| `--text-muted` | `#8093A5` | `#6E8398` | catatan kaki |
| `--brand-navy` | `#103A5D` | — | gradien hero |
| `--brand-yellow` | `#F9C642` | — | garis aksen kartu insight |

Aturan tak bisa ditawar: **teks memakai token teks, tidak pernah warna seri.** Angka,
label, dan legenda tetap berwarna tinta; identitas dibawa oleh penanda warna kecil di
sebelahnya.

---

## 6. Tipografi

| Peran | Ukuran | Bobot |
|---|---|---|
| Angka KPI | 34px | 700 |
| Judul halaman | 26px | 700 |
| Judul seksi | 18px | 600 |
| Judul chart | 15px | 600 |
| Teks isi | 14px | 400 |
| Label sumbu / catatan | 12px | 400 |

Angka besar memakai **tabular numerals** supaya digit tidak bergoyang saat filter berubah.
Format Indonesia: pemisah ribuan titik (`218.928`), desimal koma (`28,4`).

---

## 7. Komponen

**Prinsip Streamlit 1.57+: pakai native dulu, kustom hanya kalau tidak ada padanannya.**
`st.metric` sejak 1.57 sudah mendukung `border`, sparkline (`chart_data`), dan tooltip
(`help=`) — kartu KPI **tidak dibuat manual**. Ini mengubah §7.1–7.3 versi sebelumnya, yang
merancang kartu KPI kustom dengan badge di label; itu sendiri adalah salah satu sumber
"terlalu AI" yang diralat §11.

### 7.1 Baris KPI (native)
```python
st.metric("Pendaftaran", "218.928", help="Termasuk 172.389 pelamar unik")
```
Konteks (badge sumber, catatan) pindah ke `help=` — muncul saat diarahkan kursor, tidak
menempati ruang permanen. Tidak ada badge tertulis di layar kecuali halaman itu sendiri
butuh spanduk (§7.3).

### 7.2 Judul chart = temuan (D1, D3)
Bukan komponen terpisah — ini cara menulis judul `blok_chart()`. Judul chart utama tiap
halaman ditulis sebagai kalimat temuan, bukan nama kategori:
> "Tes online kehilangan separuh pesertanya" — bukan "No-show per tahap"

Ini **menggantikan** kartu insight terpisah yang direncanakan sebelumnya. Satu halaman
maksimal satu kalimat temuan (D3), dan tempatnya adalah judul chart utama — bukan blok
tambahan di bawahnya.

### 7.3 Spanduk sumber data (dipakai jarang, D4)
Satu spanduk per halaman **hanya kalau seluruh halaman itu dimodelkan** (halaman 2). Bukan
badge di tiap KPI — itu menambah kebisingan pada 218.928, 7.711, dst yang semuanya `NYATA`
dan tidak butuh penanda berulang.

### 7.4 "Tentang halaman ini" (D2)
Satu `st.expander` tertutup secara default, berisi definisi metrik & jebakan data untuk
halaman itu (mis. "kenapa tahun RBB ditandai berbeda"). Dibaca sekali oleh pengguna baru,
tidak mengganggu pengguna yang sudah hafal — ini jawaban atas keluhan "caption yang sama
dibaca 10× jadi kebisingan".

### 7.5 Toggle Mode Analis
Sakelar di baris global tepat di bawah bar navigasi atas. Statusnya di `st.session_state`, berlaku lintas halaman — analis tidak
perlu mengklik ulang.

---

## 8. Aturan chart

### 8.1 Pemilihan bentuk & pustaka

| Tugas data | Bentuk | Pustaka | Contoh di dashboard |
|---|---|---|---|
| Satu angka utama | `st.metric` | native | 7.711 diterima |
| Besaran antar kategori | batang horizontal | Altair | pembidangan, gap FTK per unit |
| Perubahan sepanjang waktu | batang per tahun (bukan garis lintas-jalur) | Altair | pendaftaran 2019–2025 |
| Bagian dari keseluruhan | batang bertumpuk | Altair | komposisi jenjang |
| Besaran di dua dimensi | heatmap | Altair | unit × sub-bidang |
| Perubahan dua titik | slope chart | Altair | rencana vs realisasi |

**Chart eksotis — jangkar perhatian, satu per halaman, Plotly:**

| Halaman | Bentuk | Kenapa Plotly |
|---|---|---|
| 3 Tahapan seleksi | Sankey alur gugur | Altair tidak native mendukung Sankey |
| 6 Penempatan | Treemap unit × bidang | Proporsi bersarang, label langsung per sel |
| 4 Kandidat | Peta (`scatter_geo`) volume tes per kota | Batas negara bawaan, tanpa GeoJSON |

Plotly membaca `chartCategoricalColors`/`chartSequentialColors` dari
`.streamlit/config.toml` secara otomatis — **tidak ada palet kedua untuk dirawat.** Tiap
chart eksotis wajib punya label langsung di atas marknya (nama tahap di simpul Sankey, nama
unit di sel treemap) supaya terbaca tanpa legenda terpisah — kalau butuh legenda untuk
dipahami, itu gagal sebagai jangkar perhatian dan diganti bentuk lain.

### 8.2 Larangan keras

- **Tidak ada sumbu ganda.** Ini kesalahan chart nomor satu. Rencana awal "pendaftar vs
  diterima dalam satu chart bersumbu ganda" **dibatalkan** — diganti dua chart bertumpuk
  yang berbagi sumbu x (small multiples), skalanya masing-masing.
- **Tidak ada pie chart lebih dari 3 irisan.** Untuk komposisi 10 bidang pembidangan,
  pakai batang horizontal.
- **Tidak ada warna pelangi** untuk besaran, dan tidak ada hue di titik tengah ramp
  divergen.
- **Warna mengikuti entitas, bukan peringkat.** Filter yang mengurangi jumlah seri tidak
  boleh mengecat ulang seri yang tersisa — "Distribusi" selalu warna yang sama.
- **Tidak ada angka di setiap titik.** Label langsung hanya pada titik yang bermakna
  (awal, akhir, puncak).

### 8.3 Anatomi tanda
- Batang: ujung membulat 4px, jarak 2px antar segmen bertumpuk
- Garis: tebal 2px, penanda ≥ 8px
- Grid & sumbu: resesif — abu muda, tanpa garis vertikal kecuali perlu
- Legenda selalu ada untuk ≥ 2 seri; satu seri tidak perlu legenda (judul sudah menamainya)

### 8.4 Interaksi
Tooltip pada semua chart. Garis/area memakai crosshair + tooltip; batang/sel memakai
tooltip per tanda. Filter berbaris dalam satu baris di atas chart, bukan di sidebar
tersembunyi.

---

## 9. Mode gelap

Dipilih, bukan dibalik otomatis. Nilai gelap sudah divalidasi terhadap permukaan
`#132C42` sebagai satu set — semua enam slot kategori lolos 3:1 di mode gelap (lebih baik
daripada mode terang). Token didefinisikan di `core/theme.py` dan diinjeksikan sebagai CSS
custom property, satu tempat untuk kedua mode.

---

## 10. Daftar periksa sebelum sebuah halaman dianggap selesai

- [ ] Halaman yang datanya terhubung ke profesi memanggil `ui.bar_filter()` dan SEMUA chart-nya tunduk pada filter itu; halaman yang tidak bisa disaring menyatakannya
- [ ] Tiap chart ada di dalam `ui.seksi(judul, bantuan)`: judul = nama benda, bantuan = cara membaca (D1 baru)
- [ ] Bentuk chart dipilih menurut tugas datanya, bukan batang di mana-mana (§8.1)
- [ ] Tiap chart punya keadaan kosong (`ui.kosong`) untuk filter yang tidak menyisakan data
- [ ] Tidak ada `st.caption` penjelas permanen di bawah chart; konteks di `help=` atau tombol (?) (D2)
- [ ] Tidak ada em dash atau en dash di teks yang tampil
- [ ] Tidak ada badge `NYATA` berulang di tiap KPI; spanduk `DIMODELKAN` hanya kalau seluruh halaman begitu (D4)
- [ ] Tidak ada emoji, tidak ada spanduk hero gradien (D6)
- [ ] Chart eksotis (kalau ada) punya label langsung di atas mark, terbaca tanpa legenda
- [ ] Tidak ada sumbu ganda
- [ ] Chart dengan slot aqua/kuning/magenta punya label langsung atau tampilan tabel
- [ ] Scatter/peta memakai maksimal 3 warna kategori
- [ ] Warna status selalu berpasangan dengan ikon + label
- [ ] Mode gelap diperiksa dengan mata, bukan diasumsikan
- [ ] Angka cocok dengan `metrik.md`
- [ ] Tidak ada PII kandidat yang tampil atau bisa disebut oleh chatbot
- [ ] Chart terbaca tanpa membaca judulnya — kalau harus baca penjelasan dulu, bentuknya diganti

---

## 12. Revamp dashboard (revisi 2026-09-16) — MENGGANTIKAN sebagian §11

Permintaan pemilik: dashboard harus lebih terasa *dashboard* untuk manajemen, bentuk
chart beragam (bukan batang di mana-mana), pola tersembunyi di data diangkat, penjelasan
cukup lewat tombol (?) di tepi tiap seksi, dan filter yang membuat semua chart saling
melengkapi.

| Doktrin §11 | Status | Pengganti |
|---|---|---|
| D1 judul = temuan | **Dicabut** | Judul = nama benda ("Tingkat lulus per tahap dan tahun"). Kalimat temuan basi saat filter atau data berubah, judulnya tidak |
| D2 penjelasan on-demand | Bertahan, bentuk baru | Tombol (?) popover di tepi kanan tiap `ui.seksi()`. Expander "Tentang halaman ini" dihapus |
| D3 maks 1 kalimat temuan | **Dicabut** | Tidak ada kalimat temuan sama sekali di UI |
| D4 badge hanya saat membedakan | Bertahan | Spanduk native `st.warning` untuk halaman yang seluruhnya dimodelkan |
| D5 maks 4 blok | **Dicabut** | Satu halaman = baris KPI + beberapa seksi berpasangan; tiap seksi menjawab satu pertanyaan yang melengkapi seksi lain |
| D6 tanpa emoji, gradien, caption | Bertahan, diperluas | Juga tanpa em dash/en dash di teks tampil (antislop R-02) |

**Primitif baru** (`components/ui.py`, `components/grafik.py`): `bar_filter()`, `seksi()`,
`kosong()`, `grafik.heatmap()`, `grafik.bullet()`, `grafik.warna_kelompok()`. Primitif lama
`temuan_halaman()`, `blok_chart()`, `tentang_halaman()` dihapus.

**Huruf:** Plus Jakarta Sans (config.toml). Alasan: dirancang di Jakarta, cocok untuk UI
berbahasa Indonesia penuh, angka tetap terbaca di label sumbu kecil.

**Bentuk yang ditambahkan** (semua satu skala, tanpa sumbu ganda): heatmap berlabel (tahap x
tahun, bidang x tahun, unit x sub-bidang), dumbbell (tidak hadir online vs offline, dua
angka rencana), bullet chart (usulan vs pagu, kuota vs realisasi), histogram dengan garis
ambang (skor), rentang persentil (hari sejak melamar), dot plot berukuran (vendor), kalender
gelombang (Gantt + titik), scatter log (pendaftar vs peluang per gelombang), step chart (IPK),
funnel, lollipop (UPDL), peta berwarna tingkat lulus.

**Penegakan:** `tests/uji_disiplin.py` (tiap seksi punya bantuan, tanpa dash di teks tampil),
`tests/uji_halaman.py` (tiap halaman berfilter tahan 4 kombinasi filter, filter bertahan
lintas halaman), `tests/uji_metrik.py` (filter mempartisi total tanpa menggandakan baris),
`tests/uji_rahasia.py` (galat yang tampil di layar tidak pernah memuat kunci atau token).

### 12.1 Tindak lanjut audit 2026-09-16

Dua auditor independen (HR dan UI/UX) menilai dashboard hanya dari antarmukanya. Aturan
yang lahir dari temuan mereka:

| Aturan | Isi |
|---|---|
| **Tanpa narasi bergantung data** | Berlaku untuk judul, label KPI, dan teks (?). Kalimat seperti "terendah 2021" atau "peluang sekitar 2%" benar hanya untuk potret data hari ini dan diam-diam basi saat data bertambah. Yang boleh: cara membaca, mekanisme data, batas cakupan, dan aturan kebijakan yang memang tetap (mis. ambang IPK 3,00) |
| **Cakupan di label, bukan cuma di tooltip** | KPI yang menghitung sebagian data menulis cakupannya di labelnya sendiri ("Kuota terpenuhi, non-RBB"), supaya tidak bertentangan dengan chart di bawahnya |
| **Chart tanpa informasi dibongkar** | Batang yang semuanya sama tinggi atau persentase yang sama untuk semua baris bukan chart. Ganti bentuknya (jumlah orang jadi jeda hari) atau turunkan jadi tabel |
| **Data dimodelkan yang terlihat meyakinkan dihapus** | Histogram skor tes beserta garis ambang 60 dicabut: skornya dibangkitkan acak, jadi grafiknya menyiratkan temuan yang tidak ada. Label "dimodelkan" saja tidak cukup kalau bentuknya tetap terbaca sebagai bukti |
| **Warna wajib membawa informasi** | Treemap dulu memberi hue berbeda untuk tiap unit padahal nama unit sudah tercetak. Sekarang warna menandai bidang (5 teratas + Lainnya), dengan legenda ikut dirender karena treemap Plotly tidak punya legenda sendiri |
| **Galat tidak pernah tampil mentah** | Pesan galat penyedia bisa memuat kunci API. Semua galat yang jadi teks untuk pengguna lewat `chat.chatbot.pesan_aman()` |

---

## 11. Doktrin keterbacaan (revisi 2026-08-19) — lihat §12 untuk yang dicabut

Ditulis setelah review halaman 1: *"secara desain masih terlalu AI — info di mana-mana,
banyak caption kecil, menandakan grafiknya sendiri tidak bisa dibaca sekali lihat."*

Alasannya dua lapis, dan yang kedua lebih menentukan untuk dashboard ini secara spesifik:

1. Kalau tiap grafik butuh kalimat penjelas, itu bukti grafiknya tidak terbaca sekali lihat.
2. **Dashboard ini untuk dilihat berulang tiap hari** sebagai alat monitoring. Penjelasan
   punya masa pakai — setelah dilihat sepuluh kali, caption berubah jadi kebisingan yang
   menyita ruang dari angka yang benar-benar berubah tiap hari.

### D1 — Judul chart = temuan, bukan kategori
"Tes online kehilangan separuh pesertanya" bukan "No-show per tahap". Judul harus bisa
berdiri sendiri sebagai kesimpulan; chart di bawahnya adalah buktinya.

### D2 — Penjelasan bersifat on-demand, bukan permanen
Konteks pindah ke tooltip `help=` (§7.1) dan satu expander "Tentang halaman ini" per
halaman (§7.4) — tersedia bagi pembaca pertama, tidak menyita ruang bagi pembaca ke-sepuluh.

### D3 — Maksimal 1 kalimat temuan per halaman
Bukan satu kartu insight per chart (pola lama). Satu temuan, ditaruh sebagai judul chart
utama (§7.2) — kalau perlu lebih dari satu kalimat untuk menjelaskan satu chart, bentuk
chart-nya yang salah, bukan butuh lebih banyak teks.

### D4 — Badge sumber data hanya saat membedakan
Bukan badge `NYATA`/`DIMODELKAN` di tiap KPI (§7.1 versi lama). Satu spanduk per halaman
kalau seluruh halaman itu dimodelkan (§7.3) — badge yang berulang di angka yang semuanya
sama-sama nyata tidak menambah informasi, hanya menambah piksel.

### D5 — Maksimal 4 blok per halaman
1 baris KPI + 1 chart penarik perhatian (jangkar) + maksimal 2 chart pendukung. Lebih dari
itu, pecah jadi lapis analis (di balik toggle) atau halaman terpisah.

### D6 — Tanpa emoji, tanpa spanduk hero gradien, tanpa caption permanen
Ikon Material (`:material/...:`) dipakai seperlunya untuk navigasi/status, bukan emoji.
Judul halaman polos (`st.title` / `st.header`), bukan kartu gradien kustom — tanggal potong
data cukup ditampilkan sekali di baris global bawah nav, bukan diulang di tiap hero.

### Konsekuensi untuk chart eksotis
Sankey, treemap, dan peta **dipertahankan** — perannya sebagai jangkar perhatian halaman,
bukan dekorasi yang butuh dijelaskan. Uji D1 tetap berlaku: kalau bentuknya sendiri tidak
terbaca tanpa caption, diganti bentuk lain (lihat §8.1).

### Penegakan
D1–D6 dicek mekanis oleh `tests/uji_disiplin.py` — bukan niat baik yang bisa luntur per
halaman. Lihat `docs/PRD.md` §7 kriteria sukses dan rencana pengujian di plan eksekusi.
