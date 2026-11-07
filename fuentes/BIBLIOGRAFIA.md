# Bibliografía y fuentes

Convención heredada del EP: **HECHO** (fuente identificable) · **SUPUESTO** (decisión o dato didáctico) · **PENDIENTE** (por validar con ACL). El inventario completo del EP, con URL y fechas, está en `docs/antecedentes/repo_ep_v3/02_fuentes/FUENTES.csv`.

## Material del curso (UNI FIIS · GE703)

| ID | Material | Ubicación | Uso en la PC3 | Acceso |
|---|---|---|---|---|
| C01 | Semana 6 · CRM, marketing y ventas (presentación) | `docs/antecedentes/repo_ep_v3/01_evidencias/06_S6_Presentacion_CRM_Marketing_Ventas.pdf` | Frontera CRM–ERP (lám. 9), excepciones con objeto, causa, responsable y fecha límite (lám. 18), agentes por proceso y orquestador (lám. 21) | 10/10/2026 |
| C03 | Semana 6 · Plantilla de contrato CRM–ERP | `docs/antecedentes/repo_ep_v3/01_evidencias/08_S6_Plantilla_Contrato_CRM_ERP_original.pdf` | Estructura del contrato y del agente CRM | 10/10/2026 |
| C07 | Semana 5 · Macroprocesos ERP (presentación) | `docs/antecedentes/repo_ep_v3/01_evidencias/07_S5_Presentacion_Macroprocesos.pdf` | Límites de un agente: observa, recomienda y escala; no aprueba ni modifica compromisos (lám. 26) | 03/10/2026 |
| C08 | PC3 · Instrucciones y rúbricas | `docs/antecedentes/GE703_PC3_Instrucciones_y_Rubrica_Agente_SIE.pdf` | Alcance del informe y del paquete del agente, entregables y rúbricas | 07/11/2026 |
| C09 | PC4 · Instrucciones y rúbricas | `docs/antecedentes/GE703_PC4_Instrucciones_y_Rubrica_Agente_SIE.pdf` | Continuidad del diseño de datos hacia la PC4 | 07/11/2026 |
| C10 | Plantilla general del informe PC3 y PC4 | `docs/antecedentes/GE703_PC3_PC4_Plantilla_Informe_General_Agente_SIE.docx` | Estructura del informe | 07/11/2026 |

## Trabajo previo del grupo

| ID | Documento | Uso en la PC3 |
|---|---|---|
| S06 | PC1 G2 · Justificación de arquitectura ERP base (v1.0) | SAP ECC/APO como backbone; hipótesis H1 |
| S11 | PC2 G2 · contrato CRM–ERP v1.0 (`docs/antecedentes/GE703_PC2_G2_Contrato_CRM_ERP_ACL.docx`) | §6, especificación preliminar del agente CRM (ADR-003) |
| EP | Examen parcial G2 v3.0 (`docs/antecedentes/repo_ep_v3/`) | Contrato I8 v1.1, códigos, casos, modelo de datos sintéticos y validador |

## Fuentes públicas (heredadas del EP)

| ID | Fuente | Dato | Tipo | Acceso |
|---|---|---|---|---|
| F01 | Arca Continental Lindley, "Nosotros" · https://www.arcacontinentallindley.pe/nosotros/ | 6 plantas, más de 4,500 colaboradores y más de 370 mil clientes | HECHO | 19/09/2026 y 23/10/2026 |
| F03 | Arca Continental Lindley, "200 mil bodegueros incorporan herramientas digitales…" · https://www.arcacontinentallindley.pe/blog/200-mil-bodegueros-incorporan-herramientas-digitales-para-gestionar-pedidos-y-reposicion/ | TUALI: unos 200 mil bodegueros, casi 4 de cada 10 bodegas del país | HECHO | 19/09/2026 y 23/10/2026 |
| F15 | SAP Learning, flujo de pedido de SAP Sales Cloud a SAP S/4HANA · https://learning.sap.com/learning-journeys/discover-sap-sales-cloud/determining-the-sales-order-process-flow-from-sap-sales-cloud-to-sap-s4hana_a869a9b5-3b95-4282-9104-6d3a601e9b32 | IDs y estados que el ERP devuelve al CRM | HECHO | 11/10/2026 |
| F16 | SAP Support, Business Suite 7 maintenance strategy · https://support.sap.com/en/release-upgrade-maintenance/maintenance-information/maintenance-strategy/s4hana-business-suite7.html | Mantenimiento principal de ECC hasta fines de 2027 | HECHO | 25/09/2026 y 23/10/2026 |
| F17 | Ley 29733, Ley de Protección de Datos Personales · https://losandes.pe/wp-content/uploads/7-Ley-29733-Proteccion-de-datos-personales.pdf | Consentimiento y finalidad | HECHO | 11/10/2026 |
| S08 | SAP PRESS, "5 SAP Cloud for Customer features to use after integrating with SAP ERP" · https://blog.sap-press.com/5-sap-cloud-for-customer-features-to-use-after-integrating-with-sap-erp | Precio, ATP y crédito consultados al ERP desde el CRM | HECHO (secundaria) | 11/10/2026 |
| S10 | LP Derecho, Reglamento de la Ley 29733 (DS 016-2024-JUS) · https://lpderecho.pe/reglamento-ley-proteccion-datos-personales-decreto-supremo-016-2024-jus/ | Marco reglamentario del consentimiento | HECHO (secundaria) | 11/10/2026 |

## Supuestos propios de la PC3

La parada OT-2026-0107, la capacidad asignada (60 paquetes/día), los activos, la criticidad, el plazo de escalamiento y las reglas de fecha de entrega son **SUPUESTOS** del equipo, documentados en `datos/FUENTES_DATOS.md` y `procesos/REGLAS.md`. No hay datos de mantenimiento de ACL.
