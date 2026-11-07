"""Intérprete del modo `reglas`: sin LLM, determinista.

Reconoce el cliente por su nombre comercial (consulta al CRM), un ID de cotización si aparece
(`COT-NNN-VNN`), la cantidad mencionada ("600 paquetes"; "500 ml" no es una cantidad), el producto y,
si el sistema no lo informa, el canal.
"""

from __future__ import annotations

import re
from datetime import date

from sie.agentes.comercial.intencion import Intencion
from sie.crm.consultas import ConsultasCRM, normalizar

_COTIZACION = re.compile(r"\bCOT-\d{3}-V\d{2}\b", re.IGNORECASE)
_CANTIDAD = re.compile(r"\b(\d{1,6})\s*(?:paquetes?|cajas?|cj|pqts?)\b", re.IGNORECASE)
_CANALES = (("tuali", "TUALI"), ("llam", "Teléfono"), ("telefon", "Teléfono"), ("whatsapp", "Teléfono"),
            ("preventa", "Preventa"), ("preventista", "Preventa"), ("ac movil", "Preventa"))


class InterpreteReglas:
    def __init__(self, crm: ConsultasCRM) -> None:
        self.crm = crm
        self.ultimas_trazas: list[dict] = []

    def _producto(self, texto: str) -> str | None:
        t = normalizar(texto)
        for p in self.crm.conn.execute("SELECT id_producto, descripcion FROM productos"):
            nombre = normalizar(re.split(r"\s+(?:PET|·)", p["descripcion"])[0])
            if nombre and nombre in t:
                return p["id_producto"]
        return None

    def interpretar(self, texto: str, fecha_negocio: date, canal: str | None = None) -> Intencion:
        cot = _COTIZACION.search(texto)
        cantidad = _CANTIDAD.search(texto)
        canal_texto = next((c for clave, c in _CANALES if clave in normalizar(texto)), None)
        id_cliente = self.crm.identificar_cliente(texto)
        intencion = Intencion(
            texto=texto,
            id_cliente=id_cliente,
            canal_origen=canal or canal_texto,
            id_cotizacion=cot.group(0).upper() if cot else None,
            cantidad_mencionada=int(cantidad.group(1)) if cantidad else None,
            producto_mencionado=self._producto(texto),
            fuente="reglas",
        )
        partes = [id_cliente or "cliente no identificado"]
        if intencion.cantidad_mencionada:
            partes.append(f"{intencion.cantidad_mencionada} paquetes")
        if intencion.id_cotizacion:
            partes.append(intencion.id_cotizacion)
        intencion.resumen = " · ".join(partes)
        return intencion
