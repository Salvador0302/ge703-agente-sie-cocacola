"""Bitácora: interfaz común (bloque A) e implementación en memoria para pruebas.

La implementación persistente (tabla `bitacora` + `logs/bitacora.jsonl`) está en
`sie.bitacora.persistente` (bloque C). La bitácora guarda identificadores, códigos y reglas,
nunca datos personales (contrato I8: "bitácora sin datos personales").
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any, Protocol


def ahora_iso() -> str:
    """Marca de tiempo real con zona horaria (no confundir con la fecha de negocio)."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


@dataclass
class EntradaBitacora:
    agente: str               # "comercial", "erp", "orquestador", "humano"
    paso: str                 # p. ej. "interpretar", "C5", "enviar EV-02", "escalar"
    resultado: str            # texto breve: "ATP 380 de 600"
    fecha_negocio: date | None = None
    run_id: str = ""
    regla: str | None = None  # C1..C5, P1..P3, R1..R9, ADR-xxx
    codigo: str | None = None  # código del contrato o resultado interno
    entrada: dict[str, Any] = field(default_factory=dict)
    ids: dict[str, Any] = field(default_factory=dict)  # id_solicitud, intento, id_pedido, id_ot...
    escalado_a: str | None = None
    motivo: str | None = None
    fecha_limite: date | None = None
    respuesta_humana: str | None = None
    modo: str | None = None   # reglas | llm
    detalle: dict[str, Any] = field(default_factory=dict)
    ts: str = field(default_factory=ahora_iso)

    def a_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for clave in ("fecha_negocio", "fecha_limite"):
            if isinstance(d[clave], date):
                d[clave] = d[clave].isoformat()
        return d

    @classmethod
    def desde_dict(cls, d: dict[str, Any]) -> EntradaBitacora:
        d = dict(d)
        for clave in ("fecha_negocio", "fecha_limite"):
            if d.get(clave):
                d[clave] = date.fromisoformat(d[clave])
        return cls(**d)


class Bitacora(Protocol):
    def registrar(self, entrada: EntradaBitacora) -> None: ...

    def leer(self, run_id: str | None = None, id_solicitud: str | None = None,
             ultimas: int | None = None) -> list[EntradaBitacora]: ...


def _coincide(e: EntradaBitacora, run_id: str | None, id_solicitud: str | None) -> bool:
    if run_id and e.run_id != run_id:
        return False
    if id_solicitud and e.ids.get("id_solicitud") != id_solicitud:
        return False
    return True


class BitacoraMemoria:
    """Bitácora en memoria para pruebas y para la UI cuando no se quiere escribir en disco."""

    def __init__(self) -> None:
        self.entradas: list[EntradaBitacora] = []

    def registrar(self, entrada: EntradaBitacora) -> None:
        self.entradas.append(entrada)

    def leer(self, run_id: str | None = None, id_solicitud: str | None = None,
             ultimas: int | None = None) -> list[EntradaBitacora]:
        sel = [e for e in self.entradas if _coincide(e, run_id, id_solicitud)]
        return sel[-ultimas:] if ultimas else sel
