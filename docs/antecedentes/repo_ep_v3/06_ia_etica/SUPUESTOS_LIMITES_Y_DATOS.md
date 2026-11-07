# Supuestos, límites y tratamiento de datos sensibles · EP

## Tratamiento de datos sensibles

| Dato | Tratamiento |
|---|---|
| Clientes y contactos | Sintéticos: nombres con "(sintético)" o "Contacto ficticio", correos `@example.com`, teléfonos `SIM-TEL-…` |
| Documentos fiscales | Sintéticos: `SIM-RUC10-…` y `SIM-RUC20-…`; no se usa ningún RUC real |
| Direcciones | Ficticias ("Jr. Simulado…"); los distritos reales solo como referencia geográfica |
| Consentimiento | Un lead sin consentimiento se descarta y no se conservan datos adicionales (LEAD-007), según la Ley 29733 (F17) y su reglamento (S10) |
| Bitácora del contrato | Guarda identificadores y códigos, no datos personales |
| Datos de ACL | No se usa información interna ni confidencial; solo cifras públicas con fuente y fecha de acceso |
| Registro del vocal | Solo nombre y grupo del compañero que formula la pregunta, en el formulario del panel (se guarda únicamente en el navegador de quien lo llena) |

## Supuestos vigentes

| ID | Supuesto | Dónde se valida |
|---|---|---|
| S-A | El CRM es SAP Sales Cloud y la integración usa SAP Integration Suite | B13, B14 |
| S-B | El preventista registra en el CRM los pedidos telefónicos (R8) | B24 |
| S-C | Umbrales de descuento: hasta 5 % preventista, 5–12 % supervisor, más de 12 % fuera de política | B15 |
| S-D | Bodega nueva al contado; mayorista con límite y plazo | B16 |
| S-E | Facturación por entrega | B17 |
| S-F | 46 % de clientes sin TUALI (cálculo 200 mil / 370 mil) | B23 |
| S-G | Reposición desde planta en 3 días; insumos del MRP | B25 |
| S-H | Piloto de 8 semanas en el CD Lima Norte | B26 |
| S-I | Precios, stocks, importes y fechas del modelo | Datos sintéticos; no se validan |

## Límites del EP

- El alcance llega hasta la solicitud de creación de pedido y sus respuestas (sesión 6). Pedido operativo, entrega, facturación y posventa son continuidad.
- La prueba es de escritorio: no ejecuta interfaces reales ni accede a sistemas de ACL.
- P2P se representa a nivel de mapa para mostrar la transacción que lo conecta con O2C.
- Las interfaces I1–I10 son una arquitectura lógica propuesta, no un inventario productivo.
- La recomendación es académica: no adjudica licencias, presupuesto ni partner.
- No se diseña ni evalúa un agente comercial.

## Propiedad intelectual

- Las marcas (Coca-Cola, Inca Kola, Fanta, Powerade, San Luis, Frugos del Valle, TUALI, SAP, Anaplan) se usan solo para identificación académica. El panel no usa logotipos.
- Los diagramas y el panel son elaboración propia del equipo.
- Los materiales del curso en `01_evidencias/` pertenecen a la UNI FIIS (GE703) y se incluyen solo para revisión académica.
