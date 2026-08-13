"""
database.py — Koneksi dan utilitas SQLite untuk Keday 70 BI Dashboard.

File ini menyediakan helper untuk mendapatkan koneksi ke database SQLite
yang menjadi penyimpanan utama data operasional Keday 70.
"""
import sqlite3
from backend.config.settings import DB_FILE


def get_db_path() -> str:
    """Kembalikan path absolut ke file database SQLite."""
    return str(DB_FILE)


def get_connection() -> sqlite3.Connection:
    """
    Buat koneksi baru ke database SQLite.
    Caller bertanggung jawab menutup koneksi setelah selesai.
    """
    conn = sqlite3.connect(get_db_path())
    # Aktifkan foreign keys (best practice)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn
