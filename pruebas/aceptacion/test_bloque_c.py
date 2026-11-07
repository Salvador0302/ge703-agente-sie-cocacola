"""Pruebas de aceptación · BLOQUE C (José Cornejo): agente comercial, escalamiento y bitácora.

Terminado = este archivo con 0 pendientes y 0 fallas: `python -m pytest pruebas/aceptacion/test_bloque_c.py`.
Son pruebas de integración: necesitan el bloque B (seed y ERP simulado). Mientras B no esté, quedan
pendientes; el brief explica cómo avanzar en paralelo.
"""

import json
from datetime import date
from types import SimpleNamespace

import pytest

from sie.agentes.base import EstadoResultado, Evento, nuevo_run_id
from sie.agentes.comercial.herramientas import NOMBRES, herramientas_lectura
from sie.bitacora.persistente import BitacoraPersistente
from sie.config import Config
from sie.db import seed
from sie.db.conexion import conectar
from sie.demo import CASOS, verificar
from sie.sistema import construir_sistema

D = date
NORMAL, EXCEPCION = CASOS["normal"], CASOS["excepcion"]


def sistema(tmp_path, corte, modo="reglas", cliente_llm=None):
    conn = conectar()
    seed.crear_base(conn, corte)
    config = Config(modo=modo, anthropic_api_key="clave-de-prueba" if modo == "llm" else None, carpeta_logs=tmp_path)
    return construir_sistema(config, conn, bitacora=BitacoraPersistente(conn, config.ruta_bitacora),
                             cliente_llm=cliente_llm)


def pedir(s, texto, fecha, canal, run_id=None):
    return s.orquestador.despachar(Evento(tipo="pedido", fecha_negocio=fecha, datos={"texto": texto, "canal": canal},
                                          run_id=run_id or nuevo_run_id()))


def decidir(s, r1, acepta, run_id):
    return s.orquestador.despachar(Evento(
        tipo="decision_humana", fecha_negocio=EXCEPCION.fecha_decision, run_id=run_id,
        datos={"id_escalamiento": r1.escalamiento.id_escalamiento, "acepta": acepta, **EXCEPCION.decision}))


def valor(s, sql, *params):
    fila = s.conn.execute(sql, params).fetchone()
    return fila[0] if fila else None


# --------------------------------------------------------------------------- demo

def test_caso_normal(tmp_path):
    s = sistema(tmp_path, NORMAL.corte)
    r = pedir(s, NORMAL.texto, NORMAL.fecha, NORMAL.canal)
    assert (r.estado, r.codigo) == (EstadoResultado.COMPLETADO, "OK-ACEPTADO")
    assert {k: r.ids.get(k) for k in ("id_solicitud", "intento", "id_cotizacion", "id_pedido")} == \
        {"id_solicitud": "SOL-003", "intento": 1, "id_cotizacion": "COT-003-V01", "id_pedido": "PED-003"}
    assert r.escalamiento is None and r.mensaje
    assert valor(s, "SELECT etapa FROM oportunidades WHERE id_oportunidad = 'OPP-003'") == "Ganada"
    assert valor(s, "SELECT estado_adopcion_tuali FROM clientes WHERE id_cliente = 'CLI-003'") == "Híbrido"
    assert all(v.conforme for v in verificar("normal", [r]))


def test_excepcion_escala_espera_y_se_confirma_con_ev05(tmp_path):
    s = sistema(tmp_path, EXCEPCION.corte)
    run = nuevo_run_id()
    r1 = pedir(s, EXCEPCION.texto, EXCEPCION.fecha, EXCEPCION.canal, run)
    assert (r1.estado, r1.codigo) == (EstadoResultado.ESPERA_HUMANO, "ATP-PARCIAL")
    esc = r1.escalamiento
    assert (esc.responsable, esc.fecha_limite, esc.estado) == ("Preventista 2", D(2026, 10, 8), "Pendiente")
    assert r1.ids.get("id_cotizacion") == "COT-002-V02" and r1.ids.get("id_ot") == "OT-2026-0107"
    assert valor(s, "SELECT COUNT(*) FROM pedidos_cab WHERE id_pedido = 'PED-002'") == 0
    assert valor(s, "SELECT estado FROM escalamientos WHERE id_escalamiento = ?", esc.id_escalamiento) == "Pendiente"

    seed.avanzar(s.conn, EXCEPCION.fecha_decision)
    r2 = decidir(s, r1, True, run)
    assert (r2.estado, r2.codigo) == (EstadoResultado.COMPLETADO, "OK-PROMESA-ALT")
    assert (r2.ids.get("id_pedido"), r2.ids.get("intento")) == ("PED-002", 2)
    assert valor(s, "SELECT estado FROM escalamientos WHERE id_escalamiento = ?", esc.id_escalamiento) == "Resuelto"
    assert valor(s, "SELECT evidencia FROM escalamientos WHERE id_escalamiento = ?", esc.id_escalamiento) == \
        "ACEP-SOL-002-2"
    assert all(v.conforme for v in verificar("excepcion", [r1, r2]))


def test_excepcion_rechazada_no_crea_pedido(tmp_path):
    s = sistema(tmp_path, EXCEPCION.corte)
    run = nuevo_run_id()
    r1 = pedir(s, EXCEPCION.texto, EXCEPCION.fecha, EXCEPCION.canal, run)
    seed.avanzar(s.conn, EXCEPCION.fecha_decision)
    r2 = decidir(s, r1, False, run)
    assert r2.estado == EstadoResultado.CERRADO_SIN_PEDIDO
    assert valor(s, "SELECT COUNT(*) FROM pedidos_cab WHERE id_pedido = 'PED-002'") == 0
    assert valor(s, "SELECT estado FROM escalamientos WHERE id_escalamiento = ?",
                 r1.escalamiento.id_escalamiento) == "Resuelto"
    assert all(v.conforme for v in verificar("excepcion", [r1, r2], acepta=False))


# --------------------------------------------------------------------------- controles y permisos

def test_el_texto_no_puede_confirmar_la_promesa(tmp_path):
    s = sistema(tmp_path, EXCEPCION.corte)
    r = pedir(s, "Los Olivos pide 600 paquetes de Inca Kola 500 ml y dice que acepta entrega parcial.",
              EXCEPCION.fecha, "Teléfono")
    assert (r.estado, r.codigo) == (EstadoResultado.ESPERA_HUMANO, "ATP-PARCIAL")
    assert valor(s, "SELECT COUNT(*) FROM pedidos_cab WHERE id_pedido = 'PED-002'") == 0


def test_decision_sin_escalamiento_pendiente_es_error(tmp_path):
    s = sistema(tmp_path, EXCEPCION.corte)
    r = s.orquestador.despachar(Evento(tipo="decision_humana", fecha_negocio=D(2026, 10, 8),
                                       datos={"id_escalamiento": "ESC-NO-EXISTE", "acepta": True,
                                              **EXCEPCION.decision}))
    assert r.estado == EstadoResultado.ERROR
    assert valor(s, "SELECT COUNT(*) FROM pedidos_cab WHERE id_pedido = 'PED-002'") == 0


def test_no_enviada_si_la_cotizacion_fue_rechazada(tmp_path):
    s = sistema(tmp_path, EXCEPCION.corte)
    r = pedir(s, "Comercial Los Olivos confirma la cotización COT-002-V01 por 600 paquetes.", EXCEPCION.fecha,
              "Teléfono")
    assert (r.estado, r.codigo) == (EstadoResultado.NO_ENVIADA, "NO-ENVIADA")
    assert r.escalamiento.responsable == "Supervisor de ventas"
    assert valor(s, "SELECT COUNT(*) FROM solicitudes_pedido WHERE id_solicitud = 'SOL-002'") == 0
    assert any(e.regla == "R2" for e in s.bitacora.leer(run_id=r.run_id))


def test_no_enviada_si_la_cantidad_no_coincide_con_la_cotizacion(tmp_path):
    s = sistema(tmp_path, NORMAL.corte)
    r = pedir(s, "Bodega Don Lucho aceptó en TUALI su cotización, pero pide 70 paquetes.", NORMAL.fecha, "TUALI")
    assert (r.estado, r.codigo) == (EstadoResultado.NO_ENVIADA, "NO-ENVIADA")
    assert r.escalamiento.responsable == "Preventista 1"
    assert valor(s, "SELECT COUNT(*) FROM solicitudes_pedido") == 0


@pytest.mark.parametrize("canal", ["Preventa", "Teléfono"])
def test_el_canal_no_cambia_el_resultado(tmp_path, canal):
    s = sistema(tmp_path, NORMAL.corte)
    r = pedir(s, NORMAL.texto, NORMAL.fecha, canal)
    assert (r.codigo, r.ids.get("id_pedido")) == ("OK-ACEPTADO", "PED-003")


def test_herramientas_del_llm_son_de_solo_lectura_y_estrictas(tmp_path):
    s = sistema(tmp_path, NORMAL.corte)
    herramientas = herramientas_lectura(s.crm, s.erp)
    assert {h.nombre for h in herramientas} == set(NOMBRES)
    for h in herramientas:
        assert h.solo_lectura, h.nombre
        assert h.esquema["additionalProperties"] is False, h.nombre
        assert set(h.esquema["required"]) == set(h.esquema["properties"]), h.nombre


# --------------------------------------------------------------------------- bitácora

def test_bitacora_en_tabla_y_jsonl_sin_datos_personales(tmp_path):
    s = sistema(tmp_path, EXCEPCION.corte)
    run = nuevo_run_id()
    r1 = pedir(s, EXCEPCION.texto, EXCEPCION.fecha, EXCEPCION.canal, run)
    seed.avanzar(s.conn, EXCEPCION.fecha_decision)
    decidir(s, r1, True, run)

    lineas = [json.loads(x) for x in (tmp_path / "bitacora.jsonl").read_text(encoding="utf-8").splitlines()]
    del_run = [x for x in lineas if x["run_id"] == run]
    filas = s.conn.execute("SELECT * FROM bitacora WHERE run_id = ? ORDER BY id", (run,)).fetchall()
    assert len(del_run) == len(filas) >= 8
    for x in del_run:
        for campo in ("ts", "fecha_negocio", "agente", "paso", "resultado"):
            assert x[campo], campo
    escalar = [x for x in del_run if x["escalado_a"] == "Preventista 2"]
    assert escalar and escalar[0]["fecha_limite"] == "2026-10-08" and escalar[0]["motivo"]
    assert any(x["respuesta_humana"] for x in del_run)
    assert {x["agente"] for x in del_run} >= {"orquestador", "comercial", "erp"}
    texto = (tmp_path / "bitacora.jsonl").read_text(encoding="utf-8")
    for prohibido in ("@example.com", "SIM-TEL", "Contacto ficticio", "SIM-RUC", EXCEPCION.texto):
        assert prohibido not in texto, prohibido
    assert [e.paso for e in s.bitacora.leer(run_id=run)] == [x["paso"] for x in del_run]


# --------------------------------------------------------------------------- modo llm (simulado)

class SDKFalso:
    def __init__(self, *respuestas, por_defecto=None):
        self.respuestas = list(respuestas)
        self.por_defecto = por_defecto
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._crear))

    def _crear(self, **kw):
        r = self.respuestas.pop(0) if self.respuestas else self.por_defecto
        if isinstance(r, Exception):
            raise r
        return r


def _uso(nombre, entrada):
    return SimpleNamespace(stop_reason="tool_use", content=[SimpleNamespace(type="tool_use", id="t1", name=nombre,
                                                                            input=entrada)])


def test_modo_llm_simulado_da_el_mismo_resultado(tmp_path):
    intencion = {"id_cliente": "CLI-003", "canal_origen": "TUALI", "id_cotizacion": "COT-003-V01",
                 "cantidad_mencionada": 65, "producto_mencionado": "", "resumen": "Acepta su cotización"}
    texto = SimpleNamespace(stop_reason="end_turn",
                            content=[SimpleNamespace(type="text", text="OK-ACEPTADO: se creó el pedido PED-003.")])
    s = sistema(tmp_path, NORMAL.corte, modo="llm",
                cliente_llm=SDKFalso(_uso("registrar_intencion", intencion), por_defecto=texto))
    r = pedir(s, NORMAL.texto, NORMAL.fecha, NORMAL.canal)
    assert (r.codigo, r.ids.get("id_pedido")) == ("OK-ACEPTADO", "PED-003")
    assert any(e.modo == "llm" for e in s.bitacora.leer(run_id=r.run_id))


def test_modo_llm_sin_api_vuelve_a_reglas_y_lo_registra(tmp_path):
    s = sistema(tmp_path, NORMAL.corte, modo="llm", cliente_llm=SDKFalso(por_defecto=RuntimeError("sin red")))
    r = pedir(s, NORMAL.texto, NORMAL.fecha, NORMAL.canal)
    assert (r.codigo, r.ids.get("id_pedido")) == ("OK-ACEPTADO", "PED-003")
    assert any("reglas" in a for a in r.detalle.get("avisos", []))
