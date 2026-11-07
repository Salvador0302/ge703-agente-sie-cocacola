"""Herramientas de lectura del agente comercial.

Son las únicas que recibe el modo `llm`. Todas son `solo_lectura=True`, con esquema estricto
(todas las propiedades en `required` y `additionalProperties: false`). Ninguna crea, modifica ni envía nada.
"""

from __future__ import annotations

from datetime import date

from sie.agentes.base import Herramienta
from sie.crm.consultas import ConsultasCRM
from sie.erp.servicio import ServicioERP

NOMBRES = ("buscar_cliente", "listar_cotizaciones", "ver_cotizacion", "consultar_atp")


def _esquema(**propiedades: dict) -> dict:
    return {"type": "object", "properties": propiedades, "required": list(propiedades), "additionalProperties": False}


_TEXTO = {"type": "string"}
_FECHA = {"type": "string", "description": "Fecha de negocio AAAA-MM-DD"}


def herramientas_lectura(crm: ConsultasCRM, erp: ServicioERP) -> list[Herramienta]:
    def listar(id_cliente: str, fecha: str):
        return crm.cotizaciones_del_cliente(id_cliente, date.fromisoformat(fecha))

    def ver(id_cotizacion: str):
        return crm.cotizacion(id_cotizacion) or {"error": f"La cotización {id_cotizacion} no existe"}

    def atp(id_producto: str, fecha: str):
        d = erp.consultar_atp(id_producto, date.fromisoformat(fecha))
        return {"id_producto": d.id_producto, "fecha": d.fecha.isoformat(), "fisico": d.fisico,
                "reservado": d.reservado, "disponible": d.disponible,
                "nota": "Consulta no vinculante (I3): el ERP decide al recibir EV-02"}

    return [
        Herramienta("buscar_cliente", "Busca clientes por nombre comercial o ID. Devuelve ID, tipo, ejecutivo y canal.",
                    _esquema(texto=_TEXTO), lambda texto: crm.buscar_clientes(texto)),
        Herramienta("listar_cotizaciones", "Lista las cotizaciones de un cliente emitidas hasta una fecha, con su estado.",
                    _esquema(id_cliente=_TEXTO, fecha=_FECHA), listar),
        Herramienta("ver_cotizacion", "Muestra una cotización con sus líneas.",
                    _esquema(id_cotizacion=_TEXTO), ver),
        Herramienta("consultar_atp", "Consulta la disponibilidad (ATP) de un producto a una fecha. No reserva nada.",
                    _esquema(id_producto=_TEXTO, fecha=_FECHA), atp),
    ]
