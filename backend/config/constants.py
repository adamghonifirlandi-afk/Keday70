# ── Urutan bulan Indonesia ────────────────────────────────────────────────────
BULAN_ORDER = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]
BULAN_TO_NUM = {b: i+1 for i, b in enumerate(BULAN_ORDER)}
NUM_TO_BULAN = {v: k for k, v in BULAN_TO_NUM.items()}

BULAN_SHORT = {
    "Januari": "Jan", "Februari": "Feb", "Maret": "Mar", "April": "Apr",
    "Mei": "Mei", "Juni": "Jun", "Juli": "Jul", "Agustus": "Agt",
    "September": "Sep", "Oktober": "Okt", "November": "Nov", "Desember": "Des",
}

# ── Hari ─────────────────────────────────────────────────────────────────────
HARI_ORDER = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

# ── Sesi ─────────────────────────────────────────────────────────────────────
SESSION_ORDER = ["Pagi", "Siang", "Sore", "Malam"]

# ── Kategori produk ───────────────────────────────────────────────────────────
KATEGORI_PRODUK = ["Coffee", "Non-Coffee", "Main Course"]

# ── Kategori pengeluaran ──────────────────────────────────────────────────────
KATEGORI_BELANJA = [
    "Bahan Baku Coffee", "Bahan Baku Non-Coffee",
    "Bahan Baku Makanan", "Packaging & Supplies"
]
KATEGORI_OPS = [
    "Gaji & Upah", "Sewa Tempat", "Administrasi & Perawatan", "Komunikasi"
]

# ── Metode pembayaran ─────────────────────────────────────────────────────────
PAYMENT_METHODS = ["QRIS", "Tunai", "Transfer Bank"]

# ── Mode filter ───────────────────────────────────────────────────────────────
FILTER_MODES = ["Hari", "Minggu", "Bulan"]
