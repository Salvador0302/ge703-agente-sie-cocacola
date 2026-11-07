"""Capa I8 + ERP simulado · BLOQUE B (Gianmarco Leandro).

Punto de entrada único para el agente: recibe EV-02/EV-05 y responde EV-03/EV-04.

Orden de controles (plan PC3, §6): P1 datos obligatorios (`DATO-OBLIG`) → P2 idempotencia
(`DUPLICADO`; un mismo `id_solicitud + intento` repetido devuelve la misma respuesta sin crear nada) →
C1–C5 (`reglas.evaluar`). Si el código crea pedido, inserta pedidos_cab/det con el ID `PED-NNN` y los
mismos importes que el EP, registra la solicitud en `solicitudes_pedido` y los tramos en
`promesa_tramos`. Cada paso queda en la bitácora (agente "erp").
"""

from __future__ import annotations

import sqlite3
from datetime import date

from sie.bitacora import Bitacora
from sie.contrato import RespuestaERP, SolicitudPedido
from sie.erp.atp import DetalleATP
from sie.erp.causas import CausaFaltante

_PENDIENTE = "Bloque B (Gianmarco): capa I8 y ERP simulado. Ver arquitectura/bloques/BLOQUE_B.md."


class ServicioERP:
    def __init__(self, conn: sqlite3.Connection, bitacora: Bitacora | None = None) -> None:
        self.conn = conn
        self.bitacora = bitacora

    def recibir(self, sol: SolicitudPedido, run_id: str = "") -> RespuestaERP:
        """Procesa EV-02 o EV-05 y devuelve la respuesta del contrato. Único método que crea pedidos."""
        raise NotImplementedError(_PENDIENTE)

    def consultar_atp(self, id_producto: str, fecha: date) -> DetalleATP:
        """Consulta no vinculante (I3): no reserva nada."""
        raise NotImplementedError(_PENDIENTE)

    def explicar_faltante(self, id_producto: str, fecha: date) -> CausaFaltante | None:
        raise NotImplementedError(_PENDIENTE)
