"""Bloque A · el orquestador enruta por tipo de evento y registra los agentes futuros."""

from datetime import date

import pytest

from sie.agentes.base import Agente, EstadoResultado, Evento, ResultadoAgente
from sie.bitacora import BitacoraMemoria
from sie.orquestador import AGENTES_PREVISTOS, RUTAS, Orquestador, TipoEventoDesconocido


class AgenteFalso:
    nombre = "comercial"
    tipos_evento = frozenset({"pedido", "decision_humana"})

    def __init__(self):
        self.recibidos = []

    def manejar(self, evento):
        self.recibidos.append(evento)
        return ResultadoAgente(agente=self.nombre, estado=EstadoResultado.COMPLETADO, mensaje="ok",
                               codigo="OK-ACEPTADO")


def test_enruta_pedido_al_agente_comercial():
    bit = BitacoraMemoria()
    agente = AgenteFalso()
    assert isinstance(agente, Agente)
    orq = Orquestador(bit, [agente])
    evento = Evento(tipo="pedido", fecha_negocio=date(2026, 10, 2), datos={"texto": "x"})
    r = orq.despachar(evento)
    assert r.codigo == "OK-ACEPTADO"
    assert r.run_id == evento.run_id
    assert agente.recibidos == [evento]
    assert [(e.agente, e.paso) for e in bit.entradas] == [("orquestador", "enrutar")]
    assert bit.entradas[0].fecha_negocio == date(2026, 10, 2)


@pytest.mark.parametrize("tipo,agente", [("entrega", "logistica"), ("factura", "finanzas_operativas"),
                                         ("abastecimiento", "cadena_suministro"), ("indicadores", "ceo")])
def test_agentes_futuros_quedan_registrados_como_no_implementados(tipo, agente):
    bit = BitacoraMemoria()
    r = Orquestador(bit, [AgenteFalso()]).despachar(Evento(tipo=tipo, fecha_negocio=date(2026, 10, 9)))
    assert r.estado == EstadoResultado.NO_IMPLEMENTADO
    assert r.agente == agente
    assert bit.entradas[-1].paso == "no implementado"
    assert bit.entradas[-1].codigo == "NO_IMPLEMENTADO"


def test_rutas_y_agentes_previstos_son_coherentes():
    nombres = [a.nombre for a in AGENTES_PREVISTOS]
    assert nombres == ["comercial", "cadena_suministro", "logistica", "finanzas_operativas", "ceo"]
    assert set(RUTAS.values()) == set(nombres)
    estado = {f["agente"]: f["estado"] for f in Orquestador(BitacoraMemoria(), [AgenteFalso()]).estado()}
    assert estado["comercial"] == "implementado"
    assert all(v == "no implementado aún" for k, v in estado.items() if k != "comercial")


def test_tipo_desconocido():
    with pytest.raises(TipoEventoDesconocido):
        Orquestador(BitacoraMemoria()).despachar(Evento(tipo="vender_todo", fecha_negocio=date(2026, 10, 2)))


def test_no_registra_agentes_fuera_del_plan_ni_rutas_ajenas():
    class Intruso(AgenteFalso):
        nombre = "aprobador_de_descuentos"

    class RutaAjena(AgenteFalso):
        tipos_evento = frozenset({"pedido", "factura"})

    with pytest.raises(ValueError):
        Orquestador(BitacoraMemoria(), [Intruso()])
    with pytest.raises(ValueError):
        Orquestador(BitacoraMemoria(), [RutaAjena()])
