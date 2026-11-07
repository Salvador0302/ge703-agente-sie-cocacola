# Contrato de transición CRM–ERP · ACL · v1.1 (EP, 23/10/2026)

**Proceso:** canal tradicional de Lima Norte, de la campaña y el lead hasta la solicitud de creación de pedido y sus respuestas.
**Sistemas:** SAP Sales Cloud (CRM) [SUPUESTO] → SAP Integration Suite [SUPUESTO] → SAP ECC (ERP, decisión del PC1).
**Cambio respecto de v1.0 (PC2):** EV-02 y EV-05 llevan `canal_origen`. Todo pedido, nazca en TUALI, en AC Móvil o en una llamada, pasa por este contrato con las mismas reglas.

## 1. Sistemas de registro

| Objeto | Sistema de registro | Lo que el otro sistema solo consulta |
|---|---|---|
| Campaña, lead, contacto, consentimiento, canal y adopción | CRM | — |
| Oportunidad y cotización versionada | CRM | Precio, descuento permitido, ATP y crédito (I3) |
| Solicitud de creación de pedido + intento | Bitácora de Integration Suite | Estado visible en el CRM |
| Cliente, crédito, producto, precio, regla de descuento | ERP | Contexto comercial en el CRM |
| Pedido, ATP, entrega, factura | ERP | Estado y documentos en el CRM (EV-03, EV-06, EV-07) |

## 2. Objetos y estados

| Objeto | Estados |
|---|---|
| Lead | Nuevo → En calificación → Calificado \| Descartado → Convertido |
| Oportunidad | Calificada → Propuesta → Ganada \| Perdida |
| Cotización (versionada) | Borrador → Pendiente de aprobación → Aceptada \| Rechazada \| Vencida |
| **Solicitud de creación de pedido** | **Enviada → Aceptada \| Rechazada \| Promesa alternativa → (EV-05) → Aceptada** |
| Pedido | Confirmado → Entrega parcial → Entregado → Cerrado |
| Cliente (adopción TUALI) | No usa → Híbrido → Digital |

## 3. Evento de transición y datos mínimos (EV-02)

`id_solicitud + intento` · `canal_origen` (nuevo) · `id_cotizacion + versión` · `id_oportunidad` · `id_cliente` y código ERP · dirección de entrega · líneas (producto, cantidad, `id_precio`, descuento, `id_regla_descuento`) · condición de pago · aprobador y fecha si el descuento supera 5 % · `acepta_entrega_parcial` · fecha de envío.

Detalle de los siete eventos en `eventos_contrato.csv`.

## 4. Controles del ERP, en orden

| # | Validación | Si falla | Riesgo que previene |
|---|---|---|---|
| C1 | Cliente activo y sincronizado | `CLI-NO-VALIDO` | Pedido sobre identidad ambigua o duplicada |
| C2 | Crédito no bloqueado; contado o total ≤ límite | `CRED-BLOQ` | Venta a cliente con deuda o sin respaldo |
| C3 | Precio de cada línea vigente en ECC a la fecha de envío | `PRECIO-NO-VIG` | Precio o promoción no autorizados |
| C4 | Descuento dentro de la regla del preventista o versión aprobada por el supervisor | `DESC-SIN-APROB` | Descuento fuera de política |
| C5 | Cantidad ≤ ATP del CD | `ATP-PARCIAL` (o `OK-PROMESA-ALT` si es confirmación con parcial aceptado) | Promesa inviable (H1) |
| — | Todo correcto | `OK-ACEPTADO` | — |

**Idempotencia (R7):** un reintento conserva el `id_solicitud` y aumenta `intento`. Nunca se crean dos pedidos para una misma cotización (`DUPLICADO` devuelve el pedido existente).

## 5. Respuestas del ERP

Toda respuesta trae código, causa, responsable y siguiente paso (`codigos_respuesta.csv`, 9 códigos). EV-03 acepta o rechaza; EV-04 propone una promesa alternativa con cantidad y fecha; EV-06 y EV-07 informan cambios de promesa, entrega y factura (detalle en la S7).

## 6. Decisiones con responsable humano

| Decisión | Responsable | Evidencia |
|---|---|---|
| Descuento mayor a 5 % y hasta 12 % | Supervisor de ventas | Aprobador y fecha en la versión de la cotización |
| Alta o fusión de cliente | Analista de datos maestros | Búsqueda por documento fiscal (EV-01) |
| Crédito bloqueado o excedido | Créditos y cobranzas | Estado de crédito y decisión registrada |
| Promesa alternativa | Planeamiento del CD propone; el cliente acepta por medio del preventista | EV-04 y EV-05 con evidencia de aceptación |

## 7. Indicadores con los datos de prueba (no son de ACL)

Aceptación al primer envío 70 % (7/10) · promesa alternativa 10 % (1/10) · 12 de 12 intentos conformes en tres canales. Línea base real pendiente (B18).

## 8. Mensajes de ejemplo

`ejemplos_mensajes/` contiene la solicitud y la respuesta de: EPN (SOL-003, normal por TUALI), EPX (SOL-002 intentos 1 y 2, excepción por teléfono), C1 (SOL-011, crédito bloqueado, teléfono) y C2 (SOL-005, precio no vigente y reintento, preventa). El formato es ilustrativo [SUPUESTO] y no reproduce la API de SAP.
