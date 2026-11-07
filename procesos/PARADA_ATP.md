# De la parada de mantenimiento a la promesa al cliente

Puente entre la demo del agente y el informe de la PC3 (activos, mantenimiento y cadena de suministro I). **Todos los datos de la parada son sintéticos.**

## Cadena causal

| Eslabón | Dato | Dónde está |
|---|---|---|
| 1. Activo crítico | ACT-LLN-01, línea de llenado PET 500 ml, planta Lima (ALM-002), criticidad A | `datos/seed/activos.csv` |
| 2. Mantenimiento | OT-2026-0107, preventivo mayor planificado, del 03/10 06:00 al 07/10 06:00: 96 h | `datos/seed/ordenes_trabajo.csv` |
| 3. Capacidad perdida | 60 paquetes/día de PRD-001 asignados al CD × 4 días = 240 paquetes | `activos.capacidad_paq_dia` |
| 4. Reposición afectada | Lote REP-2026-041 de 240 paquetes: previsto en el CD el 06/10, reprogramado al 12/10 | `datos/seed/plan_reposicion.csv` |
| 5. Disponibilidad (ATP) | Al 07/10: 402 físicos − 22 reservados = 380 (sin la parada habría 380 + 240 = 620) | `erp/atp.py`, `erp/causas.py` |
| 6. Excepción | Los Olivos pide 600 → C5 falla → `ATP-PARCIAL` | `erp/reglas.py` |
| 7. Promesa al cliente | 380 el 09/10 desde el CD + 220 el 12/10 con la reposición; decide Preventista 2 con el cliente | `erp/promesa.py`, agente comercial |
| 8. Pedido | Con la aceptación (EV-05): `OK-PROMESA-ALT`, PED-002 | `erp/servicio.py` |

Se reproduce con `cd producto` y `python -m sie demo excepcion`. La bitácora muestra la entrada "causa del faltante" con la OT.

## Indicadores para el informe

| Indicador | Cálculo | Valor |
|---|---|---|
| Disponibilidad de ACT-LLN-01 en octubre | (744 h − 96 h) / 744 h | 87,1 % |
| Capacidad perdida | 4 días × 60 paquetes | 240 paquetes de PRD-001 |
| ATP de PRD-001 al 07/10 | Con y sin la parada | 380 frente a 620 |
| Nivel de servicio de PED-002 en la fecha prometida | 380 / 600 | 63,3 % |
| Demora del faltante | 09/10 frente a 12/10 | 3 días (220 paquetes) |

## Decisión que sustenta

La promoción CAMP-002 se vendió sin mirar una parada planificada: es la hipótesis H1 del PC1 (promociones desincronizadas de la planificación y la disponibilidad). El contrato I8 lo contiene, porque el ERP no promete lo que no hay y la persona responsable decide con el cliente. Para el informe, la decisión de fondo es coordinar el calendario de mantenimiento con el de promociones (S&OP): si la OT se hubiera conocido al cotizar, la promesa habría salido escalonada desde el inicio.
