"""Consultas del CRM simulado · BLOQUE C (José Cornejo). Interfaz definida por el bloque A.

El CRM es sistema de registro de campaña, lead, oportunidad, cotización, canal y adopción de TUALI.
El agente lee aquí y arma EV-02/EV-05 con los datos de la cotización aceptada; nunca con cantidades,
precios o descuentos tomados del texto libre. Las únicas escrituras del CRM ocurren tras la respuesta
del ERP (EV-03): etapa de la oportunidad y adopción de TUALI (R9).
"""

from __future__ import annotations

import sqlite3
from datetime import date
from typing import Any

from sie.contrato import Aceptacion, Canal, RespuestaERP, SolicitudPedido, TipoMensaje

_PENDIENTE = "Bloque C (José): CRM simulado. Ver arquitectura/bloques/BLOQUE_C.md."


class ConsultasCRM:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def buscar_clientes(self, texto: str) -> list[dict[str, Any]]:
        """Clientes cuyo nombre comercial, razón social o ID coincide con `texto` (sin datos de contacto)."""
        raise NotImplementedError(_PENDIENTE)

    def cotizaciones_del_cliente(self, id_cliente: str, fecha: date) -> list[dict[str, Any]]:
        """Cabeceras de cotización del cliente emitidas hasta `fecha`, con estado y vigencia."""
        raise NotImplementedError(_PENDIENTE)

    def cotizacion(self, id_cotizacion: str) -> dict[str, Any] | None:
        """Cabecera con sus líneas (`lineas`), o None si no existe."""
        raise NotImplementedError(_PENDIENTE)

    def construir_solicitud(self, id_cotizacion: str, canal: Canal, fecha_envio: date, intento: int = 1,
                            tipo: TipoMensaje = TipoMensaje.SOLICITUD_INICIAL,
                            aceptacion: Aceptacion | None = None) -> SolicitudPedido:
        """Arma EV-02 (o EV-05 si `tipo` es Confirmación promesa) desde la cotización aceptada."""
        raise NotImplementedError(_PENDIENTE)

    def registrar_respuesta(self, respuesta: RespuestaERP, canal: Canal, fecha: date) -> None:
        """Tras un OK: oportunidad `Ganada` y adopción de TUALI recalculada (R9)."""
        raise NotImplementedError(_PENDIENTE)
