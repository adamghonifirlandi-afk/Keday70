from fastapi import APIRouter, Query, HTTPException
import pandas as pd
import json
from typing import Optional

from backend.core.loader import load_all
from backend.core.filter import apply_filter, get_filter_options
from backend.core.processor import (
    compute_kpi, revenue_by_period, revenue_by_category,
    revenue_by_payment, revenue_by_session, top_products, profit_waterfall,
    expense_breakdown, get_daily_expense, product_analysis, qty_by_category,
    expense_group_label, revenue_by_year
)

router = APIRouter()

def df_to_dict(df: pd.DataFrame) -> list:
    if df.empty:
        return []
    return json.loads(df.to_json(orient="records", date_format="iso"))


def _parse_year(year: Optional[str]) -> Optional[int]:
    """Parse year query param: 'Semua'/None → None, '2024' → 2024."""
    if not year or year == "Semua":
        return None
    try:
        return int(year)
    except (ValueError, TypeError):
        return None


def _filter_by_year(data: dict[str, pd.DataFrame], year_int: Optional[int]) -> dict[str, pd.DataFrame]:
    """Pre-filter data by year (used for 'all_data' scoping in trend contexts)."""
    if year_int is None:
        return data
    result = {}
    for key, df in data.items():
        if key == "products":
            result[key] = df
        elif "Year" in df.columns:
            result[key] = df[df["Year"] == year_int].copy()
        else:
            result[key] = df
    return result


@router.get("/data")
def get_dashboard_data(
    mode: str = Query("Bulan", description="Hari, Minggu, atau Bulan"),
    value: str = Query(None, description="Nilai filter spesifik"),
    year: str = Query(None, description="Tahun filter: 2024, 2025, atau Semua")
):
    all_data = load_all()
    year_int = _parse_year(year)

    try:
        filtered = apply_filter(all_data, mode, value, year=year_int)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    tx = filtered["transactions"]
    belanja = filtered["belanja"]
    ops = filtered["operasional"]
    products = all_data["products"]

    kpi = compute_kpi(tx, belanja, ops, mode, value)
    product_df = product_analysis(products, tx)

    # ── Trend chart: mode "Semua Tahun" → agregasi tahunan ──────────────
    is_all_years = year_int is None
    if is_all_years and (not value or value == "Semua"):
        # Semua Tahun + Semua filter → trend tahunan
        revenue_trend = df_to_dict(revenue_by_year(all_data["transactions"]))
    else:
        # Tahun tertentu → trend sesuai mode (bulanan/mingguan/harian)
        # Scope all_data ke tahun yang dipilih agar trend tidak bocor ke tahun lain
        scoped_data = _filter_by_year(all_data, year_int)

        # Smart Trend Aggregation Context (to prevent 1-dot charts)
        tx_trend = tx
        m_val = None
        if value and value != "Semua":
            from backend.config.constants import BULAN_TO_NUM
            if mode == "Bulan":
                tx_trend = scoped_data["transactions"]
            elif mode == "Minggu" and "-W" in str(value):
                try:
                    from datetime import datetime
                    m_val = datetime.strptime(f"{value}-1", "%G-W%V-%u").month
                except:
                    m_val = tx["Month_Num"].iloc[0] if not tx.empty else 1
            elif mode == "Hari":
                if value in BULAN_TO_NUM:
                    m_val = BULAN_TO_NUM[value]
                else:
                    try:
                        m_val = pd.to_datetime(value).month
                    except:
                        m_val = tx["Month_Num"].iloc[0] if not tx.empty else 1

            if m_val is not None:
                if not scoped_data["transactions"].empty:
                    tx_trend = scoped_data["transactions"][scoped_data["transactions"]["Month_Num"] == m_val]
                else:
                    tx_trend = scoped_data["transactions"]

        revenue_trend = df_to_dict(revenue_by_period(tx_trend, mode, context_year=year_int, context_month=m_val))

    return {
        "kpi": kpi,
        "is_yearly_trend": is_all_years and (not value or value == "Semua"),
        "charts": {
            "revenue": revenue_trend,
            "category": df_to_dict(revenue_by_category(tx)),
            "category_qty": df_to_dict(qty_by_category(tx)),
            "payment": df_to_dict(revenue_by_payment(tx)),
            "session": df_to_dict(revenue_by_session(tx)),
            "top_products": df_to_dict(top_products(tx, 5)),
            "product_revenue_top": df_to_dict(product_df.head(8)),
            "product_analysis": df_to_dict(product_df),
            "waterfall": df_to_dict(profit_waterfall(kpi))
        }
    }

@router.get("/filter-options")
def get_options(
    mode: str = Query("Bulan"),
    year: str = Query(None)
):
    all_data = load_all()
    year_int = _parse_year(year)
    return get_filter_options(all_data, mode, year=year_int)

@router.get("/products")
def get_products(
    mode: str = Query("Bulan"),
    value: str = Query(None),
    year: str = Query(None)
):
    all_data = load_all()
    year_int = _parse_year(year)
    filtered = apply_filter(all_data, mode, value, year=year_int)
    tx = filtered["transactions"]
    products = all_data["products"]

    product_df = product_analysis(products, tx)
    sold_df = product_df[product_df["Revenue"] > 0].copy()
    category_qty = qty_by_category(tx)

    avg_margin = round(float(sold_df["MarginPct"].mean()), 1) if not sold_df.empty else 0
    total_qty = int(sold_df["Qty"].sum()) if not sold_df.empty else 0

    best_seller = None
    if not sold_df.empty:
        row = sold_df.sort_values("Qty", ascending=False).iloc[0]
        best_seller = {
            "Product Name": row["Product Name"],
            "Revenue": int(row["Revenue"]),
            "Qty": int(row["Qty"]),
        }

    highest_margin = None
    if not sold_df.empty:
        row = sold_df.sort_values(["MarginPct", "Revenue"], ascending=[False, False]).iloc[0]
        highest_margin = {
            "Product Name": row["Product Name"],
            "MarginPct": float(row["MarginPct"]),
            "Revenue": int(row["Revenue"]),
        }

    return {
        "kpi": {
            "sold_products": int(len(sold_df)),
            "total_qty": total_qty,
            "avg_margin": avg_margin,
            "best_seller": best_seller,
            "highest_margin": highest_margin,
        },
        "top_products": df_to_dict(sold_df.head(8)),
        "category_qty": df_to_dict(category_qty),
        # Return all sold products so table rows align with sold_products KPI
        "products": df_to_dict(sold_df),
    }

@router.get("/profit")
def get_profit(
    mode: str = Query("Bulan"),
    value: str = Query(None),
    year: str = Query(None)
):
    import calendar
    all_data = load_all()
    year_int = _parse_year(year)
    filtered = apply_filter(all_data, mode, value, year=year_int)
    tx = filtered["transactions"]
    belanja = filtered["belanja"]
    ops = filtered["operasional"]

    kpi = compute_kpi(tx, belanja, ops, mode, value)
    margin_pct = kpi["margin_pct"]

    # Waterfall data (clean, no simulation labels)
    waterfall = [
        {"Komponen": "Pendapatan", "Nilai": kpi["total_revenue"], "Tipe": "revenue"},
        {"Komponen": "Bahan Baku", "Nilai": -kpi["total_belanja"], "Tipe": "expense"},
        {"Komponen": "Biaya Ops", "Nilai": -kpi["total_ops"], "Tipe": "expense"},
        {"Komponen": "Laba Bersih", "Nilai": kpi["estimasi_laba"], "Tipe": "profit"},
    ]

    # ── Trend context: scope ke tahun yang dipilih ──────────────────────
    scoped_data = _filter_by_year(all_data, year_int)
    tx_t = scoped_data["transactions"]
    bel_t = scoped_data["belanja"]
    ops_t = scoped_data["operasional"]

    is_all_years = year_int is None
    if is_all_years and (not value or value == "Semua"):
        # Semua Tahun → trend margin tahunan
        margin_trend = _build_yearly_margin_trend(all_data)
    else:
        # Tahun tertentu → trend sesuai mode
        m_val = None
        if value and value != "Semua":
            from backend.config.constants import BULAN_TO_NUM
            if mode == "Minggu" and "-W" in str(value):
                try:
                    from datetime import datetime
                    m_val = datetime.strptime(f"{value}-1", "%G-W%V-%u").month
                except:
                    m_val = tx["Month_Num"].iloc[0] if not tx.empty else 1
            elif mode == "Hari":
                if value in BULAN_TO_NUM:
                    m_val = BULAN_TO_NUM[value]
                else:
                    try:
                        m_val = pd.to_datetime(value).month
                    except:
                        m_val = tx["Month_Num"].iloc[0] if not tx.empty else 1

            if m_val is not None:
                if not scoped_data["transactions"].empty:
                    tx_t = scoped_data["transactions"][scoped_data["transactions"]["Month_Num"] == m_val]
                else:
                    tx_t = scoped_data["transactions"]

        margin_trend = _build_margin_trend(tx_t, bel_t, ops_t, mode, calendar, context_year=year_int, context_month=m_val)

    # Summary table
    gross_profit = kpi["total_revenue"] - kpi["total_belanja"]
    summary = [
        {"Komponen": "Pendapatan Kotor", "Nilai": kpi["total_revenue"], "Format": "currency", "Sign": 1},
        {"Komponen": "HPP / Bahan Baku", "Nilai": -kpi["total_belanja"], "Format": "currency", "Sign": -1},
        {"Komponen": "Biaya Operasional", "Nilai": -kpi["total_ops"], "Format": "currency", "Sign": -1},
        {"Komponen": "Laba Kotor", "Nilai": gross_profit, "Format": "currency", "Sign": 1},
        {"Komponen": "Laba Bersih", "Nilai": kpi["estimasi_laba"], "Format": "currency", "Sign": 1},
        {"Komponen": "Margin Laba Bersih", "Nilai": margin_pct, "Format": "percent", "Sign": 1},
    ]

    return {
        "kpi": {**kpi, "margin_pct": margin_pct},
        "waterfall": waterfall,
        "margin_trend": margin_trend,
        "is_yearly_trend": is_all_years and (not value or value == "Semua"),
        "summary": summary
    }


def _build_yearly_margin_trend(all_data: dict) -> list:
    """Build margin trend per tahun untuk mode Semua Tahun."""
    import calendar
    current_year = pd.Timestamp.now().year
    year_range = list(range(current_year - 10, current_year + 1))
    margin_trend = []

    for y in year_range:
        tx_y = all_data["transactions"]
        bel_y = all_data["belanja"]
        ops_y = all_data["operasional"]

        if "Year" in tx_y.columns:
            tx_y = tx_y[tx_y["Year"] == y]
        if "Year" in bel_y.columns:
            bel_y = bel_y[bel_y["Year"] == y]
        if "Year" in ops_y.columns:
            ops_y = ops_y[ops_y["Year"] == y]

        r = int(tx_y["Total Price Idr"].sum()) if not tx_y.empty else 0
        b = int(bel_y["Total Biaya (IDR)"].sum()) if not bel_y.empty and "Total Biaya (IDR)" in bel_y.columns else 0
        o = int(ops_y["Jumlah (IDR)"].sum()) if not ops_y.empty and "Jumlah (IDR)" in ops_y.columns else 0
        total_exp = b + o
        laba = r - total_exp
        margin = round(laba / r * 100, 1) if r > 0 else 0

        margin_trend.append({
            "Label": str(y),
            "Margin": margin,
            "Laba": laba
        })

    return margin_trend


def _build_margin_trend(tx_t, bel_t, ops_t, mode, calendar, context_year=None, context_month=None) -> list:
    """Build margin trend per periode (hari/minggu/bulan) — calendar based zero filling."""
    margin_trend = []
    import datetime

    # Defaults
    if context_year is None:
        if not tx_t.empty and "Transaction Date" in tx_t.columns:
            context_year = int(tx_t["Transaction Date"].dt.year.mode()[0])
        else:
            context_year = datetime.date.today().year

    if context_month is None:
        if not tx_t.empty and "Month_Num" in tx_t.columns:
            context_month = int(tx_t["Month_Num"].mode()[0])
        else:
            context_month = 1

    if mode == "Hari":
        if tx_t.empty or "Transaction Date" not in tx_t.columns:
            rev = {}
        else:
            rev = tx_t.groupby(tx_t["Transaction Date"].dt.date)["Total Price Idr"].sum().to_dict()
            
        num_days = calendar.monthrange(context_year, context_month)[1]
        
        bel_m = bel_t[bel_t["Month_Num"] == context_month]["Total Biaya (IDR)"].sum() if not bel_t.empty else 0
        ops_m = ops_t[ops_t["Month_Num"] == context_month]["Jumlah (IDR)"].sum() if not ops_t.empty else 0
        dim = num_days
        e = bel_m / dim if dim > 0 else 0
        o = ops_m / dim if dim > 0 else 0
        total_exp = e + o
            
        for d in range(1, num_days + 1):
            dt = datetime.date(context_year, context_month, d)
            r = rev.get(dt, 0)
            margin = round((r - total_exp) / r * 100, 1) if r > 0 else 0
            margin_trend.append({
                "Label": dt.strftime("%d %b"),
                "Margin": margin,
                "Laba": int(r - total_exp)
            })

    elif mode == "Minggu":
        if tx_t.empty or "Week_Start" not in tx_t.columns:
            rev = {}
        else:
            tx_copy = tx_t.copy()
            tx_copy["Week_Start_dt"] = pd.to_datetime(tx_copy["Week_Start"]).dt.date
            rev = tx_copy.groupby("Week_Start_dt")["Total Price Idr"].sum().to_dict()

        num_days = calendar.monthrange(context_year, context_month)[1]
        weeks = set()
        for d in range(1, num_days + 1):
            dt = datetime.date(context_year, context_month, d)
            monday = dt - datetime.timedelta(days=dt.weekday())
            weeks.add(monday)
            
        bel_m = bel_t[bel_t["Month_Num"] == context_month]["Total Biaya (IDR)"].sum() if not bel_t.empty else 0
        ops_m = ops_t[ops_t["Month_Num"] == context_month]["Jumlah (IDR)"].sum() if not ops_t.empty else 0
        dim = num_days
        e = (bel_m / dim) * 7 if dim > 0 else 0
        o = (ops_m / dim) * 7 if dim > 0 else 0
        total_exp = e + o

        for dt in sorted(list(weeks)):
            r = rev.get(dt, 0)
            margin = round((r - total_exp) / r * 100, 1) if r > 0 else 0
            wk_num = dt.isocalendar().week
            margin_trend.append({
                "Label": f"W{wk_num}",
                "Margin": margin,
                "Laba": int(r - total_exp)
            })

    else:
        # Mode Bulan
        from backend.config.constants import BULAN_ORDER, BULAN_SHORT, BULAN_TO_NUM
        if tx_t.empty or "Month" not in tx_t.columns:
            rev = {}
        else:
            rev = tx_t.groupby("Month")["Total Price Idr"].sum().to_dict()

        for b in BULAN_ORDER:
            m_num = BULAN_TO_NUM.get(b)
            if m_num is None:
                continue
            r = rev.get(b, 0)
            bel_m = bel_t[bel_t["Month_Num"] == m_num]["Total Biaya (IDR)"].sum() if not bel_t.empty else 0
            ops_m = ops_t[ops_t["Month_Num"] == m_num]["Jumlah (IDR)"].sum() if not ops_t.empty else 0
            total_exp = bel_m + ops_m
            margin = round((r - total_exp) / r * 100, 1) if r > 0 else 0
            margin_trend.append({"Label": BULAN_SHORT.get(b, b), "Margin": float(margin), "Laba": int(r - total_exp)})

    return margin_trend


@router.get("/transactions")
def get_transactions(
    mode: str = Query("Bulan"),
    value: str = Query(None),
    category: str = Query(None),
    year: str = Query(None)
):
    all_data = load_all()
    year_int = _parse_year(year)
    filtered = apply_filter(all_data, mode, value, year=year_int)
    tx = filtered["transactions"]

    # Category Filter explicitly for this view
    if category and category != "Semua":
        tx = tx[tx["Category"].str.lower() == category.lower()]

    tx_sorted = tx.fillna("").sort_values("Transaction Date", ascending=False)

    # Calc Transaksi KPIs
    total_tx = len(tx)
    total_revenue = tx["Total Price Idr"].sum() if total_tx > 0 else 0
    total_qty = tx["Quantity"].sum() if total_tx > 0 else 0
    avg_order = tx["Total Price Idr"].mean() if total_tx > 0 else 0

    kpis = {
        "total_revenue": float(total_revenue),
        "total_tx": int(total_tx),
        "avg_order": float(avg_order),
        "total_qty": int(total_qty)
    }

    # Smart Trend Aggregation Context — scope ke tahun yang dipilih
    scoped_data = _filter_by_year(all_data, year_int)
    is_all_years = year_int is None

    if is_all_years and (not value or value == "Semua"):
        # Semua Tahun → trend tahunan
        context_tx_base = all_data["transactions"]
        if category and category != "Semua":
            context_tx_base = context_tx_base[context_tx_base["Category"].str.lower() == category.lower()]
        chart_period = df_to_dict(revenue_by_year(context_tx_base))
    else:
        context_tx = tx
        m_val = None
        if value and value != "Semua":
            base_tx = scoped_data["transactions"]
            if category and category != "Semua":
                base_tx = base_tx[base_tx["Category"].str.lower() == category.lower()]

            from backend.config.constants import BULAN_TO_NUM
            if mode == "Bulan":
                context_tx = base_tx
            elif mode == "Minggu" and "-W" in str(value):
                try:
                    from datetime import datetime
                    m_val = datetime.strptime(f"{value}-1", "%G-W%V-%u").month
                except:
                    m_val = tx["Month_Num"].iloc[0] if not tx.empty else 1
            elif mode == "Hari":
                if value in BULAN_TO_NUM:
                    m_val = BULAN_TO_NUM[value]
                else:
                    try:
                        m_val = pd.to_datetime(value).month
                    except:
                        m_val = tx["Month_Num"].iloc[0] if not tx.empty else 1

            if m_val is not None:
                if not base_tx.empty:
                    context_tx = base_tx[base_tx["Month_Num"] == m_val]
                else:
                    context_tx = base_tx

        chart_period = df_to_dict(revenue_by_period(context_tx, mode, context_year=year_int, context_month=m_val))

    # Get categories from scoped data (only from selected year)
    scoped_tx = scoped_data["transactions"] if year_int is not None else all_data["transactions"]
    categories = scoped_tx["Category"].dropna().unique().tolist()

    return {
        "kpi": kpis,
        "chart_period": chart_period,
        "chart_products": df_to_dict(top_products(tx, 10)),
        "is_yearly_trend": is_all_years and (not value or value == "Semua"),
        "categories": categories,
        "transactions": df_to_dict(tx_sorted.head(500))
    }

@router.get("/expenses")
def get_expenses(
    mode: str = Query("Bulan"),
    value: str = Query(None),
    year: str = Query(None)
):
    import calendar
    all_data = load_all()
    year_int = _parse_year(year)
    filtered = apply_filter(all_data, mode, value, year=year_int)
    tx = filtered["transactions"]
    belanja = filtered["belanja"]
    ops = filtered["operasional"]

    # ── Tentukan jumlah hari periode ──────────────────────────────────────────
    if mode == "Hari":
        days_in_period = 1
    elif mode == "Minggu":
        days_in_period = 7
    else:
        # Mode Bulan: pakai hari sesungguhnya bulan yang dipilih
        if not tx.empty:
            m = int(tx["Transaction Date"].dt.month.mode()[0])
            y = int(tx["Transaction Date"].dt.year.mode()[0])
            days_in_period = calendar.monthrange(y, m)[1]
        elif not belanja.empty:
            m = int(belanja["Month_Num"].mode()[0])
            y_ref = year_int if year_int else pd.Timestamp.now().year
            days_in_period = calendar.monthrange(y_ref, m)[1]
        else:
            days_in_period = 30

    # ── Konversi pengeluaran ke basis harian lalu kalikan periode ─────────────
    de = get_daily_expense(belanja, ops, tx)
    total_belanja = int(de["daily_belanja"] * days_in_period)
    total_ops     = int(de["daily_ops"]     * days_in_period)
    total_pengeluaran = total_belanja + total_ops

    # ── Breakdown per kategori (juga dikonversi ke basis harian × periode) ────
    breakdown = expense_breakdown(belanja, ops)
    days_map = de["days_map"]

    breakdown_rows = []
    for _, row in breakdown.iterrows():
        daily_val = 0.0

        if not belanja.empty:
            grp_belanja = belanja[belanja["Kategori Belanja"] == row["Kategori"]]
            for m, g in grp_belanja.groupby("Month_Num"):
                d = days_map.get(int(m), 30)
                daily_val += g["Total Biaya (IDR)"].sum() / d

        if not ops.empty:
            grp_ops = ops[ops["Kategori"] == row["Kategori"]]
            for m, g in grp_ops.groupby("Month_Num"):
                d = days_map.get(int(m), 30)
                daily_val += g["Jumlah (IDR)"].sum() / d

        val = daily_val * days_in_period
        pct = float(round(val / total_pengeluaran * 100, 1)) if total_pengeluaran > 0 else 0.0
        tipe = row.get("Tipe") or expense_group_label(row["Kategori"])
        breakdown_rows.append({
            "Kategori": row["Kategori"],
            "Tipe": tipe,
            "Jumlah": int(val),
            "Pct": pct
        })

    breakdown_rows.sort(key=lambda x: x["Jumlah"], reverse=True)

    composition = [
        {"Label": "Belanja", "Jumlah": total_belanja, "Tipe": "Belanja"},
        {"Label": "Operasional", "Jumlah": total_ops, "Tipe": "Operasional"},
    ]

    return {
        "kpi": {
            "total_belanja":     total_belanja,
            "total_ops":         total_ops,
            "total_pengeluaran": total_pengeluaran
        },
        "breakdown":   breakdown_rows,
        "composition": composition,
        "top_items":   breakdown_rows[:10]
    }
