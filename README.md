# Dashboard Business Intelligence (BI) Keuangan Keday 70

> **Rancang Bangun Dashboard BI Keuangan Keday 70 Berbasis Vue 3 dan Vite dengan Integrasi Generative AI dan Orkestrasi Workflow n8n**

---

## Gambaran Umum

Sistem ini adalah dashboard Business Intelligence yang dirancang khusus untuk UMKM kuliner **Keday 70** di Cikampek, Jawa Barat. Dashboard ini mengubah data transaksi mentah dari spreadsheet menjadi visualisasi keuangan interaktif, dilengkapi fitur **chat-with-data** berbasis AI yang memungkinkan pemilik usaha bertanya langsung ke data dalam bahasa sehari-hari.

---

## Tech Stack

| Layer | Teknologi | Keterangan |
|-------|-----------|------------|
| **Frontend** | Vue 3 + Vite | Antarmuka dashboard SPA (Single Page Application), reaktif dan berbasis komponen |
| **Styling** | Tailwind CSS | Utility-first CSS framework untuk tampilan modern dan responsif |
| **Backend** | Python + FastAPI | REST API untuk pengolahan data, kalkulasi KPI, dan konteks AI |
| **Database** | SQLite | Database utama sistem — menyimpan data hasil ETL dari spreadsheet |
| **Data Processing** | Pandas + NumPy | Analisis data transaksi, agregasi, dan komputasi metrik keuangan |
| **Data Ingestion** | Spreadsheet (Excel) | Sumber data awal (ingestion layer) — di-sync otomatis ke SQLite saat startup |
| **Workflow Automation** | n8n (self-hosted) | Orkestrasi alur kerja: menghubungkan frontend → backend → AI secara otomatis |
| **Generative AI** | Grok API (xAI) | Model bahasa besar (LLM) untuk fitur tanya-jawab (chat-with-data) |
| **HTTP Client** | Axios | Komunikasi frontend-backend via REST API |
| **Charting** | Chart.js | Library visualisasi grafik (bar, line, pie, waterfall) |

---

## Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PENGGUNA (Browser)                         │
│                    http://localhost:5173                            │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │    FRONTEND (Vue 3)     │
              │  - Dashboard View       │
              │  - Transaksi View       │
              │  - Pengeluaran View     │
              │  - Laba Rugi View       │
              │  - Produk View          │
              │  - Chat Panel           │
              └─────┬──────────┬────────┘
                    │          │
         ┌──────────▼──┐  ┌───▼──────────────────┐
         │  REST API   │  │  Chat Message        │
         │  (Axios)    │  │  (Axios → Backend)   │
         └──────┬──────┘  └───┬──────────────────┘
                │             │
    ┌───────────▼─────────────▼──────────────┐
    │       BACKEND (FastAPI - port 8000)    │
    │                                        │
    │  /api/dashboard/data    → KPI, grafik  │
    │  /api/dashboard/filter-options         │
    │  /api/dashboard/ai-context → prompt AI │
    │  /api/chat/message      → kirim ke n8n │
    │  /api/reload            → re-sync data │
    │                                        │
    │  Core Modules:                         │
    │  - loader.py     → baca dari SQLite    │
    │  - processor.py  → hitung KPI & metrik │
    │  - filter.py     → filter Hari/Minggu/ │
    │                    Bulan                │
    │  - database.py   → koneksi SQLite      │
    │  - sync_excel_to_sqlite.py → ETL       │
    └──────┬─────────────────┬───────────────┘
           │                 │
  ┌────────▼─────┐   ┌──────▼──────────────────────────────┐
  │   SQLite     │   │         n8n (port 5678)             │
  │ (keday70.db) │   │  Webhook → Backend → Grok → Respond │
  │              │   └──────────────────────────────────────┘
  │  Tabel:      │                    │
  │  - transac.  │           ┌────────▼────────┐
  │  - belanja   │           │   Grok API      │
  │  - operasi.  │           │   (xAI LLM)     │
  │  - produk    │           └─────────────────┘
  └──────▲───────┘
         │ ETL (startup)
  ┌──────┴───────┐
  │  Spreadsheet │
  │  (Excel)     │
  │  Data Source │
  └──────────────┘
```

---

## Alur Kerja Sistem

### 1. Alur Dashboard (Visualisasi Data)

```
Spreadsheet (.xlsx)
      │
      ▼
  sync_excel_to_sqlite.py (ETL: baca, transform, feature engineering)
      │
      ▼
  SQLite Database (keday70.db)
      │
      ▼
  loader.py (baca dari SQLite via pd.read_sql)
      │
      ▼
  processor.py (hitung KPI, revenue, top produk, pengeluaran, laba rugi)
      │
      ▼
  filter.py (filter berdasarkan mode: Hari / Minggu / Bulan)
      │
      ▼
  FastAPI endpoint /api/dashboard/data (return JSON)
      │
      ▼
  Vue 3 Frontend (render grafik, tabel, KPI cards)
```

**Penjelasan:**
1. Saat dashboard dibuka, frontend memanggil `/api/dashboard/filter-options` untuk mendapatkan opsi filter (daftar bulan, minggu, tanggal).
2. Kemudian memanggil `/api/dashboard/data` dengan parameter `mode` dan `value` untuk mendapatkan data sesuai filter.
3. Backend membaca file Excel melalui `loader.py`, memproses metrik melalui `processor.py`, lalu mengembalikan JSON berisi KPI, data grafik, dan tabel.
4. Frontend merender data tersebut menjadi grafik interaktif menggunakan Chart.js.

---

### 2. Alur Chat-with-Data (Integrasi n8n + Grok AI)

Ini adalah alur utama ketika pengguna bertanya melalui fitur chat:

```
  Pengguna mengetik pertanyaan di Chat Panel
      │
      ▼
  Frontend POST /api/chat/message
  {sessionId, chatInput, history}
      │
      ▼
  Backend (chat.py) meneruskan ke n8n via Webhook
  POST http://localhost:5678/webhook/chat-Keday70-v2
      │
      ▼
  ┌──────────────────────────────────────────────────────────────────┐
  │                    n8n WORKFLOW                                  │
  │                                                                  │
  │  ① Webhook (Trigger)                                             │
  │     Menerima pertanyaan dari backend                             │
  │         │                                                        │
  │         ▼                                                        │
  │  ② HTTP Request (POST ke Backend)                                │
  │     POST http://host.docker.internal:8000/api/dashboard/ai-context│
  │     Kirim pertanyaan + history ke backend                        │
  │     Backend menganalisis pertanyaan, mendeteksi:                 │
  │     - Periode (bulan/tanggal yang disebut)                       │
  │     - Kategori produk (Coffee/Non-Coffee/Main Course)            │
  │     - Nama produk spesifik                                       │
  │     - Topik (produk, tren, laba, pengeluaran, saran, dll)       │
  │     Lalu menghitung data yang relevan dan membangun              │
  │     ENRICHED PROMPT berisi konteks data + instruksi jawaban      │
  │         │                                                        │
  │         ▼                                                        │
  │  ③ HTTP Request (POST ke Grok API)                               │
  │     POST https://api.groq.com/openai/v1/chat/completions        │
  │     Mengirim enriched prompt ke Grok LLM                         │
  │     Grok menjawab berdasarkan data nyata dari prompt             │
  │         │                                                        │
  │         ▼                                                        │
  │  ④ Code in JavaScript                                            │
  │     Mengekstrak dan memformat respons dari Grok                  │
  │         │                                                        │
  │         ▼                                                        │
  │  ⑤ Respond to Webhook                                            │
  │     Mengirim jawaban akhir ke backend                            │
  └──────────────────────────────────────────────────────────────────┘
      │
      ▼
  Backend menerima jawaban, kirim ke frontend
      │
      ▼
  Chat Panel menampilkan jawaban AI ke pengguna
```

**Node-node pada n8n Workflow:**

| Node | Tipe | Fungsi |
|------|------|--------|
| **Webhook** | Trigger | Menerima POST request dari backend saat user bertanya |
| **HTTP Request** | Action | Memanggil `/api/dashboard/ai-context` di backend untuk membangun konteks data |
| **HTTP Request1** | Action | Mengirim enriched prompt ke Grok API (`https://api.groq.com/...`) |
| **Code in JavaScript** | Action | Memproses dan memformat respons dari Grok |
| **Respond to Webhook** | Action | Mengembalikan jawaban final ke backend |

---

## Fitur Dashboard

### Menu Utama

| Menu | Deskripsi |
|------|-----------|
| **Ringkasan (Dashboard)** | KPI cards (pendapatan, transaksi, pengeluaran, laba), grafik tren pendapatan, distribusi kategori, top produk, distribusi pembayaran |
| **Transaksi** | Analisis transaksi per periode, tren penjualan, distribusi per sesi waktu, top produk terlaris, komposisi kategori |
| **Pengeluaran** | Breakdown pengeluaran (belanja bahan baku vs biaya operasional), tren pengeluaran bulanan, kategori pengeluaran |
| **Laba Rugi** | Estimasi laba bersih, waterfall chart (pendapatan → HPP → biaya operasional → laba), margin per kategori |
| **Produk** | Daftar produk lengkap dengan harga jual, harga modal, margin, volume penjualan, dan pendapatan per produk |

### Fitur Tambahan

| Fitur | Deskripsi |
|-------|-----------|
| **Filter Dinamis** | Filter data berdasarkan Hari, Minggu, atau Bulan |
| **Chat-with-Data** | Tanya jawab dalam bahasa natural (contoh: "Produk apa yang paling laku bulan Desember?") |
| **Deteksi Konteks Otomatis** | Sistem AI otomatis mendeteksi periode, kategori, dan topik dari pertanyaan user |
| **Riwayat Percakapan** | Chat mengingat konteks percakapan sebelumnya dalam satu sesi |
| **Responsive Layout** | Tampilan menyesuaikan ukuran layar (desktop & mobile) |

---

## Struktur Direktori

```
keday70_v7/
├── backend/
│   ├── main.py                  # Entry point FastAPI + startup ETL
│   ├── config/
│   │   ├── settings.py          # Konfigurasi (path data, DB, URL n8n)
│   │   └── constants.py         # Konstanta (mapping bulan, kategori)
│   ├── core/
│   │   ├── database.py          # Koneksi SQLite helper
│   │   ├── sync_excel_to_sqlite.py  # ETL: Excel → SQLite
│   │   ├── loader.py            # Baca data dari SQLite (pd.read_sql)
│   │   ├── processor.py         # Hitung KPI, revenue, produk, dll
│   │   └── filter.py            # Filter data per Hari/Minggu/Bulan
│   └── routers/
│       ├── dashboard.py         # Endpoint data dashboard & filter
│       ├── chat.py              # Endpoint chat → n8n webhook
│       └── ai_context.py        # Endpoint konteks AI (enriched prompt)
│
├── frontend_vue/
│   └── src/
│       ├── App.vue              # Root component + routing
│       ├── api.js               # Axios instance
│       ├── assets/
│       │   └── main.css         # Global styles
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Sidebar.vue  # Navigasi sidebar
│       │   │   └── Topbar.vue   # Header + filter mode/value
│       │   ├── charts/
│       │   │   └── KpiCards.vue # Kartu KPI
│       │   └── chat/
│       │       └── ChatPanel.vue # Panel chat AI
│       └── views/
│           ├── DashboardView.vue    # Halaman ringkasan
│           ├── TransaksiView.vue    # Halaman transaksi
│           ├── PengeluaranView.vue  # Halaman pengeluaran
│           ├── LabaRugiView.vue     # Halaman laba rugi
│           └── ProdukView.vue       # Halaman produk
│
├── keday70.db                   # Database SQLite (auto-generated)
├── data/                        # Konfigurasi filter data
├── assets/                      # Aset statis (gambar, ikon, Excel)
├── .env                         # Variabel environment (N8N_WEBHOOK_URL)
├── requirements.txt             # Dependensi Python
├── start_dashboard.bat          # Script untuk menjalankan backend + frontend
└── README.md                    # Dokumentasi ini
```

---

## Sumber Data (Spreadsheet)

Data disimpan dalam file Excel (.xlsx) dengan 4 sheet:

| Sheet | Isi | Kolom Utama |
|-------|-----|-------------|
| **Transactions** | Catatan penjualan harian | Transaction Date, Product Name, Category, Quantity, Total Price Idr, Payment Method, Session, Day Of Week |
| **Daftar Produk** | Master data produk | Nama Produk, Harga Satuan (IDR), Harga Modal (IDR), Kategori |
| **Pengeluaran Belanja** | Pembelian bahan baku | Tanggal, Kategori, Item, Jumlah |
| **Biaya Operasional** | Biaya tetap bulanan | Bulan, Kategori (Gaji, Sewa, Utilitas, dll), Jumlah |

---

## Cara Menjalankan

### Prasyarat
- Python 3.10+
- Node.js 18+
- n8n (self-hosted, berjalan di port 5678)

### Langkah-langkah

**1. Install dependensi backend:**
```bash
pip install -r requirements.txt
```

**2. Install dependensi frontend:**
```bash
cd frontend_vue
npm install
```

**3. Jalankan n8n:**
```bash
npx n8n
```
Kemudian import workflow dan konfigurasi node-node sesuai alur di atas.

**4. Jalankan sistem (otomatis):**
```bash
start_dashboard.bat
```
Script ini menjalankan backend (port 8000) dan frontend (port 5173) secara bersamaan.

**Atau jalankan manual:**
```bash
# Terminal 1 — Backend
set PYTHONPATH=%cd%
uvicorn backend.main:app --port 8000 --reload

# Terminal 2 — Frontend
cd frontend_vue
npm run dev
```

**5. Buka browser:**
- Dashboard: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- n8n Editor: `http://localhost:5678`

---

## Konfigurasi Environment

File `.env` di root project:

```env
N8N_WEBHOOK_URL=http://localhost:5678/webhook/chat-Keday70-v2
```

---

## Contoh Pertanyaan Chat AI

| Pertanyaan | Jenis |
|------------|-------|
| "Berapa total pendapatan bulan Desember?" | Faktual |
| "Produk apa yang paling laku minggu ini?" | Top/Ranking |
| "Analisa penjualan bulan November" | Analisis Komprehensif |
| "Berapa laba bersih bulan Oktober?" | KPI |
| "Sesi waktu mana yang paling ramai?" | Sesi |
| "Bandingkan penjualan coffee dan non-coffee" | Perbandingan |
| "Beri saran untuk meningkatkan penjualan" | Rekomendasi |
| "Berapa Es Coklat terjual bulan Desember?" | Produk Spesifik |

---

## Revisi Arsitektur Data

Pada versi awal, sistem membaca data langsung dari file Excel menggunakan `pandas.read_excel()` setiap kali server dijalankan. Pendekatan ini memiliki keterbatasan dari segi performa query dan skalabilitas ketika volume data bertambah.

Sejak versi 2.0, sistem menerapkan pendekatan **ETL (Extract, Transform, Load)** sederhana:

1. **Extract** — Spreadsheet Excel tetap menjadi sumber data utama yang diisi oleh pemilik usaha.
2. **Transform** — Data dari 4 sheet (Transactions, Daftar Produk, Pengeluaran Belanja, Biaya Operasional) dibersihkan, ditransformasi, dan dilengkapi kolom turunan (feature engineering) untuk kebutuhan analisis.
3. **Load** — Hasil transformasi disimpan ke database SQLite (`keday70.db`) dengan index pada kolom-kolom yang sering difilter.

Dashboard dan chatbot AI kini mengambil data dari SQLite melalui `pd.read_sql()`, bukan langsung dari Excel. Proses sinkronisasi berjalan otomatis saat server startup dan dapat dipicu ulang melalui endpoint `POST /api/reload`.

Revisi ini dilakukan untuk:
- Meningkatkan **performa query** karena SQLite mendukung indexing.
- Menjaga **konsistensi arsitektur** dengan memisahkan data source dari database operasional.
- Mempertahankan **workflow UMKM** yang sudah terbiasa dengan spreadsheet sebagai alat pencatatan sehari-hari.

---

## Data Enrichment & Feature Engineering

Selain menggunakan data asli dari spreadsheet, sistem juga menghasilkan kolom turunan (*derived features*) selama proses ETL. Kolom-kolom ini digunakan untuk meningkatkan kualitas analisis dashboard, filtering data, serta kemampuan reasoning AI dalam menghasilkan insight bisnis.

### Transactions (Enriched Columns)

| Kolom | Tipe | Sumber | Keterangan |
|-------|------|--------|------------|
| `Is_Weekend` | Integer (0/1) | Derived dari `Day_Num` | 1 jika hari Sabtu/Minggu, untuk analisis pola weekend |
| `Revenue_Tier` | String | Derived dari `Total Price Idr` | Klasifikasi transaksi: Tinggi/Sedang/Rendah (percentile 33/66) |
| `Time_Slot` | String | Derived dari `Transaction Time` | Slot waktu granular: Pagi Awal/Pagi/Siang/Sore/Malam |
| `Hour` | Integer | Extracted dari `Transaction Time` | Jam transaksi (0-23), untuk analisis peak hour |
| `Day_Num` | Integer | Derived dari `Transaction Date` | Hari dalam minggu (0=Senin, 6=Minggu) |

### Products (Enriched Columns)

| Kolom | Tipe | Sumber | Keterangan |
|-------|------|--------|------------|
| `Profit_Per_Unit` | Integer | `Harga Satuan` - `Harga Modal` | Laba kotor per unit produk |
| `Total_Qty_Sold` | Integer | Agregasi dari `transactions` | Total unit terjual sepanjang periode |
| `Total_Revenue` | Integer | Agregasi dari `transactions` | Total pendapatan produk |
| `Total_Profit` | Integer | `Profit_Per_Unit` × `Total_Qty_Sold` | Estimasi total laba kotor produk |
| `Performance_Tier` | String | Derived dari `Total_Revenue` | Klasifikasi performa: Top/Middle/Low (percentile 33/66) |

### Belanja (Enriched Columns)

| Kolom | Tipe | Sumber | Keterangan |
|-------|------|--------|------------|
| `Cost_Type` | String | Derived dari `Kategori Belanja` | Klasifikasi: "Bahan Baku" atau "Packaging & Supplies" |

Enrichment dilakukan secara otomatis saat proses ETL (`sync_excel_to_sqlite.py`). Data asli dari spreadsheet tetap dipertahankan — kolom tambahan bersifat enhancement yang tidak mengubah raw data.

---

## Lisensi

Proyek ini dikembangkan sebagai Tugas Akhir Program Studi D-III Fakultas Vokasi, Universitas Brawijaya.
