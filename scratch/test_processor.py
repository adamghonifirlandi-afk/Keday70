import sys
import os

sys.path.append(r"c:\TA adam\output ta\keday70_v7")

from backend.core.sync_excel_to_sqlite import sync
from backend.core.loader import load_all
from backend.core.processor import revenue_by_period
from backend.routers.ai_context import get_ai_context, AIContextRequest

print("Running ETL Sync...")
sync()

print("\nTesting Processor revenue_by_period for 2025...")
all_data = load_all()
tx = all_data["transactions"]
if "Year" in tx.columns:
    tx_2025 = tx[tx["Year"] == 2025]
    trend_2025 = revenue_by_period(tx_2025, "Bulan")
    print(trend_2025)
else:
    print("Year column not found in transactions.")

print("\nTesting AI Context extraction for 2025...")
req = AIContextRequest(pertanyaan="berapa total pendapatan tahun 2025", session_id="test", history=[])
res = get_ai_context(req)
print("Res type:", type(res))
if isinstance(res, dict):
    prompt = res.get("prompt", "")
    print(prompt[:500])
elif isinstance(res, str):
    print(res[:500])
else:
    print(res)
