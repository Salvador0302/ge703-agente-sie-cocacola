"""Utilidades compartidas por las pruebas (rutas, ejemplos del contrato y pendientes)."""

from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
EP_CSV = RAIZ / "docs" / "antecedentes" / "repo_ep_v3" / "09_datos" / "csv"
EJEMPLOS = RAIZ / "arquitectura" / "contrato_i8" / "ejemplos"


def requerir(condicion: bool, mensaje: str) -> None:
    """Para entregables que son archivos: si aún no existen, la prueba queda pendiente."""
    if not condicion:
        raise NotImplementedError(mensaje)


def leer_ejemplo(nombre: str) -> dict:
    datos = json.loads((EJEMPLOS / nombre).read_text(encoding="utf-8"))
    datos.pop("_nota", None)
    return datos
