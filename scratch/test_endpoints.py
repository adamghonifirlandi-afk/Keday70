import sys
sys.path.append(r"c:\TA adam\output ta\keday70_v7")
from backend.routers.dashboard import get_dashboard_data, get_profit, get_transactions
from backend.core.loader import load_all

print("Loading data...")
data = load_all()

print("\n--- Testing Hari (15 Maret 2025) ---")
try:
    res = get_dashboard_data(mode="Hari", value="2025-03-15", year="2025")
    print("KPI Revenue:", res["kpi"]["total_revenue"])
    print("Trend Hari Len:", len(res["charts"]["revenue"]))
    if len(res["charts"]["revenue"]) > 0:
        print("First day:", res["charts"]["revenue"][0])
        print("Last day:", res["charts"]["revenue"][-1])
except Exception as e:
    import traceback
    traceback.print_exc()

print("\n--- Testing Profit Hari (15 Maret 2025) ---")
try:
    res_prof = get_profit(mode="Hari", value="2025-03-15", year="2025")
    print("Profit Trend Hari Len:", len(res_prof["margin_trend"]))
except Exception as e:
    import traceback
    traceback.print_exc()

print("\n--- Testing Filter Options 2025 ---")
from backend.core.filter import get_filter_options
opts = get_filter_options(data, mode="Hari", year=2025)
print("Min Date:", opts["min_date"])
print("Max Date:", opts["max_date"])
print("Min Week:", opts["min_week"])
print("Max Week:", opts["max_week"])
