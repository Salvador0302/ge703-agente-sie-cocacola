"""Configuración del Agente SIE.

Orden de precedencia: variables de entorno del proceso > archivo `.env` en la raíz del repo >
valores por defecto. El lector de `.env` usa solo la biblioteca estándar (sin python-dotenv).
La API key nunca se imprime ni entra en `repr()`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

#: Raíz del repositorio o del ZIP extraído (producto/sie/config.py → parents[2]).
RAIZ = Path(__file__).resolve().parents[2]

MODOS = ("reglas", "llm")
ESFUERZOS = ("low", "medium", "high", "xhigh", "max")
MODELO_POR_DEFECTO = "claude-opus-5-5"


class ErrorConfiguracion(ValueError):
    """Valor de configuración inválido; el mensaje dice cómo corregirlo."""


@dataclass(frozen=True)
class Config:
    modo: str = "reglas"
    modo_solicitado: str = "reglas"
    anthropic_api_key: str | None = field(default=None, repr=False)
    modelo: str = MODELO_POR_DEFECTO
    esfuerzo: str = "low"
    ruta_db: Path = RAIZ / "datos" / "sie.db"
    carpeta_logs: Path = RAIZ / "logs"
    avisos: tuple[str, ...] = ()

    @property
    def ruta_bitacora(self) -> Path:
        return self.carpeta_logs / "bitacora.jsonl"

    @property
    def tiene_api_key(self) -> bool:
        return bool(self.anthropic_api_key)


def leer_env(ruta: Path) -> dict[str, str]:
    """Lee un archivo `.env` simple: líneas `CLAVE=valor`, comentarios con `#`, comillas opcionales."""
    valores: dict[str, str] = {}
    if not ruta.is_file():
        return valores
    for numero, linea in enumerate(ruta.read_text(encoding="utf-8-sig").splitlines(), 1):
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        if linea.startswith("export "):
            linea = linea[len("export "):]
        if "=" not in linea:
            raise ErrorConfiguracion(f"{ruta.name}, línea {numero}: falta '=' (formato CLAVE=valor).")
        clave, valor = linea.split("=", 1)
        valor = valor.strip()
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
            valor = valor[1:-1]
        elif " #" in valor:
            valor = valor.split(" #", 1)[0].rstrip()
        valores[clave.strip()] = valor
    return valores


def cargar(entorno: Mapping[str, str] | None = None, ruta_env: Path | None = None,
           modo: str | None = None) -> Config:
    """Construye la configuración efectiva.

    `modo` (por ejemplo, desde `--modo` en la CLI) tiene prioridad sobre `AGENT_MODE`.
    Si se pide `llm` sin API key, el modo efectivo es `reglas` y se registra un aviso.
    """
    archivo = leer_env(ruta_env if ruta_env is not None else RAIZ / ".env")
    proceso = dict(os.environ if entorno is None else entorno)

    def valor(clave: str, defecto: str | None = None) -> str | None:
        v = proceso.get(clave)
        if v in (None, ""):
            v = archivo.get(clave)
        return defecto if v in (None, "") else v

    solicitado = (modo or valor("AGENT_MODE", "reglas")).strip().lower()
    if solicitado not in MODOS:
        raise ErrorConfiguracion(f"AGENT_MODE={solicitado!r} no es válido. Use 'reglas' o 'llm'.")
    esfuerzo = valor("SIE_LLM_ESFUERZO", "low").strip().lower()
    if esfuerzo not in ESFUERZOS:
        raise ErrorConfiguracion(f"SIE_LLM_ESFUERZO={esfuerzo!r} no es válido. Use uno de {', '.join(ESFUERZOS)}.")

    clave_api = valor("ANTHROPIC_API_KEY")
    avisos: list[str] = []
    efectivo = solicitado
    if solicitado == "llm" and not clave_api:
        efectivo = "reglas"
        avisos.append("AGENT_MODE=llm sin ANTHROPIC_API_KEY: se usa el modo reglas.")

    def ruta(clave: str, defecto: Path) -> Path:
        texto = valor(clave)
        if not texto:
            return defecto
        p = Path(texto)
        return p if p.is_absolute() else RAIZ / p

    return Config(
        modo=efectivo,
        modo_solicitado=solicitado,
        anthropic_api_key=clave_api,
        modelo=valor("ANTHROPIC_MODEL", MODELO_POR_DEFECTO),
        esfuerzo=esfuerzo,
        ruta_db=ruta("SIE_DB", RAIZ / "datos" / "sie.db"),
        carpeta_logs=ruta("SIE_LOGS", RAIZ / "logs"),
        avisos=tuple(avisos),
    )
