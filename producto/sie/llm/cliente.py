"""Cliente mínimo de la Claude API con bucle de herramientas propio (tool use manual).

- Modelo por defecto `claude-opus-5-5` (configurable con ANTHROPIC_MODEL) y esfuerzo `low`
  (SIE_LLM_ESFUERZO): interpretar un pedido es una tarea acotada.
- Fallback de servidor activado (`fallbacks="default"`, beta server-side-fallback-2026-07-01): si los
  filtros de seguridad rechazan la solicitud, la API la reintenta en otro modelo.
- Solo se ejecutan herramientas de la lista recibida; cualquier otra devuelve error al modelo.
- Cualquier fallo se convierte en `ErrorLLM`: quien llama vuelve al modo reglas y lo registra.
- El SDK `anthropic` se importa solo si se usa este modo.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from sie.agentes.base import Herramienta

BETA_FALLBACK = "server-side-fallback-2026-07-01"


class ErrorLLM(RuntimeError):
    """La Claude API no pudo completar la tarea; el agente debe usar el modo reglas."""


def _describir_error(error: Exception) -> str:
    nombre = type(error).__name__
    consejos = {
        "AuthenticationError": "revise ANTHROPIC_API_KEY en .env",
        "PermissionDeniedError": "la API key no tiene permiso para este modelo",
        "NotFoundError": "revise ANTHROPIC_MODEL",
        "RateLimitError": "límite de uso alcanzado; espere y reintente",
        "APIConnectionError": "sin conexión a internet o a la API",
        "APITimeoutError": "la API no respondió a tiempo",
    }
    consejo = consejos.get(nombre, "error de la API")
    return f"{nombre}: {consejo}"


class ClienteLLM:
    def __init__(self, modelo: str, esfuerzo: str = "low", api_key: str | None = None,
                 cliente: Any = None, max_iteraciones: int = 6, max_tokens: int = 16000) -> None:
        self.modelo = modelo
        self.esfuerzo = esfuerzo
        self._api_key = api_key
        self._cliente = cliente  # se inyecta un doble en las pruebas
        self.max_iteraciones = max_iteraciones
        self.max_tokens = max_tokens

    def _sdk(self) -> Any:
        if self._cliente is None:
            try:
                import anthropic
            except ImportError as e:
                raise ErrorLLM("Falta el paquete 'anthropic': ejecute pip install -r requirements.txt") from e
            self._cliente = anthropic.Anthropic(api_key=self._api_key, max_retries=2, timeout=60.0)
        return self._cliente

    def _crear(self, **parametros: Any) -> Any:
        cliente = self._sdk()
        try:
            respuesta = cliente.beta.messages.create(
                model=self.modelo,
                max_tokens=self.max_tokens,
                output_config={"effort": self.esfuerzo},
                betas=[BETA_FALLBACK],
                fallbacks="default",
                **parametros,
            )
        except Exception as e:  # noqa: BLE001 - todo fallo de la API degrada a reglas y queda en bitácora
            raise ErrorLLM(_describir_error(e)) from e
        if respuesta.stop_reason == "refusal":
            raise ErrorLLM("la API declinó la solicitud (refusal)")
        if respuesta.stop_reason == "max_tokens":
            raise ErrorLLM("respuesta truncada por max_tokens")
        return respuesta

    def resolver_con_herramientas(self, sistema: str, usuario: str, herramientas: list[Herramienta],
                                  final: Herramienta) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Bucle de herramientas. Termina cuando el modelo llama a `final`.

        Devuelve los argumentos de `final` y la traza de herramientas ejecutadas (para la bitácora).
        """
        permitidas = {h.nombre: h for h in herramientas}
        definiciones = [h.definicion() for h in herramientas] + [final.definicion()]
        mensajes: list[dict[str, Any]] = [{"role": "user", "content": usuario}]
        trazas: list[dict[str, Any]] = []
        for _ in range(self.max_iteraciones):
            respuesta = self._crear(system=sistema, tools=definiciones, messages=mensajes)
            # Se devuelve el contenido completo (incluidos bloques de pensamiento) sin modificarlo.
            mensajes.append({"role": "assistant", "content": respuesta.content})
            if respuesta.stop_reason == "pause_turn":
                continue
            usos = [b for b in respuesta.content if getattr(b, "type", None) == "tool_use"]
            if not usos:
                raise ErrorLLM("el modelo terminó sin registrar la intención")
            resultados = []
            argumentos_finales = None
            for uso in usos:
                if uso.name == final.nombre:
                    argumentos_finales = dict(uso.input)
                    continue
                herramienta = permitidas.get(uso.name)
                es_error = False
                if herramienta is None:
                    contenido, es_error = f"Herramienta no permitida: {uso.name}", True
                else:
                    try:
                        contenido = json.dumps(herramienta.ejecutar(dict(uso.input)), ensure_ascii=False, default=str)
                    except (LookupError, ValueError, TypeError, sqlite3.Error) as e:
                        contenido, es_error = f"Error al consultar: {e}", True
                trazas.append({"herramienta": uso.name, "argumentos": dict(uso.input), "error": es_error})
                bloque = {"type": "tool_result", "tool_use_id": uso.id, "content": contenido}
                if es_error:
                    bloque["is_error"] = True
                resultados.append(bloque)
            if argumentos_finales is not None:
                return argumentos_finales, trazas
            mensajes.append({"role": "user", "content": resultados})
        raise ErrorLLM(f"sin respuesta final tras {self.max_iteraciones} iteraciones")

    def redactar(self, sistema: str, usuario: str) -> str:
        respuesta = self._crear(system=sistema, messages=[{"role": "user", "content": usuario}])
        texto = "".join(b.text for b in respuesta.content if getattr(b, "type", None) == "text").strip()
        if not texto:
            raise ErrorLLM("respuesta sin texto")
        return texto
