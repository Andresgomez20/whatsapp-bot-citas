from app.flujo import Mensaje
from app.seguridad import firma_valida
from app.whatsapp import construir_payload, extraer_mensajes
import hashlib, hmac


def webhook(mensajes):
    return {"object": "whatsapp_business_account", "entry": [{"changes": [{"value": {"messages": mensajes}}]}]}


def test_extrae_texto_boton_y_lista_e_ignora_estados():
    payload = webhook([
        {"from": "57300", "type": "text", "text": {"body": "hola"}},
        {"from": "57300", "type": "interactive", "interactive": {"type": "button_reply", "button_reply": {"id": "agendar", "title": "Agendar"}}},
        {"from": "57301", "type": "interactive", "interactive": {"type": "list_reply", "list_reply": {"id": "hora:09:00", "title": "09:00"}}},
        {"from": "57302", "type": "image", "image": {"id": "x"}},
    ])
    payload["entry"][0]["changes"].append({"value": {"statuses": [{"status": "read"}]}})
    assert extraer_mensajes(payload) == [("57300", "hola"), ("57300", "agendar"), ("57301", "hora:09:00")]


def test_payload_de_texto():
    p = construir_payload("57300", Mensaje("Hola"))
    assert p["type"] == "text" and p["to"] == "57300" and p["text"]["body"] == "Hola"


def test_tres_opciones_son_botones_y_recorta_titulos():
    p = construir_payload("57300", Mensaje("Elige", [("a", "Una opción con un título muy largo"), ("b", "B"), ("c", "C")]))
    botones = p["interactive"]["action"]["buttons"]
    assert p["interactive"]["type"] == "button" and len(botones) == 3
    assert len(botones[0]["reply"]["title"]) <= 20


def test_mas_de_tres_opciones_son_lista():
    opciones = [(f"hora:{h}", h) for h in ["09:00", "10:30", "12:00", "14:30", "16:00"]]
    p = construir_payload("57300", Mensaje("Horas", opciones))
    assert p["interactive"]["type"] == "list"
    assert len(p["interactive"]["action"]["sections"][0]["rows"]) == 5


def test_mensaje_para_el_dueno_va_a_su_numero():
    assert construir_payload("57300", Mensaje("Nueva cita", para="57999"))["to"] == "57999"


def test_firma():
    cuerpo = b'{"a":1}'
    firma = "sha256=" + hmac.new(b"secreto", cuerpo, hashlib.sha256).hexdigest()
    assert firma_valida(cuerpo, firma, "secreto")
    assert not firma_valida(cuerpo, firma, "otro")
    assert not firma_valida(cuerpo, None, "secreto")
    assert not firma_valida(b'{"a":2}', firma, "secreto")
