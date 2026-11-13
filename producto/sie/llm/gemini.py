"""Cliente de Gemini (Google AI Studio, nivel gratuito) por su endpoint compatible con OpenAI.

- Endpoint: https://generativelanguage.googleapis.com/v1beta/openai/chat/completions
- Autenticación: `Authorization: Bearer <GEMINI_API_KEY>` (clave de https://aistudio.google.com/apikey).
- Modelo por defecto `gemini-2.5-flash` (configurable con GEMINI_MODEL).
- Solo biblioteca estándar (urllib): no requiere instalar paquetes.
- Misma interfaz que `ClienteLLM` (resolver_con_herramientas y redactar), así el agente no cambia.
- Solo se ejecutan herramientas de la lista recibida (todas de lectura); cualquier otra devuelve error al modelo.
- Cualquier fallo se convierte en `ErrorLLM`: el agente vuelve al modo reglas y lo registra en la bitácora.
"""

from __future__ import annotations

import copy
import json
import sqlite3
import time
import urllib.error
import urllib.request
from typing import Any, Callable

from sie.agentes.base import Herramienta
from sie.llm.cliente import ClienteLLM, ErrorLLM

URL_GEMINI = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
MODELO_GEMINI_POR_DEFECTO = "gemini-2.5-flash"

Transporte = Callable[[dict[str, Any]], dict[str, Any]]


def _limpiar_esquema(esquema: Any) -> Any:
    """Adapta el esquema estricto (pensado para la Claude API) a lo que acepta Gemini.

    Quita `additionalProperties` y `strict`, y convierte enums con cadena vacía en descripción.
    """
    if isinstance(esquema, list):
        return [_limpiar_esquema(x) for x in esquema]
    if not isinstance(esquema, dict):
        return esquema
    limpio: dict[str, Any] = {}
    for clave, valor in esquema.items():
        if clave in ("additionalProperties", "strict", "$schema"):
            continue
        limpio[clave] = _limpiar_esquema(valor)
    if "enum" in limpio and "" in limpio["enum"]:
        opciones = [o for o in limpio.pop("enum") if o != ""]
        limpio["description"] = (limpio.get("description", "") +
                                 f" Valores: {', '.join(opciones)} o vacío si no se sabe.").strip()
    return limpio


def definicion_openai(h: Herramienta) -> dict[str, Any]:
    return {"type": "function",
            "function": {"name": h.nombre, "description": h.descripcion,
                         "parameters": _limpiar_esquema(copy.deepcopy(h.esquema))}}


def _consejo_http(codigo: int, cuerpo: str) -> str:
    if codigo in (401, 403):
        return f"HTTP {codigo}: revise GEMINI_API_KEY en .env"
    if codigo == 404:
        return f"HTTP {codigo}: el modelo no existe; revise GEMINI_MODEL (pruebe gemini-flash-latest)"
    if codigo == 429:
        return f"HTTP {codigo}: límite del nivel gratuito alcanzado; espere un minuto y reintente"
    if codigo == 400:
        return f"HTTP {codigo}: solicitud rechazada ({cuerpo[:160]})"
    return f"HTTP {codigo}: error de la API de Gemini"


class ClienteGemini(ClienteLLM):
    def __init__(self, modelo: str = MODELO_GEMINI_POR_DEFECTO, api_key: str | None = None,
                 transporte: Transporte | None = None, max_iteraciones: int = 6,
                 timeout: float = 60.0, url: str = URL_GEMINI) -> None:
        super().__init__(modelo=modelo, api_key=api_key, max_iteraciones=max_iteraciones)
        self._transporte = transporte  # se inyecta un doble en las pruebas
        self.timeout = timeout
        self.url = url

    # ------------------------------------------------------------------ transporte HTTP
    def _http(self, cuerpo: dict[str, Any]) -> dict[str, Any]:
        if not self._api_key:
            raise ErrorLLM("falta GEMINI_API_KEY en .env")
        datos = json.dumps(cuerpo, ensure_ascii=False).encode("utf-8")
        for intento in range(2):
            solicitud = urllib.request.Request(
                self.url, data=datos, method="POST",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self._api_key}"})
            try:
                with urllib.request.urlopen(solicitud, timeout=self.timeout) as r:
                    return json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                texto = e.read().decode("utf-8", "replace") if e.fp else ""
                if e.code in (429, 500, 503) and intento == 0:
                    time.sleep(3)
                    continue
                raise ErrorLLM(_consejo_http(e.code, texto)) from e
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                raise ErrorLLM(f"sin conexión con la API de Gemini ({type(e).__name__})") from e
            except json.JSONDecodeError as e:
                raise ErrorLLM("respuesta de Gemini no es JSON") from e
        raise ErrorLLM("la API de Gemini no respondió")

    def _crear(self, **cuerpo: Any) -> dict[str, Any]:  # type: ignore[override]
        cuerpo = {"model": self.modelo, **cuerpo}
        respuesta = (self._transporte or self._http)(cuerpo)
        opciones = respuesta.get("choices") or []
        if not opciones:
            raise ErrorLLM(f"Gemini no devolvió opciones ({str(respuesta)[:120]})")
        return opciones[0]

    # ------------------------------------------------------------------ interfaz del agente
    def resolver_con_herramientas(self, sistema: str, usuario: str, herramientas: list[Herramienta],
                                  final: Herramienta) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        permitidas = {h.nombre: h for h in herramientas}
        definiciones = [definicion_openai(h) for h in herramientas] + [definicion_openai(final)]
        mensajes: list[dict[str, Any]] = [{"role": "system", "content": sistema},
                                          {"role": "user", "content": usuario}]
        trazas: list[dict[str, Any]] = []
        recordatorio_enviado = False
        for _ in range(self.max_iteraciones):
            opcion = self._crear(messages=mensajes, tools=definiciones, tool_choice="auto")
            mensaje = opcion.get("message") or {}
            llamadas = mensaje.get("tool_calls") or []
            if not llamadas:
                if recordatorio_enviado:
                    raise ErrorLLM("el modelo terminó sin registrar la intención")
                recordatorio_enviado = True
                mensajes.append({"role": "assistant", "content": mensaje.get("content") or ""})
                mensajes.append({"role": "user", "content": f"Llama ahora a {final.nombre} con lo identificado."})
                continue
            # Se devuelve el mensaje del modelo tal cual (incluye firmas de pensamiento si las hay).
            asistente = {k: v for k, v in mensaje.items() if k in ("role", "content", "tool_calls", "extra_content")}
            asistente["role"] = "assistant"
            asistente.setdefault("content", "")
            if asistente["content"] is None:
                asistente["content"] = ""
            mensajes.append(asistente)
            argumentos_finales = None
            for llamada in llamadas:
                funcion = llamada.get("function") or {}
                nombre = funcion.get("name", "")
                try:
                    argumentos = json.loads(funcion.get("arguments") or "{}")
                except json.JSONDecodeError:
                    argumentos = {}
                if nombre == final.nombre:
                    argumentos_finales = argumentos
                    continue
                herramienta = permitidas.get(nombre)
                es_error = False
                if herramienta is None:
                    contenido, es_error = f"Herramienta no permitida: {nombre}", True
                else:
                    try:
                        contenido = json.dumps(herramienta.ejecutar(argumentos), ensure_ascii=False, default=str)
                    except (LookupError, ValueError, TypeError, sqlite3.Error) as e:
                        contenido, es_error = f"Error al consultar: {e}", True
                trazas.append({"herramienta": nombre, "argumentos": argumentos, "error": es_error})
                mensajes.append({"role": "tool", "tool_call_id": llamada.get("id", nombre), "content": contenido})
            if argumentos_finales is not None:
                return argumentos_finales, trazas
        raise ErrorLLM(f"sin respuesta final tras {self.max_iteraciones} iteraciones")

    def redactar(self, sistema: str, usuario: str) -> str:
        opcion = self._crear(messages=[{"role": "system", "content": sistema},
                                       {"role": "user", "content": usuario}])
        texto = ((opcion.get("message") or {}).get("content") or "").strip()
        if not texto:
            raise ErrorLLM("respuesta sin texto")
        return texto
