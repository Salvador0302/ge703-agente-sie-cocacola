"""Seed por fecha de corte (ADR-004).

Los CSV del EP (`datos/seed/`) muestran el estado al 11/10/2026. Para que la demo cree SOL-003,
PED-003, SOL-002 y PED-002 sin `DUPLICADO`, la base se carga hasta una fecha de corte:

- Documentos del CRM (campañas, leads, oportunidades, cotizaciones): fecha ≤ corte.
- Transacciones del ERP (solicitudes, pedidos, movimientos, entregas, facturas, pagos): fecha < corte.
- Maestros, activos, órdenes de trabajo y plan de reposición: siempre.
- Estados previos: una oportunidad solo está `Ganada` si su pedido existe; CLI-003 está `No usa` hasta
  su primer pedido por TUALI (PED-003). La adopción de TUALI se normaliza a `Digital`, `Híbrido` o `No usa`.
"""

from __future__ import annotations

import csv
import sqlite3
from datetime import date
from functools import lru_cache

from sie.config import RAIZ

CARPETA_SEED = RAIZ / "datos" / "seed"
ESQUEMA = RAIZ / "producto" / "sie" / "db" / "esquema.sql"
VERSION_ESQUEMA = ("4.0", "2026-11-07", "PC3: tablas del EP, activos, OT, plan de reposición, tramos, escalamientos y bitácora")

#: (tabla, columna de fecha, regla). "siempre" = maestro; "<=" = documento CRM; "<" = transacción ERP.
#: Las tablas de detalle siguen a su cabecera. El orden respeta las claves foráneas.
PLAN_DE_CARGA: tuple[tuple[str, str | None, str], ...] = (
    ("almacenes", None, "siempre"),
    ("productos", None, "siempre"),
    ("listas_precios", None, "siempre"),
    ("reglas_descuento", None, "siempre"),
    ("clientes", None, "siempre"),
    ("contactos", None, "siempre"),
    ("direcciones", None, "siempre"),
    ("activos", None, "siempre"),
    ("ordenes_trabajo", None, "siempre"),
    ("plan_reposicion", None, "siempre"),
    ("campanas", "fecha_inicio", "<="),
    ("leads", "fecha_captura", "<="),
    ("oportunidades", "fecha_apertura", "<="),
    ("cotizaciones_cab", "fecha_emision", "<="),
    ("cotizaciones_det", "id_cotizacion", "cabecera:cotizaciones_cab"),
    ("pedidos_cab", "fecha_confirmacion", "<"),
    ("pedidos_det", "id_pedido", "cabecera:pedidos_cab"),
    ("solicitudes_pedido", "fecha_envio", "<"),
    ("entregas_cab", "fecha_entrega", "<"),
    ("entregas_det", "id_entrega", "cabecera:entregas_cab"),
    ("facturas_cab", "fecha_emision", "<"),
    ("facturas_det", "id_factura", "cabecera:facturas_cab"),
    ("pagos", "fecha_pago", "<"),
    ("movimientos_inventario", "fecha_movimiento", "<"),
)

ADOPCION_VALIDA = ("Digital", "Híbrido", "No usa")

#: Estados de la demo antes de que exista el pedido que los cambia: (cliente, columna, valor previo, pedido).
ESTADOS_PREVIOS_CLIENTE = (("CLI-003", "estado_adopcion_tuali", "No usa", "PED-003"),)


@lru_cache(maxsize=None)
def _leer_csv(tabla: str) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    with open(CARPETA_SEED / f"{tabla}.csv", encoding="utf-8-sig", newline="") as f:
        lector = csv.DictReader(f)
        filas = tuple(lector)
        return tuple(lector.fieldnames or ()), filas


def _normalizar_adopcion(valor: str) -> str:
    for opcion in ADOPCION_VALIDA:
        if valor.startswith(opcion):
            return opcion
    return valor


def _filas_hasta(tabla: str, columna: str | None, regla: str, fecha: date, incluidas: dict[str, set[str]]):
    _, filas = _leer_csv(tabla)
    limite = fecha.isoformat()
    for fila in filas:
        if regla == "siempre":
            yield fila
        elif regla == "<=" and fila[columna] <= limite:
            yield fila
        elif regla == "<" and fila[columna] < limite:
            yield fila
        elif regla.startswith("cabecera:") and fila[columna] in incluidas[regla.split(":", 1)[1]]:
            yield fila


def _cargar(conn: sqlite3.Connection, fecha: date) -> int:
    """INSERT OR IGNORE de todo lo que existía antes de `fecha`. Devuelve las filas agregadas."""
    agregadas = 0
    incluidas: dict[str, set[str]] = {}
    for tabla, columna, regla in PLAN_DE_CARGA:
        columnas, _ = _leer_csv(tabla)
        clave = columnas[0]
        filas = list(_filas_hasta(tabla, columna, regla, fecha, incluidas))
        incluidas[tabla] = {f[clave] for f in filas}
        if tabla == "clientes":
            filas = [{**f, "estado_adopcion_tuali": _normalizar_adopcion(f["estado_adopcion_tuali"])} for f in filas]
        sql = (f"INSERT OR IGNORE INTO {tabla} ({', '.join(columnas)}) "
               f"VALUES ({', '.join('?' for _ in columnas)})")
        cursor = conn.executemany(sql, ([f[c] if f[c] != "" else None for c in columnas] for f in filas))
        agregadas += max(cursor.rowcount, 0)
    return agregadas


def _ajustar_estados(conn: sqlite3.Connection) -> None:
    """Restaura los estados previos de la demo según los pedidos que existen en la base."""
    _, oportunidades = _leer_csv("oportunidades")
    for opp in oportunidades:
        if opp["etapa"] != "Ganada":
            continue
        tiene_pedido = conn.execute(
            "SELECT 1 FROM pedidos_cab p JOIN cotizaciones_cab c ON c.id_cotizacion = p.id_cotizacion "
            "WHERE c.id_oportunidad = ?", (opp["id_oportunidad"],)).fetchone()
        if tiene_pedido:
            conn.execute("UPDATE oportunidades SET etapa = 'Ganada', probabilidad = ?, fecha_cierre_real = ? "
                         "WHERE id_oportunidad = ?",
                         (opp["probabilidad"], opp["fecha_cierre_real"] or None, opp["id_oportunidad"]))
        else:
            conn.execute("UPDATE oportunidades SET etapa = 'Propuesta', fecha_cierre_real = NULL "
                         "WHERE id_oportunidad = ?", (opp["id_oportunidad"],))
    _, clientes = _leer_csv("clientes")
    original = {c["id_cliente"]: c for c in clientes}
    for id_cliente, columna, previo, id_pedido in ESTADOS_PREVIOS_CLIENTE:
        existe = conn.execute("SELECT 1 FROM pedidos_cab WHERE id_pedido = ?", (id_pedido,)).fetchone()
        valor = _normalizar_adopcion(original[id_cliente][columna]) if existe else previo
        conn.execute(f"UPDATE clientes SET {columna} = ? WHERE id_cliente = ?", (valor, id_cliente))


def crear_base(conn: sqlite3.Connection, corte: date) -> None:
    """Crea (o recrea) todas las tablas del esquema y carga el estado del mundo antes de `corte`.

    No borra la tabla `bitacora`: la crea si no existe y conserva su historial.
    """
    conn.execute("PRAGMA foreign_keys = OFF")
    tablas = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' AND name <> 'bitacora'")]
    for tabla in tablas:
        conn.execute(f"DROP TABLE IF EXISTS {tabla}")
    conn.executescript(ESQUEMA.read_text(encoding="utf-8"))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("INSERT OR REPLACE INTO esquema_version (version, fecha, descripcion) VALUES (?, ?, ?)",
                 VERSION_ESQUEMA)
    _cargar(conn, corte)
    _ajustar_estados(conn)
    conn.commit()
    errores = conn.execute("PRAGMA foreign_key_check").fetchall()
    if errores:
        raise RuntimeError(f"Seed inconsistente al corte {corte}: {len(errores)} filas con clave foránea rota, "
                           f"por ejemplo {tuple(errores[0])}")


def avanzar(conn: sqlite3.Connection, hasta: date) -> int:
    """Agrega las filas del seed con fecha anterior a `hasta` que aún no existen (INSERT OR IGNORE).

    Nunca sobrescribe lo que creó el ERP simulado (por ejemplo, PED-002). Devuelve filas agregadas.
    """
    agregadas = _cargar(conn, hasta)
    _ajustar_estados(conn)
    conn.commit()
    return agregadas
