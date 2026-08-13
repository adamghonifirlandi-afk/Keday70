import sys
sys.path.append(r"c:\TA adam\output ta\keday70_v7")
from backend.routers.ai_context import get_ai_context, AIContextRequest

tests = [
    ("EVALUASI", "ada yang perlu dikhawatirkan dari bisnis ini?"),
    ("SARAN", "saran strategi untuk meningkatkan penjualan"),
    ("PENYEBAB", "kenapa coffee lebih laku dibanding makanan?"),
    ("FAKTUAL-berapa", "berapa total pendapatan bulan oktober?"),
    ("FAKTUAL-metode", "apa saja metode pembayaran yang dipakai?"),
    ("ANALITIK", "analisis tren pendapatan bulanan"),
    ("UMUM", "jam berapa sesi paling ramai?"),
]

for name, q in tests:
    r = get_ai_context(AIContextRequest(pertanyaan=q, session_id="t", history=[]))
    prompt = r["prompt"]
    idx = prompt.find("GAYA (")
    if idx > 0:
        end = prompt.find(")", idx) + 1
        gaya = prompt[idx:end]
    else:
        gaya = "NOT FOUND"
    print(f"{name:20s} -> {gaya}")
