"""Bloque A · CLI: UTF-8 en Windows, códigos de salida, flujo de la decisión humana y esperado/observado.

El flujo de la demo se prueba con un sistema falso, para no depender de los bloques B y C.
"""

import os
import subprocess
import sys
from datetime import date

import pytest

from apoyo import RAIZ
from sie import cli
from sie.agentes.base import Escalamiento, EstadoResultado, ResultadoAgente
from sie.bitacora import BitacoraMemoria, EntradaBitacora


def ejecutar(*args, **entorno_extra):
    entorno = {k: v for k, v in os.environ.items() if not k.startswith(("PYTHONIOENCODING", "AGENT_MODE"))}
    entorno.pop("PYTHONUTF8", None)
    entorno.update(entorno_extra)
    return subprocess.run([sys.executable, "-m", "sie", *args], cwd=RAIZ / "producto", env=entorno,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)


def test_salida_redirigida_en_utf8():
    """El validador del EP fallaba con cp1252 al redirigir (incidencia I-06); la CLI no."""
    r = ejecutar("agentes")
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    salida = r.stdout.decode("utf-8")  # falla si la salida no es UTF-8
    assert "conciliación" in salida and "finanzas_operativas" in salida and "ceo" in salida


def test_version_y_configuracion_invalida():
    assert ejecutar("--version").returncode == 0
    r = ejecutar("agentes", AGENT_MODE="magia")
    assert r.returncode == cli.SALIDA_CONFIG
    assert "AGENT_MODE" in r.stderr.decode("utf-8")


def test_diagnostico_no_se_cae():
    r = ejecutar("diagnostico")
    assert r.returncode in (0, 1)
    assert "Diagnóstico del Agente SIE" in r.stdout.decode("utf-8")


def test_parte_pendiente_devuelve_codigo_2(monkeypatch, capsys):
    def pendiente(*_a, **_k):
        raise NotImplementedError("Bloque B: seed por fecha de corte.")

    monkeypatch.setattr("sie.sistema.preparar_base", pendiente)
    assert cli.main(["demo", "normal"]) == cli.SALIDA_PENDIENTE
    assert "Bloque B" in capsys.readouterr().err


class OrquestadorFalso:
    def __init__(self, bitacora, resultados):
        self.bitacora = bitacora
        self.resultados = list(resultados)
        self.eventos = []

    def despachar(self, evento):
        self.eventos.append(evento)
        self.bitacora.registrar(EntradaBitacora(agente="comercial", paso=evento.tipo, resultado="ok",
                                                run_id=evento.run_id, fecha_negocio=evento.fecha_negocio))
        r = self.resultados.pop(0)
        r.run_id = evento.run_id
        return r


def resultado_intento1():
    return ResultadoAgente(
        agente="comercial", estado=EstadoResultado.ESPERA_HUMANO, codigo="ATP-PARCIAL", mensaje="380 de 600",
        ids={"id_solicitud": "SOL-002", "intento": 1, "id_cotizacion": "COT-002-V02", "id_ot": "OT-2026-0107"},
        escalamiento=Escalamiento("ESC-SOL-002-1", "SOL-002 intento 1", "ATP 380 de 600 (C5)", "Preventista 2",
                                  date(2026, 10, 8)),
        detalle={"promesa": {"tramos": [{"cantidad": 380, "fecha": "2026-10-09"},
                                        {"cantidad": 220, "fecha": "2026-10-12"}]}})


@pytest.fixture
def sistema_falso(monkeypatch, tmp_path):
    estado = {}

    def preparar(config, corte, ruta=None):
        estado["corte"] = corte
        return "conexion-falsa"

    def construir(config, conn, bitacora=None, cliente_llm=None):
        bit = BitacoraMemoria()
        estado["orq"] = OrquestadorFalso(bit, estado["resultados"])
        return type("S", (), {"orquestador": estado["orq"], "bitacora": bit})()

    monkeypatch.setattr("sie.sistema.preparar_base", preparar)
    monkeypatch.setattr("sie.sistema.construir_sistema", construir)
    monkeypatch.setattr("sie.db.seed.avanzar", lambda conn, hasta: estado.setdefault("avances", []).append(hasta))
    monkeypatch.setenv("SIE_LOGS", str(tmp_path))
    return estado


def test_demo_excepcion_con_aceptacion(sistema_falso, capsys):
    sistema_falso["resultados"] = [resultado_intento1(), ResultadoAgente(
        agente="comercial", estado=EstadoResultado.COMPLETADO, codigo="OK-PROMESA-ALT", mensaje="PED-002",
        ids={"id_solicitud": "SOL-002", "intento": 2, "id_pedido": "PED-002"})]
    assert cli.main(["demo", "excepcion", "--acepta"]) == cli.SALIDA_OK
    salida = capsys.readouterr().out
    assert "8 de 8 verificaciones conformes" in salida
    assert sistema_falso["corte"] == date(2026, 10, 7)
    assert sistema_falso["avances"] == [date(2026, 10, 8)]
    pedido, decision = sistema_falso["orq"].eventos
    assert decision.tipo == "decision_humana" and decision.run_id == pedido.run_id
    assert decision.fecha_negocio == date(2026, 10, 8)
    assert decision.datos == {"id_escalamiento": "ESC-SOL-002-1", "acepta": True, "registrada_por": "Preventista 2",
                              "medio": "Llamada telefónica", "evidencia": "ACEP-SOL-002-2"}


def test_demo_excepcion_con_rechazo(sistema_falso, capsys):
    sistema_falso["resultados"] = [resultado_intento1(), ResultadoAgente(
        agente="comercial", estado=EstadoResultado.CERRADO_SIN_PEDIDO, codigo=None, mensaje="Sin pedido")]
    assert cli.main(["demo", "excepcion", "--rechaza"]) == cli.SALIDA_OK
    assert "7 de 7 verificaciones conformes" in capsys.readouterr().out
    assert sistema_falso["orq"].eventos[1].datos["acepta"] is False


def test_demo_sin_decision_en_entrada_no_interactiva(sistema_falso, monkeypatch, capsys):
    sistema_falso["resultados"] = [resultado_intento1()]
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    assert cli.main(["demo", "excepcion"]) == cli.SALIDA_FALLA
    assert "--acepta o --rechaza" in capsys.readouterr().err


def test_demo_normal_no_conforme_devuelve_1(sistema_falso, capsys):
    sistema_falso["resultados"] = [ResultadoAgente(agente="comercial", estado=EstadoResultado.ESCALADO,
                                                   codigo="CRED-BLOQ", mensaje="x", ids={"id_solicitud": "SOL-003"})]
    assert cli.main(["demo", "normal"]) == cli.SALIDA_FALLA
    assert "NO CONFORME" in capsys.readouterr().out
