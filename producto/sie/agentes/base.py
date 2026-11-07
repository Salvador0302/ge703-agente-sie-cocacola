"""Tipos comunes a todos los agentes: evento de entrada, resultado, escalamiento y herramienta.

Todo agente nuevo (cadena de suministro, logística, finanzas operativas) implementa el protocolo
`Agente` y se registra en el orquestador; no necesita cambiar nada de este módulo.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any, Callable, Protocol, runtime_checkable


def nuevo_run_id() -> str:
    """Identificador de una corrida (agrupa en la bitácora los eventos de un mismo caso)."""
    return f"RUN-{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:4]}"


class EstadoResultado(StrEnum):
    COMPLETADO = "COMPLETADO"                  # el ERP aceptó y no queda decisión pendiente
    ESCALADO = "ESCALADO"                      # el ERP rechazó; el responsable debe corregir
    ESPERA_HUMANO = "ESPERA_HUMANO"            # el flujo sigue solo con una decisión humana
    NO_ENVIADA = "NO_ENVIADA"                  # la cotización no era solicitable (R2)
    CERRADO_SIN_PEDIDO = "CERRADO_SIN_PEDIDO"  # la persona responsable rechazó la propuesta
    NO_IMPLEMENTADO = "NO_IMPLEMENTADO"        # tipo de evento de un agente futuro
    ERROR = "ERROR"


@dataclass
class Evento:
    """Lo que entra al orquestador. `tipo` decide a qué agente va."""

    tipo: str
    fecha_negocio: date
    datos: dict[str, Any] = field(default_factory=dict)
    origen: str = "cli"
    run_id: str = field(default_factory=nuevo_run_id)
    id_evento: str = field(default_factory=lambda: uuid.uuid4().hex[:12])


@dataclass
class Escalamiento:
    """Toda excepción conserva objeto, causa, estado, responsable y fecha límite (S6, lámina 18)."""

    id_escalamiento: str
    objeto: str
    causa: str
    responsable: str
    fecha_limite: date
    estado: str = "Pendiente"  # Pendiente | Resuelto
    opciones: list[str] = field(default_factory=list)
    respuesta_humana: str | None = None
    datos: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResultadoAgente:
    agente: str
    estado: EstadoResultado
    mensaje: str
    codigo: str | None = None
    ids: dict[str, Any] = field(default_factory=dict)
    escalamiento: Escalamiento | None = None
    detalle: dict[str, Any] = field(default_factory=dict)
    run_id: str = ""


@dataclass(frozen=True)
class Herramienta:
    """Herramienta que un agente expone al LLM. En el agente comercial todas son de solo lectura."""

    nombre: str
    descripcion: str
    esquema: dict[str, Any]
    funcion: Callable[..., Any]
    solo_lectura: bool = True

    def definicion(self) -> dict[str, Any]:
        """Definición para la Claude API (tool use estricto)."""
        return {
            "name": self.nombre,
            "description": self.descripcion,
            "input_schema": self.esquema,
            "strict": True,
        }

    def ejecutar(self, argumentos: dict[str, Any]) -> Any:
        return self.funcion(**argumentos)


@runtime_checkable
class Agente(Protocol):
    nombre: str
    tipos_evento: frozenset[str]

    def manejar(self, evento: Evento) -> ResultadoAgente: ...
