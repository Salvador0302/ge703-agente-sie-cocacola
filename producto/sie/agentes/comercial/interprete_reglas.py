"""Intérprete del modo `reglas` · BLOQUE C (José Cornejo).

Sin LLM: reconoce el cliente por su nombre comercial (consulta al CRM), un ID de cotización si aparece
(`COT-NNN-VNN`), la cantidad mencionada ("600 paquetes") y el canal. Determinista y probado.
"""

from __future__ import annotations

from datetime import date

from sie.agentes.comercial.intencion import Intencion
from sie.crm.consultas import ConsultasCRM


class InterpreteReglas:
    def __init__(self, crm: ConsultasCRM) -> None:
        self.crm = crm

    def interpretar(self, texto: str, fecha_negocio: date, canal: str | None = None) -> Intencion:
        raise NotImplementedError("Bloque C (José): intérprete por reglas. Ver arquitectura/bloques/BLOQUE_C.md.")
