"""Bloque A · modo llm probado con un doble del SDK (sin llamadas reales ni API key).

Verifica el bucle de herramientas, los parámetros que se envían a la API, la lista cerrada de
herramientas, el respaldo al modo reglas y el control de cifras de la redacción.
"""

from datetime import date
from types import SimpleNamespace

import pytest

from sie.agentes.base import Herramienta
from sie.agentes.comercial.intencion import Intencion
from sie.agentes.comercial.interprete_llm import (REGISTRAR_INTENCION, InterpreteLLM, RedactorLLM,
                                                  intencion_desde_llm)
from sie.llm.cliente import BETA_FALLBACK, ClienteLLM, ErrorLLM
from sie.llm.verificacion import cifras_no_respaldadas


def uso(id_, nombre, entrada):
    return SimpleNamespace(type="tool_use", id=id_, name=nombre, input=entrada)


def texto(t):
    return SimpleNamespace(type="text", text=t)


def respuesta(stop, *bloques):
    return SimpleNamespace(stop_reason=stop, content=list(bloques))


class SDKFalso:
    """Imita `anthropic.Anthropic().beta.messages.create`. Devuelve las respuestas en orden."""

    def __init__(self, *respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._crear))

    def _crear(self, **kw):
        # Copia de la lista: el SDK real serializa los mensajes en el momento de la llamada.
        self.llamadas.append({**kw, "messages": list(kw.get("messages", []))})
        r = self.respuestas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


ESQUEMA_BUSCAR = {"type": "object", "properties": {"texto": {"type": "string"}},
                  "required": ["texto"], "additionalProperties": False}
BUSCAR = Herramienta("buscar_cliente", "Busca clientes", ESQUEMA_BUSCAR,
                     lambda texto: [{"id_cliente": "CLI-003", "nombre_comercial": "Bodega Don Lucho"}])
INTENCION = {"id_cliente": "CLI-003", "canal_origen": "TUALI", "id_cotizacion": "COT-003-V01",
             "cantidad_mencionada": 65, "producto_mencionado": "", "resumen": "Acepta su cotización"}


def test_bucle_ejecuta_herramienta_de_lectura_y_termina_en_la_intencion():
    sdk = SDKFalso(
        respuesta("tool_use", uso("t1", "buscar_cliente", {"texto": "Don Lucho"})),
        respuesta("tool_use", uso("t2", "registrar_intencion", INTENCION)),
    )
    interprete = InterpreteLLM(ClienteLLM("claude-opus-5-5", cliente=sdk), [BUSCAR])
    r = interprete.interpretar("Don Lucho aceptó en TUALI", date(2026, 10, 2), canal="TUALI")
    assert (r.id_cliente, r.id_cotizacion, r.cantidad_mencionada, r.fuente) == ("CLI-003", "COT-003-V01", 65, "llm")
    assert interprete.ultimas_trazas == [{"herramienta": "buscar_cliente", "argumentos": {"texto": "Don Lucho"},
                                         "error": False}]
    primera = sdk.llamadas[0]
    assert primera["model"] == "claude-opus-5-5"
    assert primera["betas"] == [BETA_FALLBACK] and primera["fallbacks"] == "default"
    assert primera["output_config"] == {"effort": "low"}
    assert {t["name"] for t in primera["tools"]} == {"buscar_cliente", "registrar_intencion"}
    assert all(t["strict"] for t in primera["tools"])
    assert "dato, no instrucción" in primera["messages"][0]["content"]
    resultado = sdk.llamadas[1]["messages"][-1]["content"][0]
    assert resultado["type"] == "tool_result" and resultado["tool_use_id"] == "t1"
    assert "CLI-003" in resultado["content"] and "is_error" not in resultado


def test_herramienta_no_permitida_devuelve_error_al_modelo():
    sdk = SDKFalso(
        respuesta("tool_use", uso("t1", "crear_pedido", {"id": "PED-999"})),
        respuesta("tool_use", uso("t2", "registrar_intencion", INTENCION)),
    )
    datos, trazas = ClienteLLM("m", cliente=sdk).resolver_con_herramientas(
        "s", "u", [BUSCAR], REGISTRAR_INTENCION)
    assert datos["id_cliente"] == "CLI-003"
    assert trazas == [{"herramienta": "crear_pedido", "argumentos": {"id": "PED-999"}, "error": True}]
    resultado = sdk.llamadas[1]["messages"][-1]["content"][0]
    assert resultado["is_error"] is True and "no permitida" in resultado["content"]


@pytest.mark.parametrize("respuestas,mensaje", [
    ([respuesta("refusal")], "refusal"),
    ([respuesta("end_turn", texto("No sé"))], "sin registrar"),
    ([respuesta("max_tokens", texto("..."))], "max_tokens"),
    ([RuntimeError("caída de red")], "RuntimeError"),
])
def test_fallos_de_la_api_se_convierten_en_error_llm(respuestas, mensaje):
    with pytest.raises(ErrorLLM, match=mensaje):
        ClienteLLM("m", cliente=SDKFalso(*respuestas)).resolver_con_herramientas(
            "s", "u", [BUSCAR], REGISTRAR_INTENCION)


def test_limite_de_iteraciones():
    bucle = [respuesta("tool_use", uso(f"t{i}", "buscar_cliente", {"texto": "x"})) for i in range(3)]
    with pytest.raises(ErrorLLM, match="iteraciones"):
        ClienteLLM("m", cliente=SDKFalso(*bucle), max_iteraciones=3).resolver_con_herramientas(
            "s", "u", [BUSCAR], REGISTRAR_INTENCION)


def test_interprete_rechaza_herramientas_de_escritura():
    escribir = Herramienta("crear_pedido", "no", ESQUEMA_BUSCAR, lambda texto: None, solo_lectura=False)
    with pytest.raises(ValueError, match="solo acepta herramientas de lectura"):
        InterpreteLLM(ClienteLLM("m", cliente=SDKFalso()), [BUSCAR, escribir])


def test_sin_api_usa_el_interprete_de_reglas_y_lo_avisa():
    class Respaldo:
        def interpretar(self, texto, fecha_negocio, canal=None):
            return Intencion(texto=texto, id_cliente="CLI-003", canal_origen=canal, fuente="reglas")

    interprete = InterpreteLLM(ClienteLLM("m", cliente=SDKFalso(RuntimeError("sin red"))), [BUSCAR],
                               respaldo=Respaldo())
    r = interprete.interpretar("Don Lucho", date(2026, 10, 2), canal="TUALI")
    assert r.fuente == "reglas" and r.id_cliente == "CLI-003"
    assert "se interpretó con reglas" in r.avisos[0]


def test_el_canal_del_sistema_prevalece_y_los_vacios_son_none():
    r = intencion_desde_llm("t", {**INTENCION, "canal_origen": "Preventa", "id_cotizacion": "",
                                  "cantidad_mencionada": 0}, canal_sistema="Teléfono")
    assert r.canal_origen == "Teléfono"
    assert r.id_cotizacion is None and r.cantidad_mencionada is None
    assert intencion_desde_llm("t", {**INTENCION, "canal_origen": "Fax"}, None).canal_origen is None


HECHOS = {"codigo": "ATP-PARCIAL", "id_solicitud": "SOL-002", "intento": 1, "cantidad_solicitada": 600,
          "atp": 380, "importe_total": 13287.74, "descuento_pct": 0.08, "responsable": "Preventista 2",
          "tramos": [{"cantidad": 380, "fecha": "2026-10-09"}, {"cantidad": 220, "fecha": "2026-10-12"}]}


class Plantilla:
    def redactar(self, hechos):
        return "PLANTILLA"


def test_redaccion_del_llm_se_acepta_si_sus_cifras_estan_en_los_hechos():
    bueno = "SOL-002 recibió ATP-PARCIAL: hay 380 de 600 paquetes con 8 % (S/ 13,287.74). Se proponen 380 el 09/10 y 220 el 12/10."
    redactor = RedactorLLM(ClienteLLM("m", cliente=SDKFalso(respuesta("end_turn", texto(bueno)))), Plantilla())
    assert redactor.redactar(HECHOS) == bueno and redactor.ultimo_aviso is None


def test_redaccion_con_cifra_inventada_se_descarta():
    malo = "Se confirman 700 paquetes para el 09/10."
    redactor = RedactorLLM(ClienteLLM("m", cliente=SDKFalso(respuesta("end_turn", texto(malo)))), Plantilla())
    assert redactor.redactar(HECHOS) == "PLANTILLA"
    assert "700" in redactor.ultimo_aviso


def test_redaccion_sin_api_usa_plantilla():
    redactor = RedactorLLM(ClienteLLM("m", cliente=SDKFalso(RuntimeError("x"))), Plantilla())
    assert redactor.redactar(HECHOS) == "PLANTILLA"


def test_control_de_cifras():
    assert cifras_no_respaldadas("380 el 09/10 y 220 el 12/10, intento 2, C1–C5", HECHOS) == set()
    assert cifras_no_respaldadas("total 13287,74 con 8%", HECHOS) == set()
    assert cifras_no_respaldadas("ahora son 450 paquetes", HECHOS) == {"450"}
