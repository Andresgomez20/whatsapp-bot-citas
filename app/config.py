"""Configuración por variables de entorno (ver .env.example)."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    access_token: str
    phone_number_id: str
    verify_token: str
    app_secret: str
    telefono_dueno: str
    graph_version: str
    archivo_citas: str


def cargar() -> Config:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    faltan = [v for v in ("WHATSAPP_TOKEN", "WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_VERIFY_TOKEN", "WHATSAPP_APP_SECRET") if not os.getenv(v)]
    if faltan:
        raise RuntimeError(f"Faltan variables de entorno: {', '.join(faltan)}. Copia .env.example a .env y complétalo.")
    return Config(
        access_token=os.environ["WHATSAPP_TOKEN"],
        phone_number_id=os.environ["WHATSAPP_PHONE_NUMBER_ID"],
        verify_token=os.environ["WHATSAPP_VERIFY_TOKEN"],
        app_secret=os.environ["WHATSAPP_APP_SECRET"],
        telefono_dueno=os.getenv("TELEFONO_DUENO", ""),
        graph_version=os.getenv("GRAPH_API_VERSION", "v21.0"),
        archivo_citas=os.getenv("ARCHIVO_CITAS", "datos/citas.json"),
    )
