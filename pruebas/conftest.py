"""Configuración común de pytest.

Una prueba que llega a código aún no implementado (`NotImplementedError`) se informa como
**pendiente** (omitida) con el bloque responsable, en lugar de como falla. Cuando el bloque está
implementado, la prueba corre de verdad y debe pasar.
"""

from __future__ import annotations

import pytest

from apoyo import EJEMPLOS, leer_ejemplo


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    resultado = yield
    reporte = resultado.get_result()
    if call.excinfo is not None and call.excinfo.errisinstance(NotImplementedError) and call.when in ("setup", "call"):
        reporte.outcome = "skipped"
        reporte.longrepr = (str(item.path), item.location[1] or 0, f"Pendiente: {call.excinfo.value}")


@pytest.fixture
def ejemplos() -> dict[str, dict]:
    return {p.name: leer_ejemplo(p.name) for p in sorted(EJEMPLOS.glob("*.json"))}
