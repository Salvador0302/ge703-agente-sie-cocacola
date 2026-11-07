"""Herramientas de lectura del agente comercial · BLOQUE C (José Cornejo).

Son las únicas que recibe el modo `llm`. Todas deben ser `solo_lectura=True`, con esquema estricto
(todas las propiedades en `required` y `additionalProperties: false`). Nombres fijos:
`buscar_cliente`, `listar_cotizaciones`, `ver_cotizacion`, `consultar_atp`.
"""

from __future__ import annotations

from sie.agentes.base import Herramienta
from sie.crm.consultas import ConsultasCRM
from sie.erp.servicio import ServicioERP

NOMBRES = ("buscar_cliente", "listar_cotizaciones", "ver_cotizacion", "consultar_atp")


def herramientas_lectura(crm: ConsultasCRM, erp: ServicioERP) -> list[Herramienta]:
    raise NotImplementedError("Bloque C (José): herramientas de lectura. Ver arquitectura/bloques/BLOQUE_C.md.")
