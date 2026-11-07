"""Ensamblado del sistema: une configuración, base, bitácora, ERP, CRM, agente y orquestador.

La CLI, la UI y las pruebas de integración construyen el sistema con esta única función, de modo que
el modo `reglas` y el modo `llm` comparten todo menos el intérprete y el redactor.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from typing import Any

from sie.bitacora import Bitacora
from sie.config import Config
from sie.db.conexion import conectar
from sie.orquestador import Orquestador


@dataclass
class Sistema:
    config: Config
    conn: sqlite3.Connection
    bitacora: Bitacora
    orquestador: Orquestador
    erp: Any
    crm: Any
    agente: Any


def preparar_base(config: Config, corte: date, ruta: Any = None) -> sqlite3.Connection:
    """Abre la base (archivo de la configuración o `ruta`) y la deja en el estado del corte."""
    from sie.db import seed

    conn = conectar(ruta if ruta is not None else config.ruta_db)
    seed.crear_base(conn, corte)
    return conn


def construir_sistema(config: Config, conn: sqlite3.Connection, bitacora: Bitacora | None = None,
                      cliente_llm: Any = None) -> Sistema:
    from sie.agentes.comercial.agente import AgenteComercial
    from sie.agentes.comercial.interprete_reglas import InterpreteReglas
    from sie.agentes.comercial.redaccion import RedactorPlantilla
    from sie.bitacora.persistente import BitacoraPersistente
    from sie.crm.consultas import ConsultasCRM
    from sie.erp.servicio import ServicioERP

    bit = bitacora if bitacora is not None else BitacoraPersistente(conn, config.ruta_bitacora)
    erp = ServicioERP(conn, bitacora=bit)
    crm = ConsultasCRM(conn)
    interprete: Any = InterpreteReglas(crm)
    redactor: Any = RedactorPlantilla()
    if config.modo == "llm":
        from sie.agentes.comercial.herramientas import herramientas_lectura
        from sie.agentes.comercial.interprete_llm import InterpreteLLM, RedactorLLM
        from sie.llm.cliente import ClienteLLM

        cliente = ClienteLLM(config.modelo, config.esfuerzo, config.anthropic_api_key, cliente=cliente_llm)
        interprete = InterpreteLLM(cliente, herramientas_lectura(crm, erp), respaldo=interprete)
        redactor = RedactorLLM(cliente, respaldo=redactor)
    agente = AgenteComercial(erp=erp, crm=crm, interprete=interprete, redactor=redactor,
                             bitacora=bit, modo=config.modo)
    orquestador = Orquestador(bitacora=bit, agentes=[agente])
    return Sistema(config=config, conn=conn, bitacora=bit, orquestador=orquestador,
                   erp=erp, crm=crm, agente=agente)
