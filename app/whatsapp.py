"""Traducción entre el formato de la API de WhatsApp (Cloud API de Meta) y los mensajes del bot."""

from __future__ import annotations

from typing import Any

from .flujo import Mensaje

MAX_BOTONES = 3        # límite de botones de respuesta de WhatsApp
MAX_TITULO_BOTON = 20  # caracteres
MAX_FILAS_LISTA = 10
MAX_TITULO_FILA = 24


def extraer_mensajes(payload: dict[str, Any]) -> list[tuple[str, str]]:
    """Devuelve [(telefono, entrada)] de un webhook. La entrada es el texto o el id del botón/lista.
    Ignora avisos de estado (entregado, leído) y tipos que el bot no maneja."""
    salida: list[tuple[str, str]] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for m in change.get("value", {}).get("messages", []):
                tipo, origen = m.get("type"), m.get("from")
                if not origen:
                    continue
                if tipo == "text":
                    salida.append((origen, m.get("text", {}).get("body", "")))
                elif tipo == "interactive":
                    i = m.get("interactive", {})
                    respuesta = i.get("button_reply") or i.get("list_reply") or {}
                    if respuesta.get("id"):
                        salida.append((origen, respuesta["id"]))
                elif tipo == "button":  # respuesta a botones de una plantilla
                    salida.append((origen, m.get("button", {}).get("payload") or m.get("button", {}).get("text", "")))
    return salida


def construir_payload(telefono: str, mensaje: Mensaje) -> dict[str, Any]:
    base = {"messaging_product": "whatsapp", "recipient_type": "individual", "to": mensaje.para or telefono}
    if not mensaje.opciones:
        return {**base, "type": "text", "text": {"preview_url": False, "body": mensaje.texto}}
    if len(mensaje.opciones) <= MAX_BOTONES:
        botones = [{"type": "reply", "reply": {"id": i, "title": t[:MAX_TITULO_BOTON]}} for i, t in mensaje.opciones]
        return {**base, "type": "interactive", "interactive": {"type": "button", "body": {"text": mensaje.texto}, "action": {"buttons": botones}}}
    filas = [{"id": i, "title": t[:MAX_TITULO_FILA]} for i, t in mensaje.opciones[:MAX_FILAS_LISTA]]
    return {**base, "type": "interactive", "interactive": {
        "type": "list", "body": {"text": mensaje.texto},
        "action": {"button": "Ver opciones", "sections": [{"title": "Opciones", "rows": filas}]},
    }}


class ClienteWhatsApp:
    """Envía mensajes con la Cloud API. Necesita httpx (ver requirements.txt)."""

    def __init__(self, token: str, phone_number_id: str, version: str) -> None:
        self.url = f"https://graph.facebook.com/{version}/{phone_number_id}/messages"
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async def enviar(self, payload: dict[str, Any]) -> None:
        import httpx

        async with httpx.AsyncClient(timeout=15) as cliente:
            r = await cliente.post(self.url, headers=self.headers, json=payload)
            r.raise_for_status()
