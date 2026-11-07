# Matriz de trazabilidad · v3.0

T01–T25 vienen del PC1, T26–T55 de la PC2 y T56–T70 se agregan en el EP. Archivo completo y filtrable: `MATRIZ_TRAZABILIDAD.csv`.

## Agregadas en el EP

| ID | Afirmación | Fuente | Tipo | Fecha | Dónde se usa | Entrega |
|---|---|---|---|---|---|---|
| T56 | ACL declara más de 370 mil clientes; la misma página los llama también puntos de venta | F01 (acceso 23/10/2026) | HECHO | 23/10/2026 | Reto de negocio; panel momento 1 | EP |
| T57 | Unos 200 mil bodegueros usan TUALI, casi 4 de cada 10 bodegas del país (base ~535 mil) | F03 (acceso 23/10/2026) | HECHO | 23/10/2026 | Reto de negocio; cierra pendiente PC2 v2.1 | EP |
| T58 | Cerca del 46% de los clientes de ACL aún no usa TUALI (200 mil / 370 mil) | Cálculo del equipo con F01 y F03 | SUPUESTO | 23/10/2026 | Reto de negocio; límite del momento 1 | EP |
| T59 | Uso de TUALI por pedido y proporción de pedidos telefónicos en ACL | Equipo | PENDIENTE | 23/10/2026 | Backlog B18, B23 | EP |
| T60 | Decisión: todo pedido de TUALI, preventa o teléfono entra a ECC por el contrato I8 con C1–C5 | Equipo | DECISIÓN | 23/10/2026 | 05_arquitectura; R8 | EP |
| T61 | El pedido telefónico se registra en el CRM con canal_origen = Teléfono | Equipo | SUPUESTO | 23/10/2026 | R8; Solicitudes_pedido | EP |
| T62 | Las validaciones C1–C5 no dependen del canal de origen: 12 de 12 conformes en TUALI, preventa y teléfono | 10_pruebas/RESULTADO_VALIDACION.txt §8 | HECHO (evidencia del equipo) | 23/10/2026 | Panel momento 4 | EP |
| T63 | Escenario normal EP-N: esperado = observado en 6 de 6 verificaciones | Validador §9 | HECHO (datos sintéticos) | 23/10/2026 | 10_pruebas/PRUEBA_EP.md | EP |
| T64 | Excepción EP-X: esperado = observado en 11 de 11 verificaciones; ATP 380 recalculado | Validador §4 y §9 | HECHO (datos sintéticos) | 23/10/2026 | 10_pruebas/PRUEBA_EP.md | EP |
| T65 | El pedido confirmado consume ATP y el faltante genera el requerimiento que APO/MRP convierte en compra | Lógica estándar ERP; I2 del PC1 | SUPUESTO | 23/10/2026 | 08_procesos/MAPA_O2C_P2P.md | EP |
| T66 | Insumos de la reposición: concentrado, preformas PET, azúcar, CO₂ | Avance S5 (S2) | SUPUESTO | 23/10/2026 | Mapa O2C–P2P | EP |
| T67 | Controles P2P: presupuesto y proveedor habilitado, recepción con tolerancias, tres vías y doble autorización | Avance S5 · matriz P2P (S07); C07 | HECHO (curso) / SUPUESTO (ACL) | 23/10/2026 | Mapa O2C–P2P | EP |
| T68 | ECC: mantenimiento principal hasta fines de 2027; extendido opcional 2028–2030 | F16 (acceso 23/10/2026) | HECHO | 23/10/2026 | Arquitectura v3.0; riesgos aceptados | EP |
| T69 | Piloto de 8 semanas en el CD Lima Norte como condición de aprobación | Equipo | SUPUESTO | 23/10/2026 | Recomendación final | EP |
| T70 | Claude se utilizó como apoyo en el EP y su salida fue revisada por el equipo | 06_ia_etica/DECLARACION_IA.md | HECHO | 23/10/2026 | Uso de IA | EP |

## Resumen por tipo (T01–T70)

| Tipo | Afirmaciones |
|---|---|
| HECHO | 40 |
| SUPUESTO | 16 |
| PENDIENTE | 10 |
| DECISIÓN | 4 |
