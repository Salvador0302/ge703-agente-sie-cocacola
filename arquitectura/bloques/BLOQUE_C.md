# Brief · Bloque C · Agente comercial

**Responsable:** José Julián Cornejo Palomino · **Rama:** `bloque-c/agente-comercial` · **Plazo:** martes 10/11/2026, 23:59
**Por qué tú:** en el EP diseñaste la prueba normal y la excepción, y defendiste el escenario de quiebre. Este bloque es el agente que las ejecuta en vivo.

## Qué entregas

| Archivo | Contenido |
|---|---|
| `producto/sie/crm/consultas.py` | CRM simulado: búsquedas, cotización con líneas, `construir_solicitud`, `registrar_respuesta` (oportunidad `Ganada` y R9) |
| `producto/sie/agentes/comercial/agente.py` | Flujo del agente (abajo) |
| `producto/sie/agentes/comercial/interprete_reglas.py` | Intérprete sin LLM: cliente por nombre comercial, `COT-NNN-VNN` si aparece, cantidad ("600 paquetes"); "500 ml" no es una cantidad |
| `producto/sie/agentes/comercial/redaccion.py` | Plantillas en español por código (incluye `NO-ENVIADA` y el rechazo del cliente) |
| `producto/sie/agentes/comercial/herramientas.py` | Cuatro herramientas de lectura con esquema estricto: `buscar_cliente`, `listar_cotizaciones`, `ver_cotizacion`, `consultar_atp` |
| `producto/sie/bitacora/persistente.py` | Misma entrada en la tabla `bitacora` y en `logs/bitacora.jsonl` (UTF-8, una línea JSON por entrada); `leer` filtra por `run_id`, `id_solicitud` o últimas N |
| `agentes/comercial/FICHA.md` | Propósito, entradas, salidas, fuentes, herramientas, reglas, permisos, responsable humano, escalamiento y bitácora (lo exige la PC3) |
| `procesos/` | `REGLAS.md` (R1–R9, P1–P3, C1–C5), `TABLA_DECISIONES.md`, `EVENTOS.md`, `CONTROLES.md`, `PARADA_ATP.md` (cadena OT → capacidad → ATP → promesa) |
| `pruebas/CASOS.csv`, `pruebas/CRITERIOS_ACEPTACION.md` | Casos con esperado (los observados los genera la demo el jueves) |

Las firmas ya están en los archivos y en `arquitectura/INTERFACES.md` (§2–§4). **No las cambies sin avisar a Salvador.**

## Flujo del evento `pedido`

1. Valida `datos` (texto no vacío, canal TUALI / Preventa / Teléfono); si no, `ERROR`.
2. Interpreta (`self.interprete`) y registra en la bitácora cliente, cotización, cantidad y modo (sin el texto: guarda su longitud y un hash).
3. Elige la cotización: la indicada en el texto o, si no hay, la `Aceptada` y vigente del cliente sin pedido. Si no hay cliente o cotización → `NO-ENVIADA` (P3).
4. R2: si la cotización no está `Aceptada` o vigente, o la cantidad mencionada difiere del total cotizado → `NO-ENVIADA`, sin EV-02. Escala al Supervisor de ventas si el descuento fue `Rechazado`; si no, al ejecutivo de la cuenta.
5. Arma EV-02 con `crm.construir_solicitud` (el canal viene del evento, R8), consulta el ATP como pre-chequeo no vinculante (I3) y envía con `erp.recibir(sol, run_id)`.
6. Según el código:
   - `OK-*` → `crm.registrar_respuesta` → `COMPLETADO`.
   - `ATP-PARCIAL` → escalamiento `ESC-SOL-002-1` al ejecutivo de la cuenta (Preventista 2), fecha límite + 1 día, guardado en `escalamientos` con la promesa en `datos_json`; `ids["id_ot"]` desde `erp.explicar_faltante` → `ESPERA_HUMANO`.
   - Otro rechazo → escalamiento al responsable de la respuesta → `ESCALADO`.
7. Redacta (`self.redactor.redactar(hechos)`) y devuelve el `ResultadoAgente` con las convenciones de `INTERFACES.md` §4.

**Evento `decision_humana`:** busca el escalamiento `Pendiente` (si no existe → `ERROR`). Si el cliente acepta: EV-05 con `intento + 1`, tipo "Confirmación promesa", `Aceptacion` con los tramos propuestos → `OK-PROMESA-ALT` → `COMPLETADO`. Si rechaza: no envía nada → `CERRADO_SIN_PEDIDO`. En ambos casos marca el escalamiento `Resuelto` con la respuesta, la evidencia y la fecha.

**Permisos (ADR-003):** el agente nunca escribe en `pedidos_cab`/`pedidos_det`, nunca envía EV-05 sin `decision_humana` y las herramientas para el LLM son solo de lectura. La bitácora no guarda nombres de contacto, correos, teléfonos, RUC ni el texto libre del cliente.

## Cómo trabajar mientras B avanza

Tus pruebas son de integración y necesitan el seed y el ERP de Gianmarco (domingo y lunes). Mientras tanto:

- Empieza por `BitacoraPersistente`, `RedactorPlantilla`, `InterpreteReglas` y la ficha, con tus propias pruebas unitarias en `pruebas/unitarias/` (puedes usar una base en memoria con unas pocas filas).
- Cuando B suba avances: `git fetch origin; git merge origin/bloque-b/datos-erp` en tu rama.

```powershell
git fetch origin; git switch bloque-c/agente-comercial
py -3.11 -m venv .venv; .venv\Scripts\activate; pip install -r requirements.txt
python -m pytest pruebas/aceptacion/test_bloque_c.py      # pendientes hasta que exista el seed
cd producto; python -m sie demo normal; python -m sie demo excepcion
```

Commits pequeños **con tu propia identidad**. Si usas IA, decláralo en `fuentes/DECLARACION_IA.md`. Pull request a `main` cuando esté verde.

## Terminado cuando

- `python -m pytest pruebas/aceptacion/test_bloque_c.py` da **0 pendientes y 0 fallas**.
- `python -m sie demo normal` y `python -m sie demo excepcion --acepta` terminan con todas las verificaciones conformes.
- Puedes explicar en 1 minuto cómo se detecta, contiene y escala la excepción, y qué no puede hacer el agente.
