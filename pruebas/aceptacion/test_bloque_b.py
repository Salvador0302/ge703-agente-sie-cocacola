"""Pruebas de aceptación · BLOQUE B (Gianmarco Leandro): datos, seed por corte y ERP simulado.

Terminado = este archivo con 0 pendientes y 0 fallas: `python -m pytest pruebas/aceptacion/test_bloque_b.py`.
Los valores esperados salen de los datos y mensajes del EP (docs/antecedentes/repo_ep_v3).
"""

import copy
import csv
from datetime import date

import pytest

from apoyo import EP_CSV, leer_ejemplo
from sie.bitacora import BitacoraMemoria
from sie.contrato import (Aceptacion, Canal, Codigo, LineaSolicitud, SolicitudPedido, TipoMensaje, Tramo,
                          id_solicitud_para)
from sie.db import seed
from sie.db.conexion import conectar
from sie.erp import atp, causas
from sie.erp.servicio import ServicioERP

D = date
CORTE_NORMAL, CORTE_EXCEPCION, DECISION = D(2026, 10, 2), D(2026, 10, 7), D(2026, 10, 8)

TABLAS_EP = ["campanas", "clientes", "contactos", "direcciones", "productos", "listas_precios", "reglas_descuento",
             "almacenes", "leads", "oportunidades", "cotizaciones_cab", "cotizaciones_det", "solicitudes_pedido",
             "pedidos_cab", "pedidos_det", "entregas_cab", "entregas_det", "facturas_cab", "facturas_det", "pagos",
             "movimientos_inventario"]
TABLAS_NUEVAS = ["activos", "ordenes_trabajo", "plan_reposicion", "promesa_tramos", "escalamientos", "bitacora",
                 "esquema_version"]
COLUMNAS_BITACORA = {"id", "ts", "fecha_negocio", "run_id", "agente", "paso", "regla", "codigo", "resultado",
                     "entrada_json", "ids_json", "escalado_a", "motivo", "fecha_limite", "respuesta_humana", "modo",
                     "detalle_json"}
COLUMNAS_ESCALAMIENTOS = {"id_escalamiento", "run_id", "id_solicitud", "intento", "objeto", "causa", "responsable",
                          "fecha_limite", "estado", "opciones_json", "datos_json", "respuesta_humana",
                          "fecha_respuesta", "evidencia"}
CAPTURA = {"TUALI": "Cliente en app TUALI (cotización aceptada en la app)",
           "Preventa": "Preventista en AC Móvil",
           "Teléfono": "Preventista registra en el CRM el pedido recibido por teléfono/WhatsApp"}
TRAMOS_SOL_002 = [Tramo(380, D(2026, 10, 9), "ALM-001 CD Lima Norte"),
                  Tramo(220, D(2026, 10, 12), "Reposición desde ALM-002 (planta) · plan APO (I2)")]


# --------------------------------------------------------------------------- apoyo

def base(corte):
    conn = conectar()
    seed.crear_base(conn, corte)
    return conn


def _si(valor):
    return valor in (1, "1", True, "Si", "Sí", "SI", "TRUE", "true")


def _num(valor):
    return float(valor) if valor not in (None, "") else 0.0


def _fecha(valor):
    return D.fromisoformat(str(valor)[:10]) if valor else None


def solicitud(conn, id_cotizacion, canal, fecha, intento=1, tipo=TipoMensaje.SOLICITUD_INICIAL, aceptacion=None):
    """Arma EV-02/EV-05 desde la base, como lo haría el CRM (independiente del bloque C)."""
    cab = conn.execute("SELECT * FROM cotizaciones_cab WHERE id_cotizacion = ?", (id_cotizacion,)).fetchone()
    opp = conn.execute("SELECT * FROM oportunidades WHERE id_oportunidad = ?", (cab["id_oportunidad"],)).fetchone()
    cli = conn.execute("SELECT * FROM clientes WHERE id_cliente = ?", (opp["id_cliente"],)).fetchone()
    det = conn.execute("SELECT * FROM cotizaciones_det WHERE id_cotizacion = ? ORDER BY numero_linea",
                       (id_cotizacion,)).fetchall()
    return SolicitudPedido(
        id_solicitud=id_solicitud_para(id_cotizacion), intento=intento, tipo_mensaje=tipo, canal_origen=Canal(canal),
        fecha_envio=fecha, id_cotizacion=id_cotizacion, version_cotizacion=int(_num(cab["version"])),
        id_oportunidad=cab["id_oportunidad"], id_cliente=cli["id_cliente"],
        codigo_cliente_erp=cli["codigo_cliente_erp"] or None, id_direccion_entrega=cab["id_direccion_entrega"],
        condicion_pago_dias=int(_num(cli["condicion_pago_dias"])), estado_descuento=cab["estado_descuento"],
        acepta_entrega_parcial=_si(cab["acepta_entrega_parcial"]),
        lineas=[LineaSolicitud(int(_num(d["numero_linea"])), d["id_producto"], int(_num(d["cantidad"])), d["id_precio"],
                               _num(d["precio_unitario"]), _num(d["descuento_pct"]), d["id_regla_descuento"])
                for d in det],
        importe_total_cotizado=_num(cab["importe_total"]), aprobador=cab["aprobador"] or None,
        fecha_aprobacion=_fecha(cab["fecha_aprobacion"]), capturado_por=CAPTURA[canal], aceptacion=aceptacion)


def aceptacion_sol_002():
    return Aceptacion(acepta=True, registrada_por="Preventista 2", fecha=DECISION, medio="Llamada telefónica",
                      evidencia="ACEP-SOL-002-2", tramos_aceptados=TRAMOS_SOL_002)


def leer_ep(nombre):
    with open(EP_CSV / f"{nombre}.csv", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sin_causa(d):
    d = copy.deepcopy(d)
    d.pop("causa", None)
    return d


def pedidos(conn, id_pedido):
    return conn.execute("SELECT COUNT(*) FROM pedidos_cab WHERE id_pedido = ?", (id_pedido,)).fetchone()[0]


# --------------------------------------------------------------------------- seed

def test_esquema_tiene_las_tablas_del_ep_y_las_nuevas():
    conn = base(CORTE_EXCEPCION)
    tablas = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert set(TABLAS_EP + TABLAS_NUEVAS) <= tablas
    assert COLUMNAS_BITACORA <= {r[1] for r in conn.execute("PRAGMA table_info(bitacora)")}
    assert COLUMNAS_ESCALAMIENTOS <= {r[1] for r in conn.execute("PRAGMA table_info(escalamientos)")}
    assert "causa" in {r[1] for r in conn.execute("PRAGMA table_info(solicitudes_pedido)")}


def test_seed_reproduce_los_mensajes_del_ep():
    """Si los datos de la base son fieles al EP, el EV-02 armado desde ella es idéntico al ejemplo."""
    assert solicitud(base(CORTE_NORMAL), "COT-003-V01", "TUALI", CORTE_NORMAL).a_dict() == \
        leer_ejemplo("EPN_SOL-003_intento1_solicitud.json")
    assert solicitud(base(CORTE_EXCEPCION), "COT-002-V02", "Teléfono", CORTE_EXCEPCION).a_dict() == \
        leer_ejemplo("EPX_SOL-002_intento1_solicitud.json")


def test_corte_no_carga_documentos_futuros():
    normal = base(CORTE_NORMAL)
    assert normal.execute("SELECT COUNT(*) FROM pedidos_cab").fetchone()[0] == 0
    assert normal.execute("SELECT COUNT(*) FROM solicitudes_pedido").fetchone()[0] == 0
    cotizaciones = {r[0] for r in normal.execute("SELECT id_cotizacion FROM cotizaciones_cab")}
    assert "COT-003-V01" in cotizaciones and "COT-002-V02" not in cotizaciones

    excepcion = base(CORTE_EXCEPCION)
    ids = {r[0] for r in excepcion.execute("SELECT id_pedido FROM pedidos_cab")}
    assert ids == {"PED-001", "PED-003", "PED-004", "PED-006", "PED-007", "PED-008"}
    cotizaciones = {r[0] for r in excepcion.execute("SELECT id_cotizacion FROM cotizaciones_cab")}
    assert {"COT-002-V01", "COT-002-V02"} <= cotizaciones


def test_avanzar_agrega_lo_ocurrido_sin_crear_el_pedido_de_la_demo():
    conn = base(CORTE_EXCEPCION)
    agregadas = seed.avanzar(conn, DECISION)
    assert agregadas > 0
    assert conn.execute("SELECT COUNT(*) FROM entregas_cab WHERE id_entrega = 'ENT-001'").fetchone()[0] == 1
    assert pedidos(conn, "PED-002") == 0
    assert seed.avanzar(conn, DECISION) == 0  # idempotente


def test_estados_previos_de_los_casos():
    def etapa(conn, opp):
        return conn.execute("SELECT etapa FROM oportunidades WHERE id_oportunidad = ?", (opp,)).fetchone()[0]

    def adopcion(conn, cli):
        return conn.execute("SELECT estado_adopcion_tuali FROM clientes WHERE id_cliente = ?", (cli,)).fetchone()[0]

    normal = base(CORTE_NORMAL)
    assert etapa(normal, "OPP-003") == "Propuesta" and adopcion(normal, "CLI-003") == "No usa"
    excepcion = base(CORTE_EXCEPCION)
    assert etapa(excepcion, "OPP-002") == "Propuesta"
    assert etapa(excepcion, "OPP-003") == "Ganada" and adopcion(excepcion, "CLI-003") == "Híbrido"
    dominios = {r[0] for r in excepcion.execute("SELECT DISTINCT estado_adopcion_tuali FROM clientes")}
    assert dominios <= {"Digital", "Híbrido", "No usa"}


def test_datos_sinteticos_marcados():
    conn = base(CORTE_EXCEPCION)
    assert conn.execute("SELECT COUNT(*) FROM clientes WHERE razon_social NOT LIKE '%(sintético)%'").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM contactos WHERE email NOT LIKE '%@example.com'").fetchone()[0] == 0
    for tabla in ("activos", "ordenes_trabajo", "plan_reposicion"):
        assert conn.execute(f"SELECT COUNT(*) FROM {tabla} WHERE sintetico <> 1").fetchone()[0] == 0, tabla


def test_parada_de_mantenimiento_para_el_informe():
    conn = base(CORTE_EXCEPCION)
    activos = {r["id_activo"]: r for r in conn.execute("SELECT * FROM activos")}
    assert {"ACT-LLN-01", "ACT-SOP-01", "ACT-CAM-01", "ACT-MON-01"} <= set(activos)
    assert activos["ACT-LLN-01"]["criticidad"] == "A"
    ot = conn.execute("SELECT * FROM ordenes_trabajo WHERE id_ot = 'OT-2026-0107'").fetchone()
    assert ot["id_activo"] == "ACT-LLN-01" and int(ot["horas_parada"]) == 96
    assert str(ot["inicio"]).startswith("2026-10-03") and str(ot["fin"]).startswith("2026-10-07")
    rep = conn.execute("SELECT * FROM plan_reposicion WHERE id_ot_causa = 'OT-2026-0107'").fetchone()
    assert rep["id_producto"] == "PRD-001" and int(rep["cantidad"]) == 240
    assert (str(rep["fecha_plan_original"]), str(rep["fecha_reprogramada"])) == ("2026-10-06", "2026-10-12")


# --------------------------------------------------------------------------- ATP y causa

def test_atp_de_la_excepcion_igual_al_validador_del_ep():
    conn = base(CORTE_EXCEPCION)
    d = atp.calcular(conn, "PRD-001", CORTE_EXCEPCION)
    assert (d.fisico, d.reservado, d.disponible) == (402, 22, 380)
    seed.avanzar(conn, DECISION)
    d = atp.calcular(conn, "PRD-001", DECISION)
    assert (d.fisico, d.reservado, d.disponible) == (392, 12, 380)


def test_atp_del_caso_normal():
    assert atp.calcular(base(CORTE_NORMAL), "PRD-001", CORTE_NORMAL).disponible == 492


def test_causa_del_faltante():
    conn = base(CORTE_EXCEPCION)
    c = causas.explicar_faltante(conn, "PRD-001", CORTE_EXCEPCION)
    assert (c.id_ot, c.id_activo, c.horas_parada, c.paquetes_perdidos) == ("OT-2026-0107", "ACT-LLN-01", 96, 240)
    assert (c.fecha_plan_original, c.fecha_reprogramada) == (D(2026, 10, 6), D(2026, 10, 12))
    assert (c.atp_con_parada, c.atp_sin_parada) == (380, 620)
    assert causas.explicar_faltante(conn, "PRD-003", CORTE_EXCEPCION) is None


# --------------------------------------------------------------------------- ERP: casos de la demo

def test_caso_normal_responde_como_el_ejemplo_del_ep():
    conn = base(CORTE_NORMAL)
    r = ServicioERP(conn, BitacoraMemoria()).recibir(solicitud(conn, "COT-003-V01", "TUALI", CORTE_NORMAL))
    esperado = leer_ejemplo("EPN_SOL-003_intento1_respuesta.json")
    esperado["pedido"] = {"fecha_confirmacion": "2026-10-02", "fecha_prometida": "2026-10-03",
                          "fecha_revision_promesa": None, "estado_pedido": "Confirmado"}
    assert sin_causa(r.a_dict()) == esperado
    assert pedidos(conn, "PED-003") == 1


def test_excepcion_intento_1_propone_promesa_y_no_crea_pedido():
    conn = base(CORTE_EXCEPCION)
    bit = BitacoraMemoria()
    r = ServicioERP(conn, bit).recibir(solicitud(conn, "COT-002-V02", "Teléfono", CORTE_EXCEPCION))
    assert sin_causa(r.a_dict()) == leer_ejemplo("EPX_SOL-002_intento1_respuesta.json")
    assert pedidos(conn, "PED-002") == 0
    erp = [e for e in bit.entradas if e.agente == "erp"]
    assert any(e.regla == "C5" and e.codigo == "ATP-PARCIAL" for e in erp)
    assert any(e.ids.get("id_ot") == "OT-2026-0107" for e in erp)
    assert all(e.fecha_negocio == CORTE_EXCEPCION for e in erp)


def test_excepcion_intento_2_con_aceptacion_crea_ped_002():
    conn = base(CORTE_EXCEPCION)
    erp = ServicioERP(conn, BitacoraMemoria())
    erp.recibir(solicitud(conn, "COT-002-V02", "Teléfono", CORTE_EXCEPCION))
    seed.avanzar(conn, DECISION)
    r = erp.recibir(solicitud(conn, "COT-002-V02", "Teléfono", DECISION, intento=2,
                              tipo=TipoMensaje.CONFIRMACION_PROMESA, aceptacion=aceptacion_sol_002()))
    esperado = leer_ejemplo("EPX_SOL-002_intento2_respuesta.json")
    esperado["pedido"]["estado_pedido"] = esperado["pedido"].pop("estado_pedido_al_corte")
    esperado["pedido"]["estado_pedido"] = "Confirmado"
    assert sin_causa(r.a_dict()) == esperado
    assert pedidos(conn, "PED-002") == 1
    tramos = conn.execute("SELECT cantidad, fecha FROM promesa_tramos WHERE id_solicitud = 'SOL-002' "
                          "AND intento = 2 ORDER BY numero_tramo").fetchall()
    assert [(int(t[0]), str(t[1])) for t in tramos] == [(380, "2026-10-09"), (220, "2026-10-12")]


# --------------------------------------------------------------------------- ERP: controles

def test_idempotencia_y_duplicado():
    conn = base(CORTE_NORMAL)
    erp = ServicioERP(conn, BitacoraMemoria())
    sol = solicitud(conn, "COT-003-V01", "TUALI", CORTE_NORMAL)
    primera = erp.recibir(sol)
    assert erp.recibir(sol).a_dict() == primera.a_dict()  # mismo id + intento: misma respuesta
    otra = erp.recibir(solicitud(conn, "COT-003-V01", "TUALI", CORTE_NORMAL, intento=2, tipo=TipoMensaje.REINTENTO))
    assert (otra.codigo_respuesta, otra.id_pedido) == (Codigo.DUPLICADO, "PED-003")
    assert otra.responsable_siguiente_paso == "Soporte de integración"
    assert pedidos(conn, "PED-003") == 1


def test_dato_obligatorio_y_ev05_sin_aceptacion():
    conn = base(CORTE_EXCEPCION)
    erp = ServicioERP(conn, BitacoraMemoria())
    sin_lineas = solicitud(conn, "COT-002-V02", "Teléfono", CORTE_EXCEPCION)
    sin_lineas.lineas = []
    r = erp.recibir(sin_lineas)
    assert (r.codigo_respuesta, r.responsable_siguiente_paso, r.id_pedido) == (Codigo.DATO_OBLIG, "Preventista", None)
    ev05 = solicitud(conn, "COT-002-V02", "Teléfono", DECISION, intento=2, tipo=TipoMensaje.CONFIRMACION_PROMESA)
    assert erp.recibir(ev05).codigo_respuesta == Codigo.DATO_OBLIG
    assert pedidos(conn, "PED-002") == 0


def test_cliente_sin_alta_es_cli_no_valido():
    conn = base(CORTE_NORMAL)
    sol = solicitud(conn, "COT-003-V01", "TUALI", CORTE_NORMAL)
    sol.id_cliente, sol.codigo_cliente_erp = "CLI-012", None
    r = ServicioERP(conn, BitacoraMemoria()).recibir(sol)
    assert (r.codigo_respuesta, r.responsable_siguiente_paso) == (Codigo.CLI_NO_VALIDO, "Analista de datos maestros")


def test_credito_bloqueado_cambia_el_codigo():
    """La prueba del EP depende de las reglas: si se bloquea el crédito de CLI-002, SOL-002 da CRED-BLOQ."""
    conn = base(CORTE_EXCEPCION)
    conn.execute("UPDATE clientes SET estado_credito = 'Bloqueado' WHERE id_cliente = 'CLI-002'")
    r = ServicioERP(conn, BitacoraMemoria()).recibir(solicitud(conn, "COT-002-V02", "Teléfono", CORTE_EXCEPCION))
    assert (r.codigo_respuesta, r.responsable_siguiente_paso) == (Codigo.CRED_BLOQ, "Créditos y cobranzas")


def test_descuento_sobre_12_por_ciento_nunca_pasa():
    conn = base(CORTE_EXCEPCION)
    sol = solicitud(conn, "COT-002-V02", "Teléfono", CORTE_EXCEPCION)
    sol.lineas[0].descuento_pct = 0.13
    assert ServicioERP(conn, BitacoraMemoria()).recibir(sol).codigo_respuesta == Codigo.DESC_SIN_APROB


@pytest.mark.parametrize("canal", ["TUALI", "Preventa", "Teléfono"])
def test_el_canal_no_cambia_el_resultado(canal):
    conn = base(CORTE_NORMAL)
    r = ServicioERP(conn, BitacoraMemoria()).recibir(solicitud(conn, "COT-003-V01", canal, CORTE_NORMAL))
    assert (r.codigo_respuesta, r.id_pedido) == (Codigo.OK_ACEPTADO, "PED-003")


# --------------------------------------------------------------------------- regresión del EP

def test_regresion_doce_intentos_y_pedidos_identicos_al_ep():
    """Reproduce los 12 intentos del EP en orden cronológico sobre una sola línea de tiempo."""
    conn = base(CORTE_NORMAL)
    erp = ServicioERP(conn, BitacoraMemoria())
    intentos = sorted(leer_ep("Solicitudes_pedido"), key=lambda f: f["fecha_envio"])  # orden estable
    for fila in intentos:
        fecha = D.fromisoformat(fila["fecha_envio"])
        seed.avanzar(conn, fecha)
        tipo = TipoMensaje(fila["tipo_mensaje"])
        acept = aceptacion_sol_002() if tipo == TipoMensaje.CONFIRMACION_PROMESA else None
        r = erp.recibir(solicitud(conn, fila["id_cotizacion"], fila["canal_origen"], fecha, int(fila["intento"]),
                                  tipo, acept))
        clave = f"{fila['id_solicitud']}-{fila['intento']}"
        assert str(r.codigo_respuesta) == fila["codigo_respuesta"], clave
        assert (r.id_pedido or "") == fila["id_pedido"], clave
    for ep in leer_ep("Pedidos_cab"):
        propio = conn.execute("SELECT * FROM pedidos_cab WHERE id_pedido = ?", (ep["id_pedido"],)).fetchone()
        for campo in ("base_imponible", "importe_igv", "importe_total"):
            assert _num(propio[campo]) == pytest.approx(_num(ep[campo]), abs=0.005), (ep["id_pedido"], campo)
        if ep["id_pedido"] in ("PED-002", "PED-003"):
            for campo in ("fecha_confirmacion", "fecha_prometida", "fecha_revision_promesa"):
                assert (propio[campo] or "") == ep[campo], (ep["id_pedido"], campo)
    for ep in leer_ep("Pedidos_det"):
        propio = conn.execute("SELECT * FROM pedidos_det WHERE id_pedido = ? AND numero_linea = ?",
                              (ep["id_pedido"], int(ep["numero_linea"]))).fetchone()
        assert propio["id_producto"] == ep["id_producto"]
        for campo in ("cantidad", "precio_unitario", "descuento_pct", "base_imponible", "importe_total"):
            assert _num(propio[campo]) == pytest.approx(_num(ep[campo]), abs=0.005), (ep["id_pedido"], campo)
