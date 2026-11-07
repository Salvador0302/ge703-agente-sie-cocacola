# Registro de cambios de la arquitectura desde el PC1

| Versión | Fecha | Qué cambió | Por qué | Evidencia |
|---|---|---|---|---|
| PC1 · v1.0 | 25/09/2026 | SAP ECC/APO como backbone; Anaplan (RGM), AC Móvil/TUALI y WMS/TMS; interfaces I1–I7; hipótesis H1 | Continuidad con SAP en uso (criterio C1), escala nacional (6 plantas, +370 mil clientes) | `01_evidencias/02_PC1_G2_Entregable_Final.pdf` |
| Avance S5 · v0.1 | 03/10/2026 | Macroprocesos de ACL; SIPOC O2C; matriz de eventos, datos y controles de O2C y P2P | Convertir la arquitectura en procesos verificables | `01_evidencias/03_S5_Avance_Grupo2_Macroprocesos.pdf` |
| PC2 · v2.0 | 11/10/2026 | Se agrega SAP Sales Cloud (CRM) y el contrato I8 (EV-01 a EV-07, C1–C5, nueve códigos); nuevas I9 e I10; se modifican I3 (el CRM consulta, no calcula) e I4 (pasa por I8) | Separar relación (CRM) de compromiso (ERP); resolver el pendiente del PC1 "tratamiento de rechazos" | `01_evidencias/04_PC2_v2.0_*.pdf`, `05_PC2_v2.0_Contrato_*.pdf` |
| PC2 · v2.1 | 16/10/2026 | Se precisa el problema: clientes que piden por teléfono y no usan TUALI; TUALI, preventa y teléfono como canales que alimentan un mismo CRM | El reto es migrar a quien no suelta el teléfono, incluidos los híbridos | Entrega PC2 en Drive |
| **EP · v3.0** | **23/10/2026** | **El teléfono entra al CRM y los tres canales usan I8; `canal_origen` en EV-02; mapa O2C–P2P con la transacción que conecta; I4 e I9 actualizadas** | **Mismas reglas para todos los canales y medición de la migración; conectar el tramo comercial con abastecimiento** | `ARQUITECTURA_v3.md`, `../08_procesos/MAPA_O2C_P2P.md`, `../10_pruebas/RESULTADO_VALIDACION.txt` §8 |

## Lo que se mantiene sin cambios desde el PC1

- SAP ECC/APO como backbone y único sistema que compromete.
- Anaplan como capacidad especializada de RGM, no transaccional.
- I1, I2, I5, I6 e I7.
- Hipótesis H1: ahora es la excepción prioritaria del contrato (SOL-002).
- Pendientes B01–B09 del PC1 (salvo B10–B12, cerrados en v1.0).
