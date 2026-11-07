# Backlog priorizado · v3.0

Validaciones que pueden cambiar o fortalecer la decisión del comité. B01–B12 vienen del PC1, B13–B22 de la PC2 y B23–B27 del EP.

## Top 5 para la recomendación final

| ID | Pendiente | Por qué condiciona la decisión |
|---|---|---|
| B13 | Confirmar el CRM real de ACL | Si no es SAP Sales Cloud, cambia el mecanismo técnico de I8 (no la frontera) |
| B14 | Cómo entran hoy a SAP los pedidos de TUALI y AC Móvil | Valida que el contrato único reemplaza algo existente y no duplica |
| B01 | Instancia y versión SAP de ACL Perú | Define si el backbone ECC/APO se mantiene o migra a S/4HANA |
| B18 | Línea base por canal y tiempos | Sin ella no se puede medir el éxito del piloto |
| B15·B16 | Políticas reales de descuento y crédito | Los umbrales 5 % / 12 % y el crédito por segmento son supuestos |

## Lista completa

| ID | Prioridad | Pendiente | Propósito | Responsable de validar | Estado | Origen |
|---|---|---|---|---|---|---|
| B01 | Crítica | Confirmar instancia y versión SAP actual en ACL Perú | Determinar si el backbone propuesto coincide con el landscape productivo real | Equipo ACL / TI | PENDIENTE | PC1 |
| B02 | Crítica | Inventariar interfaces actuales | Origen, destino, datos, protocolo, frecuencia, latencia, volumen, criticidad y responsable; ahora incluye I8–I10 | Arquitectura / TI | PENDIENTE | PC1 |
| B03 | Crítica | Obtener línea base del problema | OOS, fill rate, forecast vs. real, reprogramaciones y timestamps | Comercial / Supply Chain | PENDIENTE | PC1 |
| B04 | Alta | Confirmar gobierno local vs. corporativo | Definir qué decisiones son de ACL Perú y cuáles de Arca Continental | Patrocinio / TI | PENDIENTE | PC1 |
| B05 | Alta | Confirmar alcance actual de WMS/TMS y sistemas de planta | Evitar basarse en paisaje histórico | Logística / TI | PENDIENTE | PC1 |
| B06 | Alta | Validar requerimientos tributarios peruanos exactos | Confirmar SUNAT/PLE/PDT y demás obligaciones dentro del alcance | Finanzas / TI | PENDIENTE | PC1 |
| B07 | Media | Obtener presupuesto TI específico | Separarlo de la inversión corporativa de infraestructura | Finanzas / TI | PENDIENTE | PC1 |
| B08 | Media | Confirmar conectividad de las seis plantas | Disponibilidad y restricciones de red/integración | Infraestructura | PENDIENTE | PC1 |
| B09 | Media | Obtener volumen transaccional | Pedidos, facturas, inventario y usuarios concurrentes | TI / Operaciones | PENDIENTE | PC1 |
| B10 | Documental | Completar URL del repositorio en el entregable | Insertar enlace definitivo | Equipo | CERRADO (PC1 v1.0) | PC1 |
| B11 | Documental | Completar los dos expositores | Registrar nombres reales | Equipo | CERRADO (PC1 v1.0) | PC1 |
| B12 | Documental | Completar contribuciones verificables | Vincular cada aporte con archivo, revisión o prueba | Equipo | CERRADO (PC1 v1.0) | PC1 |
| B13 | Crítica | Confirmar el CRM real de ACL | Si no es SAP Sales Cloud, revisar frontera, I8, I9 y mecanismo técnico del contrato | Comercial / TI ACL | PENDIENTE | PC2 |
| B14 | Crítica | Confirmar cómo ingresan hoy a SAP los pedidos de TUALI y AC Móvil | Validar la decisión de un contrato único (I4 vía I8) y sus códigos de respuesta | TI / Integración | PENDIENTE | PC2 |
| B15 | Alta | Validar política real de descuentos por rol | Reemplazar los umbrales 5% / 12% (R3) por los de ACL | RGM / Ventas | PENDIENTE | PC2 |
| B16 | Alta | Validar política de crédito por segmento | Confirmar contado para bodega nueva y límites de mayoristas (R5) | Créditos y cobranzas | PENDIENTE | PC2 |
| B17 | Alta | Validar regla de facturación | Facturación por entrega vs. entrega completa en canal tradicional | Finanzas | PENDIENTE | PC2 |
| B18 | Alta | Medir línea base de los indicadores del contrato | Línea base de la decisión del EP: pedidos por canal (TUALI, preventa, teléfono), tiempo de cotización a pedido confirmado y aceptación al primer envío | Comercial / TI | PENDIENTE | PC2 |
| B19 | Media | Detallar EV-06 y EV-07 en la Semana 7 | Pedido operativo, entrega, facturación y posventa a partir de PED-002 y PED-009 | Equipo | PENDIENTE (S7–PC3) | PC2 |
| B20 | Documental | Registrar la revisión cruzada | El grupo no asistió a la S6; completar en S7 si el docente lo permite | Equipo | PENDIENTE (no se realizó en S6) | PC2 |
| B21 | Documental | Ensayo de los dos expositores | Salvador Barrionuevo y José Cornejo dominan decisiones, contrato, prueba y límites | Expositores | CERRADO (PC2 v2.1, 17/10) | PC2 |
| B22 | Media | Especificar el agente CRM | Desarrollar la sección 6 del contrato cuando el curso lo requiera | Equipo | PENDIENTE (unidad posterior) | PC2 |
| B23 | Alta | Medir la adopción real de TUALI por cliente | Reemplazar el cálculo del 46% por el uso por pedido y el segmento de clientes híbridos | Comercial / TI ACL | PENDIENTE | EP |
| B24 | Alta | Definir cómo registra el preventista un pedido telefónico en el CRM | Validar R8 en campo: tiempo de registro, datos mínimos y quién captura | Ventas / TI | PENDIENTE | EP |
| B25 | Media | Detallar P2P de insumos y su vínculo con APO/MRP | Confirmar insumos, proveedores (incluido TCCC) y responsables reales | Planeamiento / Compras | PENDIENTE (PC3–PC4) | EP |
| B26 | Media | Diseñar el piloto del contrato único en el CD Lima Norte | Alcance, duración, indicadores y criterio de salida del piloto | Equipo / patrocinio | PENDIENTE | EP |
| B27 | Documental | Registrar el vocal invitado, su pregunta y la respuesta del vocero | Completar 11_comite/REGISTRO_VOCAL.md después del comité | Vocero designado | PENDIENTE (24/10) | EP |
