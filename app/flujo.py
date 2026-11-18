"""Lógica de la conversación. No sabe nada de WhatsApp: recibe texto o el id de un botón
y devuelve mensajes. Por eso se puede probar sin claves ni internet."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Callable

from . import negocio
from .agenda import Agenda, Cita


@dataclass
class Mensaje:
    texto: str
    opciones: list[tuple[str, str]] = field(default_factory=list)  # (id, título)
    para: str | None = None  # None = el usuario que escribió; si no, otro número (el dueño)


@dataclass
class Sesion:
    estado: str = "menu"
    servicio: str | None = None
    dia: str | None = None
    hora: str | None = None


MENU = [("servicios", "Servicios y precios"), ("agendar", "Agendar una cita"), ("horario", "Horario y ubicación")]
SALUDOS = {"hola", "buenas", "buenos dias", "buenas tardes", "menu", "inicio", "empezar", "0"}
NUMEROS_MENU = {"1": "servicios", "2": "agendar", "3": "horario"}


def normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFD", texto.strip().lower())
    return "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn")


class Bot:
    def __init__(self, agenda: Agenda, telefono_dueno: str | None = None, hoy: Callable[[], date] = date.today) -> None:
        self.agenda = agenda
        self.telefono_dueno = telefono_dueno
        self.hoy = hoy
        self.sesiones: dict[str, Sesion] = {}

    # ---------- punto de entrada ----------
    def responder(self, usuario: str, entrada: str) -> list[Mensaje]:
        sesion = self.sesiones.setdefault(usuario, Sesion(estado="nuevo"))
        texto = normalizar(entrada)

        if sesion.estado == "nuevo" or texto in SALUDOS:
            self.sesiones[usuario] = Sesion()
            return [Mensaje(f"¡Hola! 👋 Soy el asistente de {negocio.NOMBRE}."), self._menu()]
        if texto in {"cancelar", "salir"}:
            self.sesiones[usuario] = Sesion()
            return [Mensaje("Listo, cancelé lo que estábamos haciendo."), self._menu()]

        manejador = {
            "menu": self._en_menu,
            "eligiendo_servicio": self._en_servicio,
            "eligiendo_dia": self._en_dia,
            "eligiendo_hora": self._en_hora,
            "confirmando": self._en_confirmacion,
        }[sesion.estado]
        return manejador(usuario, sesion, texto)

    # ---------- estados ----------
    def _en_menu(self, usuario: str, sesion: Sesion, texto: str) -> list[Mensaje]:
        opcion = NUMEROS_MENU.get(texto, texto)
        if opcion == "servicios" or "precio" in texto or "servicio" in texto:
            lineas = [f"• {n}: {negocio.precio(p)} ({m} min)" for n, p, m in negocio.SERVICIOS.values()]
            return [Mensaje("\n".join(lineas)), self._menu("¿Quieres agendar?")]
        if opcion == "horario" or "horario" in texto or "donde" in texto or "ubicacion" in texto:
            return [Mensaje(negocio.HORARIO), self._menu()]
        if opcion == "agendar" or "cita" in texto or "agendar" in texto or "reservar" in texto:
            return self._pedir_servicio(sesion)
        return [Mensaje("No entendí 🤔. Elige una opción o escribe *menú* cuando quieras volver al inicio."), self._menu()]

    def _pedir_servicio(self, sesion: Sesion) -> list[Mensaje]:
        sesion.estado = "eligiendo_servicio"
        opciones = [(f"svc:{k}", nombre) for k, (nombre, _, _) in negocio.SERVICIOS.items()]
        return [Mensaje("¿Qué servicio quieres?", opciones)]

    def _en_servicio(self, usuario: str, sesion: Sesion, texto: str) -> list[Mensaje]:
        clave = texto.removeprefix("svc:")
        if clave not in negocio.SERVICIOS:
            clave = next((k for k, (n, _, _) in negocio.SERVICIOS.items() if normalizar(n) == texto), "")
        if not clave:
            return [Mensaje("Elige uno de los servicios de la lista, por favor.")] + self._pedir_servicio(sesion)
        sesion.servicio = clave
        sesion.estado = "eligiendo_dia"
        return [self._pedir_dia()]

    def _dias_disponibles(self) -> list[date]:
        dias, d = [], self.hoy()
        while len(dias) < negocio.DIAS_A_MOSTRAR:
            d += timedelta(days=1)
            if d.weekday() not in negocio.DIAS_CERRADO:
                dias.append(d)
        return dias

    @staticmethod
    def _etiqueta_dia(d: date) -> str:
        return f"{negocio.DIAS_SEMANA[d.weekday()]} {d.day} {negocio.MESES[d.month - 1]}"

    def _pedir_dia(self) -> Mensaje:
        opciones = [(f"dia:{d.isoformat()}", self._etiqueta_dia(d)) for d in self._dias_disponibles()]
        return Mensaje("¿Qué día te queda bien?", opciones)

    def _en_dia(self, usuario: str, sesion: Sesion, texto: str) -> list[Mensaje]:
        validos = {d.isoformat(): d for d in self._dias_disponibles()}
        dia = texto.removeprefix("dia:")
        if dia not in validos:
            return [Mensaje("Elige uno de los días de la lista, por favor."), self._pedir_dia()]
        libres = [h for h in negocio.HORAS if not self.agenda.ocupado(dia, h)]
        if not libres:
            return [Mensaje("Ese día ya no tiene horas libres 😕. Elige otro."), self._pedir_dia()]
        sesion.dia = dia
        sesion.estado = "eligiendo_hora"
        return [self._pedir_hora(dia)]

    def _pedir_hora(self, dia: str) -> Mensaje:
        libres = [h for h in negocio.HORAS if not self.agenda.ocupado(dia, h)]
        etiqueta = self._etiqueta_dia(date.fromisoformat(dia))
        return Mensaje(f"Horas libres el {etiqueta}:", [(f"hora:{h}", h) for h in libres])

    def _en_hora(self, usuario: str, sesion: Sesion, texto: str) -> list[Mensaje]:
        hora = texto.removeprefix("hora:")
        if hora not in negocio.HORAS or self.agenda.ocupado(sesion.dia or "", hora):
            return [Mensaje("Elige una de las horas libres, por favor."), self._pedir_hora(sesion.dia or "")]
        sesion.hora = hora
        sesion.estado = "confirmando"
        nombre, valor, _ = negocio.SERVICIOS[sesion.servicio or ""]
        etiqueta = self._etiqueta_dia(date.fromisoformat(sesion.dia or ""))
        return [Mensaje(
            f"Resumen de tu cita:\n{nombre} · {negocio.precio(valor)}\n{etiqueta} a las {hora}\n¿La confirmo?",
            [("confirmar:si", "Sí, confirmar"), ("confirmar:no", "Cambiar")],
        )]

    def _en_confirmacion(self, usuario: str, sesion: Sesion, texto: str) -> list[Mensaje]:
        if texto in {"confirmar:no", "no", "cambiar"}:
            return self._pedir_servicio(sesion)
        if texto not in {"confirmar:si", "si", "confirmar"}:
            return [Mensaje("¿Confirmo la cita?", [("confirmar:si", "Sí, confirmar"), ("confirmar:no", "Cambiar")])]

        cita = Cita(usuario, sesion.servicio or "", sesion.dia or "", sesion.hora or "")
        if not self.agenda.reservar(cita):
            sesion.estado = "eligiendo_hora"
            return [Mensaje("Uy, alguien acaba de tomar esa hora. Elige otra:"), self._pedir_hora(cita.dia)]

        self.sesiones[usuario] = Sesion()
        nombre = negocio.SERVICIOS[cita.servicio][0]
        etiqueta = self._etiqueta_dia(date.fromisoformat(cita.dia))
        salida = [Mensaje(f"¡Listo! ✅ Tu cita quedó agendada: {nombre}, {etiqueta} a las {cita.hora}.\nSi necesitas cancelar, escríbenos por aquí.")]
        if self.telefono_dueno:
            salida.append(Mensaje(f"📅 Nueva cita: {nombre}, {etiqueta} a las {cita.hora}. Cliente: +{usuario}", para=self.telefono_dueno))
        return salida

    def _menu(self, texto: str = "¿En qué te ayudo?") -> Mensaje:
        return Mensaje(texto, list(MENU))
