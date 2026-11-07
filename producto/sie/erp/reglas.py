"""Motor de reglas C1–C5 del contrato I8.

Evalúa las cinco validaciones siempre (para la trazabilidad) y el **primer** control que falla define el
código, en el orden C1 → C2 → C3 → C4 → C5. Determinista: usa `sol.fecha_envio`, nunca la fecha del
sistema. Tabla de decisiones completa en `arquitectura/PLAN_PC3.md` §6.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import date

from sie.contrato import Codigo, SolicitudPedido, TipoMensaje
from sie.erp import atp, importes
from sie.erp.atp import DetalleATP

#: Descuento que el preventista aplica sin aprobación y máximo de política (R3, supuesto del equipo).
DESCUENTO_PREVENTISTA = 0.05
DESCUENTO_MAXIMO = 0.12
_TOLERANCIA = 1e-9


@dataclass
class Evaluacion:
    c1_cliente: bool
    c2_credito: bool
    c3_precio: bool
    c4_descuento: bool
    c5_atp: bool
    codigo: Codigo                       # código resultante según el orden y el tipo de mensaje
    regla: str                           # "C1".."C5" que decidió, "C5b" (promesa aceptada) u "OK"
    causa: str                           # texto con el dato que decide, p. ej. "ATP 380 de 600 (C5)"
    atp_por_linea: dict[int, DetalleATP] = field(default_factory=dict)  # numero_linea → ATP
    textos: dict[str, str] = field(default_factory=dict)  # "C1".."C5" → explicación de cada control

    @property
    def vector(self) -> str:
        """'V V V V F' como en el validador del EP."""
        return " ".join("V" if c else "F" for c in
                        (self.c1_cliente, self.c2_credito, self.c3_precio, self.c4_descuento, self.c5_atp))


def _fecha(texto: str | None) -> date | None:
    return date.fromisoformat(texto[:10]) if texto else None


def _pct(valor: float) -> str:
    return f"{valor * 100:g} %"


def _c1(conn: sqlite3.Connection, sol: SolicitudPedido) -> tuple[bool, str]:
    cli = conn.execute("SELECT * FROM clientes WHERE id_cliente = ?", (sol.id_cliente,)).fetchone()
    if cli is None:
        return False, f"Cliente {sol.id_cliente} inexistente (C1)"
    if cli["estado_cliente"] != "Activo" or cli["estado_sincronizacion"] != "Sincronizado" \
            or not cli["codigo_cliente_erp"]:
        return False, (f"Cliente {sol.id_cliente} {cli['estado_cliente']}, {cli['estado_sincronizacion']}, "
                       f"código ERP {cli['codigo_cliente_erp'] or 'pendiente'} (C1)")
    return True, f"Cliente {sol.id_cliente} activo y sincronizado ({cli['codigo_cliente_erp']})"


def _c2(conn: sqlite3.Connection, sol: SolicitudPedido) -> tuple[bool, str]:
    cli = conn.execute("SELECT * FROM clientes WHERE id_cliente = ?", (sol.id_cliente,)).fetchone()
    if cli is None:
        return False, "Sin cliente para evaluar el crédito (C2)"
    if cli["estado_credito"] == "Bloqueado":
        return False, "Crédito del cliente en estado Bloqueado (C2)"
    if int(cli["condicion_pago_dias"] or 0) == 0:
        return True, "Venta al contado"
    total = importes.de_documento(sol.lineas).total
    limite = importes.redondear(importes.a_decimal(cli["limite_credito"] or 0))
    if total > limite:
        return False, f"Total S/ {total} supera el límite de crédito S/ {limite} (C2)"
    return True, f"Total S/ {total} dentro del límite S/ {limite}"


def _c3(conn: sqlite3.Connection, sol: SolicitudPedido) -> tuple[bool, str]:
    for linea in sol.lineas:
        p = conn.execute("SELECT * FROM listas_precios WHERE id_precio = ?", (linea.id_precio,)).fetchone()
        if p is None or p["id_producto"] != linea.id_producto:
            return False, f"{linea.id_precio} no corresponde a {linea.id_producto} (C3)"
        desde, hasta = _fecha(p["vigente_desde"]), _fecha(p["vigente_hasta"])
        if p["estado_lista"] != "Activa":
            return False, f"{linea.id_precio} en lista {p['estado_lista']} (C3)"
        if desde and sol.fecha_envio < desde:
            return False, f"{linea.id_precio} vigente recién desde {desde.isoformat()} (C3)"
        if hasta and sol.fecha_envio > hasta:
            return False, f"{linea.id_precio} vencido desde {hasta.isoformat()} (C3)"
    return True, "Precios vigentes a la fecha de envío"


def _c4(conn: sqlite3.Connection, sol: SolicitudPedido) -> tuple[bool, str]:
    mayor = 0.0
    for linea in sol.lineas:
        regla = conn.execute("SELECT 1 FROM reglas_descuento WHERE id_regla_descuento = ?",
                             (linea.id_regla_descuento,)).fetchone()
        if regla is None:
            return False, f"Regla de descuento {linea.id_regla_descuento} inexistente (C4)"
        d = float(linea.descuento_pct)
        mayor = max(mayor, d)
        if d > DESCUENTO_MAXIMO + _TOLERANCIA:
            return False, f"Descuento {_pct(d)} fuera de política (más de 12 %) (C4)"
        if d > DESCUENTO_PREVENTISTA + _TOLERANCIA:
            aprobado = (sol.estado_descuento == "Aprobado" and sol.aprobador and sol.fecha_aprobacion
                        and sol.fecha_aprobacion <= sol.fecha_envio)
            if not aprobado:
                return False, f"Descuento {_pct(d)} sin aprobación registrada (C4)"
    if mayor > DESCUENTO_PREVENTISTA + _TOLERANCIA:
        return True, f"Descuento {_pct(mayor)} aprobado por {sol.aprobador} el {sol.fecha_aprobacion.isoformat()}"
    return True, f"Descuento {_pct(mayor)} dentro del límite del preventista (5 %)"


def _c5(conn: sqlite3.Connection, sol: SolicitudPedido) -> tuple[bool, str, dict[int, DetalleATP]]:
    por_linea = {l.numero_linea: atp.calcular(conn, l.id_producto, sol.fecha_envio) for l in sol.lineas}
    faltantes = [l for l in sol.lineas if l.cantidad > por_linea[l.numero_linea].disponible]
    if faltantes:
        l = faltantes[0]
        return False, f"ATP {por_linea[l.numero_linea].disponible} de {l.cantidad} de {l.id_producto} (C5)", por_linea
    return True, "ATP suficiente en todas las líneas", por_linea


def _promesa_aceptada(sol: SolicitudPedido, por_linea: dict[int, DetalleATP]) -> bool:
    """C5b: EV-05 con aceptación registrada y ATP suficiente para el primer tramo aceptado."""
    a = sol.aceptacion
    if sol.tipo_mensaje != TipoMensaje.CONFIRMACION_PROMESA or a is None or not a.acepta or not a.tramos_aceptados:
        return False
    disponible = sum(max(d.disponible, 0) for d in por_linea.values())
    return disponible >= a.tramos_aceptados[0].cantidad


def evaluar(conn: sqlite3.Connection, sol: SolicitudPedido) -> Evaluacion:
    c1, t1 = _c1(conn, sol)
    c2, t2 = _c2(conn, sol)
    c3, t3 = _c3(conn, sol)
    c4, t4 = _c4(conn, sol)
    c5, t5, por_linea = _c5(conn, sol)
    textos = {"C1": t1, "C2": t2, "C3": t3, "C4": t4, "C5": t5}
    for regla, ok, codigo, texto in (("C1", c1, Codigo.CLI_NO_VALIDO, t1), ("C2", c2, Codigo.CRED_BLOQ, t2),
                                     ("C3", c3, Codigo.PRECIO_NO_VIG, t3), ("C4", c4, Codigo.DESC_SIN_APROB, t4)):
        if not ok:
            return Evaluacion(c1, c2, c3, c4, c5, codigo, regla, texto, por_linea, textos)
    if c5:
        return Evaluacion(c1, c2, c3, c4, c5, Codigo.OK_ACEPTADO, "OK", "C1–C5 conformes", por_linea, textos)
    if _promesa_aceptada(sol, por_linea):
        return Evaluacion(c1, c2, c3, c4, c5, Codigo.OK_PROMESA_ALT, "C5b",
                          f"{t5} · promesa alternativa aceptada por el cliente", por_linea, textos)
    return Evaluacion(c1, c2, c3, c4, c5, Codigo.ATP_PARCIAL, "C5", t5, por_linea, textos)
