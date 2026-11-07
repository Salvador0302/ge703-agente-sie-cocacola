"""Fecha de entrega y promesa alternativa (EV-04).

- Fecha de entrega: siguiente día (fecha + 1) dentro de la ventana de entrega de la dirección.
- Promesa alternativa: tramo 1 = ATP disponible desde el CD, con un día más para que el cliente
  confirme; tramo 2 = faltante con la fecha de la próxima reposición del plan (plan_reposicion).
Valor de control (SOL-002 intento 1, 07/10): 380 el 09/10 desde "ALM-001 CD Lima Norte" y 220 el 12/10
desde "Reposición desde ALM-002 (planta) · plan APO (I2)".
"""

from __future__ import annotations

import re
import sqlite3
from datetime import date, timedelta

from sie.contrato import PromesaAlternativa, SolicitudPedido, Tramo
from sie.erp.reglas import Evaluacion

ALMACEN_CD = "ALM-001"
_DIAS = {"lun": 0, "mar": 1, "mié": 2, "mie": 2, "jue": 3, "vie": 4, "sáb": 5, "sab": 5, "dom": 6}


def dias_de_ventana(ventana: str | None) -> set[int]:
    """'Lun-Sáb 08:00-13:00' → {0..5}; 'Lun-Vie ...' → {0..4}; sin ventana → todos los días."""
    m = re.match(r"\s*([A-Za-zÁÉÍÓÚáéíóú]{3})\s*-\s*([A-Za-zÁÉÍÓÚáéíóú]{3})", ventana or "")
    if not m or m.group(1).lower() not in _DIAS or m.group(2).lower() not in _DIAS:
        return set(range(7))
    inicio, fin = _DIAS[m.group(1).lower()], _DIAS[m.group(2).lower()]
    return set(range(inicio, fin + 1)) if inicio <= fin else set(range(inicio, 7)) | set(range(0, fin + 1))


def fecha_entrega(conn: sqlite3.Connection, id_direccion: str, desde: date) -> date:
    fila = conn.execute("SELECT ventana_entrega FROM direcciones WHERE id_direccion = ?", (id_direccion,)).fetchone()
    dias = dias_de_ventana(fila["ventana_entrega"] if fila else None)
    fecha = desde + timedelta(days=1)
    while fecha.weekday() not in dias:
        fecha += timedelta(days=1)
    return fecha


def _origen_cd(conn: sqlite3.Connection) -> str:
    fila = conn.execute("SELECT nombre_almacen FROM almacenes WHERE id_almacen = ?", (ALMACEN_CD,)).fetchone()
    nombre = (fila["nombre_almacen"] if fila else "").replace(" (supuesto)", "")
    return f"{ALMACEN_CD} {nombre}".strip()


def proxima_reposicion(conn: sqlite3.Connection, id_producto: str, desde: date) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT r.*, a.tipo_almacen FROM plan_reposicion r
        LEFT JOIN almacenes a ON a.id_almacen = r.id_almacen_origen
        WHERE r.id_producto = ? AND r.id_almacen_destino = ?
          AND COALESCE(r.fecha_reprogramada, r.fecha_plan_original) >= ?
        ORDER BY COALESCE(r.fecha_reprogramada, r.fecha_plan_original)
        LIMIT 1
        """, (id_producto, ALMACEN_CD, desde.isoformat())).fetchone()


def proponer(conn: sqlite3.Connection, sol: SolicitudPedido, evaluacion: Evaluacion) -> PromesaAlternativa:
    disponible = sum(min(l.cantidad, max(evaluacion.atp_por_linea[l.numero_linea].disponible, 0))
                     for l in sol.lineas)
    faltante = sol.cantidad_total - disponible
    tramos: list[Tramo] = []
    if disponible > 0:
        # Un día para que el cliente confirme la promesa y luego el siguiente día de su ventana.
        tramos.append(Tramo(disponible, fecha_entrega(conn, sol.id_direccion_entrega,
                                                      sol.fecha_envio + timedelta(days=1)), _origen_cd(conn)))
    cortas = [l for l in sol.lineas if l.cantidad > evaluacion.atp_por_linea[l.numero_linea].disponible]
    reposiciones = [proxima_reposicion(conn, l.id_producto, sol.fecha_envio) for l in cortas]
    if faltante > 0 and reposiciones and all(reposiciones):
        fecha = max(date.fromisoformat(r["fecha_reprogramada"] or r["fecha_plan_original"]) for r in reposiciones)
        origen = reposiciones[0]["id_almacen_origen"]
        tipo = (reposiciones[0]["tipo_almacen"] or "").lower()
        tramos.append(Tramo(faltante, fecha, f"Reposición desde {origen} ({tipo}) · plan APO (I2)"))
    return PromesaAlternativa(cantidad_solicitada=sol.cantidad_total, cantidad_atp_confirmada=disponible,
                              tramos=tramos, requiere_aceptacion_cliente=True)
