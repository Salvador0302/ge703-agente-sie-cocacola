"""Bloque A · configuración desde entorno y .env, sin dependencias externas."""

import pytest

from sie.config import RAIZ, ErrorConfiguracion, cargar, leer_env


def test_valores_por_defecto(tmp_path):
    c = cargar(entorno={}, ruta_env=tmp_path / "no-existe.env")
    assert c.modo == "reglas"
    assert c.modelo == "claude-opus-5-5"
    assert c.esfuerzo == "low"
    assert c.ruta_db == RAIZ / "datos" / "sie.db"
    assert c.ruta_bitacora == RAIZ / "logs" / "bitacora.jsonl"
    assert c.avisos == ()


def test_lector_de_env(tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        "# comentario\n"
        "AGENT_MODE=llm\n"
        "export ANTHROPIC_MODEL='claude-sonnet-5-5'\n"
        'ANTHROPIC_API_KEY="clave-de-prueba"\n'
        "SIE_DB=otra/base.db  # comentario al final\n"
        "\n",
        encoding="utf-8",
    )
    valores = leer_env(env)
    assert valores == {"AGENT_MODE": "llm", "ANTHROPIC_MODEL": "claude-sonnet-5-5",
                       "ANTHROPIC_API_KEY": "clave-de-prueba", "SIE_DB": "otra/base.db"}
    c = cargar(entorno={}, ruta_env=env)
    assert c.modo == "llm"
    assert c.ruta_db == RAIZ / "otra" / "base.db"


def test_llm_sin_api_key_usa_reglas_y_avisa(tmp_path):
    c = cargar(entorno={"AGENT_MODE": "llm"}, ruta_env=tmp_path / "x.env")
    assert c.modo == "reglas" and c.modo_solicitado == "llm"
    assert any("ANTHROPIC_API_KEY" in a for a in c.avisos)


def test_entorno_del_proceso_prevalece_sobre_env_y_flag_sobre_ambos(tmp_path):
    env = tmp_path / ".env"
    env.write_text("AGENT_MODE=llm\nANTHROPIC_API_KEY=k\n", encoding="utf-8")
    assert cargar(entorno={"AGENT_MODE": "reglas"}, ruta_env=env).modo == "reglas"
    assert cargar(entorno={"AGENT_MODE": "reglas"}, ruta_env=env, modo="llm").modo == "llm"


def test_valores_invalidos(tmp_path):
    with pytest.raises(ErrorConfiguracion):
        cargar(entorno={"AGENT_MODE": "magia"}, ruta_env=tmp_path / "x.env")
    with pytest.raises(ErrorConfiguracion):
        cargar(entorno={"SIE_LLM_ESFUERZO": "extremo"}, ruta_env=tmp_path / "x.env")
    malo = tmp_path / ".env"
    malo.write_text("ESTO NO ES CLAVE VALOR\n", encoding="utf-8")
    with pytest.raises(ErrorConfiguracion):
        leer_env(malo)


def test_la_api_key_no_aparece_en_repr(tmp_path):
    c = cargar(entorno={"ANTHROPIC_API_KEY": "sk-ant-secreto"}, ruta_env=tmp_path / "x.env")
    assert c.tiene_api_key
    assert "sk-ant-secreto" not in repr(c)
