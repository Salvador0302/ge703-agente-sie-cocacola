# Guion del comité de decisión ERP · 15 minutos

Cada intervención dice tres cosas: **qué decisión defiendo, con qué evidencia y qué límite reconozco**. El guion sirve para ensayar; en el comité se explica con el panel, sin leer. Ritmo de referencia: unas 130 palabras por minuto.

| Min | Momento | Responsable | Panel |
|---|---|---|---|
| 0–1 | Decisión solicitada | Salvador Barrionuevo | Tecla 1 |
| 1–4 | Arquitectura base | Salvador Barrionuevo | Tecla 2 |
| 4–6 | Recorrido O2C | José Cornejo | Tecla 3 |
| 6–9 | Contrato CRM–ERP | Gianmarco Leandro | Tecla 4 |
| 9–11 | Escenario de quiebre | José Cornejo | Tecla 5 |
| 11–14 | Recomendación final | David Urbano | Tecla 6 |
| 14–15 | Pregunta y respuesta | Vocal invitado y vocero (los designa el docente) | Tecla 7 |

---

## 1 · Decisión solicitada · 0–1′ · Salvador

Buenos días. Somos el grupo 2: Coca-Cola, a través de Arca Continental Lindley.

El reto: ACL tiene más de 370 mil clientes y unos 200 mil ya usan TUALI. Cerca del 46 % sigue pidiendo por teléfono o al preventista, donde precio, stock y crédito se confirman a mano y la promesa sale sin mirar el stock. Es la hipótesis H1 de nuestro PC1.

Pedimos aprobar **un pedido, un contrato, tres canales**: venga de TUALI, de preventa o de una llamada, todo pedido entra a SAP ECC por el mismo contrato, con cinco validaciones y una respuesta con código. TUALI queda como canal preferente.

Éxito es que ningún pedido se cree sin validar, ninguna promesa supere el stock y el canal no cambie el resultado. En la prueba: 12 de 12.

---

## 2 · Arquitectura base · 1–4′ · Salvador

Esta es la arquitectura v3.0. En gris está lo que viene del PC1: SAP ECC con APO como backbone, Anaplan para revenue management, AC Móvil y TUALI como canales, y WMS/TMS para la logística.

En la PC2 agregamos el CRM, SAP Sales Cloud. Lo marcamos como supuesto porque no hay evidencia pública del CRM real de ACL. El CRM registra la relación: campaña, lead, oportunidad y cotización. Entre el CRM y el ERP está SAP Integration Suite, que lleva el contrato I8 y guarda una bitácora de cada solicitud.

El cambio de este examen está en granate: el teléfono deja de ser un canal fuera del sistema. Cuando un cliente llama, el preventista registra el pedido en el CRM y ese pedido pasa por el mismo contrato que uno de TUALI. Antes, con la interfaz I4, los pedidos de canal iban directo a ECC y el teléfono quedaba afuera.

¿Por qué esta arquitectura? Por tres razones. Primero, hay continuidad con SAP, que es el criterio C1 del PC1. Segundo, un solo sistema compromete: el CRM consulta precio, stock y crédito por I3, pero no reserva nada. Si el CRM o el canal pudieran prometer, volveríamos a tener promesas sin stock. Tercero, con el campo canal de origen sabemos quién pide por teléfono, quién es híbrido y quién ya es digital, y así la migración a TUALI se puede dirigir y medir.

En la tabla está el registro de cambios: v1.0 en el PC1, v2.0 y v2.1 en la PC2, y v3.0 ahora.

El límite que reconozco es que no sabemos qué CRM ni qué versión de SAP usa ACL hoy, y que ECC tiene mantenimiento principal hasta fines de 2027. Por eso elegimos un CRM que también se integra con S/4HANA: el contrato no cambia si ACL migra.

Le paso la palabra a José, que recorre una venta real del modelo.

---

## 3 · Recorrido O2C · 4–6′ · José

Este es el mapa integrado de O2C y P2P. Arriba está el hilo de Bodega Don Lucho, un cliente que pedía por teléfono todas las semanas.

La campaña CAMP-004, "Pásate a TUALI", le ofrece 2 % en su primer pedido por la app. El 30 de setiembre el preventista lo visita, le hace una demostración y el cliente acepta probar. Ese es el lead LEAD-013, y se califica porque está en la ruta, tiene smartphone y dio consentimiento para recibir mensajes. Luego vienen la oportunidad OPP-003 y la cotización COT-003-V01: 65 paquetes con 5 % de descuento, que es 3 % de la promoción más 2 % del bono. Está dentro del límite del preventista, así que no necesita aprobación. El cliente la acepta en TUALI, sin llamada.

Aquí está la frontera: la cotización no reserva stock. El CRM manda la solicitud SOL-003 con canal de origen TUALI, el ERP pasa las cinco validaciones y responde OK-ACEPTADO con el pedido PED-003.

Ahora, ¿dónde conecta con P2P? En el pedido confirmado, porque consume el stock disponible del centro de distribución. Cuando falta, como en el caso que veremos después, APO planifica la reposición y el MRP genera la necesidad de compra de insumos: concentrado, preformas, azúcar. Ahí empieza P2P, con su solicitud de compra, orden, recepción, factura y pago. También se encuentran en tesorería, donde se concilian el cobro y el pago.

El límite: entrega, factura y cobro aparecen solo como continuidad, y P2P está a nivel de mapa con insumos supuestos.

Gianmarco explica las reglas del contrato que acabamos de usar.

---

## 4 · Contrato CRM–ERP · 6–9′ · Gianmarco

El contrato define cómo una cotización se convierte en pedido, y lo explico en cuatro partes.

**Sistemas de registro.** Campaña, lead, oportunidad, cotización y canal viven en el CRM. Cliente, crédito, precio, descuento, stock y pedido viven en el ERP. La solicitud y sus intentos se guardan en la bitácora de Integration Suite.

**Estados.** La solicitud nace como Enviada y termina Aceptada, Rechazada o en Promesa alternativa. Si es promesa, solo pasa a Aceptada cuando el cliente confirma.

**Datos mínimos del evento de transición, EV-02.** Lleva el identificador de la solicitud y el número de intento, el canal de origen, que es lo nuevo de esta versión, la cotización con su versión, el cliente, la dirección, las líneas con producto, cantidad, precio y regla de descuento, la condición de pago, el aprobador si el descuento pasa de 5 % y si el cliente acepta una entrega parcial.

**Controles.** El ERP valida en este orden. C1: cliente activo y sincronizado. C2: crédito no bloqueado y dentro del límite. C3: precio vigente a la fecha de envío. C4: descuento dentro de la regla o aprobado. C5: cantidad dentro del stock disponible. El primer control que falla define el código de respuesta. Hay nueve códigos y cada uno dice quién corrige y cuál es el siguiente paso: un crédito bloqueado va a Créditos y Cobranzas y un precio no vigente va al analista de precios.

Para evitar pedidos duplicados, cada reintento conserva el mismo identificador y sube el número de intento. Nunca hay dos pedidos para una misma cotización.

La prueba lo confirma: 12 intentos en tres canales, 12 conformes, y el canal no cambia ninguna regla.

El límite: el formato del mensaje es ilustrativo, no es la API de SAP, y los umbrales de 5 y 12 % son supuestos que hay que validar con ACL.

José vuelve con la excepción que más nos importa.

---

## 5 · Escenario de quiebre · 9–11′ · José

La excepción prioritaria es la hipótesis H1: una promoción sin stock suficiente.

Comercial Los Olivos es un mayorista híbrido: usa TUALI para lo pequeño y llama para lo grande. El 6 de octubre llama y pide 600 paquetes de Inca Kola de la promoción, con 10 % de descuento. El preventista lo registra en el CRM. El supervisor rechaza el 10 % y aprueba 8 % en la versión 2. La versión con 10 % nunca llega al ERP.

El 7 de octubre sale la solicitud. Las validaciones de cliente, crédito, precio y descuento pasan, pero falla el stock: hay 380 de 600. Lo calculamos desde los movimientos de inventario: 402 en físico menos 22 reservados. El ERP no confirma ni rechaza en silencio. Responde ATP-PARCIAL y propone 380 para el 9 de octubre y 220 para el 12, con reposición desde planta.

**Se detecta** en el ERP, con C5, al momento del envío y no en la llamada. **Se contiene** porque en el primer intento no se crea ningún pedido y la entrega parcial exige que el cliente la acepte. **Se escala** así: Planeamiento del CD propone la promesa, el preventista la gestiona y, si la reposición se atrasa, el evento EV-06 abre un caso de atención.

El cliente acepta, el segundo intento responde OK-PROMESA-ALT y nace el pedido PED-002. En el validador, el esperado coincide con el observado en las 11 verificaciones.

El límite: es una prueba de escritorio con datos sintéticos, y la fecha de reposición es un supuesto.

David presenta la recomendación del comité.

---

## 6 · Recomendación final · 11–14′ · David

Nuestra recomendación es **aprobar con condiciones**.

La condición principal es un piloto en el CD Lima Norte, en el canal tradicional, durante 8 semanas, que es un supuesto nuestro. El teléfono no se elimina, pero todo pedido telefónico se registra en el CRM y pasa por el contrato. Antes de empezar se mide la línea base: qué porcentaje de pedidos llega por cada canal y cuánto tarda una cotización en convertirse en pedido confirmado.

**Riesgos que aceptamos**, cada uno con su respuesta:
- No conocemos el CRM real de ACL. La frontera y el contrato no dependen del producto; si no es Sales Cloud, se ajusta I8.
- ECC sale de mantenimiento principal en 2027. El CRM elegido también se integra con S/4HANA y el contrato se conserva.
- La prueba es de escritorio. El validador es reproducible y el siguiente paso es un ambiente de prueba.
- Hay clientes que no quieren la app. Por eso no se obliga a nadie: la migración es por incentivo y el teléfono sigue con las mismas reglas.

**Pendientes priorizados:** confirmar el CRM real de ACL (B13); confirmar cómo entran hoy a SAP los pedidos de TUALI y AC Móvil (B14); confirmar la versión de SAP de ACL (B01); medir la línea base (B18); y validar las políticas reales de descuento y crédito (B15 y B16).

**Siguiente incremento:** en la semana 7 y la PC3 seguimos el pedido hasta la entrega y la factura, con la factura parcial de PED-002. Después vienen producción y MRP, donde la reposición de los 220 paquetes conecta con P2P. Con contratos ya probados se podrá diseñar un agente por proceso.

**Límites:** es una recomendación académica, sin licencias ni presupuesto, y no cubre la ejecución del pedido, la facturación ni la posventa. Las fuentes llevan fecha de acceso, y declaramos el uso de IA con validación del equipo.

Gracias. Quedamos atentos a la pregunta del vocal.

---

## 7 · Pregunta y respuesta · 14–15′ · Vocero

1. **Evidencia:** muestra en el panel el dato o la prueba que responde (teclas 1–6).
2. **Decisión:** di qué decisión se apoya en esa evidencia.
3. **Límite:** reconoce qué falta validar.

Ejemplo: "En el validador, la solicitud de Los Olivos da ATP-PARCIAL con 380 de 600. Por eso el ERP propone una promesa y el pedido solo nace con la aceptación del cliente. Reconocemos que es una prueba de escritorio con datos sintéticos."

Registra la pregunta y la respuesta en `REGISTRO_VOCAL.md` o en el momento 7 del panel.
