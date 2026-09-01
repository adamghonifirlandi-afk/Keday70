from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import requests
import re
from backend.config.settings import N8N_WEBHOOK_URL, GROQ_API_KEY, GROQ_MODEL, ENVIRONMENT
from backend.routers.ai_context import get_ai_context, AIContextRequest

router = APIRouter()

class ChatRequest(BaseModel):
    sessionId: str
    chatInput: str
    action: str = "sendMessage"
    history: Optional[list] = []

def _strip_markdown(text: str) -> str:
    # Bersihkan markdown formatting yang tidak diinginkan (dari n8n JS code)
    text = re.sub(r'\*\*', '', text)    # hapus bold markdown
    text = re.sub(r'##\s*', '', text)   # hapus heading markdown
    text = re.sub(r'__', '', text)      # hapus underscore markdown
    text = re.sub(r'\*', '', text)      # hapus italic markdown
    return text.strip()

@router.post("/message")
def send_chat_message(req: ChatRequest):
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

    # Jika GROQ_API_KEY ada, panggil Groq API secara langsung (Production Mode)
    if GROQ_API_KEY:
        try:
            # 1. Build AI context
            context_req = AIContextRequest(
                pertanyaan=req.chatInput,
                session_id=req.sessionId,
                history=clean_history[-6:]
            )
            context_res = get_ai_context(context_req)
            system_prompt = context_res.get("prompt", "")

            # 2. Call Groq API
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": req.chatInput}
                ],
                "temperature": 0.7,
                "max_tokens": 2048,
                "top_p": 0.9
            }
            
            resp = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
            groq_response = resp.json()
            
            output = ""
            if "choices" in groq_response and len(groq_response["choices"]) > 0:
                output = groq_response["choices"][0]["message"]["content"] or ""
            elif "error" in groq_response:
                output = f"Error dari Groq: {groq_response['error'].get('message', str(groq_response['error']))}"
            else:
                output = "Maaf, tidak ada respons dari AI. Coba lagi."
                
            output = _strip_markdown(output)
            return {"output": output}

        except requests.exceptions.Timeout:
            raise HTTPException(status_code=504, detail="Layanan AI sedang tidak tersedia (timeout). Silakan coba lagi nanti.")
        except Exception as e:
            if ENVIRONMENT == "production":
                raise HTTPException(status_code=500, detail="Layanan AI sedang tidak tersedia. Silakan coba lagi nanti.")
            else:
                raise HTTPException(status_code=500, detail=f"Gagal memanggil AI: {str(e)}")

    # ── Fallback ke n8n (Development Mode) ────────────────────────────────────
    if not N8N_WEBHOOK_URL:
        return {
            "output": "GROQ_API_KEY atau N8N_WEBHOOK_URL belum dikonfigurasi.",
            "status": "warning"
        }

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
        raise HTTPException(status_code=504, detail="Layanan AI sedang tidak tersedia (timeout). Silakan coba lagi nanti.")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Layanan AI sedang tidak tersedia. Pastikan n8n berjalan atau set GROQ_API_KEY.")
    except Exception as e:
        if ENVIRONMENT == "production":
            raise HTTPException(status_code=500, detail="Layanan AI sedang tidak tersedia. Silakan coba lagi nanti.")
        else:
            raise HTTPException(status_code=500, detail=f"Gagal menghubungi n8n: {str(e)}")