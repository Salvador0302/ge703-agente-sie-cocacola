"""Redacción por plantillas: el redactor del modo `reglas` y el respaldo del modo `llm`.

Convierte los hechos del resultado en una explicación breve en español. Solo usa cifras de los hechos.
"""

from __future__ import annotations

from datetime import date
from typing import Any


def _dmy(valor: Any) -> str:
    if not valor:
        return "—"
    d = valor if isinstance(valor, date) else date.fromisoformat(str(valor)[:10])
    return d.strftime("%d/%m/%Y")


def _tramos(promesa: dict | None) -> str:
    tramos = (promesa or {}).get("tramos") or []
    return " y ".join(f"{t['cantidad']} paquetes el {_dmy(t['fecha'])}" for t in tramos) or "sin tramos"


class RedactorPlantilla:
    def redactar(self, hechos: dict[str, Any]) -> str:
        estado = hechos.get("estado")
        codigo = hechos.get("codigo")
        sol = f"{hechos.get('id_solicitud')} intento {hechos.get('intento')}"
        responsable = hechos.get("responsable") or "el responsable"
        siguiente = hechos.get("siguiente_paso") or ""
        if estado == "NO_ENVIADA":
            return (f"La solicitud no se envió al ERP: {hechos.get('causa')}. "
                    f"{responsable} debe resolverlo antes del {_dmy(hechos.get('fecha_limite'))}.")
        if estado == "CERRADO_SIN_PEDIDO":
            return (f"{hechos.get('registrada_por', responsable)} registró que el cliente rechaza la promesa alternativa "
                    f"de {hechos.get('id_solicitud')}. No se envía EV-05 y no se crea pedido.")
        if estado == "ERROR":
            return f"No se procesó el evento: {hechos.get('causa')}."
        if codigo == "OK-ACEPTADO":
            return (f"El ERP aceptó {sol} (OK-ACEPTADO) y creó el pedido {hechos.get('id_pedido')} con entrega "
                    f"prometida el {_dmy(hechos.get('fecha_prometida'))}. Siguiente paso: {siguiente} ({responsable}).")
        if codigo == "OK-PROMESA-ALT":
            return (f"Con la aceptación del cliente, el ERP creó el pedido {hechos.get('id_pedido')} con entrega parcial "
                    f"(OK-PROMESA-ALT): {_tramos(hechos.get('promesa'))}. Siguiente paso: {siguiente} ({responsable}).")
        if codigo == "ATP-PARCIAL":
            causa = hechos.get("causa_faltante") or {}
            texto_causa = (f" La causa es la parada {causa['id_ot']} de {causa['id_activo']} ({causa['horas_parada']} h, "
                           f"{causa['paquetes_perdidos']} paquetes menos); sin ella habría {causa['atp_sin_parada']}."
                           if causa else "")
            return (f"El ERP no confirma los {hechos.get('cantidad_solicitada')} paquetes de {sol}: hay "
                    f"{hechos.get('atp')} disponibles (ATP-PARCIAL).{texto_causa} Propone {_tramos(hechos.get('promesa'))}. "
                    f"{responsable} debe confirmar con el cliente antes del {_dmy(hechos.get('fecha_limite'))}; "
                    f"sin esa aceptación no se crea el pedido.")
        return (f"El ERP rechazó {sol} ({codigo}): {hechos.get('causa')}. "
                f"{responsable} debe: {siguiente}.")
