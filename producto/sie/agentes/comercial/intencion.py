"""Interfaces del agente comercial que comparten el modo reglas (bloque C) y el modo llm (bloque A).

El intérprete solo **identifica** cliente, canal y cotización a partir del texto. No valida nada:
el agente comprueba después que la cotización exista, sea del cliente y esté aceptada y vigente (R2),
y el ERP valida C1–C5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Protocol


@dataclass
class Intencion:
    texto: str
    id_cliente: str | None = None
    canal_origen: str | None = None
    id_cotizacion: str | None = None
    cantidad_mencionada: int | None = None
    producto_mencionado: str | None = None
    resumen: str = ""
    fuente: str = "reglas"  # reglas | llm
    avisos: list[str] = field(default_factory=list)


class Interprete(Protocol):
    def interpretar(self, texto: str, fecha_negocio: date, canal: str | None = None) -> Intencion: ...


class Redactor(Protocol):
    def redactar(self, hechos: dict[str, Any]) -> str: ...
