# Dashboard Rekrutmen PLN v2

Dashboard 8 halaman di atas `rekrutmen.duckdb` (35 tabel, 4,22 juta baris), lengkap
dengan chatbot text-to-SQL "RecruitMan". Seluruh data adalah data tiruan (mock),
bukan data pegawai PLN.

Versi online berjalan di Streamlit Community Cloud, membaca data dari MotherDuck.
Cara deploy dan cara memperbarui datanya ada di [`docs/DEPLOY.md`](docs/DEPLOY.md).

## Jalankan lokal

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Data dibaca **read-only** dari `data/rekrutmen.duckdb`. Berkas itu tidak ikut
di-commit (62 MB), jadi ada dua pilihan: minta salinannya ke pemilik repo lalu taruh
di `data/`, atau isi `motherduck_token` di `.streamlit/secrets.toml` supaya data
dibaca dari MotherDuck.

Chatbot butuh kredensial LLM: salin `.streamlit/secrets.toml.example` ke
`.streamlit/secrets.toml` lalu isi satu blok `[llm.*]` atau lebih (endpoint apa pun
yang kompatibel OpenAI). Tanpa itu chatbot menampilkan pesan fallback dan tujuh
halaman lain tetap berfungsi penuh.

## Sumber data: dua mode

`core/db.py` memilih sendiri berdasarkan ada tidaknya `motherduck_token` di
environment variable atau `st.secrets`:

| Token | Sumber |
|---|---|
| ada | MotherDuck, database `rekrutmen` — dipakai Streamlit Cloud |
| kosong | berkas `data/rekrutmen.duckdb` — pengembangan sehari-hari |

Dialek SQL sama persis di kedua mode, jadi tak ada query yang perlu bercabang.

## Struktur

```
streamlit_app.py      titik masuk — navigasi, sakelar mode analis, popover chatbot
core/
  db.py               pemilihan sumber data + koneksi & cache query
  metrics.py          SATU implementasi tiap KPI (dipakai halaman & chatbot)
  theme.py            token warna
  format.py           format angka gaya Indonesia
components/ui.py      hero, kartu insight, badge, sakelar mode analis
app_pages/            satu berkas per halaman
chat/
  chatbot.py          agen text-to-SQL — prompt skema, loop agentic, render chart
  chat_ui.py          tampilan percakapan (halaman penuh & popover mengambang)
  chat_store.py       riwayat percakapan di SQLite (data/chat_history.db)
tests/                uji halaman & uji metrik (pytest)
docs/                 PRD, kamus metrik, wireframe, design system, deploy, backlog
```

## Dua aturan arsitektur

1. **Halaman tidak menulis SQL agregat sendiri.** Semua angka lewat `core/metrics.py`,
   supaya halaman dan chatbot tidak pernah memberi angka berbeda.
2. **Database tidak dimuat ke memori.** 4,22 juta baris — yang di-cache hasil query,
   bukan tabelnya.

## Halaman

| Halaman | Isi |
|---|---|
| Ringkasan | KPI utama, tren tahunan, corong, gugur per tahap, rencana vs realisasi |
| Perencanaan | pagu vs usulan, gap FTK per unit, proyeksi kekosongan, heatmap kebutuhan |
| Tahapan seleksi | konversi per tahap, no-show per tahap & mode, jejak RBB |
| Kandidat | akun & kelengkapannya, pendidikan, umur–gender, rumpun, sebaran kota |
| Pasca-seleksi & OJT | pipeline posisi, pembidangan, sebaran UPDL, timeline kohort |
| Penempatan | jenis penempatan, treemap, grade masuk, rencana vs realisasi |
| Kualitas data | kelengkapan per kohort, volume per sistem, selisih angka rencana |
| RecruitMan | chatbot text-to-SQL; juga tersedia sebagai popover di semua halaman |

## Tes

```bash
python -m pytest tests
```

90 tes: setiap halaman dirender sampai selesai, setiap metrik dicek bentuk dan
nilainya. Jalan di kedua mode sumber data.

## Dokumen

Baca `docs/PRD.md` dulu, lalu `docs/metrik.md` (kamus metrik + SQL terverifikasi).
`docs/DEPLOY.md` untuk deployment, `docs/backlog.md` untuk ide yang belum masuk cakupan.
