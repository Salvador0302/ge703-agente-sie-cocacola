# Resultado esperado frente a observado · PC3

**Ejecución:** 07/11/2026, Windows 11, Python 3.11.0, modo `reglas`, desde la carpeta `producto/`.
**Evidencia:** salidas completas en `pruebas/evidencia/` (rutas locales reemplazadas por `<raíz del proyecto>`).

## Caso normal · Bodega Don Lucho por TUALI (02/10/2026)

`python -m sie demo normal` → `pruebas/evidencia/02_demo_normal.txt`

| Verificación | Esperado | Observado | Resultado |
|---|---|---|---|
| Código de respuesta | OK-ACEPTADO | OK-ACEPTADO | Conforme |
| Solicitud e intento | SOL-003 · 1 | SOL-003 · 1 | Conforme |
| Pedido creado | PED-003 | PED-003 | Conforme |
| Escalamiento | ninguno | ninguno | Conforme |

Además, en la traza: C1–C5 = V V V V V; importe S/ 1,589.02; entrega prometida el 03/10/2026; OPP-003 `Ganada`; CLI-003 pasa de "No usa" a "Híbrido".

## Excepción · Comercial Los Olivos por teléfono (07/10 y 08/10/2026)

`python -m sie demo excepcion --acepta` → `pruebas/evidencia/03_demo_excepcion_acepta.txt`

| Verificación | Esperado | Observado | Resultado |
|---|---|---|---|
| Intento 1: código | ATP-PARCIAL | ATP-PARCIAL | Conforme |
| Intento 1: cotización enviada | COT-002-V02 | COT-002-V02 | Conforme |
| Intento 1: pedido creado | ninguno | ninguno | Conforme |
| Intento 1: promesa propuesta | 380 el 2026-10-09 + 220 el 2026-10-12 | 380 el 2026-10-09 + 220 el 2026-10-12 | Conforme |
| Intento 1: causa del faltante | OT-2026-0107 | OT-2026-0107 | Conforme |
| Escala a | Preventista 2 | Preventista 2 | Conforme |
| Intento 2: código | OK-PROMESA-ALT | OK-PROMESA-ALT | Conforme |
| Intento 2: pedido creado | PED-002 | PED-002 | Conforme |

Además, en la traza: ATP 380 de 600 (sin la parada, 620); escalamiento ESC-SOL-002-1 con fecha límite 08/10/2026; PED-002 por S/ 13,287.74, prometido el 09/10 con revisión el 12/10. La bitácora completa del caso está en `pruebas/evidencia/05_bitacora_excepcion.txt`.

## Excepción rechazada por el cliente

`python -m sie demo excepcion --rechaza` → `pruebas/evidencia/04_demo_excepcion_rechaza.txt`: las 6 verificaciones del intento 1 y "Tras el rechazo: pedido creado = ninguno" (**7 de 7 conformes**). No se envía EV-05.

## Pruebas automáticas

`python -m pytest pruebas -v` → `pruebas/evidencia/06_pytest.txt`: **85 de 85 pasan**. Entre ellas:

- los 12 intentos del EP reproducidos con sus códigos;
- los 9 pedidos idénticos al EP al céntimo;
- las respuestas iguales a los mensajes de ejemplo del contrato;
- los controles de permisos;
- la bitácora sin datos personales;
- el ZIP verificado desde una copia extraída.

## Cálculo a mano (Gianmarco Leandro)

Pendiente: resultados esperados calculados a mano en `pruebas/CASOS.csv` y su comparación con lo observado (ver `arquitectura/ROLES_EQUIPO.md`).
