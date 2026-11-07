# Criterios de aceptación del incremento PC3

El incremento se acepta cuando se cumplen todos los criterios. Cada uno tiene una verificación ejecutable.

| # | Criterio | Cómo se verifica |
|---|---|---|
| CA-01 | El caso normal crea PED-003 con `OK-ACEPTADO` y sin escalamiento | `python -m sie demo normal` → 4 de 4 conformes |
| CA-02 | La excepción responde `ATP-PARCIAL` con 380 de 600, la causa OT-2026-0107 y la promesa 380 el 09/10 + 220 el 12/10, sin crear pedido | `python -m sie demo excepcion` → verificaciones del intento 1 |
| CA-03 | Solo con la aceptación registrada del Preventista 2 (EV-05) nace PED-002 con `OK-PROMESA-ALT`; si el cliente rechaza, no hay pedido | `demo excepcion --acepta` (8 de 8) y `--rechaza` (7 de 7) |
| CA-04 | Las reglas C1–C5 reproducen los 12 intentos del EP y sus pedidos al céntimo | `python -m pytest pruebas/aceptacion/test_bloque_b.py` |
| CA-05 | El agente no crea pedidos, no confirma promesas sin decisión humana y el LLM solo tiene herramientas de lectura | `python -m pytest pruebas/aceptacion/test_bloque_c.py` |
| CA-06 | Cada paso queda en la tabla y en el JSONL de la bitácora, sin datos personales | `test_bitacora_en_tabla_y_jsonl_sin_datos_personales` y `python -m sie bitacora --run <run>` |
| CA-07 | La demo funciona sin API key ni dependencias, en Windows con Python 3.11 | `python -m sie diagnostico` desde el ZIP extraído |
| CA-08 | El paquete de entrega se arma sin secretos ni archivos generados y se verifica solo | `python entrega/armar_zip.py --verificar` |
| CA-09 | La demo completa (normal + excepción) cabe en menos de 3 minutos | Ensayo cronometrado del 12/11/2026 |

Los resultados esperados calculados a mano para cada caso están en `pruebas/CASOS.csv` (los registra Gianmarco Leandro, ver `arquitectura/ROLES_EQUIPO.md`).
