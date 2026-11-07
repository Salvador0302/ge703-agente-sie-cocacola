"""Consultas del CRM simulado (SAP Sales Cloud [SUPUESTO]).

El CRM es sistema de registro de campaña, lead, oportunidad, cotización, canal y adopción de TUALI.
El agente lee aquí y arma EV-02/EV-05 con los datos de la cotización aceptada; nunca con cantidades,
precios o descuentos tomados del texto libre. Las únicas escrituras del CRM ocurren tras la respuesta
del ERP (EV-03): etapa de la oportunidad y adopción de TUALI (R9).
Las consultas no devuelven datos de contacto (nombres de personas, correos, teléfonos ni documentos).
"""

from __future__ import annotations

import sqlite3
import unicodedata
from datetime import date
from typing import Any

from sie.contrato import (Aceptacion, Canal, LineaSolicitud, RespuestaERP, SolicitudPedido, TipoMensaje,
                          id_solicitud_para)

#: Quién captura el pedido según el canal (R8), como en los mensajes de ejemplo del EP.
CAPTURADO_POR = {
    Canal.TUALI: "Cliente en app TUALI (cotización aceptada en la app)",
    Canal.PREVENTA: "Preventista en AC Móvil",
    Canal.TELEFONO: "Preventista registra en el CRM el pedido recibido por teléfono/WhatsApp",
}
_PREFIJOS_GENERICOS = ("bodega ", "comercial ", "minimarket ", "distribuidora ")


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes: 'Teléfono' → 'telefono'."""
    sin_tildes = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).lower()


def _si(valor: Any) -> bool:
    return valor in (1, "1", True, "Si", "Sí", "SI", "TRUE", "true")


def _fecha(valor: str | None) -> date | None:
    return date.fromisoformat(valor[:10]) if valor else None


class ConsultasCRM:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    # ----------------------------------------------------------------------- clientes

    def buscar_clientes(self, texto: str) -> list[dict[str, Any]]:
        """Clientes cuyo nombre comercial, razón social o ID coincide con `texto` (sin datos de contacto)."""
        t = normalizar(texto)
        encontrados = []
        for c in self.conn.execute("SELECT * FROM clientes ORDER BY id_cliente"):
            nombre = normalizar(c["nombre_comercial"])
            distintivo = next((nombre[len(p):] for p in _PREFIJOS_GENERICOS if nombre.startswith(p)), nombre)
            if (c["id_cliente"].lower() in t or nombre in t or (t and t in nombre)
                    or (len(distintivo) >= 5 and distintivo in t)):
                encontrados.append(self._cliente(c))
        return encontrados

    def identificar_cliente(self, texto: str) -> str | None:
        """El cliente mencionado en un texto libre; None si no hay o si es ambiguo."""
        candidatos = self.buscar_clientes(texto)
        if len(candidatos) == 1:
            return candidatos[0]["id_cliente"]
        t = normalizar(texto)
        exactos = [c for c in candidatos if normalizar(c["nombre_comercial"]) in t]
        return exactos[0]["id_cliente"] if len(exactos) == 1 else None

    def cliente(self, id_cliente: str) -> dict[str, Any] | None:
        fila = self.conn.execute("SELECT * FROM clientes WHERE id_cliente = ?", (id_cliente,)).fetchone()
        return self._cliente(fila) if fila else None

    @staticmethod
    def _cliente(c: sqlite3.Row) -> dict[str, Any]:
        return {"id_cliente": c["id_cliente"], "nombre_comercial": c["nombre_comercial"],
                "tipo_cliente": c["tipo_cliente"], "segmento_cliente": c["segmento_cliente"],
                "ejecutivo_cuenta": c["ejecutivo_cuenta"], "canal_pedido_habitual": c["canal_pedido_habitual"],
                "estado_adopcion_tuali": c["estado_adopcion_tuali"]}

    # ----------------------------------------------------------------------- cotizaciones

    def cotizaciones_del_cliente(self, id_cliente: str, fecha: date) -> list[dict[str, Any]]:
        """Cabeceras de cotización del cliente emitidas hasta `fecha`, con estado y vigencia."""
        filas = self.conn.execute(
            """
            SELECT c.id_cotizacion, c.version, c.fecha_emision, c.vigente_hasta, c.estado_cotizacion,
                   c.estado_descuento, c.importe_total,
                   (SELECT SUM(d.cantidad) FROM cotizaciones_det d WHERE d.id_cotizacion = c.id_cotizacion) AS cantidad_total,
                   EXISTS (SELECT 1 FROM pedidos_cab p WHERE p.id_cotizacion = c.id_cotizacion) AS tiene_pedido
            FROM cotizaciones_cab c JOIN oportunidades o ON o.id_oportunidad = c.id_oportunidad
            WHERE o.id_cliente = ? AND c.fecha_emision <= ?
            ORDER BY c.fecha_emision, c.version
            """, (id_cliente, fecha.isoformat())).fetchall()
        return [{**dict(f), "tiene_pedido": bool(f["tiene_pedido"])} for f in filas]

    def cotizacion(self, id_cotizacion: str) -> dict[str, Any] | None:
        """Cabecera con sus líneas (`lineas`), cliente y ejecutivo, o None si no existe."""
        cab = self.conn.execute(
            "SELECT c.*, o.id_cliente, cl.ejecutivo_cuenta FROM cotizaciones_cab c "
            "JOIN oportunidades o ON o.id_oportunidad = c.id_oportunidad "
            "JOIN clientes cl ON cl.id_cliente = o.id_cliente WHERE c.id_cotizacion = ?", (id_cotizacion,)).fetchone()
        if cab is None:
            return None
        lineas = [dict(d) for d in self.conn.execute(
            "SELECT numero_linea, id_producto, cantidad, id_precio, precio_unitario, descuento_pct, id_regla_descuento "
            "FROM cotizaciones_det WHERE id_cotizacion = ? ORDER BY numero_linea", (id_cotizacion,))]
        tiene_pedido = self.conn.execute("SELECT 1 FROM pedidos_cab WHERE id_cotizacion = ?", (id_cotizacion,)).fetchone()
        return {**dict(cab), "lineas": lineas, "cantidad_total": sum(int(l["cantidad"]) for l in lineas),
                "tiene_pedido": bool(tiene_pedido)}

    def ultimo_intento(self, id_solicitud: str) -> int:
        """Último intento registrado de la solicitud (0 si nunca se envió). Lectura de la bitácora I8."""
        fila = self.conn.execute("SELECT MAX(intento) FROM solicitudes_pedido WHERE id_solicitud = ?",
                                 (id_solicitud,)).fetchone()
        return int(fila[0] or 0)

    # ----------------------------------------------------------------------- mensajes del contrato

    def construir_solicitud(self, id_cotizacion: str, canal: Canal, fecha_envio: date, intento: int = 1,
                            tipo: TipoMensaje = TipoMensaje.SOLICITUD_INICIAL,
                            aceptacion: Aceptacion | None = None) -> SolicitudPedido:
        """Arma EV-02 (o EV-05 si `tipo` es Confirmación promesa) desde la cotización aceptada."""
        cot = self.cotizacion(id_cotizacion)
        if cot is None:
            raise LookupError(f"La cotización {id_cotizacion} no existe en el CRM")
        cli = self.conn.execute("SELECT * FROM clientes WHERE id_cliente = ?", (cot["id_cliente"],)).fetchone()
        canal = Canal(canal)
        return SolicitudPedido(
            id_solicitud=id_solicitud_para(id_cotizacion), intento=intento, tipo_mensaje=tipo, canal_origen=canal,
            fecha_envio=fecha_envio, id_cotizacion=id_cotizacion, version_cotizacion=int(cot["version"]),
            id_oportunidad=cot["id_oportunidad"], id_cliente=cot["id_cliente"],
            codigo_cliente_erp=cli["codigo_cliente_erp"] or None, id_direccion_entrega=cot["id_direccion_entrega"],
            condicion_pago_dias=int(cli["condicion_pago_dias"] or 0), estado_descuento=cot["estado_descuento"],
            acepta_entrega_parcial=_si(cot["acepta_entrega_parcial"]),
            lineas=[LineaSolicitud(int(l["numero_linea"]), l["id_producto"], int(l["cantidad"]), l["id_precio"],
                                   float(l["precio_unitario"]), float(l["descuento_pct"]), l["id_regla_descuento"])
                    for l in cot["lineas"]],
            importe_total_cotizado=float(cot["importe_total"]), aprobador=cot["aprobador"] or None,
            fecha_aprobacion=_fecha(cot["fecha_aprobacion"]), capturado_por=CAPTURADO_POR[canal],
            aceptacion=aceptacion)

    def registrar_respuesta(self, respuesta: RespuestaERP, canal: Canal, fecha: date) -> dict[str, str]:
        """Tras un OK: oportunidad `Ganada` y adopción de TUALI recalculada (R9). Devuelve lo que cambió."""
        if not respuesta.crea_pedido:
            return {}
        fila = self.conn.execute(
            "SELECT c.id_oportunidad, o.id_cliente, cl.estado_adopcion_tuali FROM solicitudes_pedido s "
            "JOIN cotizaciones_cab c ON c.id_cotizacion = s.id_cotizacion "
            "JOIN oportunidades o ON o.id_oportunidad = c.id_oportunidad "
            "JOIN clientes cl ON cl.id_cliente = o.id_cliente "
            "WHERE s.id_solicitud = ? AND s.intento = ?", (respuesta.id_solicitud, respuesta.intento)).fetchone()
        if fila is None:
            return {}
        cambios = {"oportunidad": f"{fila['id_oportunidad']} Ganada"}
        with self.conn:
            self.conn.execute("UPDATE oportunidades SET etapa = 'Ganada', probabilidad = 1, fecha_cierre_real = ? "
                              "WHERE id_oportunidad = ?", (fecha.isoformat(), fila["id_oportunidad"]))
            if Canal(canal) == Canal.TUALI and fila["estado_adopcion_tuali"] == "No usa":
                self.conn.execute("UPDATE clientes SET estado_adopcion_tuali = 'Híbrido' WHERE id_cliente = ?",
                                  (fila["id_cliente"],))
                cambios["adopcion"] = f"{fila['id_cliente']}: No usa → Híbrido"
        return cambios
