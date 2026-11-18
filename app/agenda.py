"""Agenda de citas. Guarda en un archivo JSON para que las reservas sobrevivan a un reinicio."""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Cita:
    telefono: str
    servicio: str
    dia: str  # AAAA-MM-DD
    hora: str  # HH:MM


class Agenda:
    def __init__(self, archivo: str | Path | None = None) -> None:
        self._archivo = Path(archivo) if archivo else None
        self._lock = threading.Lock()
        self._citas: list[Cita] = []
        if self._archivo and self._archivo.exists():
            datos = json.loads(self._archivo.read_text(encoding="utf-8"))
            self._citas = [Cita(**c) for c in datos]

    def ocupado(self, dia: str, hora: str) -> bool:
        return any(c.dia == dia and c.hora == hora for c in self._citas)

    def reservar(self, cita: Cita) -> bool:
        """Reserva la cita. Devuelve False si ese horario ya se ocupó."""
        with self._lock:
            if self.ocupado(cita.dia, cita.hora):
                return False
            self._citas.append(cita)
            self._guardar()
            return True

    def citas(self) -> list[Cita]:
        return list(self._citas)

    def _guardar(self) -> None:
        if not self._archivo:
            return
        self._archivo.parent.mkdir(parents=True, exist_ok=True)
        temporal = self._archivo.with_suffix(".tmp")
        temporal.write_text(json.dumps([asdict(c) for c in self._citas], ensure_ascii=False, indent=2), encoding="utf-8")
        temporal.replace(self._archivo)
