"""Bitácora persistente: la misma entrada en la tabla `bitacora` y en `logs/bitacora.jsonl`.

La tabla se conserva al reiniciar la base (seed) y el JSONL se escribe en modo agregar (UTF-8, una línea
JSON por entrada). Solo guarda IDs, códigos, reglas y cifras: nada de nombres de contacto, correos,
teléfonos, documentos ni texto libre del cliente.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from sie.bitacora import EntradaBitacora

_COLUMNAS = ("ts", "fecha_negocio", "run_id", "agente", "paso", "regla", "codigo", "resultado", "entrada_json",
             "ids_json", "escalado_a", "motivo", "fecha_limite", "respuesta_humana", "modo", "detalle_json")


class BitacoraPersistente:
    def __init__(self, conn: sqlite3.Connection, ruta_jsonl: Path) -> None:
        self.conn = conn
        self.ruta_jsonl = Path(ruta_jsonl)
        if conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'bitacora'").fetchone() is None:
            from sie.db.seed import ESQUEMA  # base nueva: crea las tablas vacías (CREATE IF NOT EXISTS)

            conn.executescript(ESQUEMA.read_text(encoding="utf-8"))

    def registrar(self, entrada: EntradaBitacora) -> None:
        d = entrada.a_dict()
        valores = (d["ts"], d["fecha_negocio"], d["run_id"], d["agente"], d["paso"], d["regla"], d["codigo"],
                   d["resultado"], json.dumps(d["entrada"], ensure_ascii=False),
                   json.dumps(d["ids"], ensure_ascii=False, default=str), d["escalado_a"], d["motivo"],
                   d["fecha_limite"], d["respuesta_humana"], d["modo"],
                   json.dumps(d["detalle"], ensure_ascii=False, default=str))
        with self.conn:
            self.conn.execute(f"INSERT INTO bitacora ({', '.join(_COLUMNAS)}) "
                              f"VALUES ({', '.join('?' for _ in _COLUMNAS)})", valores)
        self.ruta_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ruta_jsonl, "a", encoding="utf-8") as f:
            f.write(json.dumps(d, ensure_ascii=False, default=str) + "\n")

    def leer(self, run_id: str | None = None, id_solicitud: str | None = None,
             ultimas: int | None = None) -> list[EntradaBitacora]:
        sql, params = "SELECT * FROM bitacora", []
        if run_id:
            sql, params = sql + " WHERE run_id = ?", [run_id]
        entradas = []
        for f in self.conn.execute(sql + " ORDER BY id", params):
            ids = json.loads(f["ids_json"] or "{}")
            if id_solicitud and ids.get("id_solicitud") != id_solicitud:
                continue
            entradas.append(EntradaBitacora.desde_dict({
                "ts": f["ts"], "fecha_negocio": f["fecha_negocio"], "run_id": f["run_id"], "agente": f["agente"],
                "paso": f["paso"], "regla": f["regla"], "codigo": f["codigo"], "resultado": f["resultado"],
                "entrada": json.loads(f["entrada_json"] or "{}"), "ids": ids, "escalado_a": f["escalado_a"],
                "motivo": f["motivo"], "fecha_limite": f["fecha_limite"], "respuesta_humana": f["respuesta_humana"],
                "modo": f["modo"], "detalle": json.loads(f["detalle_json"] or "{}")}))
        return entradas[-ultimas:] if ultimas else entradas
