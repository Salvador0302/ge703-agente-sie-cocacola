"""Orquestador del Agente SIE: enruta cada evento al agente de su proceso.

Regla simple y auditable: el tipo de evento decide el agente (`RUTAS`). Si el agente de ese tipo
todavía no está implementado, el evento se registra en la bitácora como "no implementado aún" y no
se pierde. Agregar un agente en un incremento posterior es implementar `sie.agentes.base.Agente` y
llamar a `registrar()`; las rutas ya están previstas aquí.
"""

from __future__ import annotations

from dataclasses import dataclass

from sie.agentes.base import Agente, EstadoResultado, Evento, ResultadoAgente
from sie.bitacora import Bitacora, EntradaBitacora


@dataclass(frozen=True)
class AgentePrevisto:
    nombre: str
    proceso: str
    incremento: str
    nota: str = ""


#: Agentes del proyecto en el orden en que se implementan (plan PC3, §1).
AGENTES_PREVISTOS: tuple[AgentePrevisto, ...] = (
    AgentePrevisto("comercial", "Solicitud de pedido del canal tradicional (contrato I8)", "PC3"),
    AgentePrevisto("cadena_suministro", "Abastecimiento, reposición e inventario", "Semana 12"),
    AgentePrevisto("logistica", "Almacén, transporte y entrega", "Semana 13"),
    AgentePrevisto("finanzas_operativas", "Factura, cuentas por cobrar y por pagar, conciliación y controles", "PC4"),
    AgentePrevisto("ceo", "Indicadores integrados del proyecto", "Por definir",
                   "Mencionado en el curso (S5 lám. 26, S6 lám. 21); se confirma con el docente"),
)

#: Tipo de evento → agente responsable.
RUTAS: dict[str, str] = {
    "pedido": "comercial",
    "decision_humana": "comercial",
    "abastecimiento": "cadena_suministro",
    "reposicion": "cadena_suministro",
    "inventario": "cadena_suministro",
    "entrega": "logistica",
    "transporte": "logistica",
    "factura": "finanzas_operativas",
    "cobro": "finanzas_operativas",
    "pago_proveedor": "finanzas_operativas",
    "conciliacion": "finanzas_operativas",
    "indicadores": "ceo",
}


class TipoEventoDesconocido(ValueError):
    pass


class Orquestador:
    def __init__(self, bitacora: Bitacora, agentes: list[Agente] | None = None) -> None:
        self.bitacora = bitacora
        self._agentes: dict[str, Agente] = {}
        for agente in agentes or []:
            self.registrar(agente)

    def registrar(self, agente: Agente) -> None:
        previstos = {a.nombre for a in AGENTES_PREVISTOS}
        if agente.nombre not in previstos:
            raise ValueError(f"Agente {agente.nombre!r} no está previsto en AGENTES_PREVISTOS.")
        for tipo in agente.tipos_evento:
            if RUTAS.get(tipo) != agente.nombre:
                raise ValueError(f"El tipo de evento {tipo!r} no está enrutado al agente {agente.nombre!r}.")
        self._agentes[agente.nombre] = agente

    def agente_para(self, tipo: str) -> str:
        if tipo not in RUTAS:
            raise TipoEventoDesconocido(
                f"Tipo de evento desconocido: {tipo!r}. Tipos válidos: {', '.join(sorted(RUTAS))}."
            )
        return RUTAS[tipo]

    def despachar(self, evento: Evento) -> ResultadoAgente:
        nombre = self.agente_para(evento.tipo)
        self.bitacora.registrar(EntradaBitacora(
            agente="orquestador", paso="enrutar", resultado=f"{evento.tipo} → {nombre}",
            fecha_negocio=evento.fecha_negocio, run_id=evento.run_id,
            entrada={"tipo": evento.tipo, "origen": evento.origen, "id_evento": evento.id_evento},
        ))
        agente = self._agentes.get(nombre)
        if agente is None:
            previsto = next(a for a in AGENTES_PREVISTOS if a.nombre == nombre)
            mensaje = f"El agente {nombre!r} ({previsto.proceso}) no está implementado aún: {previsto.incremento}."
            self.bitacora.registrar(EntradaBitacora(
                agente="orquestador", paso="no implementado", resultado=mensaje,
                fecha_negocio=evento.fecha_negocio, run_id=evento.run_id,
                codigo=str(EstadoResultado.NO_IMPLEMENTADO), entrada={"tipo": evento.tipo},
            ))
            return ResultadoAgente(agente=nombre, estado=EstadoResultado.NO_IMPLEMENTADO,
                                   mensaje=mensaje, run_id=evento.run_id)
        resultado = agente.manejar(evento)
        resultado.run_id = resultado.run_id or evento.run_id
        return resultado

    def estado(self) -> list[dict[str, str]]:
        """Lista de agentes previstos con su estado (para `python -m sie agentes`)."""
        filas = []
        for a in AGENTES_PREVISTOS:
            tipos = sorted(t for t, n in RUTAS.items() if n == a.nombre)
            filas.append({
                "agente": a.nombre,
                "proceso": a.proceso,
                "incremento": a.incremento,
                "estado": "implementado" if a.nombre in self._agentes else "no implementado aún",
                "eventos": ", ".join(tipos),
                "nota": a.nota,
            })
        return filas
