"""Servidor del webhook. Ejecuta:  uvicorn app.main:app --reload"""

import logging

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

from . import config
from .agenda import Agenda
from .flujo import Bot
from .seguridad import firma_valida
from .whatsapp import ClienteWhatsApp, construir_payload, extraer_mensajes

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bot")

cfg = config.cargar()
bot = Bot(Agenda(cfg.archivo_citas), telefono_dueno=cfg.telefono_dueno or None)
whatsapp = ClienteWhatsApp(cfg.access_token, cfg.phone_number_id, cfg.graph_version)
app = FastAPI(title="Bot de citas para WhatsApp")


@app.get("/salud")
def salud() -> dict:
    return {"ok": True}


@app.get("/webhook")
def verificar(request: Request) -> PlainTextResponse:
    """Meta llama a esta ruta una vez para verificar el webhook."""
    q = request.query_params
    if q.get("hub.mode") == "subscribe" and q.get("hub.verify_token") == cfg.verify_token:
        return PlainTextResponse(q.get("hub.challenge", ""))
    raise HTTPException(status_code=403, detail="Token de verificación inválido")


@app.post("/webhook")
async def recibir(request: Request, tareas: BackgroundTasks) -> dict:
    cuerpo = await request.body()
    if not firma_valida(cuerpo, request.headers.get("X-Hub-Signature-256"), cfg.app_secret):
        raise HTTPException(status_code=401, detail="Firma inválida")
    for telefono, entrada in extraer_mensajes(await request.json()):
        log.info("Mensaje de %s: %r", telefono, entrada)
        for mensaje in bot.responder(telefono, entrada):
            tareas.add_task(whatsapp.enviar, construir_payload(telefono, mensaje))
    return {"ok": True}  # responder rápido; Meta reintenta si tardamos
