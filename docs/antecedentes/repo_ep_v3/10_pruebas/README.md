# Pruebas · v3.0

| Archivo | Contenido |
|---|---|
| `PRUEBA_EP.md` | Escenario normal (EP-N) y excepción prioritaria (EP-X) con resultado esperado, observado, evidencia y escalamiento |
| `CASOS_PRUEBA.csv` | EP-N, EP-X y cinco casos complementarios, con canal de origen |
| `validar_contrato.py` | Validador independiente (Python 3.8+, solo biblioteca estándar) |
| `RESULTADO_VALIDACION.txt` | Salida del validador al 23/10/2026 |

```bash
python 10_pruebas/validar_contrato.py
```

| Sección | Qué verifica |
|---|---|
| 1 | C1–C5 y código esperado de los 12 intentos; compara Python, bitácora y Excel |
| 2 | Integridad referencial de las 40 relaciones |
| 3 | Reglas R1, R2, R3 y R7 |
| 4 | ATP de PRD-001 al 07/10 desde movimientos y reservas (402 − 22 = 380) |
| 5 | Base imponible de 30 documentos recalculada desde sus líneas |
| 6 | Cadenas de trazabilidad del escenario normal, la excepción y la bodega nueva |
| 7 | Indicadores con datos de prueba |
| 8 | Mismo contrato, tres canales; controles transversales |
| 9 | Prueba del EP: esperado vs. observado |

Diseño y ejecución de la prueba: Cornejo Palomino, José Julián. Validador y consolidación: Barrionuevo Gutierrez, Salvador Jhou.
