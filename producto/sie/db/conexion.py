"""Conexión a SQLite con las opciones que asume todo el proyecto."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def conectar(ruta: Path | str = ":memory:") -> sqlite3.Connection:
    """Abre la base local. `":memory:"` crea una base temporal (pruebas).

    Activa claves foráneas y devuelve filas accesibles por nombre de columna.
    """
    if str(ruta) != ":memory:":
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(ruta))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
