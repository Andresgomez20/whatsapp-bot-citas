from datetime import date

from app.agenda import Agenda, Cita
from app.flujo import Bot

SABADO = date(2026, 11, 21)  # el siguiente día (domingo) está cerrado


def nuevo_bot(tmp_path=None, dueno="573001112233"):
    agenda = Agenda(tmp_path / "citas.json" if tmp_path else None)
    return Bot(agenda, telefono_dueno=dueno, hoy=lambda: SABADO)


def test_primer_mensaje_saluda_y_muestra_menu():
    bot = nuevo_bot()
    salida = bot.responder("57300", "buenas")
    assert "Hola" in salida[0].texto
    assert [i for i, _ in salida[1].opciones] == ["servicios", "agendar", "horario"]


def test_numero_del_menu_muestra_precios():
    bot = nuevo_bot()
    bot.responder("57300", "hola")
    salida = bot.responder("57300", "1")
    assert "$25.000" in salida[0].texto


def test_flujo_completo_agenda_y_avisa_al_dueno(tmp_path):
    bot = nuevo_bot(tmp_path)
    bot.responder("57300", "hola")
    assert bot.responder("57300", "agendar")[0].opciones[0][0] == "svc:corte"

    dias = bot.responder("57300", "svc:corte")[0].opciones
    assert [i for i, _ in dias] == ["dia:2026-11-23", "dia:2026-11-24", "dia:2026-11-25"]  # salta el domingo 22
    assert dias[0][1] == "Lun 23 nov"

    horas = bot.responder("57300", "dia:2026-11-23")[0].opciones
    assert ("hora:10:30", "10:30") in horas

    resumen = bot.responder("57300", "hora:10:30")[0]
    assert "Corte clásico" in resumen.texto and "10:30" in resumen.texto

    salida = bot.responder("57300", "Sí")  # texto con tilde también sirve
    assert "agendada" in salida[0].texto
    assert salida[1].para == "573001112233" and "Nueva cita" in salida[1].texto
    assert bot.agenda.citas() == [Cita("57300", "corte", "2026-11-23", "10:30")]
    assert (tmp_path / "citas.json").exists()


def test_hora_ocupada_no_se_ofrece():
    bot = nuevo_bot()
    bot.agenda.reservar(Cita("otro", "barba", "2026-11-23", "09:00"))
    bot.responder("57300", "hola")
    bot.responder("57300", "agendar")
    bot.responder("57300", "svc:barba")
    horas = [i for i, _ in bot.responder("57300", "dia:2026-11-23")[0].opciones]
    assert "hora:09:00" not in horas and "hora:10:30" in horas


def test_dos_personas_no_pueden_tomar_la_misma_hora():
    bot = nuevo_bot(dueno=None)
    for usuario in ("a", "b"):
        bot.responder(usuario, "hola")
        bot.responder(usuario, "agendar")
        bot.responder(usuario, "svc:corte")
        bot.responder(usuario, "dia:2026-11-23")
        bot.responder(usuario, "hora:12:00")
    assert "agendada" in bot.responder("a", "confirmar:si")[0].texto
    segunda = bot.responder("b", "confirmar:si")
    assert "alguien acaba de tomar" in segunda[0].texto


def test_texto_inesperado_y_cancelar():
    bot = nuevo_bot()
    bot.responder("57300", "hola")
    assert "No entendí" in bot.responder("57300", "asdfgh")[0].texto
    bot.responder("57300", "agendar")
    assert "Elige uno" in bot.responder("57300", "algo raro")[0].texto
    assert "cancelé" in bot.responder("57300", "cancelar")[0].texto
    assert bot.sesiones["57300"].estado == "menu"


def test_agenda_persiste_entre_reinicios(tmp_path):
    Agenda(tmp_path / "c.json").reservar(Cita("1", "corte", "2026-11-23", "09:00"))
    assert Agenda(tmp_path / "c.json").ocupado("2026-11-23", "09:00")
