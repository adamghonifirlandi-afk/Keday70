from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import requests
from backend.config.settings import N8N_WEBHOOK_URL

router = APIRouter()

class ChatRequest(BaseModel):
    sessionId: str
    chatInput: str
    action: str = "sendMessage"
    history: Optional[list] = []

@router.post("/message")
def send_chat_message(req: ChatRequest):
    if not N8N_WEBHOOK_URL:
        return {
            "output": "N8N_WEBHOOK_URL belum dikonfigurasi di file .env.",
            "status": "warning"
        }

    # ── Sanitize history ─────────────────────────────────────────────────────

    clean_history = []
    for h in (req.history or []):
        if not isinstance(h, dict):
            continue
        content = h.get("content", "")
        if not isinstance(content, str) or not content.strip():
            continue
        # Buang item yang ternyata adalah enriched prompt (bocor dari sesi lama)
        if "Kamu adalah asisten" in content and "Pertanyaan: " in content:
            content = content.split("Pertanyaan: ")[-1].strip()
        if not content:
            continue
        clean_history.append({
            "role": h.get("role", "user"),
            "content": content
        })

    # ── Kirim ke n8n (chatInput = pertanyaan ASLI, bukan enriched prompt) ────
    # n8n yang bertanggung jawab memanggil /ai-context untuk membangun konteks
    payload = {
        "sessionId": req.sessionId,
        "chatInput": req.chatInput,   # ← pertanyaan murni dari user
        "action": req.action,
        "history": clean_history[-6:],
    }

    try:
        resp = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, list) and len(data) > 0:
            data = data[0]

        output = data.get("output", data.get("text", data.get("response", "")))
        if not output:
            output = str(data)

        return {"output": output}

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request ke AI timeout (>60 detik). Coba lagi.")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Tidak bisa terhubung ke n8n. Pastikan n8n berjalan.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menghubungi n8n: {str(e)}")