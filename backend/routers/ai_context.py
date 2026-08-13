from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
import re
import pandas as pd

from backend.core.loader import load_all
from backend.core.filter import apply_filter
from backend.core.processor import (
    compute_kpi, revenue_by_period, top_products,
    expense_breakdown, product_analysis,
    revenue_by_session, revenue_by_payment, expense_group_label
)
from backend.config.constants import BULAN_TO_NUM

router = APIRouter()


class AIContextRequest(BaseModel):
    pertanyaan: str
    session_id: Optional[str] = "default"
    history: Optional[list] = []
    year: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# DETEKSI HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def detect_bulan(text: str) -> Optional[str]:
    if not isinstance(text, str):
        return None
    text_lower = text.lower()
    alias = {
        "januari": "Januari", "jan": "Januari",
        "februari": "Februari", "feb": "Februari",
        "maret": "Maret", "mar": "Maret",
        "april": "April", "apr": "April",
        "mei": "Mei",
        "juni": "Juni", "jun": "Juni",
        "juli": "Juli", "jul": "Juli",
        "agustus": "Agustus", "agt": "Agustus", "aug": "Agustus",
        "september": "September", "sep": "September",
        "oktober": "Oktober", "okt": "Oktober",
        "november": "November", "nov": "November",
        "desember": "Desember", "des": "Desember", "dec": "Desember",
    }
    for key, val in alias.items():
        if re.search(r'\b' + key + r'\b', text_lower):
            return val
    return None


def detect_tanggal(text: str) -> Optional[str]:
    if not isinstance(text, str):
        return None
    match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
    if match:
        return match.group(1)
    match = re.search(r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})', text)
    if match:
        d, m, y = match.group(1), match.group(2), match.group(3)
        return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
    match = re.search(r'tanggal\s+(\d{1,2})', text.lower())
    if match:
        day = int(match.group(1))
        bulan = detect_bulan(text)
        if bulan:
            m_num = BULAN_TO_NUM.get(bulan)
            if m_num:
                # Gunakan tahun saat ini sebagai default (bukan hardcode)
                current_year = pd.Timestamp.now().year
                return f"{current_year}-{str(m_num).zfill(2)}-{str(day).zfill(2)}"
    return None


def detect_tahun(text: str) -> Optional[str]:
    if not isinstance(text, str):
        return None
    match = re.search(r'\b(20\d{2})\b', text)
    if match:
        return match.group(1)
    return None


def detect_tahun_multi(text: str) -> List[int]:
    """Deteksi SEMUA tahun (20xx) dalam teks. Return list unik, sorted."""
    if not isinstance(text, str):
        return []
    matches = re.findall(r'\b(20\d{2})\b', text)
    return sorted(set(int(m) for m in matches))


def detect_bulan_multi(text: str) -> List[str]:
    """Deteksi SEMUA bulan dalam teks, termasuk range 'X sampai Y'."""
    if not isinstance(text, str):
        return []
    text_lower = text.lower()
    alias = {
        "januari": "Januari", "jan": "Januari",
        "februari": "Februari", "feb": "Februari",
        "maret": "Maret", "mar": "Maret",
        "april": "April", "apr": "April",
        "mei": "Mei",
        "juni": "Juni", "jun": "Juni",
        "juli": "Juli", "jul": "Juli",
        "agustus": "Agustus", "agt": "Agustus", "aug": "Agustus",
        "september": "September", "sep": "September",
        "oktober": "Oktober", "okt": "Oktober",
        "november": "November", "nov": "November",
        "desember": "Desember", "des": "Desember", "dec": "Desember",
    }
    bulan_order = ["Januari","Februari","Maret","April","Mei","Juni",
                   "Juli","Agustus","September","Oktober","November","Desember"]

    # Cek range: "oktober sampai desember", "jan hingga mar"
    range_match = re.search(
        r'(' + '|'.join(alias.keys()) + r')\s+(?:sampai|hingga|s\.?d\.?|ke|-)\s+(' + '|'.join(alias.keys()) + r')',
        text_lower
    )
    if range_match:
        start_name = alias.get(range_match.group(1))
        end_name = alias.get(range_match.group(2))
        if start_name and end_name:
            si = bulan_order.index(start_name)
            ei = bulan_order.index(end_name)
            if si <= ei:
                return bulan_order[si:ei+1]

    # Cek bulan individual
    found = []
    seen = set()
    for key, val in alias.items():
        if re.search(r'\b' + key + r'\b', text_lower):
            if val not in seen:
                found.append(val)
                seen.add(val)
    # Sort berdasarkan urutan kalender
    found.sort(key=lambda b: bulan_order.index(b) if b in bulan_order else 99)
    return found


def detect_comparison_intent(text: str) -> bool:
    """Deteksi apakah user meminta perbandingan."""
    if not isinstance(text, str):
        return False
    return bool(re.search(
        r'\bbandingkan\b|\bvs\b|\bversus\b|\bdibanding\b|\bperbandingan\b'
        r'|\bbanding\b|\bkomparasi\b|\bcompare\b',
        text.lower()
    ))


def detect_kategori(text: str) -> Optional[str]:
    """Deteksi kategori produk: Coffee, Non-Coffee, Main Course."""
    if not isinstance(text, str):
        return None
    t = text.lower()
    if re.search(r'non[- ]?coffee|non[- ]?kopi', t):
        return "Non-Coffee"
    if re.search(r'main[- ]?course|makanan|makan', t):
        return "Main Course"
    if re.search(r'\bcoffee\b|\bkopi\b', t):
        return "Coffee"
    return None


def detect_topics(text: str) -> dict:
    if not isinstance(text, str):
        return {k: False for k in [
            "produk", "transaksi", "pengeluaran", "tren", "laba",
            "sesi", "hari", "pembayaran", "top", "saran",
            "evaluasi", "penyebab"
        ]}
    t = text.lower()
    return {
        "produk":      bool(re.search(r'produk|harga|modal|margin|menu|jual|kategori|coffee|non.coffee|main.course|minuman|makanan|keuntungan|untung.per|laku.keras', t)),
        "transaksi":   bool(re.search(r'transaksi|terjual|qty|jumlah.*terjual|beli|order|penjualan|laku|tanggal|berapa.*beli|berapa.*terjual|berapa.*jual|berapa.*unit|analisis.*penjualan|penjualan.*analisis', t)),
        "pengeluaran": bool(re.search(r'pengeluaran|biaya|belanja|ops|operasional|bahan.baku|gaji|sewa|packaging', t)),
        "tren":        bool(re.search(r'tren|bulanan|per.?bulan|tiap.bulan|setiap.bulan|performa|pendapatan|revenue|naik|turun|bulan.terbaik|bulan.terburuk|analisis.*bulan|bulan.*analisis|analisa.*bulan|bulan.*analisa|penjualan.*bulan|\banalisa\b|\banalisis\b', t)),
        "laba":        bool(re.search(r'laba|profit|untung|rugi|margin|kpi|ringkasan|summary|estimasi|keuntungan', t)),
        "sesi":        bool(re.search(r'jam|sesi|pagi|siang|sore|malam|ramai|sepi|waktu|peak|sibuk', t)),
        "hari":        bool(re.search(r'senin|selasa|rabu|kamis|jumat|sabtu|minggu|hari.apa|hari.terbaik|weekend|weekday', t)),
        "pembayaran":  bool(re.search(r'bayar|payment|qris|tunai|transfer|cash|metode', t)),
        "top":         bool(re.search(r'terlaris|terbaik|terpopuler|top|ranking|peringkat|paling.laku|paling.banyak', t)),
        "saran":       bool(re.search(r'saran|rekomendasi|sebaiknya|strategi|tips|improve|tingkatkan|optimalkan|hapus|tambah|promosi', t)),
        "evaluasi":    bool(re.search(r'evaluasi|khawatir|perhatikan|waspada|risiko|masalah|concern|worry|perlu.*diperhatikan|yang.*perlu|apa.*yang.*salah', t)),
        "penyebab":    bool(re.search(r'kenapa|mengapa|why|penyebab|sebab|karena.apa|faktor|alasan|kok.bisa|gimana.bisa', t)),
    }


def detect_produk_filter(text: str, products_df) -> Optional[str]:
    """Deteksi nama produk spesifik yang disebut dalam pertanyaan."""
    if not isinstance(text, str) or products_df is None or products_df.empty:
        return None
    # Support both raw ("Nama Produk") and processed ("Product Name") column
    col = None
    if "Product Name" in products_df.columns:
        col = "Product Name"
    elif "Nama Produk" in products_df.columns:
        col = "Nama Produk"
    if not col:
        return None
    text_lower = text.lower()
    best_match = None
    best_len = 0
    for _, row in products_df.iterrows():
        name = str(row.get(col, ""))
        if not name:
            continue
        name_lower = name.lower()
        if name_lower in text_lower:
            if len(name_lower) > best_len:
                best_match = name
                best_len = len(name_lower)
        else:
            words = [w for w in name_lower.split() if len(w) > 3]
            if words and all(w in text_lower for w in words):
                if len(name_lower) > best_len:
                    best_match = name
                    best_len = len(name_lower)
    return best_match


def fmt_rp(val) -> str:
    try:
        v = int(val)
        if v >= 1_000_000:
            return f"Rp{v/1_000_000:.1f}jt"
        if v >= 1_000:
            return f"Rp{v:,}".replace(",", ".")
        return f"Rp{v}"
    except Exception:
        return str(val)


def _safe_history(history: list) -> list:
    """Return list of valid {role, content} dicts from history."""
    result = []
    if not history or not isinstance(history, list):
        return result
    for item in history:
        if not isinstance(item, dict):
            continue
        content = item.get("content", "")
        if not isinstance(content, str) or not content.strip():
            continue
        
        # Bersihkan prompt panjang yang pernah di-inject ke chatInput
        # Prompt kita selalu diakhiri dengan "\nPertanyaan: <pertanyaan_asli>"
        if "Kamu adalah asisten" in content and "Pertanyaan: " in content:
            content = content.split("Pertanyaan: ")[-1]
            
        role = item.get("role", "user")
        if not isinstance(role, str):
            role = "user"
        result.append({"role": role, "content": content.strip()})
    return result


def _build_comparison_context(all_data: dict, multi_years: list, multi_months: list, kategori: str, produk_filter: str) -> str:
    ctx = "\n=== PERBANDINGAN ===\n\n"
    years_to_loop = multi_years if multi_years else [None]
    months_to_loop = multi_months if multi_months else [None]
    
    for y in years_to_loop:
        for m in months_to_loop:
            # Setup mode/value for filter
            if m:
                mode, value = "Bulan", m
                period_name = f"Bulan {m}" + (f" {y}" if y else "")
            else:
                mode, value = "Bulan", None
                period_name = f"Tahun {y}" if y else "Seluruh Waktu"
                
            try:
                filtered = apply_filter(all_data, mode, value, year=y)
            except Exception:
                filtered = all_data
                if y is not None:
                    for key in ["transactions", "belanja", "operasional"]:
                        df = filtered.get(key, pd.DataFrame())
                        if not df.empty and "Year" in df.columns:
                            filtered[key] = df[df["Year"] == y]
            
            tx_base = filtered.get("transactions", pd.DataFrame())
            belanja = filtered.get("belanja", pd.DataFrame())
            ops = filtered.get("operasional", pd.DataFrame())
            
            # KPI
            try:
                kpi = compute_kpi(tx_base, belanja, ops, mode, value)
            except Exception:
                kpi = {
                    "total_revenue": 0, "total_tx": 0, "total_belanja": 0,
                    "total_ops": 0, "total_expense": 0, "estimasi_laba": 0,
                    "avg_order": 0, "avg_daily_tx": 0, "margin_pct": 0
                }
            laba_kotor = kpi["total_revenue"] - kpi["total_belanja"]
            
            ctx += f"--- {period_name.upper()} ---\n"
            ctx += f"Pendapatan: {fmt_rp(kpi['total_revenue'])} | Transaksi: {kpi['total_tx']}\n"
            ctx += f"HPP/Bahan Baku: {fmt_rp(kpi['total_belanja'])} | Biaya Operasional: {fmt_rp(kpi['total_ops'])}\n"
            ctx += f"Laba Kotor: {fmt_rp(laba_kotor)} | Laba Bersih: {fmt_rp(kpi['estimasi_laba'])} | Margin: {kpi['margin_pct']}%\n\n"
            
    return ctx


def _extract_relevant_history(hist: list, current_bulan, current_kategori,
                              generic_produk: bool, generic_analisa: bool) -> list:
    """
    Filter history untuk hanya menyertakan thread percakapan terkini.
    
    Strategi:
    - Proses mundur dalam pasangan (user + AI response)
    - Thread terputus ketika ditemukan pesan USER tentang periode BERBEDA
    - Thread terputus ketika pertanyaan generik tapi history punya kategori spesifik
    - Maksimal 4 pesan (2 pasang user+AI)
    
    Return: list pesan yang relevan, urutan kronologis.
    """
    if not hist:
        return []

    # Kelompokkan menjadi pasangan [user, assistant] dari belakang
    pairs = []
    i = len(hist) - 1
    while i >= 0:
        msg = hist[i]
        if msg.get("role") == "assistant" and i > 0 and hist[i-1].get("role") == "user":
            pairs.append((hist[i-1], hist[i]))
            i -= 2
        elif msg.get("role") == "user":
            pairs.append((msg,))
            i -= 1
        else:
            # AI response tanpa user sebelumnya — skip
            i -= 1

    # pairs sekarang diurutkan dari terbaru ke terlama
    relevant = []
    pair_count = 0

    for pair in pairs:
        user_msg = pair[0]
        content = user_msg.get("content", "")

        if pair_count > 0:
            msg_bulan = detect_bulan(content)
            msg_kat = detect_kategori(content)

            # Thread putus: user bicara tentang bulan BERBEDA
            if msg_bulan and current_bulan and msg_bulan != current_bulan:
                break
            # Thread putus: history punya kategori spesifik tapi
            # pertanyaan sekarang generik (minta semua produk/analisa umum)
            if msg_kat and (generic_produk or generic_analisa):
                break

        relevant = list(pair) + relevant
        pair_count += 1

        # Maksimal 2 pasang (4 pesan)
        if pair_count >= 2:
            break

    return relevant


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT UTAMA
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/ai-context")
def get_ai_context(req: AIContextRequest):
    pertanyaan = req.pertanyaan or ""
    req_year = req.year  # bisa "2024", "2025", "Semua", atau None

    # ── KRITIS: Bersihkan pertanyaan dari enriched prompt yang bocor ──────
    # n8n kadang mengirim seluruh enriched prompt sebelumnya sebagai chatInput.
    # Jika itu terjadi, ekstrak HANYA pertanyaan asli dari akhir prompt.
    if "Kamu adalah asisten" in pertanyaan and "Pertanyaan: " in pertanyaan:
        pertanyaan = pertanyaan.split("Pertanyaan: ")[-1].strip()

    try:
        all_data = load_all()
    except Exception as e:
        return {
            "prompt": f"Data tidak dapat dimuat: {e}. Pertanyaan: {pertanyaan}",
            "meta": {"error": str(e)}
        }

    hist = _safe_history(req.history)
    products_df = all_data.get("products", pd.DataFrame())

    # ══════════════════════════════════════════════════════════════════════════
    # STEP 1 — Deteksi semua filter dari pertanyaan + fallback history
    # ══════════════════════════════════════════════════════════════════════════

    # --- Deteksi apakah pertanyaan bersifat umum/generik ---
    # Pertanyaan seperti "analisa produknya", "bagaimana produknya", "semua produk"
    # harus me-RESET filter kategori & produk, bukan mewarisi dari history.
    t_lower = pertanyaan.lower()
    generic_produk = bool(re.search(
        r'produk(?:nya|mu|\s*nya)?(?:\s|$|\?)|per\s*produk|semua\s*produk'
        r'|masing.masing|tiap\s*produk|analisa\s+produk|analisis\s+produk'
        r'|data\s+produk|daftar\s+produk|list\s+produk|detail\s+produk'
        r'|bagaimana\s+produk|seperti\s+apa\s+produk|info\s+produk',
        t_lower
    ))
    # Pertanyaan analisa umum (tanpa menyebut kategori/produk spesifik)
    # "analisa bulan desember", "analisis dan saran bulan X", dll.
    generic_analisa = bool(re.search(
        r'\banalisa\s+bulan\b|\banalisis\s+bulan\b'
        r'|\banalisa\s+(?:keseluruhan|semua|data|performa|pendapatan)'
        r'|\banalisa\s*$|\banalisis\s*$'
        r'|\banalisis\s+dan\s+saran\b|\banalisa\s+dan\s+saran\b'
        r'|bagaimana\s+(?:bulan|performa|pendapatan|penjualan)'
        r'|\bringkasan\s+bulan\b|\blaporan\s+bulan\b|\breport\s+bulan\b',
        t_lower
    ))

    # --- Periode (multi-support) ---
    tanggal = detect_tanggal(pertanyaan)
    multi_years = detect_tahun_multi(pertanyaan)
    multi_months = detect_bulan_multi(pertanyaan)
    is_comparison = detect_comparison_intent(pertanyaan) or len(multi_years) > 1 or len(multi_months) > 1

    # Backward-compat: single bulan untuk filter utama
    bulan = multi_months[0] if len(multi_months) == 1 else detect_bulan(pertanyaan)
    if not tanggal and not bulan and not multi_months:
        user_msgs = [p for p in hist if p["role"] == "user"]
        for p in reversed(user_msgs[-2:]):
            bulan = detect_bulan(p["content"])
            if bulan:
                break
            tanggal = detect_tanggal(p["content"])
            if tanggal:
                break

    # --- Kategori produk ---
    kategori = detect_kategori(pertanyaan)
    # FIX BUG 2 & 5: Jika pertanyaan generik tentang produk atau analisa umum,
    # JANGAN wariskan kategori dari history
    if not kategori and not generic_produk and not generic_analisa:
        user_msgs_k = [p for p in hist if p["role"] == "user"]
        for p in reversed(user_msgs_k[-2:]):
            kategori = detect_kategori(p["content"])
            if kategori:
                break

    # --- Produk spesifik ---
    produk_filter = detect_produk_filter(pertanyaan, products_df)
    # Hanya inherit produk dari history JIKA pertanyaan saat ini BUKAN tentang
    # "produk" secara umum (misal "produknya seperti apa", "per produk", dll.)
    # Dan hanya dari pesan USER, bukan dari respons AI yang menyebut nama produk
    if not produk_filter and not generic_produk and not generic_analisa:
        user_msgs_p = [p for p in hist if p["role"] == "user"]
        for p in reversed(user_msgs_p[-2:]):
            produk_filter = detect_produk_filter(p["content"], products_df)
            if produk_filter:
                break

    # --- Topik ---
    topics = detect_topics(pertanyaan)
    if not any(topics.values()):
        for p in reversed(hist):
            if p["role"] != "user":
                continue
            extra = detect_topics(p["content"])
            for k, v in extra.items():
                if v:
                    topics[k] = True
            if any(topics.values()):
                break

    # Fallback topik umum
    if not any(topics.values()):
        topics["laba"] = True
        topics["top"] = True

    # ── COMPREHENSIVE MODE ────────────────────────────────────────────────
    # Aktifkan SEMUA topik jika:
    # - generic_analisa ("analisa bulan X", "analisis dan saran")
    # - saran terdeteksi (user minta rekomendasi → butuh semua data)
    # - saran + tren bersamaan
    #
    # PENTING: Simpan flag intent ASLI sebelum comprehensive mengubah topics
    _orig_saran = topics.get("saran", False)
    _orig_evaluasi = topics.get("evaluasi", False)
    _orig_penyebab = topics.get("penyebab", False)

    is_comprehensive = generic_analisa or _orig_saran or _orig_evaluasi
    if is_comprehensive:
        for k in topics:
            topics[k] = True

    # ══════════════════════════════════════════════════════════════════════════
    # STEP 2 — Apply filter PERIODE ke data
    #
    # PENTING: Filter periode diterapkan ke tx/belanja/ops.
    #          Filter kategori & produk TIDAK diterapkan ke data dasar
    #          karena itu akan merusak KPI pengeluaran/laba.
    #          Kategori/produk hanya dipakai saat membangun section spesifik.
    # ══════════════════════════════════════════════════════════════════════════

    # ── Parse year dari request (multi-year aware) ────────────────────────
    # Multi-year sudah dideteksi di atas; fallback ke history / req_year
    if not multi_years:
        explicit_year = detect_tahun(pertanyaan)
        if not explicit_year:
            for p in reversed(hist):
                if p["role"] == "user":
                    yr = detect_tahun(p["content"])
                    if yr:
                        explicit_year = yr
                        break
        final_year_str = explicit_year if explicit_year else req_year
        if final_year_str and final_year_str != "Semua":
            try:
                multi_years = [int(final_year_str)]
            except (ValueError, TypeError):
                pass

    # Backward-compat: year_int tunggal untuk filter utama (non-comparison)
    year_int = multi_years[0] if len(multi_years) == 1 and not is_comparison else None
    if len(multi_years) == 1:
        year_int = multi_years[0]

    year_label = ", ".join(str(y) for y in multi_years) if multi_years else "seluruh tahun"
    months_label = ", ".join(multi_months) if multi_months else ""

    if tanggal:
        mode, value = "Hari", tanggal
        periode_label = f"tanggal {tanggal}"
    elif bulan and not is_comparison:
        mode, value = "Bulan", bulan
        periode_label = f"bulan {bulan} {year_label}"
    elif is_comparison:
        mode, value = "Bulan", None
        parts = []
        if months_label:
            parts.append(months_label)
        parts.append(year_label)
        periode_label = "perbandingan " + " ".join(parts)
    else:
        mode, value = "Bulan", None
        periode_label = f"keseluruhan {year_label}"

    # Filter utama (untuk non-comparison, single period)
    try:
        filtered = apply_filter(all_data, mode, value, year=year_int)
    except Exception:
        filtered = all_data
        if year_int is not None:
            for key in ["transactions", "belanja", "operasional"]:
                df = filtered.get(key, pd.DataFrame())
                if not df.empty and "Year" in df.columns:
                    filtered[key] = df[df["Year"] == year_int]

    # Data dasar (sudah difilter periode, BELUM difilter kategori/produk)
    tx_base = filtered.get("transactions", pd.DataFrame())
    belanja = filtered.get("belanja", pd.DataFrame())
    ops = filtered.get("operasional", pd.DataFrame())

    # Data transaksi yang difilter kategori/produk (untuk section yang butuh)
    tx_scoped = tx_base.copy()
    if kategori and not tx_scoped.empty and "Category" in tx_scoped.columns:
        tx_scoped = tx_scoped[tx_scoped["Category"].str.lower() == kategori.lower()]
    if produk_filter and not tx_scoped.empty and "Product Name" in tx_scoped.columns:
        pf = tx_scoped[tx_scoped["Product Name"].str.lower() == produk_filter.lower()]
        if not pf.empty:
            tx_scoped = pf

    # ══════════════════════════════════════════════════════════════════════════
    # STEP 3 — Hitung KPI
    #
    # KPI selalu dari tx_base (full periode, tanpa filter kategori/produk)
    # agar angka laba/pengeluaran tetap akurat.
    # ══════════════════════════════════════════════════════════════════════════

    try:
        kpi = compute_kpi(tx_base, belanja, ops, mode, value)
    except Exception:
        kpi = {
            "total_revenue": 0, "total_tx": 0, "total_belanja": 0,
            "total_ops": 0, "total_expense": 0, "estimasi_laba": 0,
            "avg_order": 0, "avg_daily_tx": 0, "margin_pct": 0
        }

    laba_kotor = kpi["total_revenue"] - kpi["total_belanja"]

    # ══════════════════════════════════════════════════════════════════════════
    # STEP 4 — Bangun prompt, HANYA section yang dibutuhkan topik
    # ══════════════════════════════════════════════════════════════════════════

    filter_parts = [periode_label]
    if kategori:
        filter_parts.append(f"kategori {kategori}")
    if produk_filter:
        filter_parts.append(f"produk {produk_filter}")
    filter_label = " | ".join(filter_parts)

    ctx = f"""Kamu adalah Business Intelligence Analyst dan Konsultan Bisnis Keday 70, sebuah kedai kopi di Cikampek, Jawa Barat.
Kamu bukan chatbot yang membacakan angka — kamu adalah analis yang membantu pemilik usaha mengambil keputusan bisnis.

CARA BERPIKIR:
Untuk setiap pertanyaan, kamu selalu memikirkan 4 hal:
1. APA yang terjadi (fakta dari data)
2. MENGAPA terjadi (reasoning bisnis, perilaku pelanggan, pola pasar)
3. APA DAMPAKNYA bagi bisnis (risiko, peluang, urgensi)
4. APA YANG HARUS DILAKUKAN (tindakan konkret, realistis untuk UMKM)

PRIORITAS ANALISIS (urutkan berdasarkan dampak bisnis):
1. Profitabilitas — apakah bisnis menghasilkan laba yang sehat?
2. Pertumbuhan Penjualan — apakah revenue dan transaksi bertumbuh?
3. Efisiensi Pengeluaran — apakah biaya terkendali relatif terhadap pendapatan?
4. Kinerja Produk — produk mana yang menjadi mesin utama dan mana yang underperform?
5. Perilaku Pelanggan — pola waktu, preferensi, dan kebiasaan belanja
6. Peluang Pertumbuhan — area yang bisa didorong untuk meningkatkan omzet

Filter aktif: {filter_label}
"""

    # ── Comparison context builder ────────────────────────────────────────
    if is_comparison and (len(multi_years) > 1 or len(multi_months) > 1):
        ctx += _build_comparison_context(all_data, multi_years, multi_months, kategori, produk_filter)
    else:
        ctx += f"""Data berikut adalah fakta penjualan {year_label}.

=== KPI ({periode_label}) ===
Pendapatan: {fmt_rp(kpi['total_revenue'])} | Transaksi: {kpi['total_tx']}
HPP/Bahan Baku: {fmt_rp(kpi['total_belanja'])} | Biaya Operasional: {fmt_rp(kpi['total_ops'])}
Laba Kotor: {fmt_rp(laba_kotor)} | Laba Bersih: {fmt_rp(kpi['estimasi_laba'])} | Margin: {kpi['margin_pct']}%
"""

    # --- Riwayat (hanya thread terkini, hemat token) ---
    relevant_hist = _extract_relevant_history(
        hist, bulan, kategori, generic_produk, generic_analisa
    )
    if relevant_hist:
        h_text = "\n".join([
            f"{'User' if h['role']=='user' else 'AI'}: {h['content'][:120]}"
            for h in relevant_hist
        ])
        ctx += f"\n=== RIWAYAT ===\n{h_text}\n"

    # --- RANGKUMAN PER KATEGORI (selalu tampil untuk analisa periode) ---
    # Ini rangkuman ringkas: Coffee/Non-Coffee/Main Course masing2 berapa
    if not tx_base.empty and "Category" in tx_base.columns:
        try:
            cat_agg = tx_base.groupby("Category").agg(
                Qty=("Quantity", "sum"),
                Revenue=("Total Price Idr", "sum"),
                Tx=("Transaction Id", "count")
            ).reset_index().sort_values("Revenue", ascending=False)
            cat_lines = [f"{r['Category']}: Rev {fmt_rp(r['Revenue'])}, {int(r['Qty'])}qty, {int(r['Tx'])}tx" for _, r in cat_agg.iterrows()]
            ctx += f"\n=== PENJUALAN PER KATEGORI ({periode_label}) ===\n" + "\n".join(cat_lines) + "\n"
        except Exception:
            pass

    # --- TREN BULANAN ---
    if topics["tren"] or topics["laba"]:
        try:
            # Scope tren ke tahun yang dipilih
            tren_tx = filtered.get("transactions", all_data["transactions"])
            if year_int is None:
                tren_tx = all_data["transactions"]  # Semua Tahun
            elif "Year" in all_data["transactions"].columns:
                tren_tx = all_data["transactions"][all_data["transactions"]["Year"] == year_int]

            if kategori and "Category" in tren_tx.columns:
                tren_tx = tren_tx[tren_tx["Category"].str.lower() == kategori.lower()]
            if produk_filter and "Product Name" in tren_tx.columns:
                pf = tren_tx[tren_tx["Product Name"].str.lower() == produk_filter.lower()]
                if not pf.empty:
                    tren_tx = pf
            tren = revenue_by_period(tren_tx, "Bulan")
            if not tren.empty:
                lines = [f"{r.get('Label','?')}: {fmt_rp(r.get('Revenue',0))} ({r.get('Count',0)}tx)" for _, r in tren.iterrows()]
                ctx += "\n=== TREN BULANAN ===\n" + "\n".join(lines) + "\n"
        except Exception:
            pass

    # --- PRODUK ---
    if topics["produk"] or topics["top"] or topics["saran"]:
        try:
            tx_for_prod = tx_scoped if (kategori or produk_filter) else tx_base
            prod_df = product_analysis(products_df, tx_for_prod)
            if kategori and "Category" in prod_df.columns:
                prod_df = prod_df[prod_df["Category"].str.lower() == kategori.lower()]
            if produk_filter and "Product Name" in prod_df.columns:
                sp = prod_df[prod_df["Product Name"].str.lower() == produk_filter.lower()]
                if not sp.empty:
                    prod_df = sp
            if not prod_df.empty:
                # Urutkan berdasarkan Qty agar pertanyaan "terlaris" / "paling banyak" terjawab akurat
                prod_df = prod_df.sort_values(["Qty", "Revenue"], ascending=[False, False])
                # Comprehensive mode: tampilkan SEMUA produk lengkap
                # Non-comprehensive: top 10 saja
                if is_comprehensive or topics["produk"]:
                    show_df = prod_df
                else:
                    show_df = prod_df.head(10)
                lines = []
                for _, r in show_df.iterrows():
                    lines.append(
                        f"{r.get('Product Name','?')}|{r.get('Category','?')}"
                        f"|Jual:{fmt_rp(r.get('Price',0))}|Modal:{fmt_rp(r.get('Cost',0))}"
                        f"|Margin:{r.get('MarginPct',0)}%|Rev:{fmt_rp(r.get('Revenue',0))}"
                        f"|Qty:{int(r.get('Qty',0))}|Tx:{int(r.get('Transactions',0))}"
                    )
                label = f"PRODUK {kategori.upper()}" if kategori else "SEMUA PRODUK"
                ctx += f"\n=== {label} ===\n" + "\n".join(lines) + "\n"
        except Exception:
            pass

    # --- PENGELUARAN ---
    if topics["pengeluaran"] or topics["laba"] or topics["saran"]:
        try:
            exp = expense_breakdown(belanja, ops)
            if not exp.empty:
                lines = [
                    f"{r['Kategori']}|{expense_group_label(r['Kategori'])}|{fmt_rp(r['Jumlah'])}"
                    for _, r in exp.iterrows()
                ]
                ctx += f"\n=== PENGELUARAN ({periode_label}) ===\n" + "\n".join(lines) + "\n"
        except Exception:
            pass

    # --- SESI ---
    if topics["sesi"] or topics["saran"]:
        try:
            sesi_df = revenue_by_session(tx_scoped)
            if not sesi_df.empty:
                lines = [f"{r['Sesi']}|{fmt_rp(r['Revenue'])}" for _, r in sesi_df.iterrows()]
                ctx += "\n=== REVENUE PER SESI ===\n" + "\n".join(lines) + "\n"
            if not tx_scoped.empty and "Session" in tx_scoped.columns:
                sp = tx_scoped.groupby(["Session","Product Name"])["Quantity"].sum().reset_index()
                sp = sp.sort_values(["Session","Quantity"], ascending=[True,False])
                top_sp = sp.groupby("Session").head(3)
                if not top_sp.empty:
                    lines = [f"{r['Session']}|{r['Product Name']}|{int(r['Quantity'])}qty" for _, r in top_sp.iterrows()]
                    ctx += "\n=== TOP PRODUK PER SESI ===\n" + "\n".join(lines) + "\n"
        except Exception:
            pass

    # --- HARI ---
    if topics["hari"] or topics["saran"]:
        try:
            if not tx_scoped.empty and "Day Of Week" in tx_scoped.columns:
                dow = tx_scoped.groupby("Day Of Week").agg(
                    Revenue=("Total Price Idr","sum"), Tx=("Transaction Id","count")
                ).reset_index()
                lines = [f"{r['Day Of Week']}|{fmt_rp(r['Revenue'])}|{int(r['Tx'])}tx" for _, r in dow.sort_values("Revenue",ascending=False).iterrows()]
                ctx += "\n=== REVENUE PER HARI ===\n" + "\n".join(lines) + "\n"
        except Exception:
            pass

    # --- PEMBAYARAN ---
    if topics["pembayaran"] or is_comprehensive:
        try:
            pay = revenue_by_payment(tx_base)
            if not pay.empty:
                lines = [f"{r['Metode']}|{int(r['Jumlah'])}tx" for _, r in pay.iterrows()]
                ctx += "\n=== PEMBAYARAN ===\n" + "\n".join(lines) + "\n"
        except Exception:
            pass

    # --- TRANSAKSI (RANGKUMAN AGREGASI, bukan baris mentah) ---
    transaksi_eksplisit = topics["transaksi"] and not topics["saran"]
    if transaksi_eksplisit or produk_filter:
        try:
            if produk_filter:
                # === Produk spesifik: rangkuman LENGKAP, fleksibel ===
                all_tx = all_data["transactions"]
                if "Product Name" in all_tx.columns:
                    tx_p = all_tx[all_tx["Product Name"].str.lower() == produk_filter.lower()].copy()
                    if value:
                        try:
                            f2 = apply_filter({"transactions": tx_p, "products": products_df, "belanja": belanja, "operasional": ops}, mode, value)
                            tx_p2 = f2.get("transactions", tx_p)
                            if not tx_p2.empty:
                                tx_p = tx_p2
                        except Exception:
                            pass
                    if not tx_p.empty:
                        # Info produk — support both raw & processed column names
                        name_col = "Product Name" if "Product Name" in products_df.columns else "Nama Produk"
                        price_col = "Price" if "Price" in products_df.columns else "Harga Satuan (IDR)"
                        cost_col = "Cost" if "Cost" in products_df.columns else "Harga Modal (IDR)"
                        pr = products_df[products_df[name_col].str.lower() == produk_filter.lower()] if name_col in products_df.columns else pd.DataFrame()
                        harga = int(pr[price_col].values[0]) if not pr.empty and price_col in pr.columns else 0
                        modal = int(pr[cost_col].values[0]) if not pr.empty and cost_col in pr.columns else 0
                        mu = harga - modal
                        total_qty = int(tx_p["Quantity"].sum())
                        total_rev = int(tx_p["Total Price Idr"].sum())
                        total_tx = len(tx_p)
                        total_laba = total_qty * mu

                        ctx += f"\n=== {produk_filter.upper()} ({periode_label}) ===\n"
                        ctx += f"Harga Jual: {fmt_rp(harga)} | Modal: {fmt_rp(modal)} | Margin: {fmt_rp(mu)}/unit\n"
                        ctx += f"Total Qty: {total_qty} | Revenue: {fmt_rp(total_rev)} | Transaksi: {total_tx} | Laba: {fmt_rp(total_laba)}\n"

                        # Per sesi
                        if "Session" in tx_p.columns:
                            ses = tx_p.groupby("Session").agg(Qty=("Quantity","sum"),Rev=("Total Price Idr","sum"),Tx=("Transaction Id","count")).reset_index()
                            sl = [f"{r['Session']}: Qty {int(r['Qty'])}, Rev {fmt_rp(r['Rev'])}, {int(r['Tx'])}tx" for _, r in ses.iterrows()]
                            ctx += "Per Sesi: " + " | ".join(sl) + "\n"

                        # Per hari
                        if "Day Of Week" in tx_p.columns:
                            dow = tx_p.groupby("Day Of Week").agg(Qty=("Quantity","sum"),Tx=("Transaction Id","count")).reset_index().sort_values("Qty", ascending=False)
                            dl = [f"{r['Day Of Week']}: {int(r['Qty'])}qty ({int(r['Tx'])}tx)" for _, r in dow.iterrows()]
                            ctx += "Per Hari: " + " | ".join(dl) + "\n"

                        # Per metode bayar
                        if "Payment Method" in tx_p.columns:
                            pay = tx_p.groupby("Payment Method")["Transaction Id"].count().reset_index()
                            pay.columns = ["Metode", "Jumlah"]
                            pl = [f"{r['Metode']}: {int(r['Jumlah'])}tx" for _, r in pay.iterrows()]
                            ctx += "Metode Bayar: " + " | ".join(pl) + "\n"

                        # Per bulan (jika tidak ada filter bulan spesifik)
                        if not bulan and not tanggal:
                            tx_p["_bln"] = tx_p["Transaction Date"].dt.strftime("%Y-%m")
                            # Generate bl_map dinamis berdasarkan data (tidak hardcode tahun)
                            bulan_short_map = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"Mei",6:"Jun",7:"Jul",8:"Agt",9:"Sep",10:"Okt",11:"Nov",12:"Des"}
                            bl_map = {}
                            for yr in tx_p["Transaction Date"].dt.year.unique():
                                for mn in range(1, 13):
                                    bl_map[f"{int(yr)}-{mn:02d}"] = bulan_short_map.get(mn, str(mn))
                            bln_agg = tx_p.groupby("_bln").agg(Qty=("Quantity","sum"),Rev=("Total Price Idr","sum")).reset_index().sort_values("_bln")
                            bl_lines = [f"{bl_map.get(r['_bln'],r['_bln'])}: Qty {int(r['Qty'])}, Rev {fmt_rp(r['Rev'])}" for _, r in bln_agg.iterrows()]
                            ctx += "Per Bulan: " + " | ".join(bl_lines) + "\n"

                        # Per tanggal (jika user tanya detail tanggal/hari)
                        if topics.get("hari") or topics.get("sesi") or tanggal:
                            tx_p["_tgl"] = tx_p["Transaction Date"].dt.strftime("%Y-%m-%d")
                            tgl_agg = tx_p.groupby("_tgl").agg(Qty=("Quantity","sum"),Rev=("Total Price Idr","sum"),Tx=("Transaction Id","count")).reset_index().sort_values("_tgl")
                            tgl_lines = [f"{r['_tgl']}: Qty {int(r['Qty'])}, Rev {fmt_rp(r['Rev'])}" for _, r in tgl_agg.iterrows()]
                            ctx += "\n=== PER TANGGAL ===\n" + "\n".join(tgl_lines) + "\n"

            elif transaksi_eksplisit:
                # === Transaksi umum: RANGKUM per produk, bukan baris mentah ===
                if not tx_scoped.empty:
                    # 1) Rangkuman per kategori
                    if "Category" in tx_scoped.columns:
                        cat_agg = tx_scoped.groupby("Category").agg(
                            Qty=("Quantity", "sum"),
                            Revenue=("Total Price Idr", "sum"),
                            Tx=("Transaction Id", "count")
                        ).reset_index().sort_values("Revenue", ascending=False)
                        cat_lines = [f"{r['Category']}|Qty:{int(r['Qty'])}|Rev:{fmt_rp(r['Revenue'])}|{int(r['Tx'])}tx" for _, r in cat_agg.iterrows()]
                        kat_lbl = f" {kategori}" if kategori else ""
                        ctx += f"\n=== RANGKUMAN PER KATEGORI{kat_lbl} ({periode_label}) ===\n" + "\n".join(cat_lines) + "\n"

                    # 2) Rangkuman per produk (semua, sudah difilter kategori/periode)
                    # Hanya tampilkan jika section PRODUK belum dirender agar tidak dobel
                    if not topics.get("produk"):
                        prod_agg = tx_scoped.groupby("Product Name").agg(
                            Qty=("Quantity", "sum"),
                            Revenue=("Total Price Idr", "sum"),
                            Tx=("Transaction Id", "count")
                        ).reset_index().sort_values(["Qty", "Revenue"], ascending=[False, False])
                        prod_lines = [f"{r['Product Name']}|Qty:{int(r['Qty'])}|Rev:{fmt_rp(r['Revenue'])}|{int(r['Tx'])}tx" for _, r in prod_agg.iterrows()]
                        ctx += f"\n=== RANGKUMAN PER PRODUK ({len(prod_lines)} produk) ===\n" + "\n".join(prod_lines) + "\n"

                    # 3) Rangkuman metode pembayaran
                    if "Payment Method" in tx_scoped.columns:
                        pay_agg = tx_scoped.groupby("Payment Method").agg(
                            Tx=("Transaction Id", "count"),
                            Revenue=("Total Price Idr", "sum")
                        ).reset_index()
                        pay_lines = [f"{r['Payment Method']}|{int(r['Tx'])}tx|{fmt_rp(r['Revenue'])}" for _, r in pay_agg.iterrows()]
                        ctx += "\n=== METODE BAYAR ===\n" + "\n".join(pay_lines) + "\n"

                    # 4) Rangkuman per sesi
                    if "Session" in tx_scoped.columns:
                        ses_agg = tx_scoped.groupby("Session").agg(
                            Tx=("Transaction Id", "count"),
                            Revenue=("Total Price Idr", "sum")
                        ).reset_index()
                        ses_lines = [f"{r['Session']}|{int(r['Tx'])}tx|{fmt_rp(r['Revenue'])}" for _, r in ses_agg.iterrows()]
                        ctx += "\n=== TRANSAKSI PER SESI ===\n" + "\n".join(ses_lines) + "\n"
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    # STEP 5 — INSTRUKSI GAYA JAWABAN (adaptif berdasarkan intent user)
    # ══════════════════════════════════════════════════════════════════════════

    is_saran = _orig_saran
    is_evaluasi = _orig_evaluasi
    is_penyebab = _orig_penyebab
    is_advisory = is_saran or is_evaluasi

    # Deteksi pertanyaan langsung ("berapa...", "total...", "jumlah...") 
    # yang seharusnya dijawab faktual meskipun keyword tren/laba ikut terpicu
    is_direct_question = bool(re.search(
        r'^berapa|^total\s|^jumlah\s|^ada berapa|^hitung|^sebutkan|^apa saja metode',
        pertanyaan.lower().strip()
    ))

    is_analitik = (topics.get("tren", False) or topics.get("laba", False)) and not is_advisory and not is_penyebab and not is_direct_question
    is_faktual = is_direct_question or ((topics.get("transaksi", False) or topics.get("pembayaran", False)) and not is_advisory and not is_analitik and not is_penyebab and not is_comparison)

    ctx += """
ATURAN WAJIB:
- Jawab dalam Bahasa Indonesia. Tone: santai tapi profesional, seperti konsultan bisnis yang sedang ngobrol langsung dengan pemilik kedai.
- Semua angka HARUS dari data di atas, DILARANG mengarang atau mengasumsikan angka.
- PERHATIKAN: "Terlaris" atau "paling banyak" ditentukan oleh Qty. "Pendapatan tertinggi" ditentukan oleh Rev. Jangan tertukar.
- Jika ada section PENGELUARAN di atas, gunakan data itu untuk analisis biaya.
- DILARANG pakai simbol markdown seperti **, ##, atau _. Gunakan teks biasa.
- DILARANG pakai simbol | dalam jawaban.
- Jangan tutup jawaban dengan basa-basi ("semoga membantu", "ada pertanyaan lain?").
- Jika data tidak ada atau periode kosong, sampaikan dengan jelas dan ramah.

PRINSIP KOMUNIKASI:
Jawaban harus mudah dibaca oleh pemilik UMKM dalam waktu kurang dari 15 detik.
Prioritaskan:
1. Insight utama (apa yang paling penting diketahui)
2. Bukti pendukung (angka atau pola yang mendukung insight)
3. Tindakan atau implikasi (apa yang harus dilakukan atau diwaspadai)
BUKAN: semua angka, semua kategori, semua detail.

ATURAN KERINGKASAN:
- Maksimal 2 paragraf untuk sebagian besar pertanyaan.
- Maksimal 120 kata kecuali user meminta analisis mendalam.
- Fokus pada 1-3 insight paling penting.
- Jangan menjelaskan semua kategori jika tidak relevan.
- Jangan menjelaskan semua KPI jika tidak relevan.
- Jangan mengulang data yang memiliki makna serupa.
- Jika satu insight sudah menjelaskan kondisi bisnis, hentikan dan lanjut ke insight berikutnya.

POLA JAWABAN WAJIB:
Gunakan urutan: INSIGHT UTAMA -> BUKTI DATA -> IMPLIKASI ATAU SARAN
BUKAN: ANGKA -> ANGKA -> ANGKA -> ANGKA -> KESIMPULAN

PRINSIP KONSULTAN:
Sebelum menulis jawaban, tanyakan pada dirimu:
"Jika saya adalah konsultan bisnis yang dibayar untuk membantu pemilik Keday 70 mengambil keputusan, insight apa yang PALING BERGUNA untuk disampaikan dalam 2 paragraf?"
Bukan: "Angka apa saja yang bisa saya bacakan?"

INSIGHT ENGINE — Jika relevan, cari dan sampaikan (pilih yang paling berdampak, JANGAN semua):
- Peluang pertumbuhan yang belum dimanfaatkan
- Risiko bisnis yang perlu diwaspadai
- Produk unggulan vs produk yang perlu evaluasi
- Efisiensi biaya
- Pola pelanggan dan pola waktu penjualan

ANTI-PATTERN — JANGAN PAKAI POLA INI:
- "Yang paling perlu diperhatikan adalah..."
- "Selain itu..."
- "Perlu diperhatikan bahwa..."
- "Pendapatan bulan X mencapai..."
- "Berikut beberapa analisis..."
- "Berdasarkan data yang ada..."
- "Kategori X memiliki kontribusi..."
- "Jika kita bandingkan..."
- Jangan mendaftar angka tanpa insight (buruk: "Coffee Rp15jt. Non-Coffee Rp10jt. Main Course Rp5jt.")
- Jangan ulangi pertanyaan user.
- Jangan mengulang angka/insight yang sudah dibahas di percakapan sebelumnya.

VARIASI:
- Setiap jawaban harus punya pembuka yang BERBEDA.
- Bentuk jawaban: paragraf pendek yang mengalir natural.
- Gunakan penomoran HANYA kalau memang butuh mendaftar beberapa item spesifik.
- Gunakan persentase dan perbandingan relatif ("hampir setengah", "dua kali lipat") untuk membuat angka lebih bermakna.
"""

    if is_comparison:
        ctx += """
GAYA (PERBANDINGAN):
Struktur jawaban:
1. INSIGHT UTAMA — apa perubahan terbesar atau pola yang paling menarik dari perbandingan ini.
2. BUKTI DATA — highlight selisih atau tren naik/turun antar periode.
3. IMPLIKASI — apa arti perubahan ini bagi bisnis ke depan.

Aturan:
- Bandingkan metrik kunci antar periode secara jelas.
- Jangan hanya mendaftar angka untuk tiap tahun berturut-turut; fokus pada *selisih* dan *perkembangan*.
- Maksimal 2 paragraf.
"""
    elif is_advisory:
        if is_evaluasi:
            ctx += """
GAYA (EVALUASI/RISIKO):
Struktur jawaban:
1. Apa yang harus DIJAGA — aspek bisnis yang sudah berjalan baik dan harus dipertahankan
2. Apa yang perlu DIAWASI — indikator yang menunjukkan potensi masalah
3. Apa yang perlu DIPERBAIKI terlebih dahulu — prioritas berdasarkan dampak bisnis

Urutkan berdasarkan urgensi dan dampak bisnis, bukan abjad atau ukuran angka.
AI harus mampu mengidentifikasi area yang butuh perhatian sebelum menjadi masalah serius.
Maksimal 3 area fokus. Setiap area harus didukung data konkret.

Contoh:
"Yang perlu dijaga: Coffee masih jadi mesin utama dan marginnya sehat di atas 55%. Ini fondasi yang kuat, jangan sampai kualitas atau konsistensi rasa turun.

Yang perlu diawasi: ketergantungan revenue ke satu kategori cukup tinggi. Kalau tren konsumsi minuman bergeser atau ada kompetitor baru, dampaknya langsung terasa karena Main Course belum cukup kuat jadi penyangga.

Yang perlu diperbaiki: efisiensi operasional. Biaya sewa dan administrasi relatif tetap, tapi kalau revenue stagnan, margin akan tergerus pelan-pelan. Perlu dievaluasi apakah ada pengeluaran yang bisa dioptimalkan."
"""
        else:
            ctx += """
GAYA (SARAN/REKOMENDASI/STRATEGI):
Tujuan: memberikan arahan bisnis yang paling relevan berdasarkan kondisi aktual data.
Jawaban harus terasa seperti konsultan bisnis yang sedang berbicara langsung kepada pemilik usaha, bukan laporan formal.

Struktur: INSIGHT UTAMA -> PELUANG YANG BISA DIMANFAATKAN -> TINDAKAN YANG DISARANKAN

Aturan:
- Fokus pada 1-3 rekomendasi yang paling berdampak.
- Jangan membuat daftar panjang.
- Jangan menjelaskan semua kategori atau semua produk — pilih area yang paling berpengaruh.
- Jelaskan alasan rekomendasi secara singkat.
- JANGAN buka dengan total pendapatan atau KPI.
- Kalau user tanya soal kategori spesifik, fokus ke kategori itu saja.
- Bahasa natural, mudah dipahami pemilik UMKM.
- Maksimal 2 paragraf.

Contoh:
"Coffee masih menjadi penopang utama revenue, jadi fokus sebaiknya tetap di sana. Produk seperti Latte dan Es Coklat sudah kuat sehingga layak didorong melalui bundling atau promo pada jam ramai.

Main Course sebenarnya punya potensi, tetapi kontribusinya masih jauh di bawah beverage. Cara tercepat untuk meningkatkannya adalah melalui paket makan + minum dibanding promo makanan secara terpisah."
"""
    elif is_penyebab:
        ctx += """
GAYA (PENYEBAB/REASONING):
Struktur jawaban:
1. PENYEBAB — hipotesis utama berdasarkan data dan logika bisnis
2. BUKTI DATA — angka dan pola yang mendukung hipotesis
3. KESIMPULAN — interpretasi bisnis dan implikasi

User ingin tahu MENGAPA sesuatu terjadi. Jawab dengan reasoning bisnis, bukan sekadar angka.
Boleh menyimpulkan perilaku customer atau pola bisnis dari data yang ada.
Angka digunakan sebagai validasi reasoning, bukan sebagai pembuka.

Contoh:
"Coffee kemungkinan mendominasi karena karakter customer Keday 70 lebih kuat ke pola nongkrong dan beverage. Ini terlihat dari rata-rata transaksi per orang yang relatif rendah — menunjukkan customer datang untuk ngopi, bukan untuk makan berat.

Data mendukung: 65% transaksi adalah produk coffee, repeat order minuman lebih tinggi 3x dibanding makanan, dan peak hour justru di jam 14.00-17.00 (jam nongkrong, bukan jam makan).

Kesimpulannya, dominasi coffee bukan masalah — justru ini kekuatan Keday 70. Yang perlu dievaluasi adalah apakah Main Course bisa dijadikan pelengkap yang memperbesar basket size, bukan mencoba mengubah karakter kedai."
"""
    elif is_analitik:
        ctx += """
GAYA (ANALISIS/TREN):
Struktur jawaban:
1. TEMUAN — insight utama atau pola yang terlihat (buka dengan ini, bukan angka)
2. PENYEBAB — faktor pendorong di balik temuan
3. DAMPAK BISNIS — apa artinya bagi keputusan bisnis ke depan

Buka dengan temuan utama (pola/insight), bukan angka mentah.
Jelaskan pola yang terlihat, faktor pendorong, dan implikasi bisnis.
Gunakan data dan angka untuk MENDUKUNG insight — bukan sebaliknya.
Untuk tren: sebutkan pola dulu, baru bukti angkanya.

Contoh:
"Penjualan Keday 70 punya pola seasonal yang cukup jelas — kuartal akhir tahun secara konsisten lebih kuat dibanding awal tahun. Oktober dan November biasanya jadi bulan terbaik, sementara Januari-Februari cenderung lebih lambat.

Penyebab utamanya kemungkinan gabungan dari faktor cuaca (musim hujan mendorong konsumsi minuman hangat) dan pola pengeluaran masyarakat yang meningkat menjelang akhir tahun.

Implikasinya: alokasi budget promosi sebaiknya diperbesar di Q4 untuk memaksimalkan momentum, sementara Q1 bisa difokuskan untuk efisiensi dan eksperimen menu baru."
"""
    elif is_faktual:
        ctx += """
GAYA (DATA/FAKTA):
- Langsung ke inti, angka terlebih dahulu.
- Tidak perlu analisis panjang.
- Maksimal 2-3 kalimat untuk pertanyaan sederhana.
- 1 angka: cukup 1-2 kalimat padat.
- Beberapa item: boleh daftar singkat, satu per baris.
- Jangan jelaskan hal yang tidak ditanya.
- Boleh tambahkan 1 kalimat konteks singkat jika ada insight menarik.

Contoh:
"Total pendapatan tahun 2024 sebesar Rp316,8 juta dari 15.397 transaksi. Rata-rata nilai transaksi sekitar Rp20 ribu per order."

Contoh dengan insight singkat:
"QRIS mendominasi dengan 8.200 transaksi (53%), disusul tunai 5.100 transaksi (33%). Tren ini menunjukkan customer Keday 70 sudah sangat terbiasa dengan pembayaran digital."
"""
    else:
        ctx += """
GAYA (UMUM):
- Jawab langsung di kalimat pertama.
- Angka sebagai pendukung, bukan fokus utama.
- Panjang jawaban sesuaikan kompleksitas pertanyaan.
- Kalau cukup 2 kalimat, jangan dipanjangkan.
- Jika ada peluang untuk memberikan insight bisnis yang berguna, sampaikan secara singkat.
- Pikirkan: "Apa satu hal yang paling berguna untuk diketahui pemilik kedai terkait pertanyaan ini?"

Contoh:
"Sesi sore (14.00-17.00) justru jadi waktu paling produktif, bukan jam makan siang seperti yang biasa diasumsikan. Ini masuk akal mengingat karakter Keday 70 sebagai tempat nongkrong — pelanggan lebih sering datang untuk ngopi sore dibanding makan."
"""

    ctx += f"\nPertanyaan: {pertanyaan}"

    return {
        "prompt": ctx,
        "meta": {
            "pertanyaan_clean": pertanyaan[:80],
            "periode": periode_label,
            "mode": mode,
            "value": value,
            "kategori": kategori,
            "produk_filter": produk_filter,
            "is_comprehensive": is_comprehensive,
            "is_comparison": is_comparison,
            "multi_years": multi_years,
            "multi_months": multi_months,
            "generic_analisa": generic_analisa,
            "generic_produk": generic_produk,
            "topics": {k: v for k, v in topics.items() if v},
            "history_count": len(hist),
            "token_estimasi": len(ctx) // 4
        }
    }
