from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import os
import re
import requests

from backend.config.settings import N8N_WEBHOOK_URL, GROQ_API_KEY, GROQ_MODEL, ENVIRONMENT
from backend.routers.ai_context import get_ai_context, AIContextRequest

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    sessionId: str
    chatInput: str
    action: str = "sendMessage"
    history: Optional[list] = []


def _strip_markdown(text: str) -> str:
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'##\s*', '', text)
    text = re.sub(r'__', '', text)
    text = re.sub(r'\*', '', text)
    return text.strip()


def _safe_error_body(body) -> str:
    if body is None:
        return "empty"
    if isinstance(body, str):
        return body[:500]
    if isinstance(body, (dict, list)):
        try:
            preview = body.copy() if isinstance(body, dict) else body[:5]
            if isinstance(preview, dict):
                safe = {}
                for key in ("error", "detail", "message", "type", "code"):
                    if key in preview:
                        safe[key] = preview[key]
                return str(safe)[:500]
            return str(preview)[:500]
        except Exception:
            return str(body)[:500]
    return str(body)[:500]


@router.post("/message")
def send_chat_message(req: ChatRequest):
    clean_history = []
    for h in (req.history or []):
        if not isinstance(h, dict):
            continue
        content = h.get("content", "")
        if not isinstance(content, str) or not content.strip():
            continue
        if "Kamu adalah asisten" in content and "Pertanyaan: " in content:
            content = content.split("Pertanyaan: ")[-1].strip()
        if not content:
            continue
        clean_history.append({
            "role": h.get("role", "user"),
            "content": content,
        })

    if GROQ_API_KEY:
        model_name = os.getenv("GROQ_MODEL") or GROQ_MODEL or "openai/gpt-oss-20b"
        if model_name == "llama-3.3-70b-versatile":
            model_name = "openai/gpt-oss-20b"

        try:
            context_req = AIContextRequest(
                pertanyaan=req.chatInput,
                session_id=req.sessionId,
                history=clean_history[-6:],
            )
            context_res = get_ai_context(context_req)
            system_prompt = context_res.get("prompt", "")

            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": req.chatInput},
                ],
                "temperature": 0.7,
                "max_completion_tokens": 1024,
                "top_p": 0.9,
            }

            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=60,
            )

            if resp.status_code >= 400:
                try:
                    error_body = resp.json()
                except ValueError:
                    error_body = resp.text

                logger.warning(
                    "Groq API error | status=%s | model=%s | error_type=%s | body=%s",
                    resp.status_code,
                    model_name,
                    "HTTPError",
                    _safe_error_body(error_body),
                )
                raise HTTPException(status_code=502, detail="Layanan AI sedang tidak tersedia. Silakan coba lagi nanti.")

            groq_response = resp.json()
            output = ""
            if "choices" in groq_response and len(groq_response["choices"]) > 0:
                choice = groq_response["choices"][0]
                message = choice.get("message", {})
                output = message.get("content") or ""
            if not output:
                raise HTTPException(status_code=502, detail="Layanan AI sedang tidak tersedia. Silakan coba lagi nanti.")

            output = _strip_markdown(output)
            return {"output": output}

        except HTTPException:
            raise
        except requests.exceptions.Timeout:
            raise HTTPException(status_code=504, detail="Layanan AI sedang tidak tersedia (timeout). Silakan coba lagi nanti.")
        except requests.exceptions.RequestException as e:
            logger.warning(
                "Groq API request error | model=%s | error_type=%s | message=%s",
                model_name,
                type(e).__name__,
                str(e)[:200],
            )
            raise HTTPException(status_code=502, detail="Layanan AI sedang tidak tersedia. Silakan coba lagi nanti.")
        except Exception as e:
            logger.exception("Groq unexpected error | model=%s | error_type=%s", model_name, type(e).__name__)
            raise HTTPException(status_code=500, detail="Layanan AI sedang tidak tersedia. Silakan coba lagi nanti.")

    if not N8N_WEBHOOK_URL:
        return {
            "output": "GROQ_API_KEY atau N8N_WEBHOOK_URL belum dikonfigurasi.",
            "status": "warning",
        }

    payload = {
        "sessionId": req.sessionId,
        "chatInput": req.chatInput,
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