"""Control de cifras: un texto redactado por el LLM no puede introducir números que no estén en los hechos.

Si `cifras_no_respaldadas` devuelve algo, el agente descarta la redacción del LLM y usa la plantilla.
Así el LLM nunca decide ni altera cantidades, importes, fechas o porcentajes.
"""

from __future__ import annotations

import json
import re
from typing import Any

_NUMERO = re.compile(r"\d+(?:[.,]\d+)*")
#: Números pequeños que aparecen en el lenguaje del contrato (C1–C5, intento 2, tramo 1).
_SIEMPRE_PERMITIDOS = {0.0, 1.0, 2.0, 3.0, 4.0, 5.0}


def _lecturas(token: str) -> set[float]:
    """Interpretaciones posibles de un número escrito: 13,287.74 · 13.287,74 · 8,5 · 09."""
    candidatos = {token, token.replace(",", ""), token.replace(".", "").replace(",", ".")}
    if token.count(",") == 1 and "." not in token:
        candidatos.add(token.replace(",", "."))
    valores = set()
    for c in candidatos:
        try:
            valores.add(round(float(c), 2))
        except ValueError:
            pass
    return valores


def _numeros_de_hechos(hechos: Any) -> set[float]:
    texto = json.dumps(hechos, ensure_ascii=False, default=str)
    valores: set[float] = set()
    for token in _NUMERO.findall(texto):
        for v in _lecturas(token):
            valores.add(v)
            if 0 < v < 1:
                valores.add(round(v * 100, 2))  # 0.08 → 8 %
    return valores


def cifras_no_respaldadas(texto: str, hechos: Any) -> set[str]:
    permitidos = _numeros_de_hechos(hechos) | _SIEMPRE_PERMITIDOS
    sueltas = set()
    for token in _NUMERO.findall(texto):
        if not (_lecturas(token) & permitidos):
            sueltas.add(token)
    return sueltas
