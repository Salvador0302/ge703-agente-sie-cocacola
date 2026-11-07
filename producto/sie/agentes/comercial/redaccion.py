"""Redacción por plantillas · BLOQUE C (José Cornejo).

Convierte los hechos del resultado (código, causa, IDs, promesa, responsable, siguiente paso) en una
explicación breve en español. Es el redactor del modo `reglas` y el respaldo del modo `llm`.
"""

from __future__ import annotations

from typing import Any


class RedactorPlantilla:
    def redactar(self, hechos: dict[str, Any]) -> str:
        raise NotImplementedError("Bloque C (José): redacción por plantillas. Ver arquitectura/bloques/BLOQUE_C.md.")
