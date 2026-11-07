"""Causa de un faltante de ATP: parada → capacidad perdida → reposición reprogramada · BLOQUE B.

Datos sintéticos de `activos`, `ordenes_trabajo` y `plan_reposicion` (plan PC3, §5.3). Valor de control:
PRD-001 al 07/10/2026 → OT-2026-0107 en ACT-LLN-01, 96 h, 240 paquetes perdidos, lote previsto el 06/10
reprogramado al 12/10, ATP sin parada 620.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date


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


def explicar_faltante(conn: sqlite3.Connection, id_producto: str, fecha: date,
                      id_almacen: str = "ALM-001") -> CausaFaltante | None:
    """Devuelve la orden de trabajo que explica que una reposición prevista antes de `fecha` no llegara.

    `None` si ninguna reposición del producto hacia el almacén fue reprogramada por una OT.
    """
    raise NotImplementedError("Bloque B (Gianmarco): causa del faltante. Ver arquitectura/bloques/BLOQUE_B.md.")
