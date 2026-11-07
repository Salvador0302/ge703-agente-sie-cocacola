# Contrato de transición CRM–ERP (I8) · v1.2 (PC3, 07/11/2026)

**Base:** contrato v1.1 del EP (`docs/antecedentes/repo_ep_v3/05_arquitectura/CONTRATO_CRM_ERP.md`).
**Implementación:** `producto/sie/contrato.py` (tipos, catálogo y serialización JSON).
**Formato de mensaje:** ilustrativo [SUPUESTO]; no reproduce la API de SAP. Datos sintéticos.

## Qué cambia respecto de v1.1

| Cambio | Motivo | Decisión |
|---|---|---|
| EV-05 agrega el bloque `aceptacion` (acepta, registrada_por, fecha, medio, evidencia, tramos aceptados) | `eventos_contrato.csv` exige "evidencia de aceptación" en EV-05, pero el ejemplo del EP no la traía | Incidencia I-05 del plan |
| La respuesta informa `pedido.estado_pedido` (estado al responder) | El EP usaba `estado_pedido_al_corte` (estado al 11/10). Al responder, el pedido nace `Confirmado` | `desde_dict` acepta ambos nombres |
| El agente comercial puede enviar EV-02 y EV-05 por I8 | La §6 de la PC2 (preliminar) solo permitía lectura y recomendación | ADR-003 |
| Resultado interno `NO-ENVIADA` cuando la cotización no es solicitable (R2) | El catálogo no tiene un código para ese caso y la solicitud nunca llega al ERP | ADR-005; el catálogo sigue con nueve códigos |

Las validaciones C1–C5, su orden, los nueve códigos y la idempotencia por `id_solicitud + intento` **no cambian**.

## Archivos

| Archivo | Contenido |
|---|---|
| `codigos_respuesta.csv` | Catálogo de los nueve códigos (copia del EP) |
| `eventos_contrato.csv` | EV-01 a EV-07 con datos mínimos, control y responsable (copia del EP) |
| `interfaces.csv` | Interfaces lógicas I1–I10 (copia del EP) |
| `ejemplos/*.json` | Seis solicitudes y seis respuestas del EP; `pruebas/unitarias/test_contrato.py` comprueba que `contrato.py` las lee y las vuelve a escribir sin pérdida |

## Datos obligatorios de EV-02 (control P1 → `DATO-OBLIG`)

`id_solicitud`, `intento` ≥ 1, `tipo_mensaje`, `canal_origen` (TUALI, Preventa o Teléfono), `fecha_envio`, `id_cotizacion` y `version_cotizacion`, `id_oportunidad`, `id_cliente`, `id_direccion_entrega`, `condicion_pago_dias`, `estado_descuento`, `acepta_entrega_parcial` y al menos una línea con producto, cantidad > 0, `id_precio`, `descuento_pct` e `id_regla_descuento`. EV-05 exige además el bloque `aceptacion` completo.

No se exigen en P1, porque los cubre otro control:

- `codigo_cliente_erp`: un cliente sin código ERP es `CLI-NO-VALIDO` (C1).
- `aprobador` y `fecha_aprobacion` cuando el descuento supera 5 %: su ausencia es `DESC-SIN-APROB` (C4).

## Convenciones de identificadores

La solicitud y el pedido heredan el número de la cotización, como en todos los casos del EP: `COT-003-V01 → SOL-003 → PED-003`. Un reintento conserva `id_solicitud` y aumenta `intento`.
