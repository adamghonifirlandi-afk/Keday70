import pandas as pd
from backend.config.constants import BULAN_TO_NUM
from typing import Optional


def apply_filter(
    data: dict[str, pd.DataFrame],
    mode: str,
    value: str,
    year: Optional[int] = None,
) -> dict[str, pd.DataFrame]:
    """
    Filter data dengan dukungan multi-tahun dan format modern:
    - year: int → filter hanya tahun tersebut, None → semua tahun
    - "Bulan" ex: "Januari"
    - "ISO Week" ex: "2024-W02"
    - "ISO Date" ex: "2024-12-31"
    """
    tx       = data["transactions"].copy()
    belanja  = data["belanja"].copy()
    ops      = data["operasional"].copy()

    # ── STEP 1: Filter Tahun (diterapkan sebelum filter mode/value) ────────
    if year is not None:
        tx      = tx[tx["Year"] == year] if "Year" in tx.columns else tx
        belanja = belanja[belanja["Year"] == year] if "Year" in belanja.columns else belanja
        ops     = ops[ops["Year"] == year] if "Year" in ops.columns else ops

    # ── STEP 2: Filter mode/value (Bulan, Minggu, Hari) ───────────────────
    if not value or value == "Semua":
        return { "transactions": tx, "products": data["products"], "belanja": belanja, "operasional": ops }

    # 1. Month string
    if value in BULAN_TO_NUM:
        month_num = BULAN_TO_NUM[value]
        tx      = tx[tx["Month_Num"] == month_num]
        belanja = belanja[belanja["Month_Num"] == month_num]
        ops     = ops[ops["Month_Num"] == month_num]
        return { "transactions": tx, "products": data["products"], "belanja": belanja, "operasional": ops }

    # 2. Week ISO format e.g. "2024-W02"
    if "-W" in str(value):
        try:
            year_str, week_str = str(value).split("-W")
            week_num = int(week_str)
            tx      = tx[tx["Week"] == week_num]
            from datetime import datetime
            first_day_of_week = datetime.strptime(f"{year_str}-W{week_str}-1", "%G-W%V-%u")
            m_num = first_day_of_week.month
            belanja = belanja[belanja["Month_Num"] == m_num]
            ops     = ops[ops["Month_Num"] == m_num]
            return { "transactions": tx, "products": data["products"], "belanja": belanja, "operasional": ops }
        except Exception:
            raise ValueError(f"Format minggu ISO salah: {value}")

    # 3. YYYY-MM-DD Date
    try:
        date = pd.to_datetime(value)
        tx      = tx[tx["Transaction Date"].dt.date == date.date()]
        belanja = belanja[belanja["Month_Num"] == date.month]
        ops     = ops[ops["Month_Num"] == date.month]
    except Exception:
        # Fallback jika user mengosongkan input calendar
        return { "transactions": tx, "products": data["products"], "belanja": belanja, "operasional": ops }

    return { "transactions": tx, "products": data["products"], "belanja": belanja, "operasional": ops }


def get_filter_options(data: dict[str, pd.DataFrame], mode: str, year: Optional[int] = None) -> dict:
    """
    Dapatkan opsi filter (bulan, min/max date, min/max week) berdasarkan tahun kalender.
    Jika year diberikan, akan me-return setahun penuh terlepas dari ketersediaan data transaksi.
    """
    tx = data["transactions"]
    from backend.config.constants import BULAN_ORDER
    import datetime

    # Extract available years globally before applying year filter
    available_years = []
    if "Year" in tx.columns:
        available_years = sorted(tx["Year"].dropna().unique().astype(int).tolist())

    if year is not None:
        bulan_opts = BULAN_ORDER.copy()
        min_date = f"{year}-01-01"
        max_date = f"{year}-12-31"
        min_week = f"{year}-W01"
        
        # Cari minggu terakhir tahun ini (52 atau 53)
        last_day = datetime.date(year, 12, 31)
        max_wk_num = last_day.isocalendar().week
        if max_wk_num == 1:
            max_wk_num = datetime.date(year, 12, 24).isocalendar().week
        max_week = f"{year}-W{max_wk_num:02d}"
    else:
        bulan_opts = BULAN_ORDER.copy()
        if available_years:
            min_y = available_years[0]
            max_y = available_years[-1]
            min_date = f"{min_y}-01-01"
            max_date = f"{max_y}-12-31"
            min_week = f"{min_y}-W01"
            
            last_day = datetime.date(max_y, 12, 31)
            max_wk_num = last_day.isocalendar().week
            if max_wk_num == 1:
                max_wk_num = datetime.date(max_y, 12, 24).isocalendar().week
            max_week = f"{max_y}-W{max_wk_num:02d}"
        else:
            current_y = pd.Timestamp.now().year
            min_date = f"{current_y}-01-01"
            max_date = f"{current_y}-12-31"
            min_week = f"{current_y}-W01"
            max_week = f"{current_y}-W52"

    return {
        "years": [str(y) for y in available_years],
        "months": bulan_opts,
        "min_date": min_date,
        "max_date": max_date,
        "min_week": min_week,
        "max_week": max_week
    }

