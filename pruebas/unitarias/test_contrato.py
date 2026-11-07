"""Bloque A · el contrato tipado reproduce los mensajes y el catálogo del EP."""

import copy
import csv
from datetime import date

import pytest

from apoyo import RAIZ, leer_ejemplo
from sie.contrato import (CATALOGO, Aceptacion, Codigo, EstadoSolicitud, EventoContrato, RespuestaERP,
                          SolicitudPedido, TipoMensaje, Tramo, id_pedido_para, id_solicitud_para)


def test_solicitudes_del_ep_ida_y_vuelta(ejemplos):
    solicitudes = {n: d for n, d in ejemplos.items() if n.endswith("_solicitud.json")}
    assert len(solicitudes) == 6
    for nombre, d in solicitudes.items():
        assert SolicitudPedido.desde_dict(d).a_dict() == d, nombre


def test_respuestas_del_ep_ida_y_vuelta(ejemplos):
    respuestas = {n: d for n, d in ejemplos.items() if n.endswith("_respuesta.json")}
    assert len(respuestas) == 6
    for nombre, d in respuestas.items():
        esperado = copy.deepcopy(d)
        if "pedido" in esperado:  # v1.2: estado_pedido_al_corte → estado_pedido
            esperado["pedido"]["estado_pedido"] = esperado["pedido"].pop("estado_pedido_al_corte")
        assert RespuestaERP.desde_dict(d).a_dict() == esperado, nombre


def test_catalogo_igual_al_csv_del_contrato():
    with open(RAIZ / "arquitectura" / "contrato_i8" / "codigos_respuesta.csv", encoding="utf-8-sig", newline="") as f:
        filas = {r["Código"]: r for r in csv.DictReader(f)}
    assert set(filas) == {str(c) for c in Codigo} == {str(c) for c in CATALOGO}
    for codigo, entrada in CATALOGO.items():
        fila = filas[str(codigo)]
        assert entrada.significado == fila["Significado"]
        assert entrada.siguiente_paso == fila["Siguiente paso"]
        assert entrada.reintento == fila["¿Reintento?"]
        assert (entrada.quien_corrige or "—") == fila["Quién corrige"]


def test_estado_evento_y_pedido_por_codigo():
    assert CATALOGO[Codigo.ATP_PARCIAL].estado == EstadoSolicitud.PROMESA_ALTERNATIVA
    assert CATALOGO[Codigo.ATP_PARCIAL].evento == EventoContrato.EV04
    assert {c for c, e in CATALOGO.items() if e.crea_pedido} == {Codigo.OK_ACEPTADO, Codigo.OK_PROMESA_ALT}
    rechazos = {c for c, e in CATALOGO.items() if e.estado == EstadoSolicitud.RECHAZADA}
    assert rechazos == set(Codigo) - {Codigo.OK_ACEPTADO, Codigo.OK_PROMESA_ALT, Codigo.ATP_PARCIAL}


def test_datos_obligatorios():
    base = SolicitudPedido.desde_dict(leer_ejemplo("EPN_SOL-003_intento1_solicitud.json"))
    assert base.faltantes() == []
    assert base.evento == EventoContrato.EV02
    assert base.cantidad_total == 65

    sin_lineas = copy.deepcopy(base)
    sin_lineas.lineas = []
    assert "lineas" in sin_lineas.faltantes()

    sin_canal = copy.deepcopy(base)
    sin_canal.canal_origen = "WhatsApp"
    assert "canal_origen" in sin_canal.faltantes()

    sin_codigo_erp = copy.deepcopy(base)  # lo resuelve C1 (CLI-NO-VALIDO), no P1
    sin_codigo_erp.codigo_cliente_erp = None
    assert sin_codigo_erp.faltantes() == []

    linea_cero = copy.deepcopy(base)
    linea_cero.lineas[0].cantidad = 0
    assert "lineas[1].cantidad" in linea_cero.faltantes()


def test_ev05_exige_aceptacion_v12():
    ev05 = SolicitudPedido.desde_dict(leer_ejemplo("EPX_SOL-002_intento2_solicitud.json"))
    assert ev05.evento == EventoContrato.EV05
    assert "aceptacion" in ev05.faltantes()  # el ejemplo del EP no traía la evidencia (incidencia I-05)
    ev05.aceptacion = Aceptacion(
        acepta=True, registrada_por="Preventista 2", fecha=date(2026, 10, 8), medio="Llamada telefónica",
        evidencia="ACEP-SOL-002-2",
        tramos_aceptados=[Tramo(380, date(2026, 10, 9), "ALM-001 CD Lima Norte"),
                          Tramo(220, date(2026, 10, 12), "Reposición desde ALM-002 (planta) · plan APO (I2)")])
    assert ev05.faltantes() == []
    assert SolicitudPedido.desde_dict(ev05.a_dict()).a_dict() == ev05.a_dict()
    assert ev05.a_dict()["aceptacion"]["tramos_aceptados"][1] == {
        "cantidad": 220, "fecha": "2026-10-12", "origen": "Reposición desde ALM-002 (planta) · plan APO (I2)"}


def test_tipos_y_canales_del_ep():
    assert {str(t) for t in TipoMensaje} == {"Solicitud inicial", "Reintento", "Confirmación promesa"}


def test_identificadores_heredan_el_numero():
    assert id_solicitud_para("COT-003-V01") == "SOL-003"
    assert id_solicitud_para("COT-002-V02") == "SOL-002"
    assert id_pedido_para("SOL-002") == "PED-002"
    with pytest.raises(ValueError):
        id_solicitud_para("COTIZACION")
