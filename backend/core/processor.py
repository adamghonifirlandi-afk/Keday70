import pandas as pd
import numpy as np
import calendar
from backend.config.constants import KATEGORI_OPS


def _normalize_category(value) -> str:
    text = str(value or "").strip().lower()
    return (
        text.replace("&", "dan")
        .replace("-", " ")
        .replace("_", " ")
        .replace("  ", " ")
    )


def is_operational_category(category) -> bool:
    normalized_ops = {_normalize_category(item) for item in KATEGORI_OPS}
    return _normalize_category(category) in normalized_ops


def expense_group_label(category) -> str:
    return "Operasional" if is_operational_category(category) else "Belanja"


def _days_in_month_for(df_belanja: pd.DataFrame, df_ops: pd.DataFrame, tx: pd.DataFrame) -> dict:
    """
    Kembalikan dict {month_num: days_in_month} untuk setiap bulan yang ada
    di pengeluaran. Dipakai untuk konversi ke basis harian.
    """
    months = set()
    if not df_belanja.empty and "Month_Num" in df_belanja.columns:
        months.update(df_belanja["Month_Num"].dropna().unique())
    if not df_ops.empty and "Month_Num" in df_ops.columns:
        months.update(df_ops["Month_Num"].dropna().unique())
    if not tx.empty and "Month_Num" in tx.columns:
        months.update(tx["Month_Num"].dropna().unique())

    # Ambil tahun dari tx jika ada, fallback ke tahun saat ini
    year = pd.Timestamp.now().year
    if not tx.empty and "Transaction Date" in tx.columns:
        year = int(tx["Transaction Date"].dt.year.mode()[0])

    return {int(m): calendar.monthrange(year, int(m))[1] for m in months if pd.notnull(m)}


def get_daily_expense(belanja: pd.DataFrame, ops: pd.DataFrame, tx: pd.DataFrame) -> dict:
    """
    Hitung total pengeluaran harian dengan cara:
      - Ambil total belanja per bulan -> bagi hari dalam bulan itu
      - Ambil total ops per bulan     -> bagi hari dalam bulan itu
    Hasilnya: total rata-rata harian yang bisa dikalikan jumlah hari periode.

    Return:
        {
          'daily_belanja': float,  # rata-rata belanja per hari
          'daily_ops'    : float,  # rata-rata ops per hari
          'days_map'     : dict,   # {month_num: days_in_month}
          'months'       : list,   # daftar bulan unik
        }
    """
    days_map = _days_in_month_for(belanja, ops, tx)

    daily_belanja = 0.0
    daily_ops = 0.0

    if not belanja.empty:
        for (category, m), grp in belanja.groupby(["Kategori Belanja", "Month_Num"], dropna=False):
            d = days_map.get(int(m), 30)
            daily_value = grp["Total Biaya (IDR)"].sum() / d
            if is_operational_category(category):
                daily_ops += daily_value
            else:
                daily_belanja += daily_value

    if not ops.empty:
        for (category, m), grp in ops.groupby(["Kategori", "Month_Num"], dropna=False):
            d = days_map.get(int(m), 30)
            daily_value = grp["Jumlah (IDR)"].sum() / d
            if is_operational_category(category):
                daily_ops += daily_value
            else:
                daily_belanja += daily_value

    return {
        "daily_belanja": daily_belanja,
        "daily_ops":     daily_ops,
        "days_map":      days_map,
        "months":        sorted(days_map.keys()),
    }


def compute_kpi(tx: pd.DataFrame, belanja: pd.DataFrame, ops: pd.DataFrame, mode: str = "Bulan", value: str = None) -> dict:
    total_revenue   = int(tx["Total Price Idr"].sum())
    total_tx        = int(len(tx))

    # ── Hitung hari dalam periode ────────────────────────────────────────────
    # Untuk mode Bulan: gunakan hari sesungguhnya bulan tsb
    # Untuk mode Minggu: 7 hari
    # Untuk mode Hari  : 1 hari
    days_map = _days_in_month_for(belanja, ops, tx)

    if mode == "Hari":
        days_in_period = 1
    elif mode == "Minggu":
        days_in_period = 7
    else:
        # Bulan — jumlah hari sesungguhnya bulan yang dipilih
        if not tx.empty:
            m = int(tx["Transaction Date"].dt.month.mode()[0])
            y = int(tx["Transaction Date"].dt.year.mode()[0])
            days_in_period = calendar.monthrange(y, m)[1]
        elif days_map:
            # fallback: rata-rata hari dari bulan-bulan yang ada
            days_in_period = int(np.mean(list(days_map.values())))
        else:
            days_in_period = 30

    # ── Hitung belanja & ops dengan konversi harian ──────────────────────────
    # Setiap pengeluaran (baik dicatat harian maupun bulanan) dikonversi ke
    # basis harian terlebih dahulu (total_bulan / hari_dalam_bulan),
    # lalu dikali jumlah hari dalam periode yang dipilih.
    de = get_daily_expense(belanja, ops, tx)
    total_belanja = int(de["daily_belanja"] * days_in_period)
    total_ops     = int(de["daily_ops"]     * days_in_period)

    total_expense   = total_belanja + total_ops
    estimasi_laba   = total_revenue - total_expense
    avg_order       = int(tx["Total Price Idr"].mean()) if total_tx > 0 else 0
    avg_daily_tx    = round(total_tx / max(days_in_period, 1), 1)

    return {
        "total_revenue":  total_revenue,
        "total_tx":       total_tx,
        "total_belanja":  total_belanja,
        "total_ops":      total_ops,
        "total_expense":  total_expense,
        "estimasi_laba":  estimasi_laba,
        "avg_order":      avg_order,
        "avg_daily_tx":   avg_daily_tx,
        "margin_pct":     round(estimasi_laba / total_revenue * 100, 1) if total_revenue > 0 else 0,
    }

def revenue_by_period(tx: pd.DataFrame, mode: str, context_year: int = None, context_month: int = None) -> pd.DataFrame:
    import calendar
    import datetime
    
    # Defaults jika context tidak ada tapi tx ada
    if context_year is None and not tx.empty and "Transaction Date" in tx.columns:
        context_year = int(tx["Transaction Date"].dt.year.mode()[0])
    if context_year is None:
        context_year = datetime.date.today().year

    if context_month is None and not tx.empty and "Month_Num" in tx.columns:
        context_month = int(tx["Month_Num"].mode()[0])
    if context_month is None:
        context_month = 1
        
    if mode == "Hari":
        if tx.empty or "Transaction Date" not in tx.columns:
            grp = pd.DataFrame(columns=["Periode", "Revenue", "Count"])
        else:
            grp = tx.groupby(tx["Transaction Date"].dt.date)["Total Price Idr"].agg(["sum", "count"]).reset_index()
            grp.columns = ["Periode", "Revenue", "Count"]

        num_days = calendar.monthrange(context_year, context_month)[1]
        all_days = [datetime.date(context_year, context_month, d) for d in range(1, num_days + 1)]
        full_df = pd.DataFrame({"Periode": all_days})
        
        grp = full_df.merge(grp, on="Periode", how="left")
        grp["Revenue"] = grp["Revenue"].fillna(0).astype(int)
        grp["Count"] = grp["Count"].fillna(0).astype(int)
        grp["Periode"] = pd.to_datetime(grp["Periode"])
        grp["Label"] = grp["Periode"].dt.strftime("%d %b")

    elif mode == "Minggu":
        if tx.empty or "Week_Start" not in tx.columns:
            grp = pd.DataFrame(columns=["Periode", "Revenue", "Count"])
        else:
            grp = tx.groupby("Week_Start")["Total Price Idr"].agg(["sum", "count"]).reset_index()
            grp.columns = ["Periode", "Revenue", "Count"]
            grp["Periode"] = pd.to_datetime(grp["Periode"])

        num_days = calendar.monthrange(context_year, context_month)[1]
        weeks = set()
        for d in range(1, num_days + 1):
            dt = datetime.date(context_year, context_month, d)
            monday = dt - datetime.timedelta(days=dt.weekday())
            weeks.add(monday)
            
        full_df = pd.DataFrame({"Periode": pd.to_datetime(list(weeks))})
        full_df = full_df.sort_values("Periode")
        
        grp = full_df.merge(grp, on="Periode", how="left")
        grp["Revenue"] = grp["Revenue"].fillna(0).astype(int)
        grp["Count"] = grp["Count"].fillna(0).astype(int)
        grp["Label"] = "W" + (grp["Periode"].dt.isocalendar().week.astype(str))

    else:
        from backend.config.constants import BULAN_SHORT, BULAN_ORDER
        if tx.empty or "Month" not in tx.columns:
            grp = pd.DataFrame(columns=["Periode", "Revenue", "Count"])
        else:
            grp = tx.groupby("Month")["Total Price Idr"].agg(["sum", "count"]).reset_index()
            grp.columns = ["Periode", "Revenue", "Count"]
            
        full_months = pd.DataFrame({"Periode": BULAN_ORDER})
        grp = full_months.merge(grp, on="Periode", how="left")
        grp["Revenue"] = grp["Revenue"].fillna(0).astype(int)
        grp["Count"] = grp["Count"].fillna(0).astype(int)
        
        grp["Sort"] = grp["Periode"].map({b: i for i, b in enumerate(BULAN_ORDER)})
        grp = grp.sort_values("Sort")
        grp["Label"] = grp["Periode"].map(BULAN_SHORT)
    return grp


def revenue_by_year(tx: pd.DataFrame) -> pd.DataFrame:
    """
    Agregasi revenue dan transaksi per tahun untuk mode 'Semua Tahun'.
    Menampilkan 10 tahun terakhir hingga tahun saat ini (termasuk tahun tanpa data = 0).
    """
    current_year = pd.Timestamp.now().year
    year_range = list(range(current_year - 10, current_year + 1))  # 11 tahun

    if tx.empty or "Year" not in tx.columns:
        return pd.DataFrame({
            "Periode": year_range,
            "Revenue": [0] * len(year_range),
            "Count": [0] * len(year_range),
            "Label": [str(y) for y in year_range],
        })

    grp = tx.groupby("Year")["Total Price Idr"].agg(["sum", "count"]).reset_index()
    grp.columns = ["Year", "Revenue", "Count"]

    # Buat DataFrame lengkap dengan semua tahun dalam rentang
    full = pd.DataFrame({"Year": year_range})
    full = full.merge(grp, on="Year", how="left")
    full["Revenue"] = full["Revenue"].fillna(0).astype(int)
    full["Count"] = full["Count"].fillna(0).astype(int)
    full["Periode"] = full["Year"]
    full["Label"] = full["Year"].astype(str)

    return full.sort_values("Year").reset_index(drop=True)


def revenue_by_category(tx: pd.DataFrame) -> pd.DataFrame:
    return (
        tx.groupby("Category")["Total Price Idr"]
        .sum().reset_index()
        .rename(columns={"Category": "Kategori", "Total Price Idr": "Revenue"})
    )


def qty_by_category(tx: pd.DataFrame) -> pd.DataFrame:
    return (
        tx.groupby("Category")["Quantity"]
        .sum().reset_index()
        .rename(columns={"Category": "Kategori", "Quantity": "Qty"})
        .sort_values("Qty", ascending=False)
    )


def revenue_by_payment(tx: pd.DataFrame) -> pd.DataFrame:
    return (
        tx.groupby("Payment Method")["Transaction Id"]
        .count().reset_index()
        .rename(columns={"Payment Method": "Metode", "Transaction Id": "Jumlah"})
    )


def revenue_by_session(tx: pd.DataFrame) -> pd.DataFrame:
    from backend.config.constants import SESSION_ORDER
    grp = (
        tx.groupby("Session")["Total Price Idr"]
        .sum().reset_index()
        .rename(columns={"Session": "Sesi", "Total Price Idr": "Revenue"})
    )
    grp["Sort"] = grp["Sesi"].map({s: i for i, s in enumerate(SESSION_ORDER)})
    return grp.sort_values("Sort")


def top_products(tx: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    return (
        tx.groupby("Product Name")
        .agg(
            Revenue=("Total Price Idr", "sum"),
            Qty=("Quantity", "sum"),
            Transaksi=("Transaction Id", "count"),
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
        .head(n)
    )


def product_analysis(products: pd.DataFrame, tx: pd.DataFrame) -> pd.DataFrame:
    product_cols = {
        "Nama Produk": "Product Name",
        "Kategori": "Category",
        "Harga Satuan (IDR)": "Price",
        "Harga Modal (IDR)": "Cost",
        "Margin Kotor (%)": "MarginPct",
        "Status": "Status",
    }

    base = products.rename(columns=product_cols).copy()

    for col in ["Product Name", "Category", "Status"]:
        if col in base.columns:
            base[col] = base[col].fillna("").astype(str).str.strip()

    for col in ["Price", "Cost", "MarginPct"]:
        if col in base.columns:
            base[col] = pd.to_numeric(base[col], errors="coerce").fillna(0)

    if "Status" in base.columns:
        base = base[base["Status"].str.lower().ne("nonaktif")]

    tx_summary = (
        tx.groupby("Product Name")
        .agg(
            Revenue=("Total Price Idr", "sum"),
            Qty=("Quantity", "sum"),
            Transactions=("Transaction Id", "count"),
        )
        .reset_index()
    )

    merged = base.merge(tx_summary, on="Product Name", how="left")

    merged["Revenue"] = merged["Revenue"].fillna(0).astype(int)
    merged["Qty"] = merged["Qty"].fillna(0).astype(int)
    merged["Transactions"] = merged["Transactions"].fillna(0).astype(int)
    merged["EstimatedProfit"] = (merged["Price"] - merged["Cost"]) * merged["Qty"]
    merged["EstimatedProfit"] = merged["EstimatedProfit"].fillna(0).astype(int)
    merged["MarginPct"] = merged["MarginPct"].round(1)

    preferred_cols = [
        "Product Name",
        "Category",
        "Price",
        "Cost",
        "MarginPct",
        "Status",
        "Revenue",
        "Qty",
        "Transactions",
        "EstimatedProfit",
    ]
    existing_cols = [col for col in preferred_cols if col in merged.columns]

    return merged[existing_cols].sort_values(
        ["Revenue", "MarginPct", "Product Name"],
        ascending=[False, False, True]
    )


def expense_breakdown(belanja: pd.DataFrame, ops: pd.DataFrame) -> pd.DataFrame:
    b = (
        belanja.groupby("Kategori Belanja")["Total Biaya (IDR)"]
        .sum().reset_index()
        .rename(columns={"Kategori Belanja": "Kategori", "Total Biaya (IDR)": "Jumlah"})
    )
    o = (
        ops.groupby("Kategori")["Jumlah (IDR)"]
        .sum().reset_index()
        .rename(columns={"Jumlah (IDR)": "Jumlah"})
    )
    combined = pd.concat([b, o], ignore_index=True)
    if combined.empty:
        return combined.assign(Tipe=[])

    combined["Tipe"] = combined["Kategori"].apply(expense_group_label)
    return (
        combined.groupby(["Kategori", "Tipe"], as_index=False)["Jumlah"]
        .sum()
        .sort_values("Jumlah", ascending=False)
    )


def profit_waterfall(kpi: dict) -> pd.DataFrame:
    rows = [
        {"Komponen": "Pendapatan",        "Nilai": kpi["total_revenue"],  "Tipe": "revenue"},
        {"Komponen": "Bahan Baku",        "Nilai": -kpi["total_belanja"], "Tipe": "expense"},
        {"Komponen": "Biaya Operasional", "Nilai": -kpi["total_ops"],     "Tipe": "expense"},
        {"Komponen": "Laba Bersih",       "Nilai": kpi["estimasi_laba"],  "Tipe": "profit"},
    ]
    return pd.DataFrame(rows)


def revenue_by_day_of_week(tx: pd.DataFrame) -> pd.DataFrame:
    from backend.config.constants import HARI_ORDER
    grp = (
        tx.groupby("Day Of Week")["Total Price Idr"]
        .sum().reset_index()
        .rename(columns={"Day Of Week": "Hari", "Total Price Idr": "Revenue"})
    )
    grp["Sort"] = grp["Hari"].map({h: i for i, h in enumerate(HARI_ORDER)})
    return grp.sort_values("Sort")
