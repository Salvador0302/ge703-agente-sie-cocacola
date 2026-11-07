# Reglas del agente comercial y tabla de decisiones

Las reglas R1–R9 vienen del EP (`docs/antecedentes/repo_ep_v3/08_procesos/REGLAS_NEGOCIO.csv`). P1–P3 y C5b son precisiones de la PC3.

## Reglas de negocio

| ID | Regla | Dónde se aplica en el Agente SIE |
|---|---|---|
| R1 | Calificación de lead (ruta, RUC, duplicado, consentimiento) | Fuera del alcance del agente comercial de la PC3 (datos del seed) |
| R2 | Solo una versión Aceptada y vigente genera solicitud; la cantidad pedida debe ser la cotizada | Agente: si no se cumple → `NO-ENVIADA` sin EV-02 (ADR-005) |
| R3 | Descuento hasta 5 % el preventista; 5–12 % con aprobación del supervisor; más de 12 % fuera de política | ERP, control C4 |
| R4 | Solo precios de lista vigentes en el ERP | ERP, control C3 |
| R5 | Bodega al contado; mayorista con límite; crédito bloqueado o excedido → rechazo | ERP, control C2 |
| R6 | Si el ATP no cubre, el ERP propone cantidad y fecha; el parcial exige aceptación del cliente | ERP (C5 → EV-04) y agente (escalamiento y EV-05) |
| R7 | Idempotencia: un reintento conserva el ID y sube el intento; nunca dos pedidos por cotización | ERP (P2) y agente (cálculo del intento) |
| R8 | Todo pedido telefónico se registra en el CRM con su canal y entra por I8 | El canal viene del evento y no cambia ninguna regla |
| R9 | Tras cada pedido se recalcula la adopción de TUALI | CRM simulado: `No usa` → `Híbrido` con el primer pedido por TUALI |

## Tabla de decisiones

| # | Condición | Resultado | Responsable | ¿Pedido? |
|---|---|---|---|---|
| P3 | No se identifica cliente o cotización, o la cotización no es del cliente | `NO-ENVIADA` | Preventista o ejecutivo de la cuenta | No |
| R2 | Cotización no aceptada, vencida o con otra cantidad | `NO-ENVIADA` | Supervisor de ventas si el descuento fue rechazado; si no, ejecutivo | No |
| P1 | Falta un dato obligatorio del mensaje | `DATO-OBLIG` | Preventista | No |
| P2 | El mismo `id_solicitud + intento` ya se procesó | Misma respuesta | — | No crea otro |
| P2 | La solicitud o la cotización ya tiene pedido | `DUPLICADO` con el pedido existente | Soporte de integración | No crea otro |
| C1 | Cliente no activo, no sincronizado o sin código ERP | `CLI-NO-VALIDO` | Analista de datos maestros | No |
| C2 | Crédito bloqueado o total sobre el límite | `CRED-BLOQ` | Créditos y cobranzas | No |
| C3 | Alguna línea sin precio vigente | `PRECIO-NO-VIG` | Analista de precios RGM | No |
| C4 | Más de 5 % sin aprobación registrada, o más de 12 % | `DESC-SIN-APROB` | Supervisor de ventas | No |
| C5 | Alguna línea supera el ATP (solicitud inicial o reintento) | `ATP-PARCIAL` + EV-04 | Planeamiento CD → ejecutivo de la cuenta | No |
| C5b | Falta ATP, pero llega EV-05 con aceptación registrada y ATP ≥ tramo 1 | `OK-PROMESA-ALT` | Ejecutivo de la cuenta | Sí |
| OK | Todo pasa | `OK-ACEPTADO` | Ejecutivo de la cuenta | Sí |

Orden: P3 y R2 en el agente (antes de enviar); P1 y P2 en la capa I8; C1 → C5 en el ERP, donde el primer control que falla define el código. El orden de P1–P3 antes de C1 no está en el contrato del EP: es un supuesto del equipo.

## Supuestos numéricos

| Supuesto | Valor | Fuente |
|---|---|---|
| Umbrales de descuento | 5 % y 12 % | R3 del EP (pendiente B15) |
| Plazo de un escalamiento | 1 día de negocio | ADR-005 |
| Fecha de entrega | Siguiente día dentro de la ventana de la dirección | EP, §5 del contrato de la PC2 |
| Confirmación del cliente en una promesa alternativa | 1 día antes del tramo 1 | Plan PC3, §6 |
| Redondeo de importes | Mitad hacia arriba, a céntimos (como Excel) | Modelo del EP (incidencia I-07) |
