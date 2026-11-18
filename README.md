# Bot de citas para WhatsApp

Bot que atiende a los clientes de un negocio por WhatsApp: muestra servicios y precios, da el horario y **agenda citas** con botones (servicio → día → hora → confirmación). Al confirmar, guarda la cita y **le avisa al dueño** por WhatsApp. Usa la **API oficial de WhatsApp Business (Cloud API de Meta)**.

> Demo del flujo en el navegador: https://andresgomez20.github.io/#demos · *English below.*

## Cómo funciona

```
WhatsApp del cliente ──► Meta (Cloud API) ──► POST /webhook (FastAPI)
                                                  │  verifica la firma X-Hub-Signature-256
                                                  ▼
                                    app/flujo.py  (lógica de la conversación)
                                                  │  app/agenda.py guarda la cita
                                                  ▼
                      app/whatsapp.py arma botones o listas y responde por la API
```

| Archivo | Qué hace |
|---|---|
| `app/negocio.py` | Nombre, servicios, precios, horas y horario. **Es lo único que cambias para otro negocio.** |
| `app/flujo.py` | Máquina de estados de la conversación. No depende de WhatsApp, así que se prueba sin claves. |
| `app/agenda.py` | Reservas en un archivo JSON; evita que dos personas tomen la misma hora. |
| `app/whatsapp.py` | Lee los webhooks y arma mensajes de texto, botones (hasta 3) o listas (hasta 10). |
| `app/seguridad.py` | Valida que cada webhook venga de Meta. |
| `app/main.py` | Servidor FastAPI con `GET /webhook` (verificación), `POST /webhook` y `GET /salud`. |

## Instalación

Requiere Python 3.11 o superior.

```bash
python3 -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # y completa los valores
```

## Pruebas

```bash
python3 -m pytest
```

Las pruebas cubren el flujo completo de agendamiento, días cerrados, horas ocupadas, dos personas reservando la misma hora, mensajes inesperados, la lectura de webhooks, el armado de botones y listas, y la validación de la firma.

## Conectarlo a WhatsApp

1. Crea una app en [Meta for Developers](https://developers.facebook.com/), agrega el producto **WhatsApp** y copia el token y el *Phone number ID* en `.env`. Meta da un número de prueba para empezar sin tener uno propio.
2. Inventa un `WHATSAPP_VERIFY_TOKEN` y copia la clave secreta de la app en `WHATSAPP_APP_SECRET`.
3. Arranca el servidor: `uvicorn app.main:app --reload --port 8000`.
4. Para probar en tu computador, expón el puerto con un túnel (por ejemplo, `ngrok http 8000` o `cloudflared tunnel --url http://localhost:8000`).
5. En Meta, en **WhatsApp → Configuración**, pon como URL del webhook `https://<tu-dirección>/webhook`, el mismo verify token, y suscríbete al campo **messages**.
6. Escríbele "hola" al número.

## Despliegue

Cualquier servicio que corra Python sirve (Render, Railway, Fly.io o un VPS). Comando de inicio: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Configura las variables de `.env` en el panel del servicio. Para varios servidores o mucho tráfico, cambia la agenda en JSON por una base de datos (PostgreSQL o MongoDB).

---

## English

WhatsApp bot that answers customers, shows services and prices, and **books appointments** with interactive buttons (service → day → time → confirm). On confirmation it stores the booking and **notifies the business owner**. Built with FastAPI on the **official WhatsApp Business Cloud API**.

- `app/flujo.py` holds a platform-independent state machine, so the conversation is unit-tested without API keys.
- Webhook requests are verified with the `X-Hub-Signature-256` HMAC signature.
- Double-booking is prevented by the agenda, which persists to JSON.
- To adapt it for another business, edit only `app/negocio.py`.

Setup: `pip install -r requirements.txt`, copy `.env.example` to `.env`, run `uvicorn app.main:app`, and point your Meta app's webhook to `/webhook`. Tests: `python3 -m pytest`.

---

Hecho por **Jorge Andrés Gómez** · [Portafolio](https://andresgomez20.github.io/) · WhatsApp +57 322 789 1135
