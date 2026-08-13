"""
sync_excel_to_sqlite.py — ETL: Excel → Transform → Enrich → SQLite

Modul ini membaca data dari file Excel Keday 70, melakukan transformasi,
feature engineering, dan data enrichment, lalu menyimpan hasilnya ke SQLite.
Fungsi sync() dipanggil sekali saat server startup.

Kolom enrichment (derived features):
  Transactions:
    - Is_Weekend      : 1 jika Sabtu/Minggu
    - Revenue_Tier    : Tinggi/Sedang/Rendah berdasarkan nilai transaksi
    - Time_Slot       : Pagi Awal/Pagi/Siang/Sore/Malam (lebih granular dari Session)
  Products:
    - Profit_Per_Unit : Harga jual - harga modal
    - Total_Qty_Sold  : Total unit terjual (dari transaksi)
    - Total_Revenue   : Total pendapatan (dari transaksi)
    - Total_Profit    : Estimasi laba kotor (Profit_Per_Unit * Qty)
    - Performance_Tier: Top/Middle/Low berdasarkan ranking revenue
  Belanja:
    - Cost_Type       : Bahan Baku / Packaging & Supplies
"""
import numpy as np
import pandas as pd
from backend.config.settings import DATA_FILE
from backend.config.constants import NUM_TO_BULAN, BULAN_TO_NUM, KATEGORI_OPS
from backend.core.database import get_connection, get_db_path


def _normalize_category(value) -> str:
    text = str(value or "").strip().lower()
    return (
        text.replace("&", "dan")
        .replace("-", " ")
        .replace("_", " ")
        .replace("  ", " ")
    )


def _is_operational_category(category) -> bool:
    normalized_ops = {_normalize_category(item) for item in KATEGORI_OPS}
    return _normalize_category(category) in normalized_ops


def sync() -> None:
    """
    Baca seluruh sheet dari Excel, transformasi + enrich, lalu tulis ke SQLite.
    Tabel yang sudah ada akan di-replace (full refresh).
    """
    print(f"[ETL] Membaca Excel: {DATA_FILE}")
    with pd.ExcelFile(DATA_FILE) as xls:
        df_tx   = _transform_transactions(xls)
        df_prod = _transform_products(xls)
        df_bel  = _transform_belanja(xls)
        df_ops  = _transform_operasional(xls)
    df_bel, df_ops = _split_expenses_by_category(df_bel, df_ops)

    # ── Post-transform enrichment (butuh cross-table) ──
    df_prod = _enrich_products(df_prod, df_tx)

    conn = get_connection()
    try:
        df_tx.to_sql("transactions", conn, if_exists="replace", index=False)
        df_prod.to_sql("products", conn, if_exists="replace", index=False)
        df_bel.to_sql("belanja", conn, if_exists="replace", index=False)
        df_ops.to_sql("operasional", conn, if_exists="replace", index=False)

        # Buat index untuk kolom yang sering difilter
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tx_month ON transactions(Month_Num)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tx_date ON transactions(Transaction_Date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tx_category ON transactions(Category)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tx_product ON transactions(Product_Name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tx_weekend ON transactions(Is_Weekend)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tx_tier ON transactions(Revenue_Tier)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_bel_month ON belanja(Month_Num)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ops_month ON operasional(Month_Num)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_prod_tier ON products(Performance_Tier)")
        conn.commit()

        # Verifikasi
        for tbl in ["transactions", "products", "belanja", "operasional"]:
            count = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            print(f"[ETL] Tabel '{tbl}': {count} baris")

        print(f"[ETL] Database tersimpan: {get_db_path()}")
    finally:
        conn.close()


# ════════════════════════════════════════════════════════════════
# TRANSFORM FUNCTIONS
# ════════════════════════════════════════════════════════════════

def _transform_transactions(xls: pd.ExcelFile) -> pd.DataFrame:
    df = pd.read_excel(xls, sheet_name="Transactions")
    df.columns = df.columns.str.strip()

    # Parse date
    df["Transaction Date"] = pd.to_datetime(
        df["Transaction Date"], dayfirst=True, errors="coerce"
    )
    df = df.dropna(subset=["Transaction Date"])

    # Feature engineering — temporal
    df["Date"] = df["Transaction Date"].dt.date
    df["Year"] = df["Transaction Date"].dt.year
    df["Month_Num"] = df["Transaction Date"].dt.month
    df["Month"] = df["Month_Num"].map(NUM_TO_BULAN)

    iso = df["Transaction Date"].dt.isocalendar()
    df["Week"] = iso.week.astype(int)
    df["Year_Week"] = iso.year.astype(str) + "-W" + iso.week.astype(str)

    df["Week_Start"] = df["Transaction Date"] - pd.to_timedelta(
        df["Transaction Date"].dt.weekday, unit="D"
    )

    df["Day_Num"] = df["Transaction Date"].dt.dayofweek  # 0=Senin, 6=Minggu

    # ── ENRICHMENT: Is_Weekend ──
    df["Is_Weekend"] = (df["Day_Num"] >= 5).astype(int)

    # ── ENRICHMENT: Hour & Time_Slot ──
    if "Transaction Time" in df.columns:
        hour_parsed = pd.to_datetime(
            df["Transaction Time"], format="%H:%M:%S", errors="coerce"
        ).dt.hour
        df["Hour"] = hour_parsed
        df["Time_Slot"] = pd.cut(
            hour_parsed,
            bins=[-1, 8, 11, 14, 17, 24],
            labels=["Pagi Awal", "Pagi", "Siang", "Sore", "Malam"]
        ).astype(str).replace("nan", "Unknown")
    else:
        df["Hour"] = None
        df["Time_Slot"] = "Unknown"

    # ── ENRICHMENT: Revenue_Tier ──
    q33 = df["Total Price Idr"].quantile(0.33)
    q66 = df["Total Price Idr"].quantile(0.66)
    df["Revenue_Tier"] = np.where(
        df["Total Price Idr"] >= q66, "Tinggi",
        np.where(df["Total Price Idr"] >= q33, "Sedang", "Rendah")
    )

    # Konversi datetime ke string untuk SQLite compatibility
    df["Transaction_Date"] = df["Transaction Date"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df["Date_Str"] = df["Transaction Date"].dt.strftime("%Y-%m-%d")
    df["Week_Start_Str"] = df["Week_Start"].dt.strftime("%Y-%m-%d")

    # Rename kolom dengan spasi agar lebih SQL-friendly
    df = df.rename(columns={
        "Transaction Id":   "Transaction_Id",
        "Transaction Date": "Transaction_Date_Orig",
        "Transaction Time": "Transaction_Time",
        "Day Of Week":      "Day_Of_Week",
        "Product Name":     "Product_Name",
        "Unit Price Idr":   "Unit_Price_Idr",
        "Total Price Idr":  "Total_Price_Idr",
        "Payment Method":   "Payment_Method",
    })

    # Drop kolom datetime (SQLite tidak support native datetime)
    df = df.drop(columns=["Transaction_Date_Orig", "Week_Start"], errors="ignore")

    return df


def _transform_products(xls: pd.ExcelFile) -> pd.DataFrame:
    df = pd.read_excel(xls, sheet_name="Daftar Produk")
    df.columns = df.columns.str.strip()

    # ── ENRICHMENT: Profit_Per_Unit ──
    harga = pd.to_numeric(df.get("Harga Satuan (IDR)", 0), errors="coerce").fillna(0)
    modal = pd.to_numeric(df.get("Harga Modal (IDR)", 0), errors="coerce").fillna(0)
    df["Profit_Per_Unit"] = (harga - modal).astype(int)

    # Rename untuk SQL-friendly
    df = df.rename(columns={
        "Nama Produk":       "Nama_Produk",
        "Harga Satuan (IDR)": "Harga_Satuan_IDR",
        "Harga Modal (IDR)":  "Harga_Modal_IDR",
        "Margin Kotor (%)":   "Margin_Kotor_Pct",
    })

    return df


def _enrich_products(df_prod: pd.DataFrame, df_tx: pd.DataFrame) -> pd.DataFrame:
    """
    Enrichment yang butuh data transaksi: Total_Qty_Sold, Total_Revenue,
    Total_Profit, Performance_Tier.
    """
    if df_tx.empty or "Product_Name" not in df_tx.columns:
        df_prod["Total_Qty_Sold"] = 0
        df_prod["Total_Revenue"] = 0
        df_prod["Total_Profit"] = 0
        df_prod["Performance_Tier"] = "Low"
        return df_prod

    tx_agg = df_tx.groupby("Product_Name").agg(
        Total_Qty_Sold=("Quantity", "sum"),
        Total_Revenue=("Total_Price_Idr", "sum"),
    ).reset_index()

    df_prod = df_prod.merge(
        tx_agg, left_on="Nama_Produk", right_on="Product_Name", how="left"
    ).drop(columns=["Product_Name"], errors="ignore")

    df_prod["Total_Qty_Sold"] = df_prod["Total_Qty_Sold"].fillna(0).astype(int)
    df_prod["Total_Revenue"] = df_prod["Total_Revenue"].fillna(0).astype(int)
    df_prod["Total_Profit"] = (
        df_prod["Profit_Per_Unit"] * df_prod["Total_Qty_Sold"]
    ).astype(int)

    # ── Performance_Tier: Top 33% = Top, Middle 33% = Middle, Bottom = Low ──
    rev = df_prod["Total_Revenue"]
    q66 = rev.quantile(0.66)
    q33 = rev.quantile(0.33)
    df_prod["Performance_Tier"] = np.where(
        rev >= q66, "Top",
        np.where(rev >= q33, "Middle", "Low")
    )

    return df_prod


def _transform_belanja(xls: pd.ExcelFile) -> pd.DataFrame:
    df = pd.read_excel(xls, sheet_name="Pengeluaran Belanja")
    df.columns = df.columns.str.strip()

    df["Tanggal"] = pd.to_datetime(
        df["Tanggal"], dayfirst=True, errors="coerce"
    )
    df = df.dropna(subset=["Tanggal"])

    df["Year"] = df["Tanggal"].dt.year
    df["Month_Num"] = df["Tanggal"].dt.month
    df["Month"] = df["Month_Num"].map(NUM_TO_BULAN)

    # ── ENRICHMENT: Cost_Type ──
    kat = df.get("Kategori Belanja", pd.Series(dtype=str)).fillna("").str.lower()
    df["Cost_Type"] = np.where(
        kat.str.contains("packaging|supplies", na=False),
        "Packaging & Supplies",
        "Bahan Baku"
    )

    # String date untuk SQLite
    df["Tanggal_Str"] = df["Tanggal"].dt.strftime("%Y-%m-%d")
    df = df.drop(columns=["Tanggal"])

    # Rename
    df = df.rename(columns={
        "Kategori Belanja": "Kategori_Belanja",
        "Nama Item":        "Nama_Item",
        "Harga Satuan (IDR)": "Harga_Satuan_IDR",
        "Total Biaya (IDR)":  "Total_Biaya_IDR",
    })

    return df


def _transform_operasional(xls: pd.ExcelFile) -> pd.DataFrame:
    df = pd.read_excel(xls, sheet_name="Biaya Operasional")
    df.columns = df.columns.str.strip()

    # Merge kategori Utilitas → Operasional
    if "Kategori" in df.columns:
        df["Kategori"] = df["Kategori"].replace("Utilitas", "Operasional")

    # Mapping bulan → angka
    df["Month_Num"] = df["Bulan"].map(BULAN_TO_NUM)
    df["Month"] = df["Month_Num"].map(NUM_TO_BULAN)

    if "Tahun" in df.columns:
        df["Year"] = df["Tahun"]

    # Tanggal Pembayaran → string
    if "Tanggal Pembayaran" in df.columns:
        df["Tanggal Pembayaran"] = pd.to_datetime(
            df["Tanggal Pembayaran"], errors="coerce"
        )
        df["Tanggal_Pembayaran_Str"] = df["Tanggal Pembayaran"].dt.strftime("%Y-%m-%d")
        if "Year" not in df.columns:
            df["Year"] = df["Tanggal Pembayaran"].dt.year
        df = df.drop(columns=["Tanggal Pembayaran"])

    if "Year" not in df.columns:
        df["Year"] = pd.Timestamp.now().year

    # Rename
    df = df.rename(columns={
        "Jumlah (IDR)": "Jumlah_IDR",
    })

    return df


def _split_expenses_by_category(
    df_belanja: pd.DataFrame,
    df_ops: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Pastikan database mengikuti aturan kategori:
    kategori di KATEGORI_OPS masuk tabel operasional, kategori lain masuk belanja.
    """
    belanja_ops_mask = df_belanja["Kategori_Belanja"].apply(_is_operational_category)
    ops_ops_mask = df_ops["Kategori"].apply(_is_operational_category)

    belanja_keep = df_belanja[~belanja_ops_mask].copy()
    ops_keep = df_ops[ops_ops_mask].copy()

    belanja_to_ops = _belanja_rows_to_ops(df_belanja[belanja_ops_mask], df_ops.columns)
    ops_to_belanja = _ops_rows_to_belanja(df_ops[~ops_ops_mask], df_belanja.columns)

    final_belanja = pd.concat([belanja_keep, ops_to_belanja], ignore_index=True)
    final_ops = pd.concat([ops_keep, belanja_to_ops], ignore_index=True)

    return final_belanja, final_ops


def _belanja_rows_to_ops(rows: pd.DataFrame, target_columns) -> pd.DataFrame:
    if rows.empty:
        return pd.DataFrame(columns=target_columns)

    out = pd.DataFrame()
    out["No"] = rows.get("No")
    out["Bulan"] = rows.get("Bulan")
    out["Kategori"] = rows["Kategori_Belanja"]
    out["Keterangan"] = rows.get("Nama_Item", rows["Kategori_Belanja"]).fillna(rows["Kategori_Belanja"])
    out["Jumlah_IDR"] = rows["Total_Biaya_IDR"]
    out["Month_Num"] = rows.get("Month_Num")
    out["Month"] = rows.get("Month")
    out["Tanggal_Pembayaran_Str"] = rows.get("Tanggal_Str")
    if "Year" in target_columns:
        out["Year"] = rows.get("Year")

    return out.reindex(columns=target_columns)


def _ops_rows_to_belanja(rows: pd.DataFrame, target_columns) -> pd.DataFrame:
    if rows.empty:
        return pd.DataFrame(columns=target_columns)

    out = pd.DataFrame()
    out["No"] = rows.get("No")
    out["Bulan"] = rows.get("Bulan")
    out["Kategori_Belanja"] = rows["Kategori"]
    out["Nama_Item"] = rows.get("Keterangan", rows["Kategori"]).fillna(rows["Kategori"])
    out["Jumlah"] = 1
    out["Satuan"] = "bulan"
    out["Harga_Satuan_IDR"] = rows["Jumlah_IDR"]
    out["Total_Biaya_IDR"] = rows["Jumlah_IDR"]
    out["Keterangan"] = rows.get("Keterangan")
    out["Year"] = rows.get("Year", pd.Timestamp.now().year)
    out["Month_Num"] = rows.get("Month_Num")
    out["Month"] = rows.get("Month")
    out["Cost_Type"] = "Belanja"
    out["Tanggal_Str"] = rows.get("Tanggal_Pembayaran_Str")

    return out.reindex(columns=target_columns)
