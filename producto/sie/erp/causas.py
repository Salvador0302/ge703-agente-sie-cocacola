"""Causa de un faltante de ATP: parada → capacidad perdida → reposición reprogramada.

Datos sintéticos de `activos`, `ordenes_trabajo` y `plan_reposicion` (plan PC3, §5.3). Valor de control:
PRD-001 al 07/10/2026 → OT-2026-0107 en ACT-LLN-01, 96 h, 240 paquetes perdidos, lote previsto el 06/10
reprogramado al 12/10, ATP sin parada 620.
"""

from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from datetime import date

from sie.erp import atp


@dataclass(frozen=True)
class CausaFaltante:
    id_ot: str
    id_activo: str
    descripcion_activo: str
    horas_parada: int
    paquetes_perdidos: int
    id_reposicion: str
    fecha_plan_original: date
    fecha_reprogramada: date
    atp_con_parada: int
    atp_sin_parada: int

    def a_dict(self) -> dict:
        d = asdict(self)
        d["fecha_plan_original"] = self.fecha_plan_original.isoformat()
        d["fecha_reprogramada"] = self.fecha_reprogramada.isoformat()
        return d


def explicar_faltante(conn: sqlite3.Connection, id_producto: str, fecha: date,
                      id_almacen: str = "ALM-001") -> CausaFaltante | None:
    """Devuelve la orden de trabajo que explica que una reposición prevista antes de `fecha` no llegara.

    `None` si ninguna reposición del producto hacia el almacén fue reprogramada por una OT.
    """
    f = fecha.isoformat()
    fila = conn.execute(
        """
        SELECT r.id_reposicion, r.cantidad, r.fecha_plan_original, r.fecha_reprogramada,
               o.id_ot, o.horas_parada, a.id_activo, a.nombre, a.capacidad_paq_dia
        FROM plan_reposicion r
        JOIN ordenes_trabajo o ON o.id_ot = r.id_ot_causa
        JOIN activos a ON a.id_activo = o.id_activo
        WHERE r.id_producto = ? AND r.id_almacen_destino = ?
          AND r.fecha_plan_original < ? AND r.fecha_reprogramada >= ?
        ORDER BY r.fecha_plan_original
        LIMIT 1
        """, (id_producto, id_almacen, f, f)).fetchone()
    if fila is None:
        return None
    horas = int(fila["horas_parada"])
    perdidos = int(fila["capacidad_paq_dia"]) * horas // 24 if fila["capacidad_paq_dia"] else int(fila["cantidad"])
    con_parada = atp.calcular(conn, id_producto, fecha, id_almacen).disponible
    return CausaFaltante(
        id_ot=fila["id_ot"], id_activo=fila["id_activo"], descripcion_activo=fila["nombre"], horas_parada=horas,
        paquetes_perdidos=perdidos, id_reposicion=fila["id_reposicion"],
        fecha_plan_original=date.fromisoformat(fila["fecha_plan_original"]),
        fecha_reprogramada=date.fromisoformat(fila["fecha_reprogramada"]),
        atp_con_parada=con_parada, atp_sin_parada=con_parada + int(fila["cantidad"]),
    )
