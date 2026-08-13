"""
loader.py — Data access layer untuk Keday 70 BI Dashboard.

Membaca data dari database SQLite dan mengembalikan dict[str, pd.DataFrame]
dengan kolom-kolom yang sesuai dengan kebutuhan processor, filter, dan ai_context.

Kolom di SQLite menggunakan underscore (SQL-friendly), tetapi di sini
di-rename kembali ke format asli agar seluruh downstream logic tetap kompatibel.
"""
import pandas as pd
from backend.core.database import get_connection

_CACHED_DATA = None


def load_all() -> dict[str, pd.DataFrame]:
    """
    Muat seluruh data dari SQLite dan kembalikan sebagai dict DataFrame.
    Hasil di-cache dalam memori agar tidak perlu query ulang setiap request.
    """
    global _CACHED_DATA
    if _CACHED_DATA is not None:
        return _CACHED_DATA

    conn = get_connection()
    try:
        _CACHED_DATA = {
            "transactions": _load_transactions(conn),
            "products":     _load_products(conn),
            "belanja":      _load_belanja(conn),
            "operasional":  _load_operasional(conn),
        }
    finally:
        conn.close()

    return _CACHED_DATA


def reload_data() -> dict[str, pd.DataFrame]:
    """Force reload data dari SQLite (hapus cache)."""
    global _CACHED_DATA
    _CACHED_DATA = None
    return load_all()


# ═══════════════════════════════════════════════════════════════
# LOAD FUNCTIONS — baca SQLite, rename kolom ke format downstream
# ═══════════════════════════════════════════════════════════════

def _load_transactions(conn) -> pd.DataFrame:
    df = pd.read_sql("SELECT * FROM transactions", conn)

    # Rename kembali ke format yang diharapkan downstream
    df = df.rename(columns={
        "Transaction_Id":    "Transaction Id",
        "Transaction_Date":  "_tx_date_str",
        "Transaction_Time":  "Transaction Time",
        "Day_Of_Week":       "Day Of Week",
        "Product_Name":      "Product Name",
        "Unit_Price_Idr":    "Unit Price Idr",
        "Total_Price_Idr":   "Total Price Idr",
        "Payment_Method":    "Payment Method",
    })

    # Reconstruct datetime columns dari string
    df["Transaction Date"] = pd.to_datetime(df["_tx_date_str"], errors="coerce")
    df["Date"] = df["Transaction Date"].dt.date
    df["Week_Start"] = pd.to_datetime(df["Week_Start_Str"], errors="coerce")

    # Drop helper columns
    df = df.drop(columns=["_tx_date_str", "Date_Str", "Week_Start_Str"], errors="ignore")

    return df


def _load_products(conn) -> pd.DataFrame:
    df = pd.read_sql("SELECT * FROM products", conn)

    # Rename kembali ke format downstream
    df = df.rename(columns={
        "Nama_Produk":       "Nama Produk",
        "Harga_Satuan_IDR":  "Harga Satuan (IDR)",
        "Harga_Modal_IDR":   "Harga Modal (IDR)",
        "Margin_Kotor_Pct":  "Margin Kotor (%)",
    })

    return df


def _load_belanja(conn) -> pd.DataFrame:
    df = pd.read_sql("SELECT * FROM belanja", conn)

    # Rename kembali
    df = df.rename(columns={
        "Kategori_Belanja":  "Kategori Belanja",
        "Nama_Item":         "Nama Item",
        "Harga_Satuan_IDR":  "Harga Satuan (IDR)",
        "Total_Biaya_IDR":   "Total Biaya (IDR)",
    })

    # Reconstruct datetime
    df["Tanggal"] = pd.to_datetime(df["Tanggal_Str"], errors="coerce")
    df = df.drop(columns=["Tanggal_Str"], errors="ignore")

    return df


def _load_operasional(conn) -> pd.DataFrame:
    df = pd.read_sql("SELECT * FROM operasional", conn)

    # Rename kembali
    df = df.rename(columns={
        "Jumlah_IDR": "Jumlah (IDR)",
    })

    # Reconstruct datetime jika ada
    if "Tanggal_Pembayaran_Str" in df.columns:
        df["Tanggal Pembayaran"] = pd.to_datetime(
            df["Tanggal_Pembayaran_Str"], errors="coerce"
        )
        df = df.drop(columns=["Tanggal_Pembayaran_Str"], errors="ignore")

    return df