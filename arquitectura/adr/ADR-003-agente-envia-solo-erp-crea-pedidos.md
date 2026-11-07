# ADR-003 · El agente envía EV-02 y EV-05 por I8; solo el ERP simulado crea pedidos

**Estado:** aceptada · 07/11/2026 · decisión aprobada por Salvador Barrionuevo

## Contexto

- La sección 6 del contrato de la PC2 ("Agente CRM y orquestación", especificación **preliminar**) permitía al agente leer el CRM, consultar precio y ATP, y recomendar; prohibía "aprobar descuentos, cambiar maestros, crear pedidos o modificar compromisos".
- La lámina 26 de la S5 lo confirma: "Ningún agente aprueba pagos, cambia datos maestros, emite documentos ni modifica compromisos fuera de permisos, controles, bitácora y escalamiento humano".
- El EP fijó que SAP ECC es el único sistema que compromete precio, crédito, ATP y pedido.
- La PC3 pide que el agente reciba una solicitud y responda con un código del contrato. Para eso, alguien tiene que enviar EV-02.

## Decisión

1. El agente comercial **envía** EV-02 (solicitud inicial o reintento) por la interfaz I8, en nombre del canal que la capturó: el cliente en TUALI o el preventista en AC Móvil o por teléfono (R8).
2. El agente envía EV-05 **solo** después de un evento `decision_humana` con la aceptación registrada del cliente (ADR-005). Ningún texto de entrada puede confirmar una promesa.
3. **Solo el ERP simulado (`ServicioERP.recibir`) crea pedidos.** El agente no tiene acceso de escritura a `pedidos_cab` ni a `pedidos_det`, y el modo `llm` no recibe ninguna herramienta de envío.
4. Esto amplía la §6 de la PC2 (cierra el pendiente B22, "Especificar el agente CRM") y queda en el contrato I8 v1.2.

## Alternativas descartadas

- **El agente solo recomienda y el preventista envía:** más fiel a la §6 preliminar, pero agrega un paso humano también en el caso normal (TUALI), donde el cliente ya aceptó en la app.
- **El agente crea el pedido directamente:** rompe la frontera CRM–ERP del EP.

## Consecuencias

- Los permisos se verifican con pruebas: herramientas del LLM solo de lectura; sin `decision_humana` no hay EV-05; ningún pedido sin código OK del ERP.
- La ficha del agente (`agentes/comercial/FICHA.md`) declara estos permisos.
