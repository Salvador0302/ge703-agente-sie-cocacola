"""Bitácora persistente · BLOQUE C (José Cornejo). Interfaz: `sie.bitacora.Bitacora`.

Cada `registrar()` escribe la misma entrada en la tabla `bitacora` de SQLite y como una línea JSON en
`logs/bitacora.jsonl` (UTF-8, append). Debe guardar solo IDs, códigos, reglas y cifras: nada de nombres
de contacto, correos, teléfonos ni texto libre del cliente.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from sie.bitacora import EntradaBitacora

_PENDIENTE = "Bloque C (José): bitácora persistente. Ver arquitectura/bloques/BLOQUE_C.md."


class BitacoraPersistente:
    def __init__(self, conn: sqlite3.Connection, ruta_jsonl: Path) -> None:
        self.conn = conn
        self.ruta_jsonl = ruta_jsonl

    def registrar(self, entrada: EntradaBitacora) -> None:
        raise NotImplementedError(_PENDIENTE)

    def leer(self, run_id: str | None = None, id_solicitud: str | None = None,
             ultimas: int | None = None) -> list[EntradaBitacora]:
        raise NotImplementedError(_PENDIENTE)
