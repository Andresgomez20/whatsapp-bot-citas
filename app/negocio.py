"""Datos del negocio. Es el único archivo que hay que cambiar para adaptar el bot a otro cliente."""

NOMBRE = "Barbería El Roble"

# id interno -> (nombre visible, precio en COP, duración en minutos)
SERVICIOS = {
    "corte": ("Corte clásico", 25_000, 40),
    "corte_barba": ("Corte + barba", 38_000, 60),
    "barba": ("Arreglo de barba", 18_000, 25),
}

HORAS = ["09:00", "10:30", "12:00", "14:30", "16:00", "17:30"]

# 0 = lunes … 6 = domingo
DIAS_CERRADO = {6}

DIAS_A_MOSTRAR = 3

HORARIO = "Abrimos de lunes a sábado, de 9:00 a 19:00.\nCalle 10 # 43-21, Medellín."

DIAS_SEMANA = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def precio(valor: int) -> str:
    """Formato colombiano: 25000 -> '$25.000'."""
    return "$" + f"{valor:,}".replace(",", ".")
