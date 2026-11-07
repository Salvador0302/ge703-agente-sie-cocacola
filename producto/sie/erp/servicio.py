"""Capa I8 + ERP simulado: punto de entrada único para el agente.

Recibe EV-02/EV-05 y responde EV-03/EV-04. Orden de controles (plan PC3, §6):
P1 datos obligatorios (`DATO-OBLIG`) → P2 idempotencia (un mismo `id_solicitud + intento` devuelve la misma
respuesta sin crear nada) → P2 duplicado (`DUPLICADO` si la solicitud o la cotización ya tiene pedido) →
C1–C5 (`reglas.evaluar`). Si el código crea pedido, inserta pedidos_cab/det con el ID `PED-NNN` y los mismos
importes que el EP; registra cada intento en `solicitudes_pedido` y los tramos en `promesa_tramos`.
Cada paso queda en la bitácora (agente "erp"). Es el único código del proyecto que crea pedidos (ADR-003).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date

from sie.bitacora import Bitacora, EntradaBitacora
from sie.contrato import (CATALOGO, Codigo, EstadoSolicitud, EventoContrato, PedidoResumen, PromesaAlternativa,
                          RespuestaERP, SolicitudPedido, id_pedido_para)
from sie.erp import atp, causas, importes, promesa, reglas
from sie.erp.atp import DetalleATP
from sie.erp.causas import CausaFaltante

_CONTROLES = (("C1", "cliente"), ("C2", "crédito"), ("C3", "precio vigente"), ("C4", "descuento"), ("C5", "ATP"))


def _dm(fecha: date) -> str:
    return fecha.strftime("%d/%m")


def _si_no(valor: bool) -> str:
    return "Si" if valor else "No"


class ServicioERP:
    def __init__(self, conn: sqlite3.Connection, bitacora: Bitacora | None = None) -> None:
        self.conn = conn
        self.bitacora = bitacora

    # ----------------------------------------------------------------------- consultas no vinculantes (I3)

    def consultar_atp(self, id_producto: str, fecha: date) -> DetalleATP:
        """Consulta no vinculante (I3): no reserva nada."""
        return atp.calcular(self.conn, id_producto, fecha)

    def explicar_faltante(self, id_producto: str, fecha: date) -> CausaFaltante | None:
        return causas.explicar_faltante(self.conn, id_producto, fecha)

    # ----------------------------------------------------------------------- EV-02 / EV-05

    def recibir(self, sol: SolicitudPedido, run_id: str = "") -> RespuestaERP:
        """Procesa EV-02 o EV-05 y devuelve la respuesta del contrato. Único método que crea pedidos."""
        log = _Registro(self.bitacora, sol, run_id)
        log(f"recibir {str(sol.evento)[:5]}", f"{sol.tipo_mensaje} · canal {sol.canal_origen}")

        faltan = sol.faltantes()
        cotizacion = self.conn.execute("SELECT * FROM cotizaciones_cab WHERE id_cotizacion = ?",
                                       (sol.id_cotizacion,)).fetchone() if sol.id_cotizacion else None
        if not faltan and cotizacion is None:
            faltan = ["id_cotizacion (no existe en el CRM)"]
        if faltan:
            causa = f"Faltan datos obligatorios: {', '.join(faltan)} (P1)"
            resp = self._rechazo(sol, Codigo.DATO_OBLIG, causa)
            log("P1 datos obligatorios", f"F · {causa}", regla="P1", codigo=str(resp.codigo_respuesta))
            if cotizacion is not None and sol.id_solicitud and sol.intento:
                with self.conn:
                    self._guardar_solicitud(sol, resp, cantidad_atp=0, fecha_promesa=None)
            return resp

        previa = self.conn.execute("SELECT * FROM solicitudes_pedido WHERE id_solicitud = ? AND intento = ?",
                                   (sol.id_solicitud, sol.intento)).fetchone()
        if previa is not None:
            resp = self._respuesta_guardada(previa)
            log("P2 idempotencia", "intento ya procesado: se devuelve la misma respuesta", regla="P2",
                codigo=str(resp.codigo_respuesta))
            return resp

        existente = self.conn.execute(
            "SELECT id_pedido FROM pedidos_cab WHERE id_cotizacion = ? OR id_pedido = ? LIMIT 1",
            (sol.id_cotizacion, id_pedido_para(sol.id_solicitud))).fetchone()
        if existente is not None:
            causa = f"La cotización {sol.id_cotizacion} ya tiene el pedido {existente['id_pedido']} (R7)"
            resp = self._rechazo(sol, Codigo.DUPLICADO, causa, id_pedido=existente["id_pedido"])
            log("P2 duplicado", f"F · {causa}", regla="P2", codigo=str(resp.codigo_respuesta),
                ids={"id_pedido": existente["id_pedido"]})
            with self.conn:
                self._guardar_solicitud(sol, resp, cantidad_atp=0, fecha_promesa=None, id_pedido=None)
            return resp

        ev = reglas.evaluar(self.conn, sol)
        decide = "C5" if ev.regla in ("C5", "C5b") else ev.regla
        for regla, nombre in _CONTROLES:
            ok = getattr(ev, {"C1": "c1_cliente", "C2": "c2_credito", "C3": "c3_precio", "C4": "c4_descuento",
                              "C5": "c5_atp"}[regla])
            log(f"{regla} {nombre}", f"{'V' if ok else 'F'} · {ev.textos[regla]}", regla=regla,
                codigo=str(ev.codigo) if regla == decide else None)

        causa_faltante = None
        if not ev.c5_atp:
            corta = next(l for l in sol.lineas if l.cantidad > ev.atp_por_linea[l.numero_linea].disponible)
            causa_faltante = causas.explicar_faltante(self.conn, corta.id_producto, sol.fecha_envio)
            if causa_faltante is not None:
                c = causa_faltante
                log("causa del faltante",
                    f"{c.id_ot}: {c.horas_parada} h de parada en {c.id_activo} · −{c.paquetes_perdidos} paq · "
                    f"ATP {c.atp_con_parada} (sin la parada {c.atp_sin_parada})",
                    regla="R6", ids={"id_ot": c.id_ot, "id_activo": c.id_activo, "id_reposicion": c.id_reposicion},
                    detalle=c.a_dict())

        cantidad_atp = sum(min(l.cantidad, max(ev.atp_por_linea[l.numero_linea].disponible, 0)) for l in sol.lineas)
        with self.conn:
            if ev.codigo == Codigo.OK_ACEPTADO:
                resp = self._crear_pedido(sol, ev, log)
                self._guardar_solicitud(sol, resp, cantidad_atp, resp.pedido.fecha_prometida, resp.id_pedido)
            elif ev.codigo == Codigo.OK_PROMESA_ALT:
                resp = self._crear_pedido(sol, ev, log, promesa_aceptada=True)
                self._guardar_solicitud(sol, resp, cantidad_atp, sol.aceptacion.tramos_aceptados[-1].fecha,
                                        resp.id_pedido)
                self._guardar_tramos(sol, sol.aceptacion.tramos_aceptados)
            elif ev.codigo == Codigo.ATP_PARCIAL:
                propuesta = promesa.proponer(self.conn, sol, ev)
                resp = self._promesa_alternativa(sol, ev, propuesta, causa_faltante)
                fecha = propuesta.tramos[-1].fecha if propuesta.tramos else None
                self._guardar_solicitud(sol, resp, cantidad_atp, fecha)
                self._guardar_tramos(sol, propuesta.tramos)
            else:
                resp = self._rechazo(sol, ev.codigo, ev.causa)
                self._guardar_solicitud(sol, resp, cantidad_atp, None)
        log(f"responder {str(resp.evento)[:5]}", f"{resp.codigo_respuesta} · {resp.id_pedido or 'sin pedido'} · "
            f"responsable {resp.responsable_siguiente_paso}", codigo=str(resp.codigo_respuesta),
            ids={"id_pedido": resp.id_pedido} if resp.id_pedido else None)
        return resp

    # ----------------------------------------------------------------------- respuestas

    def _ejecutivo(self, id_cliente: str) -> str:
        fila = self.conn.execute("SELECT ejecutivo_cuenta FROM clientes WHERE id_cliente = ?", (id_cliente,)).fetchone()
        return (fila["ejecutivo_cuenta"] if fila else None) or "Preventista"

    def _rechazo(self, sol: SolicitudPedido, codigo: Codigo, causa: str, id_pedido: str | None = None) -> RespuestaERP:
        e = CATALOGO[codigo]
        return RespuestaERP(id_solicitud=sol.id_solicitud, intento=sol.intento, codigo_respuesta=codigo,
                            estado_solicitud=e.estado, id_pedido=id_pedido,
                            responsable_siguiente_paso=e.quien_corrige or self._ejecutivo(sol.id_cliente),
                            siguiente_paso=e.siguiente_paso, evento=e.evento, causa=causa)

    def _promesa_alternativa(self, sol: SolicitudPedido, ev: reglas.Evaluacion, propuesta: PromesaAlternativa,
                             causa: CausaFaltante | None) -> RespuestaERP:
        t = propuesta.tramos
        if len(t) >= 2:
            siguiente = f"Confirmar con el cliente {t[0].cantidad} el {_dm(t[0].fecha)} y {t[1].cantidad} el {_dm(t[1].fecha)}"
        elif t:
            siguiente = (f"Confirmar con el cliente {t[0].cantidad} el {_dm(t[0].fecha)}; Planeamiento CD debe "
                         f"programar la reposición de {propuesta.cantidad_pendiente} paquetes")
        else:
            siguiente = f"Planeamiento CD debe programar la reposición de {propuesta.cantidad_pendiente} paquetes"
        texto_causa = ev.causa + (f" · causa {causa.id_ot}" if causa else "")
        return RespuestaERP(id_solicitud=sol.id_solicitud, intento=sol.intento, codigo_respuesta=Codigo.ATP_PARCIAL,
                            estado_solicitud=EstadoSolicitud.PROMESA_ALTERNATIVA, id_pedido=None,
                            responsable_siguiente_paso=f"Planeamiento CD → {self._ejecutivo(sol.id_cliente)}",
                            siguiente_paso=siguiente, evento=EventoContrato.EV04, causa=texto_causa,
                            promesa_alternativa=propuesta)

    def _crear_pedido(self, sol: SolicitudPedido, ev: reglas.Evaluacion, log: _Registro,
                      promesa_aceptada: bool = False) -> RespuestaERP:
        id_pedido = id_pedido_para(sol.id_solicitud)
        cot = self.conn.execute("SELECT * FROM cotizaciones_cab WHERE id_cotizacion = ?", (sol.id_cotizacion,)).fetchone()
        ejecutivo = self._ejecutivo(sol.id_cliente)
        prometida = promesa.fecha_entrega(self.conn, sol.id_direccion_entrega, sol.fecha_envio)
        revision, responsable_exc, causa_exc = None, None, None
        siguiente = CATALOGO[ev.codigo].siguiente_paso
        if promesa_aceptada:
            tramos = sol.aceptacion.tramos_aceptados
            revision = tramos[-1].fecha
            pendiente = sum(t.cantidad for t in tramos[1:])
            responsable_exc = f"Planeamiento CD y {ejecutivo}"
            causa_exc = (f"ATP {tramos[0].cantidad} de {sol.cantidad_total}; {pendiente} en reposición desde planta, "
                         f"prevista {_dm(revision)}")
            siguiente = f"Seguimiento de la reposición de {pendiente} paquetes"
        por_linea = [(l, importes.de_linea(l.cantidad, l.precio_unitario, l.descuento_pct)) for l in sol.lineas]
        total = importes.CERO
        for _, imp in por_linea:
            total = total + imp
        self.conn.execute(
            "INSERT INTO pedidos_cab (id_pedido, id_cotizacion, id_direccion_entrega, fecha_confirmacion, "
            "fecha_prometida, fecha_revision_promesa, estado_pedido, resultado_credito, acepta_entrega_parcial, "
            "condicion_facturacion, moneda, responsable_excepcion, causa_excepcion, base_imponible, importe_igv, "
            "importe_total) VALUES (?, ?, ?, ?, ?, ?, 'Confirmado', 'Aprobado', ?, ?, ?, ?, ?, ?, ?, ?)",
            (id_pedido, sol.id_cotizacion, sol.id_direccion_entrega, sol.fecha_envio.isoformat(), prometida.isoformat(),
             revision.isoformat() if revision else None, _si_no(sol.acepta_entrega_parcial),
             cot["condicion_facturacion"] if cot else "Por entrega", sol.moneda, responsable_exc, causa_exc,
             float(total.base), float(total.igv), float(total.total)))
        self.conn.executemany(
            "INSERT INTO pedidos_det (id_pedido, numero_linea, id_producto, cantidad, id_precio, precio_unitario, "
            "descuento_pct, id_regla_descuento, tasa_igv, importe_bruto, importe_descuento, base_imponible, "
            "importe_igv, importe_total) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(id_pedido, l.numero_linea, l.id_producto, l.cantidad, l.id_precio, l.precio_unitario, l.descuento_pct,
              l.id_regla_descuento, float(importes.IGV), *(float(x) for x in imp.tupla)) for l, imp in por_linea])
        log("crear pedido", f"{id_pedido} · S/ {total.total} · promesa {prometida.isoformat()}"
            + (f" · revisión {revision.isoformat()}" if revision else ""), ids={"id_pedido": id_pedido})
        return RespuestaERP(id_solicitud=sol.id_solicitud, intento=sol.intento, codigo_respuesta=ev.codigo,
                            estado_solicitud=EstadoSolicitud.ACEPTADA, id_pedido=id_pedido,
                            responsable_siguiente_paso=ejecutivo, siguiente_paso=siguiente, evento=EventoContrato.EV03,
                            causa=ev.causa,
                            pedido=PedidoResumen(sol.fecha_envio, prometida, revision, "Confirmado"))

    def _respuesta_guardada(self, fila: sqlite3.Row) -> RespuestaERP:
        if fila["respuesta_json"]:
            return RespuestaERP.desde_dict(json.loads(fila["respuesta_json"]))
        codigo = Codigo(fila["codigo_respuesta"])  # intento histórico del seed (sin respuesta completa)
        return RespuestaERP(id_solicitud=fila["id_solicitud"], intento=fila["intento"], codigo_respuesta=codigo,
                            estado_solicitud=EstadoSolicitud(fila["estado_solicitud"]), id_pedido=fila["id_pedido"],
                            responsable_siguiente_paso=fila["responsable"] or "",
                            siguiente_paso=fila["siguiente_paso"] or "", evento=CATALOGO[codigo].evento,
                            causa=fila["causa"])

    # ----------------------------------------------------------------------- persistencia del contrato

    def _guardar_solicitud(self, sol: SolicitudPedido, resp: RespuestaERP, cantidad_atp: int,
                           fecha_promesa: date | None, id_pedido: str | None = None) -> None:
        self.conn.execute(
            "INSERT INTO solicitudes_pedido (id_solicitud, intento, tipo_mensaje, id_cotizacion, id_cliente, "
            "sistema_origen, fecha_envio, cantidad_solicitada, cantidad_atp_confirmada, fecha_promesa_propuesta, "
            "acepta_entrega_parcial, codigo_respuesta, estado_solicitud, id_pedido, responsable, siguiente_paso, "
            "canal_origen, causa, respuesta_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (sol.id_solicitud, sol.intento, str(sol.tipo_mensaje), sol.id_cotizacion, sol.id_cliente,
             sol.sistema_origen, sol.fecha_envio.isoformat(), sol.cantidad_total, cantidad_atp,
             fecha_promesa.isoformat() if fecha_promesa else None, _si_no(sol.acepta_entrega_parcial),
             str(resp.codigo_respuesta), str(resp.estado_solicitud), id_pedido, resp.responsable_siguiente_paso,
             resp.siguiente_paso, str(sol.canal_origen), resp.causa,
             json.dumps(resp.a_dict(), ensure_ascii=False)))

    def _guardar_tramos(self, sol: SolicitudPedido, tramos) -> None:
        self.conn.executemany(
            "INSERT INTO promesa_tramos (id_solicitud, intento, numero_tramo, cantidad, fecha, origen) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [(sol.id_solicitud, sol.intento, i, t.cantidad, t.fecha.isoformat(), t.origen)
             for i, t in enumerate(tramos, 1)])


class _Registro:
    """Escribe en la bitácora las entradas del ERP de una solicitud (si hay bitácora)."""

    def __init__(self, bitacora: Bitacora | None, sol: SolicitudPedido, run_id: str) -> None:
        self.bitacora = bitacora
        self.sol = sol
        self.run_id = run_id

    def __call__(self, paso: str, resultado: str, regla: str | None = None, codigo: str | None = None,
                 ids: dict | None = None, detalle: dict | None = None) -> None:
        if self.bitacora is None:
            return
        base = {"id_solicitud": self.sol.id_solicitud, "intento": self.sol.intento,
                "id_cotizacion": self.sol.id_cotizacion}
        self.bitacora.registrar(EntradaBitacora(
            agente="erp", paso=paso, resultado=resultado, fecha_negocio=self.sol.fecha_envio, run_id=self.run_id,
            regla=regla, codigo=codigo, ids={**base, **(ids or {})}, detalle=detalle or {}))
