"""ATP por producto, almacén y fecha · BLOQUE B (Gianmarco Leandro).

Fórmula del validador del EP (§4): físico = Σ(entradas − salidas) con fecha < `fecha`;
reservado = Σ(cantidad de pedidos confirmados antes de `fecha` − lo entregado antes de `fecha`);
disponible = físico − reservado. Valor de control: PRD-001 en ALM-001 al 07/10/2026 → 402 − 22 = 380.
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
    raise NotImplementedError("Bloque B (Gianmarco): cálculo de ATP. Ver arquitectura/bloques/BLOQUE_B.md.")
