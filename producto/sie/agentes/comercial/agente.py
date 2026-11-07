"""Agente comercial (PC3): solicitud de pedido del canal tradicional por el contrato I8.

Eventos que atiende:
- `pedido`: datos {"texto": str, "canal": "TUALI" | "Preventa" | "Teléfono"}; `fecha_negocio` = fecha de envío.
- `decision_humana`: datos {"id_escalamiento": str, "acepta": bool, "registrada_por": str,
  "medio": str, "evidencia": str}; `fecha_negocio` = fecha de la confirmación.

Flujo de `pedido`: interpretar → identificar la cotización aceptada (R2; si no, `NO-ENVIADA`) → armar
EV-02 desde el CRM → consulta no vinculante de ATP (I3) → enviar por I8 (`ServicioERP.recibir`) →
según el código: registrar en el CRM, escalar al responsable del catálogo o esperar la decisión
humana (ATP-PARCIAL) → redactar la explicación → bitácora en cada paso.

Permisos (ficha del agente, ADR-003): lee CRM y consulta ERP; envía EV-02/EV-05; **no** crea pedidos, no
aprueba descuentos, no cambia maestros y no confirma promesas sin un evento `decision_humana`.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from typing import Any

from sie.agentes.base import Escalamiento, EstadoResultado, Evento, ResultadoAgente
from sie.agentes.comercial.intencion import Interprete, Redactor
from sie.bitacora import Bitacora, EntradaBitacora
from sie.contrato import (NO_ENVIADA, Aceptacion, Canal, Codigo, PromesaAlternativa, RespuestaERP, TipoMensaje,
                          id_solicitud_para)
from sie.crm.consultas import ConsultasCRM
from sie.erp.servicio import ServicioERP

#: Plazo para que el responsable humano resuelva un escalamiento (SUPUESTO del equipo, ADR-005).
PLAZO_ESCALAMIENTO = timedelta(days=1)


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
        if evento.tipo == "pedido":
            return self._pedido(evento)
        if evento.tipo == "decision_humana":
            return self._decision(evento)
        raise ValueError(f"El agente comercial no atiende eventos {evento.tipo!r}")

    # ----------------------------------------------------------------------- bitácora y resultado

    def _log(self, evento: Evento, paso: str, resultado: str, **campos: Any) -> None:
        campos.setdefault("modo", self.modo)
        self.bitacora.registrar(EntradaBitacora(agente=self.nombre, paso=paso, resultado=resultado,
                                                fecha_negocio=evento.fecha_negocio, run_id=evento.run_id, **campos))

    def _cerrar(self, evento: Evento, estado: EstadoResultado, codigo: str | None, ids: dict, hechos: dict,
                escalamiento: Escalamiento | None = None, detalle: dict | None = None,
                avisos: list[str] | None = None) -> ResultadoAgente:
        avisos = list(avisos or [])
        mensaje = self.redactor.redactar({"estado": str(estado), "codigo": codigo, **ids, **hechos})
        aviso_redaccion = getattr(self.redactor, "ultimo_aviso", None)
        if aviso_redaccion:
            avisos.append(aviso_redaccion)
        detalle = {**(detalle or {}), "avisos": avisos}
        self._log(evento, "resultado", f"{estado} · {codigo or 'sin código'} · {ids.get('id_pedido') or 'sin pedido'}",
                  codigo=codigo, ids=ids, detalle={"avisos": avisos})
        return ResultadoAgente(agente=self.nombre, estado=estado, mensaje=mensaje, codigo=codigo, ids=ids,
                               escalamiento=escalamiento, detalle=detalle, run_id=evento.run_id)

    # ----------------------------------------------------------------------- escalamientos

    def _escalar(self, evento: Evento, id_escalamiento: str, objeto: str, causa: str, responsable: str,
                 ids: dict, opciones: list[str], datos: dict | None = None) -> Escalamiento:
        esc = Escalamiento(id_escalamiento=id_escalamiento, objeto=objeto, causa=causa, responsable=responsable,
                           fecha_limite=evento.fecha_negocio + PLAZO_ESCALAMIENTO, opciones=opciones,
                           datos=datos or {})
        with self.crm.conn:
            self.crm.conn.execute(
                "INSERT OR REPLACE INTO escalamientos (id_escalamiento, run_id, id_solicitud, intento, objeto, causa, "
                "responsable, fecha_limite, estado, opciones_json, datos_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente', ?, ?)",
                (esc.id_escalamiento, evento.run_id, ids.get("id_solicitud"), ids.get("intento"), objeto, causa,
                 responsable, esc.fecha_limite.isoformat(), json.dumps(opciones, ensure_ascii=False),
                 json.dumps(esc.datos, ensure_ascii=False, default=str)))
        self._log(evento, "escalar", f"{esc.id_escalamiento} · {objeto}", ids=ids, escalado_a=responsable,
                  motivo=causa, fecha_limite=esc.fecha_limite, codigo=ids.get("codigo"))
        return esc

    def _id_no_enviada(self, base: str) -> str:
        n = self.crm.conn.execute("SELECT COUNT(*) FROM escalamientos WHERE id_escalamiento LIKE ?",
                                  (f"ESC-{base}-R2-%",)).fetchone()[0]
        return f"ESC-{base}-R2-{n + 1}"

    def _no_enviada(self, evento: Evento, causa: str, responsable: str, ids: dict, regla: str,
                    avisos: list[str]) -> ResultadoAgente:
        self._log(evento, f"{regla} cotización solicitable", f"F · {causa}", regla=regla, codigo=NO_ENVIADA, ids=ids)
        base = ids.get("id_cotizacion") or ids.get("id_cliente") or "SIN-CLIENTE"
        esc = self._escalar(evento, self._id_no_enviada(base), f"Pedido no enviado ({base})", causa, responsable,
                            ids, ["Emitir o corregir la cotización y reenviar", "Cancelar"])
        return self._cerrar(evento, EstadoResultado.NO_ENVIADA, NO_ENVIADA, ids,
                            {"causa": causa, "responsable": responsable, "fecha_limite": esc.fecha_limite},
                            escalamiento=esc, avisos=avisos)

    # ----------------------------------------------------------------------- evento pedido

    def _pedido(self, evento: Evento) -> ResultadoAgente:
        texto = str(evento.datos.get("texto") or "").strip()
        canal = evento.datos.get("canal")
        if not texto or canal not in tuple(Canal):
            causa = "El evento debe traer texto y un canal válido (TUALI, Preventa o Teléfono)"
            self._log(evento, "validar entrada", f"F · {causa}", regla="R8")
            return self._cerrar(evento, EstadoResultado.ERROR, None, {}, {"causa": causa})
        canal = Canal(canal)
        fecha = evento.fecha_negocio

        intencion = self.interprete.interpretar(texto, fecha, str(canal))
        avisos = list(intencion.avisos)
        trazas = getattr(self.interprete, "ultimas_trazas", []) or []
        self._log(evento, "interpretar",
                  f"cliente {intencion.id_cliente or 'no identificado'} · cotización "
                  f"{intencion.id_cotizacion or 'no indicada'} · cantidad {intencion.cantidad_mencionada or 'no indicada'}",
                  entrada={"canal": str(canal), "longitud_texto": len(texto),
                           "hash_texto": hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]},
                  ids={"id_cliente": intencion.id_cliente, "id_cotizacion": intencion.id_cotizacion},
                  modo=intencion.fuente,
                  detalle={"herramientas": [t["herramienta"] for t in trazas], "avisos": avisos})

        ids: dict[str, Any] = {"id_cliente": intencion.id_cliente}
        cot = self.crm.cotizacion(intencion.id_cotizacion) if intencion.id_cotizacion else None
        if intencion.id_cotizacion and cot is None:
            ids["id_cotizacion"] = intencion.id_cotizacion
            return self._no_enviada(evento, f"La cotización {intencion.id_cotizacion} no existe en el CRM",
                                    "Preventista", ids, "P3", avisos)
        if cot and intencion.id_cliente and cot["id_cliente"] != intencion.id_cliente:
            ids["id_cotizacion"] = cot["id_cotizacion"]
            return self._no_enviada(evento, f"La cotización {cot['id_cotizacion']} no es del cliente "
                                    f"{intencion.id_cliente}", cot["ejecutivo_cuenta"], ids, "P3", avisos)
        id_cliente = intencion.id_cliente or (cot["id_cliente"] if cot else None)
        if id_cliente is None:
            return self._no_enviada(evento, "No se identificó al cliente en la solicitud", "Preventista", ids,
                                    "P3", avisos)
        ids["id_cliente"] = id_cliente
        cliente = self.crm.cliente(id_cliente)
        ejecutivo = (cliente or {}).get("ejecutivo_cuenta") or "Preventista"
        if cot is None:
            candidatas = [c for c in self.crm.cotizaciones_del_cliente(id_cliente, fecha)
                          if c["estado_cotizacion"] == "Aceptada" and fecha.isoformat() <= c["vigente_hasta"]
                          and not c["tiene_pedido"]]
            if not candidatas:
                return self._no_enviada(evento, f"El cliente {id_cliente} no tiene una cotización aceptada y vigente "
                                        f"sin pedido (R2)", ejecutivo, ids, "R2", avisos)
            cot = self.crm.cotizacion(candidatas[-1]["id_cotizacion"])
        ids["id_cotizacion"] = cot["id_cotizacion"]

        if cot["estado_cotizacion"] != "Aceptada":
            responsable = "Supervisor de ventas" if cot["estado_descuento"] == "Rechazado" else ejecutivo
            return self._no_enviada(evento, f"{cot['id_cotizacion']} está {cot['estado_cotizacion']} "
                                    f"(descuento {cot['estado_descuento']}); solo una versión Aceptada y vigente "
                                    f"genera solicitud (R2)", responsable, ids, "R2", avisos)
        if fecha.isoformat() > cot["vigente_hasta"]:
            return self._no_enviada(evento, f"{cot['id_cotizacion']} venció el {cot['vigente_hasta']} (R2)",
                                    ejecutivo, ids, "R2", avisos)
        if intencion.cantidad_mencionada and intencion.cantidad_mencionada != cot["cantidad_total"]:
            return self._no_enviada(evento, f"La cantidad pedida ({intencion.cantidad_mencionada} paquetes) no coincide "
                                    f"con la cotizada en {cot['id_cotizacion']} ({cot['cantidad_total']}); requiere "
                                    f"una nueva versión (R2)", ejecutivo, ids, "R2", avisos)
        self._log(evento, "R2 cotización solicitable",
                  f"V · {cot['id_cotizacion']} Aceptada, vigente hasta {cot['vigente_hasta']}, "
                  f"{cot['cantidad_total']} paquetes", regla="R2", ids=dict(ids))

        id_solicitud = id_solicitud_para(cot["id_cotizacion"])
        intento = self.crm.ultimo_intento(id_solicitud) + 1
        tipo = TipoMensaje.SOLICITUD_INICIAL if intento == 1 else TipoMensaje.REINTENTO
        sol = self.crm.construir_solicitud(cot["id_cotizacion"], canal, fecha, intento, tipo)
        ids.update({"id_solicitud": id_solicitud, "intento": intento})
        for linea in sol.lineas:
            d = self.erp.consultar_atp(linea.id_producto, fecha)
            self._log(evento, "pre-chequeo ATP (I3)",
                      f"{linea.id_producto}: {d.disponible} disponibles para {linea.cantidad} (no vinculante)",
                      ids=dict(ids))
        self._log(evento, "enviar EV-02", f"{id_solicitud} intento {intento} · {sol.cantidad_total} paquetes · "
                  f"canal {canal}", regla="ADR-003", ids=dict(ids))
        respuesta = self.erp.recibir(sol, run_id=evento.run_id)
        return self._tras_respuesta(evento, respuesta, canal, ids, ejecutivo, avisos, sol.cantidad_total)

    def _tras_respuesta(self, evento: Evento, respuesta: RespuestaERP, canal: Canal, ids: dict, ejecutivo: str,
                        avisos: list[str], cantidad: int) -> ResultadoAgente:
        codigo = str(respuesta.codigo_respuesta)
        if respuesta.id_pedido:
            ids["id_pedido"] = respuesta.id_pedido
        self._log(evento, "recibir respuesta", f"{codigo} · {respuesta.id_pedido or 'sin pedido'}", codigo=codigo,
                  ids=dict(ids))
        hechos: dict[str, Any] = {"causa": respuesta.causa, "responsable": respuesta.responsable_siguiente_paso,
                                  "siguiente_paso": respuesta.siguiente_paso, "cantidad_solicitada": cantidad}
        detalle: dict[str, Any] = {"respuesta": respuesta.a_dict()}
        if respuesta.crea_pedido:
            cambios = self.crm.registrar_respuesta(respuesta, canal, evento.fecha_negocio)
            self._log(evento, "registrar en CRM", " · ".join(cambios.values()) or "sin cambios", regla="R9",
                      ids=dict(ids))
            hechos["fecha_prometida"] = respuesta.pedido.fecha_prometida if respuesta.pedido else None
            if respuesta.codigo_respuesta == Codigo.OK_PROMESA_ALT:
                hechos["promesa"] = {"tramos": [t.a_dict() for t in self._tramos_aceptados(ids)]}
            return self._cerrar(evento, EstadoResultado.COMPLETADO, codigo, ids, hechos, detalle=detalle,
                                avisos=avisos)
        if respuesta.codigo_respuesta == Codigo.ATP_PARCIAL:
            promesa = respuesta.promesa_alternativa
            sol_ids = {"id_solicitud": ids["id_solicitud"], "intento": ids["intento"]}
            corta = self._producto_corto(sol_ids)
            causa = self.erp.explicar_faltante(corta, evento.fecha_negocio) if corta else None
            if causa:
                ids["id_ot"] = causa.id_ot
                detalle["causa"] = causa.a_dict()
                hechos["causa_faltante"] = causa.a_dict()
            detalle["promesa"] = promesa.a_dict()
            hechos.update({"promesa": promesa.a_dict(), "atp": promesa.cantidad_atp_confirmada})
            esc = self._escalar(
                evento, f"ESC-{ids['id_solicitud']}-{ids['intento']}", f"{ids['id_solicitud']} intento {ids['intento']}",
                respuesta.causa or "ATP insuficiente (C5)", ejecutivo, {**ids, "codigo": codigo},
                ["El cliente acepta la promesa alternativa (EV-05)", "El cliente rechaza"],
                datos={"promesa": promesa.a_dict(), "id_cotizacion": ids["id_cotizacion"], "canal": str(canal),
                       "id_cliente": ids["id_cliente"]})
            hechos.update({"fecha_limite": esc.fecha_limite, "responsable": ejecutivo})
            return self._cerrar(evento, EstadoResultado.ESPERA_HUMANO, codigo, ids, hechos, escalamiento=esc,
                                detalle=detalle, avisos=avisos)
        esc = self._escalar(evento, f"ESC-{ids['id_solicitud']}-{ids['intento']}",
                            f"{ids['id_solicitud']} intento {ids['intento']}", respuesta.causa or codigo,
                            respuesta.responsable_siguiente_paso, {**ids, "codigo": codigo}, [respuesta.siguiente_paso])
        hechos["fecha_limite"] = esc.fecha_limite
        return self._cerrar(evento, EstadoResultado.ESCALADO, codigo, ids, hechos, escalamiento=esc, detalle=detalle,
                            avisos=avisos)

    def _producto_corto(self, sol_ids: dict) -> str | None:
        fila = self.crm.conn.execute(
            "SELECT d.id_producto FROM cotizaciones_det d JOIN solicitudes_pedido s ON s.id_cotizacion = d.id_cotizacion "
            "WHERE s.id_solicitud = ? AND s.intento = ? ORDER BY d.cantidad DESC LIMIT 1",
            (sol_ids["id_solicitud"], sol_ids["intento"])).fetchone()
        return fila[0] if fila else None

    def _tramos_aceptados(self, ids: dict):
        from sie.contrato import Tramo

        return [Tramo(int(t["cantidad"]), date.fromisoformat(t["fecha"]), t["origen"]) for t in self.crm.conn.execute(
            "SELECT * FROM promesa_tramos WHERE id_solicitud = ? AND intento = ? ORDER BY numero_tramo",
            (ids["id_solicitud"], ids["intento"]))]

    # ----------------------------------------------------------------------- evento decision_humana

    def _decision(self, evento: Evento) -> ResultadoAgente:
        d = evento.datos
        id_esc = str(d.get("id_escalamiento") or "")
        fila = self.crm.conn.execute("SELECT * FROM escalamientos WHERE id_escalamiento = ?", (id_esc,)).fetchone()
        if fila is None or fila["estado"] != "Pendiente" or not fila["datos_json"]:
            causa = f"No hay un escalamiento pendiente {id_esc or '(sin ID)'} con una promesa que confirmar"
            self._log(evento, "registrar decisión humana", f"F · {causa}", regla="ADR-005")
            return self._cerrar(evento, EstadoResultado.ERROR, None, {}, {"causa": causa})
        if not d.get("registrada_por") or not d.get("evidencia"):
            causa = "La decisión debe registrar quién la toma y la evidencia de la aceptación (EV-05)"
            self._log(evento, "registrar decisión humana", f"F · {causa}", regla="ADR-005")
            return self._cerrar(evento, EstadoResultado.ERROR, None, {}, {"causa": causa})
        datos = json.loads(fila["datos_json"])
        acepta = bool(d.get("acepta"))
        ids: dict[str, Any] = {"id_cliente": datos.get("id_cliente"), "id_cotizacion": datos["id_cotizacion"],
                               "id_solicitud": fila["id_solicitud"]}
        avisos = []
        if evento.fecha_negocio > date.fromisoformat(fila["fecha_limite"]):
            avisos.append(f"Decisión registrada después de la fecha límite {fila['fecha_limite']}")
        respuesta_humana = (f"{'acepta' if acepta else 'rechaza'} · {d['registrada_por']} · {d.get('medio') or ''} · "
                            f"evidencia {d['evidencia']}")
        self._log(evento, "registrar decisión humana",
                  f"{d['registrada_por']}: el cliente {'acepta' if acepta else 'rechaza'} la promesa · "
                  f"evidencia {d['evidencia']}", regla="ADR-005", respuesta_humana=respuesta_humana,
                  ids={**ids, "id_escalamiento": id_esc})
        with self.crm.conn:
            self.crm.conn.execute(
                "UPDATE escalamientos SET estado = 'Resuelto', respuesta_humana = ?, fecha_respuesta = ?, evidencia = ? "
                "WHERE id_escalamiento = ?", (respuesta_humana, evento.fecha_negocio.isoformat(), d["evidencia"], id_esc))
        if not acepta:
            ids["intento"] = fila["intento"]
            return self._cerrar(evento, EstadoResultado.CERRADO_SIN_PEDIDO, None, ids,
                                {"registrada_por": d["registrada_por"], "responsable": d["registrada_por"]},
                                avisos=avisos)

        promesa = PromesaAlternativa.desde_dict(datos["promesa"])
        aceptacion = Aceptacion(acepta=True, registrada_por=d["registrada_por"], fecha=evento.fecha_negocio,
                                medio=d.get("medio") or "", evidencia=d["evidencia"], tramos_aceptados=promesa.tramos)
        intento = int(fila["intento"]) + 1
        canal = Canal(datos["canal"])
        sol = self.crm.construir_solicitud(datos["id_cotizacion"], canal, evento.fecha_negocio, intento,
                                           TipoMensaje.CONFIRMACION_PROMESA, aceptacion)
        ids["intento"] = intento
        self._log(evento, "enviar EV-05", f"{sol.id_solicitud} intento {intento} · tramos "
                  + " + ".join(f"{t.cantidad} el {t.fecha.isoformat()}" for t in promesa.tramos),
                  regla="ADR-003", ids=dict(ids))
        respuesta = self.erp.recibir(sol, run_id=evento.run_id)
        cliente = self.crm.cliente(datos.get("id_cliente") or sol.id_cliente) or {}
        return self._tras_respuesta(evento, respuesta, canal, ids, cliente.get("ejecutivo_cuenta") or "Preventista",
                                    avisos, sol.cantidad_total)
