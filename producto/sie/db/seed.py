"""Seed por fecha de corte · BLOQUE B (Gianmarco Leandro). Interfaz definida por el bloque A.

Los CSV del EP (`datos/seed/`) muestran el estado al 11/10/2026. Para que la demo cree SOL-003,
PED-003, SOL-002 y PED-002 sin `DUPLICADO`, la base se carga hasta una fecha de corte:

- Documentos del CRM (campañas, leads, oportunidades, cotizaciones): fecha ≤ corte.
- Transacciones del ERP (solicitudes, pedidos, movimientos, entregas, facturas, pagos): fecha < corte.
- Maestros, activos, órdenes de trabajo y plan de reposición: siempre.
- Estados previos de los casos de la demo: OPP-002 y OPP-003 en `Propuesta`; CLI-003 con
  `estado_adopcion_tuali = 'No usa'`. Dominios normalizados (`Digital`, `Híbrido`, `No usa`).

Detalle completo en `arquitectura/bloques/BLOQUE_B.md`.
"""

from __future__ import annotations

import sqlite3
from datetime import date

from sie.config import RAIZ

CARPETA_SEED = RAIZ / "datos" / "seed"
ESQUEMA = RAIZ / "producto" / "sie" / "db" / "esquema.sql"

_PENDIENTE = "Bloque B (Gianmarco): seed por fecha de corte. Ver arquitectura/bloques/BLOQUE_B.md."


def crear_base(conn: sqlite3.Connection, corte: date) -> None:
    """Crea (o recrea) todas las tablas del esquema y carga el estado del mundo antes de `corte`.

    No borra la tabla `bitacora`: la crea si no existe y conserva su historial.
    """
    raise NotImplementedError(_PENDIENTE)


def avanzar(conn: sqlite3.Connection, hasta: date) -> int:
    """Agrega las filas del seed con fecha anterior a `hasta` que aún no existen (INSERT OR IGNORE).

    Nunca sobrescribe lo que creó el ERP simulado (por ejemplo, PED-002). Devuelve filas agregadas.
    """
    raise NotImplementedError(_PENDIENTE)
