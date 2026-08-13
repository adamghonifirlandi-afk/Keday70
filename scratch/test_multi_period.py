import sys
import json
sys.path.append(r"c:\TA adam\output ta\keday70_v7")
from backend.routers.ai_context import get_ai_context, AIContextRequest

scenarios = [
    ("Skenario 1", "tahun 2024"),
    ("Skenario 2", "tahun 2024 dan 2025"),
    ("Skenario 3", "2024, 2025, dan 2026"),
    ("Skenario 4", "desember"),
    ("Skenario 5", "oktober sampai desember"),
    ("Skenario 6", "januari dan februari"),
    ("Skenario 7", "bandingkan desember 2024 dan desember 2025"),
    ("Skenario 8", "bandingkan tahun 2024 dan 2025"),
    ("Skenario 9", "bandingkan oktober, november, desember 2024"),
    ("Skenario 10", "analisa seluruh tahun 2024")
]

for name, q in scenarios:
    r = get_ai_context(AIContextRequest(pertanyaan=q, session_id="test", history=[]))
    meta = r["meta"]
    print(f"=== {name} ===")
    print(f"Q: {q}")
    print(f"Years: {meta.get('multi_years', [])}")
    print(f"Months: {meta.get('multi_months', [])}")
    print(f"Comparison Mode: {meta.get('is_comparison', False)}")
    print(f"Periode Label: {meta.get('periode')}")
    print("-" * 50)

# Print the context builder output for scenario 8
r = get_ai_context(AIContextRequest(pertanyaan="bandingkan tahun 2024 dan 2025", session_id="test", history=[]))
prompt = r["prompt"]
start_idx = prompt.find("=== PERBANDINGAN ===")
if start_idx != -1:
    end_idx = prompt.find("=== TRANSAKSI", start_idx)
    if end_idx == -1:
        end_idx = prompt.find("GAYA (", start_idx)
    print("\n\n" + "="*50)
    print("PROMPT COMPARISON CONTEXT (Skenario 8):")
    print(prompt[start_idx:end_idx if end_idx != -1 else None].strip())
    print("="*50)
