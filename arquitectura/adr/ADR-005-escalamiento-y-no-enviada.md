# ADR-005 · Una sola confirmación humana (EV-05) y resultado interno NO-ENVIADA

**Estado:** aceptada · 07/11/2026 · decisión aprobada por Salvador Barrionuevo

## Contexto

- El contrato asigna la promesa alternativa a dos personas: Planeamiento del CD la propone y el cliente la acepta por medio del preventista.
- La demo dura menos de 3 minutos dentro de una exposición de 10.
- El catálogo de nueve códigos no tiene uno para "la cotización no se puede enviar" (vencida, rechazada o con una cantidad distinta a la pedida). En el EP ese caso era un control preventivo del CRM: la V01 con 10 % "no se envió".

## Decisión

1. **Una sola pausa humana en la demo:** Preventista 2 registra la aceptación del cliente con evidencia (`ACEP-SOL-002-2`), lo que habilita EV-05. La propuesta sale del plan de reposición y figura con Planeamiento CD como responsable (`Planeamiento CD → Preventista 2`).
2. **Todo escalamiento** guarda objeto, causa, estado, responsable y fecha límite (S6, lámina 18). Plazo: un día de negocio (SUPUESTO).
3. **`NO-ENVIADA` (regla R2)** es un resultado interno del agente: no hay EV-02, no hay código del contrato y se escala al responsable (Supervisor de ventas si el descuento fue rechazado; si no, el ejecutivo de la cuenta). El catálogo del contrato sigue con nueve códigos.

## Consecuencias

- La excepción se demuestra completa (detecta, contiene, escala y confirma) en dos pasos.
- Si el cliente rechaza, el escalamiento se cierra sin pedido y queda en la bitácora.
