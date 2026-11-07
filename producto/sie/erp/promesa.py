"""Fecha de entrega y promesa alternativa (EV-04) · BLOQUE B (Gianmarco Leandro).

- Fecha de entrega: siguiente día (fecha + 1) dentro de la ventana de entrega de la dirección.
- Promesa alternativa: tramo 1 = ATP disponible desde el CD, con un día más para que el cliente
  confirme; tramo 2 = faltante con la fecha de la próxima reposición del plan (plan_reposicion).
Valor de control (SOL-002 intento 1, 07/10): 380 el 09/10 desde "ALM-001 CD Lima Norte" y 220 el 12/10
desde "Reposición desde ALM-002 (planta) · plan APO (I2)".
"""

from __future__ import annotations

import sqlite3
from datetime import date

from sie.contrato import PromesaAlternativa, SolicitudPedido
from sie.erp.reglas import Evaluacion


def fecha_entrega(conn: sqlite3.Connection, id_direccion: str, desde: date) -> date:
    raise NotImplementedError("Bloque B (Gianmarco): fecha de entrega. Ver arquitectura/bloques/BLOQUE_B.md.")


def proponer(conn: sqlite3.Connection, sol: SolicitudPedido, evaluacion: Evaluacion) -> PromesaAlternativa:
    raise NotImplementedError("Bloque B (Gianmarco): promesa alternativa. Ver arquitectura/bloques/BLOQUE_B.md.")
