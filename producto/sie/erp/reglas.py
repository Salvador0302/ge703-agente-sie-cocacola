"""Motor de reglas C1–C5 del contrato I8 · BLOQUE B (Gianmarco Leandro).

Evalúa las cinco validaciones siempre (para la trazabilidad) y el **primer** control que falla
define el código, en el orden C1 → C2 → C3 → C4 → C5. Determinista: usa `sol.fecha_envio`, nunca la
fecha del sistema. Tabla de decisiones completa en `arquitectura/PLAN_PC3.md` §6.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field

from sie.contrato import Codigo, SolicitudPedido
from sie.erp.atp import DetalleATP


@dataclass
class Evaluacion:
    c1_cliente: bool
    c2_credito: bool
    c3_precio: bool
    c4_descuento: bool
    c5_atp: bool
    codigo: Codigo                       # código resultante según el orden y el tipo de mensaje
    regla: str                           # "C1".."C5" que falló, o "OK"
    causa: str                           # texto con el dato que decide, p. ej. "ATP 380 de 600 (C5)"
    atp_por_linea: dict[int, DetalleATP] = field(default_factory=dict)  # numero_linea → ATP

    @property
    def vector(self) -> str:
        """'V V V V F' como en el validador del EP."""
        return " ".join("V" if c else "F" for c in
                        (self.c1_cliente, self.c2_credito, self.c3_precio, self.c4_descuento, self.c5_atp))


def evaluar(conn: sqlite3.Connection, sol: SolicitudPedido) -> Evaluacion:
    raise NotImplementedError("Bloque B (Gianmarco): reglas C1–C5. Ver arquitectura/bloques/BLOQUE_B.md.")
