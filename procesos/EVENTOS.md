# Eventos

## Eventos del contrato I8 (v1.2)

| Evento | Dirección | En la PC3 | Quién lo produce en el Agente SIE |
|---|---|---|---|
| EV-01 Solicitar alta de cliente | CRM → ERP | No implementado (CLI-012 sigue pendiente de alta) | — |
| EV-02 Solicitar creación de pedido | CRM → ERP | Implementado | Agente comercial (`ConsultasCRM.construir_solicitud` + `ServicioERP.recibir`) |
| EV-03 Aceptar o rechazar pedido | ERP → CRM | Implementado | ERP simulado |
| EV-04 Proponer promesa alternativa | ERP → CRM | Implementado | ERP simulado (`promesa.proponer`) |
| EV-05 Confirmar promesa | CRM → ERP | Implementado, con el bloque `aceptacion` (v1.2) | Agente comercial, solo tras `decision_humana` |
| EV-06 Notificar cambio de promesa | ERP → CRM | Previsto (semanas 12–13, si la reposición de 220 se atrasa) | Agente de cadena de suministro |
| EV-07 Notificar entrega / factura | ERP → CRM | Previsto (semana 13 y PC4: ENT-002, FAC-002) | Agentes de logística y finanzas operativas |

## Eventos del orquestador

| Tipo | Agente | Estado |
|---|---|---|
| `pedido` | comercial | Implementado |
| `decision_humana` | comercial | Implementado |
| `abastecimiento`, `reposicion`, `inventario` | cadena_suministro | Se registran como "no implementado aún" |
| `entrega`, `transporte` | logistica | Se registran como "no implementado aún" |
| `factura`, `cobro`, `pago_proveedor`, `conciliacion` | finanzas_operativas | Se registran como "no implementado aún" |
| `indicadores` | ceo | Se registra como "no implementado aún" (por confirmar con el docente) |

## Estados de la solicitud

`Enviada → Aceptada | Rechazada | Promesa alternativa → (EV-05) → Aceptada`. El pedido nace `Confirmado`; los estados `Entrega parcial`, `Entregado` y `Cerrado` los producirán los agentes de logística.
