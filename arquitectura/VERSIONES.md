# Versiones de la arquitectura

| Versión | Fecha | Entrega | Qué cambió | Evidencia |
|---|---|---|---|---|
| v1.0 | 25/09/2026 | PC1 | SAP ECC/APO como backbone; Anaplan, AC Móvil/TUALI, WMS/TMS; interfaces I1–I7; hipótesis H1 | `docs/antecedentes/repo_ep_v3/01_evidencias/02_PC1_G2_Entregable_Final.pdf` |
| v2.0 · v2.1 | 11 y 16/10/2026 | PC2 | SAP Sales Cloud (CRM) y contrato I8 v1.0: EV-01 a EV-07, C1–C5, nueve códigos; I8, I9, I10 | `docs/antecedentes/repo_ep_v3/05_arquitectura/` |
| v3.0 | 23/10/2026 | EP | "Un pedido, un contrato, tres canales"; `canal_origen`; mapa O2C–P2P; contrato v1.1 | `docs/antecedentes/repo_ep_v3/` |
| **v4.0** | **07/11/2026** | **PC3** | **Agente SIE: orquestador y agente comercial sobre el contrato I8 v1.2; ERP y CRM simulados en SQLite; modos reglas y llm; bitácora; parada de mantenimiento como causa del ATP** | `arquitectura/PLAN_PC3.md`, ADR-001 a ADR-006 |
| v5.0 | semanas 12–13 | — | Agentes de cadena de suministro y logística (reposición, inventario, almacén, transporte, entrega) | Por hacer |
| v6.0 | 04/12/2026 | PC4 | Agentes de finanzas operativas (factura, cuentas por cobrar y por pagar, conciliación) con los mismos datos | Por hacer |
| v7.0 | Examen final | EF | Integración de punta a punta, de ventas a finanzas operativas | Por hacer |

## Lo que se mantiene en v4.0

- SAP ECC sigue siendo el único sistema que compromete: en el Agente SIE, solo el ERP simulado crea pedidos (ADR-003).
- Contrato I8: mismas validaciones C1–C5, mismo orden, mismos nueve códigos e idempotencia.
- Datos del EP sin cambios de valor; se cargan por fecha de corte (ADR-004).
