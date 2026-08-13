import pandas as pd
import datetime
import calendar
from backend.config.constants import BULAN_SHORT, BULAN_ORDER

def revenue_by_period(tx: pd.DataFrame, mode: str, context_year: int = None, context_month: int = None) -> pd.DataFrame:
    # Defaults
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

# Test empty DataFrame
empty_tx = pd.DataFrame()
print(revenue_by_period(empty_tx, "Hari", 2025, 3).head())
print(revenue_by_period(empty_tx, "Minggu", 2025, 3))
