"""Contrato de transición CRM–ERP (interfaz I8) · v1.2 (PC3).

Tipos de los mensajes EV-02 y EV-05 (CRM → ERP) y EV-03 y EV-04 (ERP → CRM), catálogo de los
nueve códigos de respuesta y estados de la solicitud. El formato JSON es el de los ejemplos del EP
(`arquitectura/contrato_i8/ejemplos/`): ilustrativo [SUPUESTO], no reproduce la API de SAP.

Cambios respecto de v1.1 (EP):
- EV-05 lleva el bloque `aceptacion` con la evidencia de aceptación del cliente, que el contrato
  exigía (`eventos_contrato.csv`) y el ejemplo del EP no traía.
- La respuesta informa `pedido.estado_pedido` (estado al responder). El EP usaba
  `estado_pedido_al_corte`; `desde_dict` acepta ambos nombres.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any


class Canal(StrEnum):
    TUALI = "TUALI"
    PREVENTA = "Preventa"
    TELEFONO = "Teléfono"


class TipoMensaje(StrEnum):
    SOLICITUD_INICIAL = "Solicitud inicial"
    REINTENTO = "Reintento"
    CONFIRMACION_PROMESA = "Confirmación promesa"


class EventoContrato(StrEnum):
    EV02 = "EV-02 Solicitar creación de pedido"
    EV03 = "EV-03 Aceptar o rechazar pedido"
    EV04 = "EV-04 Proponer promesa alternativa"
    EV05 = "EV-05 Confirmar promesa"


class Codigo(StrEnum):
    OK_ACEPTADO = "OK-ACEPTADO"
    OK_PROMESA_ALT = "OK-PROMESA-ALT"
    ATP_PARCIAL = "ATP-PARCIAL"
    PRECIO_NO_VIG = "PRECIO-NO-VIG"
    DESC_SIN_APROB = "DESC-SIN-APROB"
    CRED_BLOQ = "CRED-BLOQ"
    CLI_NO_VALIDO = "CLI-NO-VALIDO"
    DATO_OBLIG = "DATO-OBLIG"
    DUPLICADO = "DUPLICADO"


class EstadoSolicitud(StrEnum):
    ENVIADA = "Enviada"
    ACEPTADA = "Aceptada"
    RECHAZADA = "Rechazada"
    PROMESA_ALTERNATIVA = "Promesa alternativa"


#: Resultado interno del agente cuando la cotización no puede enviarse (regla R2). No es un código
#: del contrato: la solicitud nunca llega al ERP (ADR-005).
NO_ENVIADA = "NO-ENVIADA"

#: Unidad de venta del modelo: paquete (CJ).
UNIDAD_PAQUETE = "CJ"


@dataclass(frozen=True)
class EntradaCatalogo:
    codigo: Codigo
    significado: str
    quien_corrige: str | None
    siguiente_paso: str
    reintento: str
    estado: EstadoSolicitud
    evento: EventoContrato
    crea_pedido: bool


def _entrada(codigo, significado, quien, siguiente, reintento, estado, evento, crea=False):
    return EntradaCatalogo(Codigo(codigo), significado, quien, siguiente, reintento, estado, evento, crea)


_E, _R, _P = EventoContrato, EstadoSolicitud, EstadoSolicitud.PROMESA_ALTERNATIVA

#: Catálogo de respuestas (codigos_respuesta.csv del EP). DUPLICADO responde "Rechazada": el
#: intento se rechaza y devuelve el pedido existente [SUPUESTO del equipo].
CATALOGO: dict[Codigo, EntradaCatalogo] = {
    e.codigo: e
    for e in (
        _entrada("OK-ACEPTADO", "Pedido creado tal como se solicitó", None,
                 "Seguimiento de entrega", "No aplica", _R.ACEPTADA, _E.EV03, True),
        _entrada("OK-PROMESA-ALT", "Pedido creado con entrega parcial aceptada por el cliente", None,
                 "Seguimiento de la reposición", "No aplica", _R.ACEPTADA, _E.EV03, True),
        _entrada("ATP-PARCIAL", "Stock insuficiente: el ERP propone cantidad y fecha alternativas",
                 "Preventista con el cliente", "Confirmar promesa (EV-05), reducir cantidad o cancelar",
                 "Sí, como Confirmación promesa", _P, _E.EV04),
        _entrada("PRECIO-NO-VIG", "Alguna línea usa un precio sin vigencia en el ERP a la fecha de envío",
                 "Analista de precios RGM", "Cargar la condición en ECC (I10) y reenviar",
                 "Sí, mismo id_solicitud", _R.RECHAZADA, _E.EV03),
        _entrada("DESC-SIN-APROB", "Descuento sobre 5% sin aprobación registrada", "Supervisor de ventas",
                 "Aprobar o emitir nueva versión de cotización", "Sí, con nueva versión", _R.RECHAZADA, _E.EV03),
        _entrada("CRED-BLOQ", "Crédito bloqueado o total mayor al límite disponible", "Créditos y cobranzas",
                 "Liberar, pedir garantía o pasar a contado", "Sí, tras la decisión", _R.RECHAZADA, _E.EV03),
        _entrada("CLI-NO-VALIDO", "Cliente inexistente, inactivo o no sincronizado",
                 "Analista de datos maestros", "Completar el alta (EV-01)", "Sí", _R.RECHAZADA, _E.EV03),
        _entrada("DATO-OBLIG", "Falta un dato obligatorio del mensaje", "Preventista",
                 "Completar y reenviar", "Sí", _R.RECHAZADA, _E.EV03),
        _entrada("DUPLICADO", "La solicitud o cotización ya tiene pedido", "Soporte de integración",
                 "Devolver el id_pedido existente; no se crea otro", "No", _R.RECHAZADA, _E.EV03),
    )
}


# --------------------------------------------------------------------------- utilidades de serialización

def _fecha(valor: Any) -> date | None:
    if valor in (None, ""):
        return None
    if isinstance(valor, date):
        return valor
    return date.fromisoformat(str(valor))


def _iso(valor: date | None) -> str | None:
    return valor.isoformat() if valor else None


# --------------------------------------------------------------------------- mensajes CRM → ERP

@dataclass
class LineaSolicitud:
    numero_linea: int
    id_producto: str
    cantidad: int
    id_precio: str
    precio_unitario: float
    descuento_pct: float
    id_regla_descuento: str
    unidad: str = UNIDAD_PAQUETE

    def a_dict(self) -> dict:
        return {
            "numero_linea": self.numero_linea,
            "id_producto": self.id_producto,
            "cantidad": self.cantidad,
            "unidad": self.unidad,
            "id_precio": self.id_precio,
            "precio_unitario": self.precio_unitario,
            "descuento_pct": self.descuento_pct,
            "id_regla_descuento": self.id_regla_descuento,
        }

    @classmethod
    def desde_dict(cls, d: dict) -> LineaSolicitud:
        return cls(
            numero_linea=d["numero_linea"],
            id_producto=d["id_producto"],
            cantidad=d["cantidad"],
            id_precio=d["id_precio"],
            precio_unitario=d["precio_unitario"],
            descuento_pct=d["descuento_pct"],
            id_regla_descuento=d["id_regla_descuento"],
            unidad=d.get("unidad", UNIDAD_PAQUETE),
        )


@dataclass
class Tramo:
    cantidad: int
    fecha: date
    origen: str

    def a_dict(self) -> dict:
        return {"cantidad": self.cantidad, "fecha": _iso(self.fecha), "origen": self.origen}

    @classmethod
    def desde_dict(cls, d: dict) -> Tramo:
        return cls(cantidad=d["cantidad"], fecha=_fecha(d["fecha"]), origen=d["origen"])


@dataclass
class Aceptacion:
    """Evidencia de que el cliente aceptó la promesa alternativa (EV-05, contrato v1.2)."""

    acepta: bool
    registrada_por: str
    fecha: date
    medio: str
    evidencia: str
    tramos_aceptados: list[Tramo] = field(default_factory=list)

    def a_dict(self) -> dict:
        return {
            "acepta": self.acepta,
            "registrada_por": self.registrada_por,
            "fecha": _iso(self.fecha),
            "medio": self.medio,
            "evidencia": self.evidencia,
            "tramos_aceptados": [t.a_dict() for t in self.tramos_aceptados],
        }

    @classmethod
    def desde_dict(cls, d: dict) -> Aceptacion:
        return cls(
            acepta=d["acepta"],
            registrada_por=d["registrada_por"],
            fecha=_fecha(d["fecha"]),
            medio=d["medio"],
            evidencia=d["evidencia"],
            tramos_aceptados=[Tramo.desde_dict(t) for t in d.get("tramos_aceptados", [])],
        )


@dataclass
class SolicitudPedido:
    """EV-02 (solicitud inicial o reintento) o EV-05 (confirmación de promesa)."""

    id_solicitud: str
    intento: int
    tipo_mensaje: TipoMensaje
    canal_origen: Canal
    fecha_envio: date
    id_cotizacion: str
    version_cotizacion: int
    id_oportunidad: str
    id_cliente: str
    codigo_cliente_erp: str | None
    id_direccion_entrega: str
    condicion_pago_dias: int
    estado_descuento: str
    acepta_entrega_parcial: bool
    lineas: list[LineaSolicitud]
    importe_total_cotizado: float | None = None
    aprobador: str | None = None
    fecha_aprobacion: date | None = None
    capturado_por: str = ""
    sistema_origen: str = "SAP Sales Cloud"
    moneda: str = "PEN"
    aceptacion: Aceptacion | None = None

    @property
    def evento(self) -> EventoContrato:
        if self.tipo_mensaje == TipoMensaje.CONFIRMACION_PROMESA:
            return EventoContrato.EV05
        return EventoContrato.EV02

    @property
    def cantidad_total(self) -> int:
        return sum(linea.cantidad for linea in self.lineas)

    def faltantes(self) -> list[str]:
        """Datos obligatorios ausentes (control P1 → `DATO-OBLIG`).

        `codigo_cliente_erp` no se exige aquí: un cliente sin código ERP es `CLI-NO-VALIDO` (C1).
        El aprobador de un descuento mayor a 5 % tampoco: su ausencia es `DESC-SIN-APROB` (C4).
        """
        faltan = []
        for nombre in ("id_solicitud", "id_cotizacion", "id_oportunidad", "id_cliente", "id_direccion_entrega",
                       "estado_descuento"):
            if not getattr(self, nombre):
                faltan.append(nombre)
        if not self.intento or self.intento < 1:
            faltan.append("intento")
        if self.version_cotizacion in (None, 0):
            faltan.append("version_cotizacion")
        if self.fecha_envio is None:
            faltan.append("fecha_envio")
        if self.condicion_pago_dias is None:
            faltan.append("condicion_pago_dias")
        if self.acepta_entrega_parcial is None:
            faltan.append("acepta_entrega_parcial")
        if self.canal_origen not in tuple(Canal):
            faltan.append("canal_origen")
        if not self.lineas:
            faltan.append("lineas")
        for linea in self.lineas:
            for nombre in ("id_producto", "id_precio", "id_regla_descuento"):
                if not getattr(linea, nombre):
                    faltan.append(f"lineas[{linea.numero_linea}].{nombre}")
            if not linea.cantidad or linea.cantidad <= 0:
                faltan.append(f"lineas[{linea.numero_linea}].cantidad")
            if linea.descuento_pct is None:
                faltan.append(f"lineas[{linea.numero_linea}].descuento_pct")
        if self.tipo_mensaje == TipoMensaje.CONFIRMACION_PROMESA:
            a = self.aceptacion
            if a is None:
                faltan.append("aceptacion")
            else:
                for nombre in ("registrada_por", "fecha", "medio", "evidencia"):
                    if not getattr(a, nombre):
                        faltan.append(f"aceptacion.{nombre}")
                if not a.tramos_aceptados:
                    faltan.append("aceptacion.tramos_aceptados")
        return faltan

    def a_dict(self) -> dict:
        d = {
            "evento": str(self.evento),
            "id_solicitud": self.id_solicitud,
            "intento": self.intento,
            "tipo_mensaje": str(self.tipo_mensaje),
            "canal_origen": str(self.canal_origen),
            "capturado_por": self.capturado_por,
            "sistema_origen": self.sistema_origen,
            "fecha_envio": _iso(self.fecha_envio),
            "id_cotizacion": self.id_cotizacion,
            "version_cotizacion": self.version_cotizacion,
            "id_oportunidad": self.id_oportunidad,
            "id_cliente": self.id_cliente,
            "codigo_cliente_erp": self.codigo_cliente_erp,
            "id_direccion_entrega": self.id_direccion_entrega,
            "moneda": self.moneda,
            "condicion_pago_dias": self.condicion_pago_dias,
            "estado_descuento": self.estado_descuento,
            "aprobador": self.aprobador,
            "fecha_aprobacion": _iso(self.fecha_aprobacion),
            "acepta_entrega_parcial": self.acepta_entrega_parcial,
            "lineas": [linea.a_dict() for linea in self.lineas],
            "importe_total_cotizado": self.importe_total_cotizado,
        }
        if self.aceptacion is not None:
            d["aceptacion"] = self.aceptacion.a_dict()
        return d

    @classmethod
    def desde_dict(cls, d: dict) -> SolicitudPedido:
        return cls(
            id_solicitud=d["id_solicitud"],
            intento=d["intento"],
            tipo_mensaje=TipoMensaje(d["tipo_mensaje"]),
            canal_origen=Canal(d["canal_origen"]),
            fecha_envio=_fecha(d["fecha_envio"]),
            id_cotizacion=d["id_cotizacion"],
            version_cotizacion=d["version_cotizacion"],
            id_oportunidad=d["id_oportunidad"],
            id_cliente=d["id_cliente"],
            codigo_cliente_erp=d.get("codigo_cliente_erp"),
            id_direccion_entrega=d["id_direccion_entrega"],
            condicion_pago_dias=d["condicion_pago_dias"],
            estado_descuento=d["estado_descuento"],
            acepta_entrega_parcial=d["acepta_entrega_parcial"],
            lineas=[LineaSolicitud.desde_dict(x) for x in d["lineas"]],
            importe_total_cotizado=d.get("importe_total_cotizado"),
            aprobador=d.get("aprobador"),
            fecha_aprobacion=_fecha(d.get("fecha_aprobacion")),
            capturado_por=d.get("capturado_por", ""),
            sistema_origen=d.get("sistema_origen", "SAP Sales Cloud"),
            moneda=d.get("moneda", "PEN"),
            aceptacion=Aceptacion.desde_dict(d["aceptacion"]) if d.get("aceptacion") else None,
        )


# --------------------------------------------------------------------------- mensajes ERP → CRM

@dataclass
class PromesaAlternativa:
    cantidad_solicitada: int
    cantidad_atp_confirmada: int
    tramos: list[Tramo]
    requiere_aceptacion_cliente: bool = True

    @property
    def cantidad_pendiente(self) -> int:
        return self.cantidad_solicitada - self.cantidad_atp_confirmada

    def a_dict(self) -> dict:
        return {
            "cantidad_solicitada": self.cantidad_solicitada,
            "cantidad_atp_confirmada": self.cantidad_atp_confirmada,
            "tramos": [t.a_dict() for t in self.tramos],
            "requiere_aceptacion_cliente": self.requiere_aceptacion_cliente,
        }

    @classmethod
    def desde_dict(cls, d: dict) -> PromesaAlternativa:
        return cls(
            cantidad_solicitada=d["cantidad_solicitada"],
            cantidad_atp_confirmada=d["cantidad_atp_confirmada"],
            tramos=[Tramo.desde_dict(t) for t in d["tramos"]],
            requiere_aceptacion_cliente=d.get("requiere_aceptacion_cliente", True),
        )


@dataclass
class PedidoResumen:
    fecha_confirmacion: date
    fecha_prometida: date
    fecha_revision_promesa: date | None
    estado_pedido: str

    def a_dict(self) -> dict:
        return {
            "fecha_confirmacion": _iso(self.fecha_confirmacion),
            "fecha_prometida": _iso(self.fecha_prometida),
            "fecha_revision_promesa": _iso(self.fecha_revision_promesa),
            "estado_pedido": self.estado_pedido,
        }

    @classmethod
    def desde_dict(cls, d: dict) -> PedidoResumen:
        return cls(
            fecha_confirmacion=_fecha(d["fecha_confirmacion"]),
            fecha_prometida=_fecha(d["fecha_prometida"]),
            fecha_revision_promesa=_fecha(d.get("fecha_revision_promesa")),
            estado_pedido=d.get("estado_pedido") or d["estado_pedido_al_corte"],
        )


@dataclass
class RespuestaERP:
    """EV-03 (acepta o rechaza) o EV-04 (promesa alternativa)."""

    id_solicitud: str
    intento: int
    codigo_respuesta: Codigo
    estado_solicitud: EstadoSolicitud
    id_pedido: str | None
    responsable_siguiente_paso: str
    siguiente_paso: str
    evento: EventoContrato
    causa: str | None = None
    pedido: PedidoResumen | None = None
    promesa_alternativa: PromesaAlternativa | None = None

    @property
    def crea_pedido(self) -> bool:
        return CATALOGO[self.codigo_respuesta].crea_pedido

    def a_dict(self) -> dict:
        d = {
            "id_solicitud": self.id_solicitud,
            "intento": self.intento,
            "codigo_respuesta": str(self.codigo_respuesta),
            "estado_solicitud": str(self.estado_solicitud),
            "id_pedido": self.id_pedido,
            "responsable_siguiente_paso": self.responsable_siguiente_paso,
            "siguiente_paso": self.siguiente_paso,
            "evento": str(self.evento),
        }
        if self.causa is not None:
            d["causa"] = self.causa
        if self.pedido is not None:
            d["pedido"] = self.pedido.a_dict()
        if self.promesa_alternativa is not None:
            d["promesa_alternativa"] = self.promesa_alternativa.a_dict()
        return d

    @classmethod
    def desde_dict(cls, d: dict) -> RespuestaERP:
        return cls(
            id_solicitud=d["id_solicitud"],
            intento=d["intento"],
            codigo_respuesta=Codigo(d["codigo_respuesta"]),
            estado_solicitud=EstadoSolicitud(d["estado_solicitud"]),
            id_pedido=d.get("id_pedido"),
            responsable_siguiente_paso=d["responsable_siguiente_paso"],
            siguiente_paso=d["siguiente_paso"],
            evento=EventoContrato(d["evento"]),
            causa=d.get("causa"),
            pedido=PedidoResumen.desde_dict(d["pedido"]) if d.get("pedido") else None,
            promesa_alternativa=(
                PromesaAlternativa.desde_dict(d["promesa_alternativa"]) if d.get("promesa_alternativa") else None
            ),
        )


# --------------------------------------------------------------------------- identificadores

def numero_documento(id_documento: str) -> str:
    """'COT-003-V01' → '003'; 'SOL-002' → '002'."""
    partes = id_documento.split("-")
    if len(partes) < 2 or not partes[1].isdigit():
        raise ValueError(f"Identificador sin número de documento: {id_documento!r}")
    return partes[1]


def id_solicitud_para(id_cotizacion: str) -> str:
    """La solicitud hereda el número de la cotización: COT-003-V01 → SOL-003 (convención del EP)."""
    return f"SOL-{numero_documento(id_cotizacion)}"


def id_pedido_para(id_solicitud: str) -> str:
    """El pedido hereda el número de la solicitud: SOL-003 → PED-003 (convención del EP)."""
    return f"PED-{numero_documento(id_solicitud)}"
