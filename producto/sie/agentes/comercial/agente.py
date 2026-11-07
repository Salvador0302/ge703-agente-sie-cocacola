"""Agente comercial · BLOQUE C (José Cornejo). Interfaz definida por el bloque A.

Eventos que atiende:
- `pedido`: datos {"texto": str, "canal": "TUALI" | "Preventa" | "Teléfono"}; `fecha_negocio` = fecha de envío.
- `decision_humana`: datos {"id_escalamiento": str, "acepta": bool, "registrada_por": str,
  "medio": str, "evidencia": str}; `fecha_negocio` = fecha de la confirmación.

Flujo de `pedido`: interpretar → identificar la cotización aceptada (R2, si no: `NO-ENVIADA`) → armar
EV-02 desde el CRM → consulta no vinculante de ATP (I3) → enviar por I8 (`ServicioERP.recibir`) →
según el código: registrar en el CRM, escalar al responsable del catálogo o esperar la decisión
humana (ATP-PARCIAL) → redactar la explicación → bitácora en cada paso.

Permisos (ficha del agente): lee CRM y consulta ERP; envía EV-02/EV-05; **no** crea pedidos, no aprueba
descuentos, no cambia maestros y no confirma promesas sin un evento `decision_humana`.
"""

from __future__ import annotations

from sie.agentes.base import Evento, ResultadoAgente
from sie.agentes.comercial.intencion import Interprete, Redactor
from sie.bitacora import Bitacora
from sie.crm.consultas import ConsultasCRM
from sie.erp.servicio import ServicioERP

_PENDIENTE = "Bloque C (José): agente comercial. Ver arquitectura/bloques/BLOQUE_C.md."


class AgenteComercial:
    nombre = "comercial"
    tipos_evento = frozenset({"pedido", "decision_humana"})

    def __init__(self, erp: ServicioERP, crm: ConsultasCRM, interprete: Interprete, redactor: Redactor,
                 bitacora: Bitacora, modo: str = "reglas") -> None:
        self.erp = erp
        self.crm = crm
        self.interprete = interprete
        self.redactor = redactor
        self.bitacora = bitacora
        self.modo = modo

    def manejar(self, evento: Evento) -> ResultadoAgente:
        raise NotImplementedError(_PENDIENTE)
