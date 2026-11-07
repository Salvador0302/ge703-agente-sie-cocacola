"""Pruebas de aceptación · BLOQUE D: UI, documentación de entrega y ZIP.

Terminado = este archivo con 0 pendientes y 0 fallas: `python -m pytest pruebas/aceptacion/test_bloque_d.py`.
La verificación del ZIP ejecuta la demo, así que requiere B y C terminados.
"""

import importlib.util
import re
import zipfile

import pytest

from apoyo import RAIZ, requerir

GUIA = RAIZ / "entrega" / "GUIA_DESPLIEGUE.md"
SECCIONES_GUIA = ["Requisitos previos", "Instalación", "Configuración", "Ejecución de la demo",
                  "Resultados esperados", "Diagnóstico y recuperación", "Dependencias y licencias",
                  "Accesos seguros", "Ficha del agente"]
#: Forma de una API key real (el prefijo se arma por partes para que este archivo no se marque a sí mismo).
API_KEY = re.compile(("sk-" + "ant-") + r"[A-Za-z0-9_\-]{20,}")
INTEGRANTES = ["Barrionuevo Gutierrez, Salvador Jhou", "Cornejo Palomino, José Julián",
               "Leandro Ochoa, Gianmarco", "Urbano Lara, David Alexis"]


def armar_zip():
    spec = importlib.util.spec_from_file_location("armar_zip", RAIZ / "entrega" / "armar_zip.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_readme():
    texto = (RAIZ / "README.md").read_text(encoding="utf-8")
    requerir(GUIA.exists(), "Bloque D: el README se completa con el enlace a entrega/GUIA_DESPLIEGUE.md.")
    for nombre in INTEGRANTES:
        assert nombre in texto, nombre
    for fragmento in ("python -m sie demo normal", "python -m sie demo excepcion", "sintétic", "GUIA_DESPLIEGUE.md"):
        assert fragmento in texto, fragmento


def test_guia_de_despliegue_completa():
    requerir(GUIA.exists(), "Bloque D: entrega/GUIA_DESPLIEGUE.md.")
    texto = GUIA.read_text(encoding="utf-8")
    titulos = [linea.lstrip("#").strip() for linea in texto.splitlines() if linea.startswith("#")]
    for seccion in SECCIONES_GUIA:
        assert any(t.startswith(seccion) or seccion in t for t in titulos), seccion
    for fragmento in ("agentes/comercial/FICHA.md", ".env.example", "python -m sie diagnostico", "AGENT_MODE"):
        assert fragmento in texto, fragmento


def test_fuentes_licencias_y_declaracion_de_ia():
    carpeta = RAIZ / "fuentes"
    requerir((carpeta / "DECLARACION_IA.md").exists(), "Bloque D: carpeta fuentes/.")
    for nombre in ("BIBLIOGRAFIA.md", "LICENCIAS.md", "DECLARACION_IA.md"):
        assert (carpeta / nombre).exists(), nombre
    ia = (carpeta / "DECLARACION_IA.md").read_text(encoding="utf-8").lower()
    assert "claude" in ia and "validación humana" in ia


def test_zip_nombre_contenido_y_exclusiones(tmp_path):
    ruta = armar_zip().construir(tmp_path, incremento="PC3")
    assert ruta.name == "GE703_PC3_Agente_G2_CocaCola.zip"
    with zipfile.ZipFile(ruta) as z:
        nombres = z.namelist()
        assert nombres, "el ZIP está vacío"
        for requerido in ("README.md", "requirements.txt", ".env.example", "producto/sie/__main__.py",
                          "entrega/GUIA_DESPLIEGUE.md", "agentes/comercial/FICHA.md"):
            assert any(n.endswith(requerido) for n in nombres), requerido
        assert any("/datos/seed/" in f"/{n}" for n in nombres)
        for n in nombres:
            partes = set(n.replace("\\", "/").split("/"))
            assert not partes & {".env", ".venv", ".git", "__pycache__", "logs", "salida"}, n
            assert not n.endswith((".db", ".pyc", ".zip")), n
            assert len(n) <= 150, n
            if n.endswith((".py", ".md", ".csv", ".txt", ".json", ".toml", ".example")):
                assert not API_KEY.search(z.read(n).decode("utf-8", "replace")), n


def test_zip_verificado_desde_una_carpeta_limpia(tmp_path):
    modulo = armar_zip()
    ruta = modulo.construir(tmp_path, incremento="PC3")
    assert modulo.verificar(ruta, ejecutar_demo=True) == []


def test_ui_streamlit_recorre_los_dos_casos(tmp_path, monkeypatch):
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("SIE_DB", str(tmp_path / "sie.db"))  # la UI usa sie_ui.db junto a esta ruta
    monkeypatch.setenv("SIE_LOGS", str(tmp_path / "logs"))
    app = AppTest.from_file(str(RAIZ / "producto" / "sie" / "ui" / "app.py"), default_timeout=90)
    app.run()
    errores = [str(e.value) for e in app.exception]
    requerir(not any("Bloque D" in e for e in errores), "Bloque D: interfaz Streamlit.")
    assert errores == []
    assert any("Agente SIE" in t.value for t in app.title)

    app.button(key="ejecutar_normal").click().run()
    assert not app.exception
    assert any("4 de 4 verificaciones conformes" in s.value for s in app.success)

    app.button(key="ejecutar_excepcion").click().run()
    assert not app.exception
    assert any("ATP-PARCIAL" in w.value for w in app.warning)
    assert "OT-2026-0107" in [m.value for m in app.metric]
    app.button(key="acepta_excepcion").click().run()
    assert not app.exception
    assert any("8 de 8 verificaciones conformes" in s.value for s in app.success)
