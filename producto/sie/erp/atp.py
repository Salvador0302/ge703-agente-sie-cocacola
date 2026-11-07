"""ATP por producto, almacén y fecha.

Fórmula del validador del EP (§4): físico = Σ(entradas − salidas) con fecha < `fecha`;
reservado = Σ(cantidad de pedidos confirmados antes de `fecha` − lo entregado antes de `fecha`);
disponible = físico − reservado. Valor de control: PRD-001 en ALM-001 al 07/10/2026 → 402 − 22 = 380.
Los pedidos del modelo se atienden desde el CD Lima Norte (ALM-001), así que la reserva no filtra almacén.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DetalleATP:
    id_producto: str
    id_almacen: str
    fecha: date
    fisico: int
    reservado: int

    @property
    def disponible(self) -> int:
        return self.fisico - self.reservado


def calcular(conn: sqlite3.Connection, id_producto: str, fecha: date, id_almacen: str = "ALM-001") -> DetalleATP:
    f = fecha.isoformat()
    fisico = conn.execute(
        "SELECT COALESCE(SUM(COALESCE(cantidad_entrada, 0) - COALESCE(cantidad_salida, 0)), 0) "
        "FROM movimientos_inventario WHERE id_producto = ? AND id_almacen = ? AND fecha_movimiento < ?",
        (id_producto, id_almacen, f)).fetchone()[0]
    reservado = conn.execute(
        """
        SELECT COALESCE(SUM(d.cantidad - COALESCE((
            SELECT SUM(ed.cantidad_entregada)
            FROM entregas_det ed JOIN entregas_cab ec ON ec.id_entrega = ed.id_entrega
            WHERE ed.id_pedido = d.id_pedido AND ed.numero_linea_pedido = d.numero_linea
              AND ec.fecha_entrega < ?), 0)), 0)
        FROM pedidos_det d JOIN pedidos_cab c ON c.id_pedido = d.id_pedido
        WHERE d.id_producto = ? AND c.fecha_confirmacion < ?
        """, (f, id_producto, f)).fetchone()[0]
    return DetalleATP(id_producto, id_almacen, fecha, int(fisico), int(reservado))
