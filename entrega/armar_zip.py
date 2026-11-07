"""Arma y verifica el paquete del agente para la entrega.

Uso (desde la raíz del proyecto):
    python entrega/armar_zip.py                       → entrega/salida/GE703_PC3_Agente_G2_CocaCola.zip
    python entrega/armar_zip.py --verificar           → además lo extrae en una carpeta temporal, revisa su
                                                        contenido, busca secretos y ejecuta la demo desde ahí
    python entrega/armar_zip.py --incremento PC4      → GE703_PC4_Agente_G2_CocaCola.zip

Usa una lista de permitidos (no de exclusión) y, si hay git, solo archivos versionados: nunca entran `.env`,
bases `*.db`, `logs/`, `.venv/`, `.git/`, `__pycache__/` ni la carpeta de salida.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
NOMBRE = "GE703_{incremento}_Agente_G2_CocaCola.zip"
SALIDA = RAIZ / "entrega" / "salida"
PERMITIDOS = ("README.md", "LICENSE", "requirements.txt", "pyproject.toml", ".env.example", "arquitectura",
              "procesos", "datos", "producto", "pruebas", "fuentes", "agentes", "entrega", "docs/antecedentes")
CARPETAS_EXCLUIDAS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "logs", "salida"}
SUFIJOS_EXCLUIDOS = (".db", ".db-journal", ".sqlite", ".pyc", ".zip", ".log")
NOMBRES_EXCLUIDOS = {".env", "secrets.toml"}
LARGO_MAXIMO = 150
#: Forma de una API key real de Anthropic (el prefijo se arma por partes para no marcarse a sí mismo).
SECRETO = re.compile(("sk-" + "ant-") + r"[A-Za-z0-9_\-]{20,}")
EXTENSIONES_TEXTO = (".py", ".md", ".csv", ".txt", ".json", ".toml", ".sql", ".example", ".html", ".svg")


def _permitido(relativa: str) -> bool:
    partes = relativa.split("/")
    if not any(relativa == p or relativa.startswith(p + "/") for p in PERMITIDOS):
        return False
    if set(partes) & CARPETAS_EXCLUIDAS or partes[-1] in NOMBRES_EXCLUIDOS:
        return False
    return not relativa.endswith(SUFIJOS_EXCLUIDOS)


def _candidatos() -> list[str]:
    """Archivos de git (versionados o nuevos, respetando .gitignore); si no hay git, todos los de la carpeta."""
    try:
        salida = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=RAIZ,
                                capture_output=True, check=True)
        archivos = [a for a in salida.stdout.decode("utf-8").split("\0") if a]
    except (OSError, subprocess.CalledProcessError):
        archivos = [p.relative_to(RAIZ).as_posix() for p in RAIZ.rglob("*") if p.is_file()]
    return sorted(a for a in archivos if (RAIZ / a).is_file() and _permitido(a))


def _carpeta(incremento: str) -> str:
    return NOMBRE.format(incremento=incremento).removesuffix(".zip")


def construir(destino: Path = SALIDA, incremento: str = "PC3") -> Path:
    """Crea el ZIP en `destino` y devuelve su ruta. El contenido va dentro de una carpeta con el mismo nombre."""
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    ruta = destino / NOMBRE.format(incremento=incremento)
    carpeta = _carpeta(incremento)
    with zipfile.ZipFile(ruta, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for relativa in _candidatos():
            z.write(RAIZ / relativa, f"{carpeta}/{relativa}")
    return ruta


def _problemas_de_contenido(z: zipfile.ZipFile) -> list[str]:
    problemas = []
    nombres = z.namelist()
    if not nombres:
        return ["el ZIP está vacío"]
    for requerido in ("README.md", "requirements.txt", ".env.example", "producto/sie/__main__.py",
                      "entrega/GUIA_DESPLIEGUE.md", "agentes/comercial/FICHA.md", "datos/seed/clientes.csv"):
        if not any(n.endswith("/" + requerido) for n in nombres):
            problemas.append(f"falta {requerido}")
    for n in nombres:
        partes = set(n.split("/"))
        if partes & CARPETAS_EXCLUIDAS or partes & NOMBRES_EXCLUIDOS or n.endswith(SUFIJOS_EXCLUIDOS):
            problemas.append(f"no debería estar: {n}")
        if len(n) > LARGO_MAXIMO:
            problemas.append(f"ruta de {len(n)} caracteres (máximo {LARGO_MAXIMO}): {n}")
        if n.endswith(EXTENSIONES_TEXTO) and SECRETO.search(z.read(n).decode("utf-8", "replace")):
            problemas.append(f"posible API key en {n}")
    return problemas


def _entorno_limpio() -> dict[str, str]:
    """Entorno sin la configuración local: como en la PC del docente recién descomprimido el ZIP."""
    quitar = ("AGENT_MODE", "ANTHROPIC_API_KEY", "ANTHROPIC_MODEL", "SIE_DB", "SIE_LOGS", "SIE_LLM_ESFUERZO",
              "PYTHONPATH", "PYTHONIOENCODING", "PYTHONUTF8")
    return {k: v for k, v in os.environ.items() if k not in quitar}


def verificar(ruta_zip: Path, ejecutar_demo: bool = True) -> list[str]:
    """Extrae el ZIP en una carpeta temporal y devuelve la lista de problemas (vacía si está correcto)."""
    with zipfile.ZipFile(ruta_zip) as z:
        problemas = _problemas_de_contenido(z)
        if problemas or not ejecutar_demo:
            return problemas
        with tempfile.TemporaryDirectory(prefix="sie_zip_") as tmp:
            z.extractall(tmp)
            producto = Path(tmp) / z.namelist()[0].split("/")[0] / "producto"
            pruebas = (("diagnostico",), ("demo", "normal"), ("demo", "excepcion", "--acepta"),
                       ("demo", "excepcion", "--rechaza"))
            for argumentos in pruebas:
                r = subprocess.run([sys.executable, "-m", "sie", *argumentos], cwd=producto, env=_entorno_limpio(),
                                   capture_output=True, timeout=300)
                salida = r.stdout.decode("utf-8", "replace")
                if r.returncode != 0:
                    detalle = (salida + r.stderr.decode("utf-8", "replace")).strip().splitlines()[-3:]
                    problemas.append(f"python -m sie {' '.join(argumentos)} terminó con código {r.returncode}: "
                                     + " | ".join(detalle))
                elif argumentos[0] == "demo" and "verificaciones conformes" not in salida:
                    problemas.append(f"python -m sie {' '.join(argumentos)} no mostró el esperado frente a observado")
    return problemas


def main(argv: list[str] | None = None) -> int:
    for flujo in (sys.stdout, sys.stderr):
        flujo.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description="Arma el ZIP de entrega del Agente SIE")
    p.add_argument("--incremento", default="PC3", choices=("PC3", "PC4", "EF"))
    p.add_argument("--destino", type=Path, default=SALIDA)
    p.add_argument("--verificar", action="store_true", help="extrae el ZIP y ejecuta la demo desde la copia")
    args = p.parse_args(argv)
    ruta = construir(args.destino, args.incremento)
    with zipfile.ZipFile(ruta) as z:
        cantidad = len(z.namelist())
    print(f"ZIP creado: {ruta} ({cantidad} archivos, {ruta.stat().st_size / 1_048_576:.1f} MB)")
    if not args.verificar:
        return 0
    problemas = verificar(ruta)
    if problemas:
        print(f"Verificación con {len(problemas)} problema(s):")
        for problema in problemas:
            print(f"  - {problema}")
        return 1
    print("Verificación correcta: contenido permitido, sin secretos, diagnóstico y demos conformes desde la copia extraída.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
