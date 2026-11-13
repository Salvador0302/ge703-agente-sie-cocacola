"""Proveedor Gemini (nivel gratuito, endpoint compatible con OpenAI) con un doble del transporte HTTP.

No llama a internet: el doble responde como la API de Gemini. La prueba real se hace con
GEMINI_API_KEY en .env y `python -m sie demo excepcion --modo llm` (ver entrega/GUIA_DESPLIEGUE.md).
"""

import json

from sie.agentes.base import EstadoResultado, Evento, nuevo_run_id
from sie.bitacora.persistente import BitacoraPersistente
from sie.config import Config, cargar
from sie.db import seed
from sie.db.conexion import conectar
from sie.demo import CASOS
from sie.llm.cliente import ErrorLLM
from sie.llm.gemini import ClienteGemini, _limpiar_esquema
from sie.sistema import construir_sistema

EXC = CASOS["excepcion"]


def _llamada(id_, nombre, args):
    return {"id": id_, "type": "function", "function": {"name": nombre, "arguments": json.dumps(args)}}


class TransporteFalso:
    """Simula a Gemini: busca al cliente, lista sus cotizaciones y registra la intención; luego redacta."""

    def __init__(self):
        self.cuerpos = []

    def __call__(self, cuerpo):
        self.cuerpos.append(cuerpo)
        if "tools" not in cuerpo:  # redacción
            return {"choices": [{"message": {"role": "assistant", "content":
                    "El ERP respondió ATP-PARCIAL por la parada OT-2026-0107; Preventista 2 debe confirmar con el cliente."}}]}
        tools_previas = [m for m in cuerpo["messages"] if m["role"] == "tool"]
        if not tools_previas:
            return {"choices": [{"message": {"role": "assistant", "content": None, "tool_calls": [
                _llamada("c1", "buscar_cliente", {"texto": "Los Olivos"})]}}]}
        if len(tools_previas) == 1:
            return {"choices": [{"message": {"role": "assistant", "content": None, "tool_calls": [
                _llamada("c2", "listar_cotizaciones", {"id_cliente": "CLI-002", "fecha": EXC.fecha.isoformat()})]}}]}
        return {"choices": [{"message": {"role": "assistant", "content": None, "tool_calls": [
            _llamada("c3", "registrar_intencion", {"id_cliente": "CLI-002", "canal_origen": "Teléfono",
                                                   "id_cotizacion": "COT-002-V02", "cantidad_mencionada": 600,
                                                   "producto_mencionado": "Inca Kola 500 ml",
                                                   "resumen": "Pide 600 paquetes de la promoción"})]}}]}


def _sistema(tmp_path, transporte):
    conn = conectar()
    seed.crear_base(conn, EXC.corte)
    config = Config(modo="llm", proveedor="gemini", modelo="gemini-2.5-flash", gemini_api_key="clave-de-prueba",
                    carpeta_logs=tmp_path)
    return construir_sistema(config, conn, bitacora=BitacoraPersistente(conn, config.ruta_bitacora),
                             cliente_llm=transporte)


def test_config_elige_gemini_con_su_clave(tmp_path):
    c = cargar(entorno={"AGENT_MODE": "llm", "GEMINI_API_KEY": "k"}, ruta_env=tmp_path / "x.env")
    assert (c.modo, c.proveedor, c.modelo, c.tiene_api_key) == ("llm", "gemini", "gemini-2.5-flash", True)
    assert "k" not in repr(c)
    sin = cargar(entorno={"AGENT_MODE": "llm", "LLM_PROVEEDOR": "gemini"}, ruta_env=tmp_path / "x.env")
    assert sin.modo == "reglas" and any("GEMINI_API_KEY" in a for a in sin.avisos)


def test_esquema_sin_campos_que_gemini_rechaza():
    e = _limpiar_esquema({"type": "object", "additionalProperties": False, "properties": {
        "canal": {"type": "string", "enum": ["TUALI", "Teléfono", ""]}}})
    assert "additionalProperties" not in e and "enum" not in e["properties"]["canal"]
    assert "TUALI" in e["properties"]["canal"]["description"]


def test_excepcion_con_gemini_usa_herramientas_y_el_erp_decide(tmp_path):
    t = TransporteFalso()
    s = _sistema(tmp_path, t)
    r = s.orquestador.despachar(Evento(tipo="pedido", fecha_negocio=EXC.fecha,
                                       datos={"texto": EXC.texto, "canal": EXC.canal}, run_id=nuevo_run_id()))
    assert (r.estado, r.codigo) == (EstadoResultado.ESPERA_HUMANO, "ATP-PARCIAL")
    assert r.ids.get("id_cotizacion") == "COT-002-V02"
    # Gemini solo recibió herramientas de lectura + registrar_intencion; nunca una de escritura.
    nombres = {d["function"]["name"] for d in t.cuerpos[0]["tools"]}
    assert nombres == {"buscar_cliente", "listar_cotizaciones", "ver_cotizacion", "consultar_atp", "registrar_intencion"}
    assert all(c["model"] == "gemini-2.5-flash" for c in t.cuerpos)


def test_falla_de_gemini_vuelve_a_reglas(tmp_path):
    def caida(_cuerpo):
        raise ErrorLLM("HTTP 429: límite del nivel gratuito alcanzado")
    s = _sistema(tmp_path, caida)
    r = s.orquestador.despachar(Evento(tipo="pedido", fecha_negocio=EXC.fecha,
                                       datos={"texto": EXC.texto, "canal": EXC.canal}, run_id=nuevo_run_id()))
    assert r.codigo == "ATP-PARCIAL"  # mismo resultado con el respaldo por reglas


def test_sin_clave_no_llama_a_internet():
    try:
        ClienteGemini(api_key=None)._crear(messages=[])
    except ErrorLLM as e:
        assert "GEMINI_API_KEY" in str(e)
    else:
        raise AssertionError("debía fallar sin clave")
