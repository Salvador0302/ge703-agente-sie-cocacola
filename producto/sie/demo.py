"""Casos de la demo PC3 y su resultado esperado (plan PC3, §7).

La CLI y la UI usan estos mismos datos, así que el esperado frente a observado es el mismo en ambas.
Todos los datos son sintéticos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from sie.agentes.base import ResultadoAgente


@dataclass(frozen=True)
class CasoDemo:
    clave: str
    titulo: str
    corte: date
    fecha: date
    canal: str
    texto: str
    fecha_decision: date | None = None
    decision: dict[str, Any] = field(default_factory=dict)


CASOS: dict[str, CasoDemo] = {
    "normal": CasoDemo(
        clave="normal",
        titulo="Caso normal · Bodega Don Lucho acepta su cotización en TUALI",
        corte=date(2026, 10, 2),
        fecha=date(2026, 10, 2),
        canal="TUALI",
        texto="Bodega Don Lucho aceptó en la app TUALI su cotización de 65 paquetes con 5 % de descuento.",
    ),
    "excepcion": CasoDemo(
        clave="excepcion",
        titulo="Excepción prioritaria · Comercial Los Olivos pide por teléfono 600 paquetes; el ATP es 380",
        corte=date(2026, 10, 7),
        fecha=date(2026, 10, 7),
        canal="Teléfono",
        texto=("Llamada de Comercial Los Olivos: pide 600 paquetes de Inca Kola 500 ml "
               "de la promoción Fin de Año."),
        fecha_decision=date(2026, 10, 8),
        decision={"registrada_por": "Preventista 2", "medio": "Llamada telefónica", "evidencia": "ACEP-SOL-002-2"},
    ),
}


@dataclass(frozen=True)
class Verificacion:
    nombre: str
    esperado: str
    observado: str

    @property
    def conforme(self) -> bool:
        return self.esperado == self.observado


def _pedido(r: ResultadoAgente | None) -> str:
    return (r.ids.get("id_pedido") if r else None) or "ninguno"


def _responsable(r: ResultadoAgente | None) -> str:
    return r.escalamiento.responsable if r and r.escalamiento else "ninguno"


def _tramos(r: ResultadoAgente | None) -> str:
    promesa = (r.detalle.get("promesa") if r else None) or {}
    tramos = promesa.get("tramos") or []
    return " + ".join(f"{t['cantidad']} el {t['fecha']}" for t in tramos) or "ninguno"


def verificar(clave: str, resultados: list[ResultadoAgente], acepta: bool = True) -> list[Verificacion]:
    """Compara lo observado con lo esperado del caso. `resultados` en orden: intento 1, decisión."""
    r1 = resultados[0] if resultados else None
    r2 = resultados[1] if len(resultados) > 1 else None
    if clave == "normal":
        return [
            Verificacion("Código de respuesta", "OK-ACEPTADO", (r1.codigo if r1 else None) or "—"),
            Verificacion("Solicitud e intento", "SOL-003 · 1",
                         f"{r1.ids.get('id_solicitud')} · {r1.ids.get('intento')}" if r1 else "—"),
            Verificacion("Pedido creado", "PED-003", _pedido(r1)),
            Verificacion("Escalamiento", "ninguno", _responsable(r1)),
        ]
    filas = [
        Verificacion("Intento 1: código", "ATP-PARCIAL", (r1.codigo if r1 else None) or "—"),
        Verificacion("Intento 1: cotización enviada", "COT-002-V02", (r1.ids.get("id_cotizacion") if r1 else None) or "—"),
        Verificacion("Intento 1: pedido creado", "ninguno", _pedido(r1)),
        Verificacion("Intento 1: promesa propuesta", "380 el 2026-10-09 + 220 el 2026-10-12", _tramos(r1)),
        Verificacion("Intento 1: causa del faltante", "OT-2026-0107", (r1.ids.get("id_ot") if r1 else None) or "—"),
        Verificacion("Escala a", "Preventista 2", _responsable(r1)),
    ]
    if acepta:
        filas += [
            Verificacion("Intento 2: código", "OK-PROMESA-ALT", (r2.codigo if r2 else None) or "—"),
            Verificacion("Intento 2: pedido creado", "PED-002", _pedido(r2)),
        ]
    else:
        filas += [Verificacion("Tras el rechazo: pedido creado", "ninguno", _pedido(r2))]
    return filas
