"""Arma y verifica el paquete del agente · BLOQUE D (David Urbano). Interfaz definida por el bloque A.

Uso previsto (desde la raíz del repo):
    python entrega/armar_zip.py --incremento PC3            → entrega/salida/GE703_PC3_Agente_G2_CocaCola.zip
    python entrega/armar_zip.py --incremento PC3 --verificar → además lo extrae en una carpeta temporal,
                                                               busca secretos y ejecuta la demo

Reglas: lista de permitidos (no de exclusión); nunca incluir `.env`, `*.db`, `logs/`, `.venv/`, `.git/`,
`__pycache__/` ni la carpeta de salida. Detalle en `arquitectura/bloques/BLOQUE_D.md`.
"""

from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
NOMBRE = "GE703_{incremento}_Agente_G2_CocaCola.zip"
_PENDIENTE = "Bloque D (David): armado del ZIP. Ver arquitectura/bloques/BLOQUE_D.md."


def construir(destino: Path, incremento: str = "PC3") -> Path:
    """Crea el ZIP en `destino` y devuelve su ruta."""
    raise NotImplementedError(_PENDIENTE)


def verificar(ruta_zip: Path, ejecutar_demo: bool = True) -> list[str]:
    """Extrae el ZIP en una carpeta temporal y devuelve la lista de problemas (vacía si está correcto)."""
    raise NotImplementedError(_PENDIENTE)


def main() -> int:
    raise NotImplementedError(_PENDIENTE)


if __name__ == "__main__":
    raise SystemExit(main())
