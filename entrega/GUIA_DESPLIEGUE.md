# Guía de despliegue y ejecución · Agente SIE · G2 · Coca-Cola / ACL (PC3)

Esta guía permite ejecutar el agente y reproducir la demo solo con los archivos entregados, en Windows. La demo usa datos **sintéticos**; ningún valor corresponde a ACL.

## Requisitos previos

| Requisito | Detalle |
|---|---|
| Sistema | Windows 10 u 11 (también funciona en macOS y Linux) |
| Python | 3.11 o superior (probado con 3.11.0 y 3.13). Compruebe con `python --version` o `py -3.11 --version` |
| Internet | No hace falta para la demo. Solo para instalar las dependencias opcionales o usar el modo LLM |
| Espacio | El ZIP pesa 4,8 MB y ocupa 6,3 MB descomprimido; unos 400 MB más si instala las dependencias opcionales en un entorno virtual |

## Instalación

1. Descomprima `GE703_PC3_Agente_G2_CocaCola.zip`. Se crea la carpeta `GE703_PC3_Agente_G2_CocaCola`.
2. Abra PowerShell en esa carpeta (en el Explorador: clic derecho → "Abrir en Terminal").
3. **Para la demo por consola no hay que instalar nada.** Opcional, para la interfaz web y las pruebas automáticas:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuración

La configuración por defecto (modo `reglas`) no necesita ningún archivo. Para cambiarla, copie `.env.example` como `.env` en la misma carpeta y edítelo:

| Variable | Valores | Por defecto |
|---|---|---|
| `AGENT_MODE` | `reglas` (sin internet ni API key) o `llm` (la IA interpreta el texto con herramientas de consulta y redacta; las reglas siguen decidiendo) | `reglas` |
| `LLM_PROVEEDOR` | `gemini` (Google AI Studio, nivel gratuito) o `anthropic` (Claude API). Si solo hay `GEMINI_API_KEY`, se usa `gemini` | `anthropic` |
| `GEMINI_API_KEY` | Clave gratuita de https://aistudio.google.com/apikey, solo para `llm` con Gemini | vacía |
| `GEMINI_MODEL` | Modelo de Gemini (si da HTTP 404, use `gemini-flash-latest`) | `gemini-2.5-flash` |
| `ANTHROPIC_API_KEY` | Clave de la Claude API, solo para `llm`. Si falta, el agente usa `reglas` y lo avisa | vacía |
| `ANTHROPIC_MODEL` | Modelo del modo `llm` | `claude-opus-5-5` |
| `SIE_LLM_ESFUERZO` | `low`, `medium`, `high`, `xhigh` o `max` | `low` |
| `SIE_DB`, `SIE_LOGS` | Rutas de la base y de la bitácora, relativas a la carpeta del proyecto | `datos/sie.db`, `logs` |

## Ejecución de la demo

Todos los comandos se ejecutan desde la carpeta `producto`:

```powershell
cd producto
python -m sie diagnostico          # 1. verifica el entorno (debe terminar en "Todo listo para la demo")
python -m sie demo normal          # 2. caso normal: Don Lucho por TUALI
python -m sie demo excepcion       # 3. excepción: Los Olivos por teléfono; pide la decisión de Preventista 2 (s/n)
python -m sie bitacora --run <run> # 4. bitácora del caso (el run aparece al final de cada demo)
python -m sie ui                   # opcional: interfaz web en http://localhost:8501 (requiere Streamlit)
```

- **Si `python` no se reconoce:** use `py -3.11 -m sie ...`.
- **Si `python` abre la Microsoft Store:** instale Python desde python.org.
- **Decisión sin preguntar:** `demo excepcion --acepta` o `--rechaza`.
- **Base reiniciada:** cada demo reinicia la base al corte de su caso, así que se puede repetir las veces que haga falta.

Otros comandos:

- `python -m sie agentes` muestra el estado de los agentes previstos.
- `python -m sie pedir "texto" --fecha 2026-10-02 --canal TUALI --corte 2026-10-02` envía un pedido en texto libre.
- `python -m sie --help` lista todos los comandos.

## Modo IA con Gemini (gratis, opcional)

1. Cree una clave gratuita en https://aistudio.google.com/apikey (cuenta de Google, sin tarjeta).
2. En la carpeta del proyecto (la que contiene `producto`), copie `.env.example` como `.env` y complete solo estas líneas:

```
AGENT_MODE=llm
LLM_PROVEEDOR=gemini
GEMINI_API_KEY=<su clave>
```

3. Ejecute `python -m sie diagnostico`: debe decir `Modo del agente: llm ... proveedor LLM gemini ... API key configurada`.
4. Ejecute las mismas demos (`python -m sie demo normal` y `python -m sie demo excepcion`). En la traza aparecen las consultas que decidió hacer la IA (`buscar_cliente`, `listar_cotizaciones`, etc.) y la explicación la redacta Gemini. Los controles C1–C5, los códigos y la promesa siguen saliendo del ERP simulado, por eso el esperado frente a observado es el mismo.
5. Si Gemini falla (clave inválida, sin internet o límite del nivel gratuito), el agente vuelve solo al modo `reglas` y lo anota como aviso: la demo no se interrumpe. Sin `.env`, todo corre en modo `reglas`.

El cliente de Gemini (`producto/sie/llm/gemini.py`) usa el endpoint compatible con OpenAI de Google y solo la biblioteca estándar de Python: no hay que instalar nada. Está cubierto por `pruebas/unitarias/test_gemini.py` con un doble de la API.

## Resultados esperados

**Caso normal** (02/10/2026, TUALI): "Bodega Don Lucho aceptó en la app TUALI su cotización de 65 paquetes…".

| Paso | Esperado |
|---|---|
| Interpretación | CLI-003 · COT-003-V01 (aceptada, 65 paquetes, 5 %) |
| Controles C1–C5 | V V V V V |
| Respuesta | `OK-ACEPTADO` · pedido **PED-003** por S/ 1,589.02 con entrega el 03/10/2026 |
| CRM | OPP-003 `Ganada`; CLI-003 pasa de "No usa" a "Híbrido" en TUALI |
| Cierre | **4 de 4 verificaciones conformes** |

**Excepción** (07/10/2026, teléfono): "Llamada de Comercial Los Olivos: pide 600 paquetes de Inca Kola 500 ml…".

| Paso | Esperado |
|---|---|
| Interpretación | CLI-002 · COT-002-V02 (8 % aprobado); la V01 con 10 % rechazada no se usa |
| Controles | C1–C4 V; **C5 F: ATP 380 de 600** |
| Causa | **OT-2026-0107**: 96 h de parada de la línea ACT-LLN-01, −240 paquetes; sin la parada el ATP sería 620 |
| Respuesta | `ATP-PARCIAL`: 380 el 09/10 y 220 el 12/10; **sin pedido** |
| Escalamiento | ESC-SOL-002-1 a **Preventista 2**, fecha límite 08/10/2026 |
| Si acepta (08/10) | EV-05 con evidencia ACEP-SOL-002-2 → `OK-PROMESA-ALT` · **PED-002** · **8 de 8 conformes** |
| Si rechaza | No se envía EV-05 ni se crea pedido · **7 de 7 conformes** |

Evidencia de una ejecución: `pruebas/evidencia/`. Las pruebas automáticas (`python -m pytest pruebas`, desde la carpeta raíz y con las dependencias instaladas) deben terminar sin fallas.

## Diagnóstico y recuperación

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `No module named sie` | El comando no se ejecutó desde `producto` | `cd producto` y repetir |
| `python` no se reconoce o abre la Store | Python no está en el PATH | Usar `py -3.11 -m sie ...` o instalar Python 3.11+ marcando "Add to PATH" |
| `Configuración inválida` (código 3) | Valor incorrecto en `.env` | Corregir el valor indicado o borrar `.env` (vuelve a `reglas`) |
| `Aviso: AGENT_MODE=llm sin ANTHROPIC_API_KEY` | Falta la clave | Agregarla en `.env` o seguir en modo `reglas` (resultado idéntico) |
| `database is locked` | La interfaz web tiene la base abierta | Cerrar la interfaz (Ctrl+C) y repetir; si persiste, borrar `datos/sie.db` (se regenera) |
| `Se requiere la decisión del responsable` | La excepción se ejecutó sin consola interactiva | Agregar `--acepta` o `--rechaza` |
| Puerto 8501 ocupado | Otra app usa el puerto | `python -m sie ui --puerto 8502` |
| `Falta Streamlit` | Dependencia opcional no instalada | `pip install -r requirements.txt`; la demo por consola no la necesita |
| `NO CONFORME` al final de una demo | Datos o código modificados | Revisar la traza; `python -m sie diagnostico`; volver a extraer el ZIP |
| Error del modo `llm` (red, clave, límite) | La Claude API no respondió | No se detiene: el agente vuelve a `reglas` y lo registra en los avisos y en la bitácora |

**Recuperación general:**

1. Borre `datos/sie.db` y `datos/sie_ui.db`: se regeneran desde `datos/seed/` en la siguiente demo.
2. La bitácora `logs/bitacora.jsonl` se puede borrar sin afectar la demo.
3. Ningún comando modifica `datos/seed/`. Si un archivo del paquete cambió, vuelva a extraer el ZIP.

## Dependencias y licencias

| Componente | Uso | Obligatorio | Licencia |
|---|---|---|---|
| Python 3.11+ (con SQLite incluido) | Núcleo, CLI y base local | Sí | PSF (SQLite: dominio público) |
| Streamlit 1.67.0 | Interfaz web | No | Apache-2.0 |
| anthropic 2.6.0 | Modo `llm` (Claude API) | No | Apache-2.0 |
| pytest 9.2.0 | Pruebas automáticas | No | MIT |
| Código del Agente SIE | Todo el paquete | — | MIT (`LICENSE`) |

Detalle de licencias, material del curso y marcas: `fuentes/LICENCIAS.md`.

## Accesos seguros

- El paquete **no contiene contraseñas ni API keys**: `.env` no se entrega y el armado del ZIP busca claves antes de cerrarlo.
- La demo completa funciona **sin clave**. Para el modo `llm`, el docente puede crear su propia clave gratuita de Gemini y ponerla en un `.env` local, o el equipo puede dar una clave temporal con límite de gasto que se revoca después de la evaluación. Nunca se envía por correo dentro del ZIP.
- La clave solo se lee de `.env` o del entorno. No se imprime, no entra en la bitácora y no aparece en los mensajes de error.
- Al modo `llm` solo viaja el texto del pedido y resultados de consultas sobre datos sintéticos.

## Ficha del agente

Ficha completa: `agentes/comercial/FICHA.md`. Resumen:

| Campo | Agente comercial |
|---|---|
| Propósito | Pasar una solicitud de pedido (TUALI, preventa o teléfono) por el contrato CRM–ERP I8 y responder con su código; escalar a una persona cuando el ERP no puede cumplir |
| Entradas | Texto del pedido, canal y fecha; decisión humana con evidencia |
| Salidas | Código del contrato, pedido, promesa por tramos, escalamiento, explicación y bitácora |
| Fuentes | CRM y ERP simulados con datos sintéticos (`datos/seed/`) |
| Herramientas | Reglas deterministas; en modo `llm`, cuatro herramientas de solo lectura |
| Reglas | R2, R6–R9 del agente; P1, P2 y C1–C5 del ERP (`procesos/REGLAS.md`) |
| Permisos | Lee y envía EV-02/EV-05; no crea pedidos, no aprueba descuentos, no cambia maestros |
| Responsable humano | Ejecutivo de la cuenta (Preventista); según el código, Supervisor de ventas, Créditos y cobranzas, Analista de precios o de datos maestros |
| Escalamiento | Objeto, causa, responsable, estado y fecha límite (1 día); `ATP-PARCIAL` espera la decisión |
| Bitácora | Tabla `bitacora` y `logs/bitacora.jsonl`, sin datos personales |
