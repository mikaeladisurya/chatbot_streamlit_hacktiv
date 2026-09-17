# Deploy ke Streamlit Community Cloud

Dashboard v2 dijalankan online lewat Streamlit Community Cloud, dengan data dibaca
dari MotherDuck (DuckDB terkelola). Berkas `rekrutmen.duckdb` (62 MB) sengaja tidak
ikut di-commit — pola `*.duckdb` di `.gitignore` mencegahnya.

## Dua mode sumber data

`core/db.py` memilih sumber data sendiri berdasarkan ada tidaknya `motherduck_token`
(dibaca dari environment variable dulu, lalu `st.secrets`):

| Token | Sumber data | Dipakai untuk |
|---|---|---|
| ada | MotherDuck, database `rekrutmen` | Streamlit Community Cloud |
| kosong | `data/rekrutmen.duckdb` | pengembangan lokal |

Dialek SQL identik di kedua mode, jadi tidak ada query di `core/metrics.py` maupun
prompt text-to-SQL di `chat/chatbot.py` yang perlu berbeda.

Untuk kembali sepenuhnya ke berkas lokal, cukup kosongkan `motherduck_token` di
`.streamlit/secrets.toml`. Tidak ada kode yang perlu diubah.

## Mengunggah ulang data ke MotherDuck

Wajib diulang setiap kali generator mockdb membangkitkan database baru —
MotherDuck menyimpan salinan, bukan tautan ke berkas lokal.

Dijalankan dari root repo, dengan `motherduck_token` di environment dan berkas
terbaru sudah disalin ke `data/`:

```python
import duckdb

con = duckdb.connect()                      # in-memory
con.execute("ATTACH 'md:'")
con.execute("DROP DATABASE IF EXISTS rekrutmen")
con.execute("CREATE DATABASE rekrutmen")
con.execute("ATTACH 'data/rekrutmen.duckdb' AS src (READ_ONLY)")
con.execute("COPY FROM DATABASE src TO rekrutmen")
```

Berkas lokal **harus** di-`ATTACH` dengan alias (`src`). Menyambungkannya langsung
membuat DuckDB menurunkan nama katalog dari nama berkas — `rekrutmen` — dan bentrok
dengan nama database cloud.

Unggahan 62 MB memakan waktu sekitar 80 detik. Verifikasi setelahnya: jumlah tabel
harus 35 dan `SELECT count(*) FROM kandidat` harus 368.912.

## Pengaturan di share.streamlit.io

| Kolom | Nilai |
|---|---|
| Repository | `mikaeladisurya/chatbot_streamlit_hacktiv` |
| Branch | `main` |
| Main file path | `streamlit_app.py` |
| Python version | 3.12 |

Dependensi diambil dari `requirements.txt` dan tema dari `.streamlit/config.toml`,
keduanya di root repo.

App dibaca dari `main`. Kerjakan perubahan di branch lain lalu gabungkan lewat PR,
supaya app online hanya berubah saat memang disengaja.

Isi Secrets lewat menu Advanced settings (atau Settings → Secrets setelah app hidup),
format TOML sama persis dengan `.streamlit/secrets.toml` lokal: `motherduck_token`
plus blok `[llm.*]`. Secrets bisa diubah kapan saja tanpa deploy ulang.

## Batas dan hal yang perlu dipantau

- **Kuota MotherDuck Lite**: 10 GB penyimpanan, 10 jam compute per bulan, plus plafon
  harian. Jam compute dihitung dari instance menyala, bukan durasi query — satu tab
  browser yang dibiarkan terbuka menjaga instance tetap warm.
- **Kecepatan**: satu pass penuh 35 metrik memakan 0,3 detik lewat berkas lokal
  dan 13 detik lewat MotherDuck. `@st.cache_data(ttl=3600)` menahan hasilnya sejam,
  jadi biaya itu hanya terasa saat halaman pertama kali dibuka.
- **Riwayat chat** (`data/chat_history.db`) ditulis ke disk container yang bersifat
  sementara dan hilang tiap kali Cloud me-restart app.
- **Kunci LLM** di Secrets dipakai oleh siapa pun yang membuka app. Kalau URL
  dibagikan luas, pantau tagihan penyedia LLM.

## Jalur mundur bila kuota MotherDuck tidak cukup

Kosongkan `motherduck_token` dan cabut `*.duckdb` dari `.gitignore` supaya
`data/rekrutmen.duckdb` ikut ter-commit. Konsekuensinya repo membawa binary
62 MB — di bawah batas keras GitHub 100 MB, tapi melewati ambang peringatan 50 MB.
