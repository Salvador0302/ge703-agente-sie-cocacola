"""Línea de comandos del Agente SIE. Ejecutar desde la carpeta `producto/`:

    python -m sie demo normal            caso normal (Don Lucho, TUALI)
    python -m sie demo excepcion         excepción (Los Olivos, ATP 380 de 600) con decisión humana
    python -m sie pedir "texto" --fecha 2026-10-02 --canal TUALI [--corte 2026-10-02]
    python -m sie decidir --escalamiento ID --acepta|--rechaza --fecha 2026-10-08
    python -m sie bitacora [--run ID] [--solicitud SOL-002] [--ultimas 20]
    python -m sie reset --corte 2026-10-02
    python -m sie agentes                agentes previstos y su estado
    python -m sie diagnostico            verifica el entorno y propone cómo corregirlo
    python -m sie ui                     abre la interfaz Streamlit

Códigos de salida: 0 correcto · 1 resultado no conforme o error · 2 parte pendiente de implementar ·
3 configuración inválida.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import webbrowser
from datetime import date

from sie import __version__
from sie.agentes.base import EstadoResultado, Evento, ResultadoAgente, nuevo_run_id
from sie.bitacora import BitacoraMemoria, EntradaBitacora
from sie.config import RAIZ, Config, ErrorConfiguracion, cargar
from sie.db.conexion import conectar
from sie.demo import CASOS, verificar

SALIDA_OK, SALIDA_FALLA, SALIDA_PENDIENTE, SALIDA_CONFIG = 0, 1, 2, 3


# --------------------------------------------------------------------------- consola

def _consola_utf8() -> None:
    """Windows usa cp1252 al redirigir la salida; sin esto, '→' o 'á' rompen la ejecución."""
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def _fecha(texto: str) -> date:
    try:
        return date.fromisoformat(texto)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"fecha inválida {texto!r}; use AAAA-MM-DD") from e


def _dmy(d: date | None) -> str:
    return d.strftime("%d/%m/%Y") if d else "—"


def _titulo(texto: str) -> None:
    print(f"\n── {texto}")


def _imprimir_traza(entradas: list[EntradaBitacora]) -> None:
    print("Traza (bitácora):")
    for e in entradas:
        regla = f" [{e.regla}]" if e.regla and e.regla not in e.paso else ""
        codigo = f" → {e.codigo}" if e.codigo and e.codigo not in e.resultado else ""
        print(f"  {e.agente:<12} {e.paso:<26} {e.resultado}{regla}{codigo}")
        if e.escalado_a:
            print(f"  {'':<12} {'':<26} escala a {e.escalado_a} · límite {_dmy(e.fecha_limite)} · {e.motivo or ''}")


def _imprimir_resultado(r: ResultadoAgente) -> None:
    ids = " · ".join(f"{k}={v}" for k, v in r.ids.items() if v not in (None, ""))
    print(f"Resultado: {r.estado} · {r.codigo or 'sin código'}" + (f" · {ids}" if ids else ""))
    if r.mensaje:
        print(f"Explicación: {r.mensaje}")
    if r.escalamiento:
        esc = r.escalamiento
        print(f"Escalamiento {esc.id_escalamiento}: {esc.responsable} · {esc.estado} · límite {_dmy(esc.fecha_limite)}")
        print(f"  Causa: {esc.causa}")


def _traza_del_run(sistema, run_id: str) -> list[EntradaBitacora]:
    return sistema.bitacora.leer(run_id=run_id)


# --------------------------------------------------------------------------- comandos

def _sistema(config: Config, conn: sqlite3.Connection):
    from sie.sistema import construir_sistema

    return construir_sistema(config, conn)


def cmd_demo(args: argparse.Namespace, config: Config) -> int:
    from sie.db import seed
    from sie.sistema import preparar_base

    caso = CASOS[args.caso]
    _titulo(f"{caso.titulo} · {_dmy(caso.fecha)} · modo {config.modo}")
    conn = preparar_base(config, caso.corte)
    sistema = _sistema(config, conn)
    run_id = nuevo_run_id()
    print(f'Entrada ({caso.canal}): "{caso.texto}"')
    r1 = sistema.orquestador.despachar(Evento(
        tipo="pedido", fecha_negocio=caso.fecha, datos={"texto": caso.texto, "canal": caso.canal},
        origen="cli-demo", run_id=run_id))
    _imprimir_traza(_traza_del_run(sistema, run_id))
    _imprimir_resultado(r1)
    resultados = [r1]
    acepta = True
    if r1.estado == EstadoResultado.ESPERA_HUMANO and r1.escalamiento:
        acepta = _decision_humana(args, r1)
        if acepta is None:
            return SALIDA_FALLA
        _titulo(f"Decisión humana · {caso.decision.get('registrada_por')} · {_dmy(caso.fecha_decision)}")
        seed.avanzar(conn, caso.fecha_decision)
        antes = len(_traza_del_run(sistema, run_id))
        r2 = sistema.orquestador.despachar(Evento(
            tipo="decision_humana", fecha_negocio=caso.fecha_decision, origen="cli-demo", run_id=run_id,
            datos={"id_escalamiento": r1.escalamiento.id_escalamiento, "acepta": acepta, **caso.decision}))
        _imprimir_traza(_traza_del_run(sistema, run_id)[antes:])
        _imprimir_resultado(r2)
        resultados.append(r2)
    return _cerrar_demo(caso.clave, resultados, acepta, run_id, config)


def _decision_humana(args: argparse.Namespace, r: ResultadoAgente) -> bool | None:
    if args.acepta:
        return True
    if args.rechaza:
        return False
    if not sys.stdin.isatty():
        print("Se requiere la decisión del responsable: agregue --acepta o --rechaza.", file=sys.stderr)
        return None
    esc = r.escalamiento
    while True:
        respuesta = input(f"\n{esc.responsable}: ¿el cliente acepta la promesa alternativa? [s/n]: ").strip().lower()
        if respuesta in ("s", "si", "sí"):
            return True
        if respuesta in ("n", "no"):
            return False


def _cerrar_demo(clave: str, resultados: list[ResultadoAgente], acepta: bool, run_id: str, config: Config) -> int:
    filas = verificar(clave, resultados, acepta)
    _titulo("Esperado frente a observado")
    ancho = max(len(f.nombre) for f in filas)
    for f in filas:
        estado = "Conforme" if f.conforme else "NO CONFORME"
        print(f"  {f.nombre:<{ancho}}  esperado: {f.esperado:<38} observado: {f.observado:<38} {estado}")
    conformes = sum(f.conforme for f in filas)
    print(f"\n{conformes} de {len(filas)} verificaciones conformes · run {run_id}")
    print(f"Bitácora: {config.ruta_bitacora}  ·  python -m sie bitacora --run {run_id}")
    return SALIDA_OK if conformes == len(filas) else SALIDA_FALLA


def cmd_pedir(args: argparse.Namespace, config: Config) -> int:
    from sie.sistema import preparar_base

    if args.corte:
        conn = preparar_base(config, args.corte)
    else:
        if not config.ruta_db.exists():
            print("No hay base de datos. Agregue --corte AAAA-MM-DD o ejecute 'python -m sie reset --corte ...'.",
                  file=sys.stderr)
            return SALIDA_FALLA
        conn = conectar(config.ruta_db)
    sistema = _sistema(config, conn)
    run_id = nuevo_run_id()
    r = sistema.orquestador.despachar(Evento(
        tipo="pedido", fecha_negocio=args.fecha, datos={"texto": args.texto, "canal": args.canal},
        origen="cli", run_id=run_id))
    _imprimir_traza(_traza_del_run(sistema, run_id))
    _imprimir_resultado(r)
    if r.estado == EstadoResultado.ESPERA_HUMANO and r.escalamiento:
        print(f"\nPara registrar la decisión: python -m sie decidir --escalamiento {r.escalamiento.id_escalamiento} "
              f"--acepta --fecha AAAA-MM-DD --evidencia REFERENCIA")
    return SALIDA_OK if r.estado != EstadoResultado.ERROR else SALIDA_FALLA


def cmd_decidir(args: argparse.Namespace, config: Config) -> int:
    from sie.db import seed

    if not config.ruta_db.exists():
        print("No hay base de datos con escalamientos pendientes.", file=sys.stderr)
        return SALIDA_FALLA
    conn = conectar(config.ruta_db)
    seed.avanzar(conn, args.fecha)
    sistema = _sistema(config, conn)
    run_id = nuevo_run_id()
    r = sistema.orquestador.despachar(Evento(
        tipo="decision_humana", fecha_negocio=args.fecha, origen="cli", run_id=run_id,
        datos={"id_escalamiento": args.escalamiento, "acepta": args.acepta, "registrada_por": args.registrada_por,
               "medio": args.medio, "evidencia": args.evidencia}))
    _imprimir_traza(_traza_del_run(sistema, run_id))
    _imprimir_resultado(r)
    return SALIDA_OK if r.estado != EstadoResultado.ERROR else SALIDA_FALLA


def cmd_reset(args: argparse.Namespace, config: Config) -> int:
    from sie.sistema import preparar_base

    preparar_base(config, args.corte).close()
    print(f"Base reiniciada al corte {_dmy(args.corte)}: {config.ruta_db}")
    return SALIDA_OK


def cmd_bitacora(args: argparse.Namespace, config: Config) -> int:
    from sie.bitacora.persistente import BitacoraPersistente

    conn = conectar(config.ruta_db)
    entradas = BitacoraPersistente(conn, config.ruta_bitacora).leer(
        run_id=args.run, id_solicitud=args.solicitud, ultimas=args.ultimas)
    if not entradas:
        print("Sin entradas para ese filtro.")
        return SALIDA_OK
    actual = None
    for e in entradas:
        if e.run_id != actual:
            actual = e.run_id
            print(f"\nrun {actual} · fecha de negocio {_dmy(e.fecha_negocio)}")
        print(f"  {e.ts}  {e.agente:<12} {e.paso:<24} {e.resultado}"
              + (f" [{e.regla}]" if e.regla else "") + (f" → {e.codigo}" if e.codigo else ""))
    return SALIDA_OK


def _estado_bloques(config: Config) -> dict[str, str]:
    """Prueba el caso normal en una base temporal en memoria para saber qué bloques ya funcionan."""
    from sie.db import seed
    from sie.sistema import construir_sistema

    estado = {}
    conn = conectar()
    try:
        seed.crear_base(conn, CASOS["normal"].corte)
        estado["B"] = "listo"
    except NotImplementedError:
        return {"B": "pendiente", "C": "pendiente (requiere B)"}
    except Exception as e:  # noqa: BLE001 - el diagnóstico informa cualquier fallo en lugar de detenerse
        return {"B": f"error {type(e).__name__}: {e}", "C": "no evaluado"}
    try:
        cfg = Config(modo="reglas", ruta_db=config.ruta_db, carpeta_logs=config.carpeta_logs)
        sistema = construir_sistema(cfg, conn, bitacora=BitacoraMemoria())
        caso = CASOS["normal"]
        r = sistema.orquestador.despachar(Evento(tipo="pedido", fecha_negocio=caso.fecha,
                                                 datos={"texto": caso.texto, "canal": caso.canal}))
        estado["C"] = "listo" if r.codigo == "OK-ACEPTADO" else f"responde {r.codigo}"
    except NotImplementedError as e:
        estado["C"] = f"pendiente ({e})"
    except Exception as e:  # noqa: BLE001
        estado["C"] = f"error {type(e).__name__}: {e}"
    return estado


def cmd_agentes(args: argparse.Namespace, config: Config) -> int:
    from sie.orquestador import AGENTES_PREVISTOS, RUTAS

    bloques = _estado_bloques(config)
    print(f"Agente SIE {__version__} · modo {config.modo}")
    for a in AGENTES_PREVISTOS:
        tipos = ", ".join(sorted(t for t, n in RUTAS.items() if n == a.nombre))
        if a.nombre == "comercial":
            estado = "implementado" if bloques.get("C") == "listo" else "en construcción"
        else:
            estado = "no implementado aún"
        print(f"  {a.nombre:<20} {estado:<20} {a.incremento:<12} eventos: {tipos}")
        print(f"  {'':<20} {a.proceso}" + (f" · {a.nota}" if a.nota else ""))
    return SALIDA_OK


def cmd_diagnostico(args: argparse.Namespace, config: Config) -> int:
    filas: list[tuple[bool, str, str]] = []

    def chequeo(ok: bool, nombre: str, detalle: str) -> None:
        filas.append((ok, nombre, detalle))

    chequeo(sys.version_info >= (3, 11), "Python 3.11 o superior",
            f"{sys.version.split()[0]} en {sys.executable}")
    seed_dir = RAIZ / "datos" / "seed"
    n_csv = len(list(seed_dir.glob("*.csv"))) if seed_dir.exists() else 0
    chequeo(n_csv > 0, "Datos de prueba (datos/seed)", f"{n_csv} archivos CSV")
    for carpeta in (config.ruta_db.parent, config.carpeta_logs):
        try:
            carpeta.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=carpeta):
                pass
            chequeo(True, f"Escritura en {carpeta.name}/", str(carpeta))
        except OSError as e:
            chequeo(False, f"Escritura en {carpeta.name}/", f"{e}; copie la carpeta a una ruta con permisos")
    chequeo(True, "SQLite", sqlite3.sqlite_version)
    bloques = _estado_bloques(config)
    chequeo(bloques.get("B") == "listo", "Datos y ERP simulado (bloque B)", bloques.get("B", "—"))
    chequeo(bloques.get("C") == "listo", "Caso normal de punta a punta (bloque C)", bloques.get("C", "—"))
    opcionales = {m: importlib.util.find_spec(m) is not None for m in ("streamlit", "anthropic", "pytest")}
    for modulo, ok in opcionales.items():
        filas.append((True, f"Opcional: {modulo}", "instalado" if ok else "no instalado (pip install -r requirements.txt)"))
    filas.append((True, "Modo del agente", f"{config.modo} (pedido: {config.modo_solicitado}); "
                                           f"API key {'configurada' if config.tiene_api_key else 'no configurada'}"))
    for aviso in config.avisos:
        filas.append((True, "Aviso", aviso))
    print(f"Diagnóstico del Agente SIE {__version__} · raíz {RAIZ}")
    for ok, nombre, detalle in filas:
        print(f"  [{'OK' if ok else 'FALLA'}] {nombre}: {detalle}")
    fallas = [f for f in filas if not f[0]]
    print("\nTodo listo para la demo." if not fallas else f"\n{len(fallas)} punto(s) por corregir.")
    return SALIDA_OK if not fallas else SALIDA_FALLA


def cmd_ui(args: argparse.Namespace, config: Config) -> int:
    if importlib.util.find_spec("streamlit") is None:
        print("Falta Streamlit: pip install -r requirements.txt (la CLI funciona sin él).", file=sys.stderr)
        return SALIDA_FALLA
    app = RAIZ / "producto" / "sie" / "ui" / "app.py"
    url = f"http://localhost:{args.puerto}"
    entorno = dict(os.environ)
    entorno["PYTHONPATH"] = os.pathsep.join(p for p in (str(RAIZ / "producto"), entorno.get("PYTHONPATH")) if p)
    comando = [sys.executable, "-m", "streamlit", "run", str(app), "--server.headless", "true",
               "--server.port", str(args.puerto), "--browser.gatherUsageStats", "false"]
    print(f"Abriendo la interfaz en {url} (Ctrl+C para detener).")
    if not args.sin_navegador:
        threading.Timer(3.0, webbrowser.open, args=(url,)).start()
    try:
        return subprocess.call(comando, env=entorno)
    except KeyboardInterrupt:
        return SALIDA_OK


# --------------------------------------------------------------------------- parser

def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m sie", description="Agente SIE · G2 · Coca-Cola / ACL (datos sintéticos)")
    p.add_argument("--version", action="version", version=f"Agente SIE {__version__}")
    sub = p.add_subparsers(dest="comando", required=True, metavar="comando")

    def con_modo(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--modo", choices=("reglas", "llm"), help="sobrescribe AGENT_MODE")

    d = sub.add_parser("demo", help="ejecuta un caso de la demo desde una base reiniciada")
    d.add_argument("caso", choices=sorted(CASOS))
    decision = d.add_mutually_exclusive_group()
    decision.add_argument("--acepta", action="store_true", help="el cliente acepta la promesa (sin preguntar)")
    decision.add_argument("--rechaza", action="store_true", help="el cliente rechaza la promesa (sin preguntar)")
    con_modo(d)
    d.set_defaults(funcion=cmd_demo)

    q = sub.add_parser("pedir", help="envía una solicitud de pedido en texto libre")
    q.add_argument("texto")
    q.add_argument("--fecha", type=_fecha, required=True, help="fecha de negocio AAAA-MM-DD")
    q.add_argument("--canal", choices=("TUALI", "Preventa", "Teléfono"), required=True)
    q.add_argument("--corte", type=_fecha, help="reinicia la base a este corte antes de enviar")
    con_modo(q)
    q.set_defaults(funcion=cmd_pedir)

    k = sub.add_parser("decidir", help="registra la decisión humana de un escalamiento pendiente")
    k.add_argument("--escalamiento", required=True)
    grupo = k.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--acepta", dest="acepta", action="store_true")
    grupo.add_argument("--rechaza", dest="acepta", action="store_false")
    k.add_argument("--fecha", type=_fecha, required=True)
    k.add_argument("--registrada-por", dest="registrada_por", default="Preventista 2")
    k.add_argument("--medio", default="Llamada telefónica")
    k.add_argument("--evidencia", required=True, help="referencia de la evidencia de aceptación")
    con_modo(k)
    k.set_defaults(funcion=cmd_decidir)

    b = sub.add_parser("bitacora", help="muestra la bitácora")
    b.add_argument("--run")
    b.add_argument("--solicitud")
    b.add_argument("--ultimas", type=int)
    b.set_defaults(funcion=cmd_bitacora)

    r = sub.add_parser("reset", help="reinicia la base al estado de un corte")
    r.add_argument("--corte", type=_fecha, required=True)
    r.set_defaults(funcion=cmd_reset)

    a = sub.add_parser("agentes", help="agentes previstos y su estado")
    a.set_defaults(funcion=cmd_agentes)

    g = sub.add_parser("diagnostico", help="verifica el entorno y los bloques")
    g.set_defaults(funcion=cmd_diagnostico)

    u = sub.add_parser("ui", help="abre la interfaz Streamlit")
    u.add_argument("--puerto", type=int, default=8501)
    u.add_argument("--sin-navegador", action="store_true")
    u.set_defaults(funcion=cmd_ui)
    return p


def main(argv: list[str] | None = None) -> int:
    _consola_utf8()
    args = _parser().parse_args(argv)
    try:
        config = cargar(modo=getattr(args, "modo", None))
    except ErrorConfiguracion as e:
        print(f"Configuración inválida: {e}", file=sys.stderr)
        return SALIDA_CONFIG
    for aviso in config.avisos:
        print(f"Aviso: {aviso}", file=sys.stderr)
    try:
        return args.funcion(args, config)
    except NotImplementedError as e:
        sys.stdout.flush()
        print(f"\nPendiente de implementar en esta rama: {e}\n"
              "Ejecute 'python -m sie diagnostico' para ver qué falta.", file=sys.stderr)
        return SALIDA_PENDIENTE
    except sqlite3.OperationalError as e:
        sys.stdout.flush()
        print(f"\nError de base de datos: {e}\nSi la interfaz está abierta, ciérrela y reintente; "
              "si persiste, borre datos/sie.db y ejecute de nuevo (se regenera desde el seed).", file=sys.stderr)
        return SALIDA_FALLA
