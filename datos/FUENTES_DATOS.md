# Fuentes de los datos de prueba

Todos los datos son **sintéticos**. Ninguna cifra, cliente, precio, stock, política o activo corresponde a ACL.

## Origen de cada archivo de `datos/seed/`

| Archivo | Origen | Corte | Tratamiento en la PC3 |
|---|---|---|---|
| 21 tablas del modelo (`campanas.csv` … `movimientos_inventario.csv`) | Modelo maestro del EP v3 (`docs/antecedentes/GE703_EP_G2_Modelo_CRM_ERP_ACL_v3.xlsx`), exportado a CSV en el EP; verificado celda por celda contra el Excel (0 diferencias en 4,113 celdas, 07/11/2026) | 11/10/2026 | Copia sin cambiar valores; solo el nombre del archivo pasa a minúsculas |
| `activos.csv` | Elaboración del equipo para la PC3 (plan, §5.3) | — | SINTÉTICO; base del informe de activos y mantenimiento |
| `ordenes_trabajo.csv` | Elaboración del equipo para la PC3 | — | SINTÉTICO; OT-2026-0107 explica el ATP reducido |
| `plan_reposicion.csv` | Elaboración del equipo para la PC3 | — | SINTÉTICO; lote de 240 paquetes reprogramado del 06/10 al 12/10 |

`Inventario_actual` (foto al 11/10) y `Prueba_contrato` (fórmulas del Excel) no se cargan en la base: el ATP se recalcula desde los movimientos y los pedidos, y la prueba del contrato la hace el código. Siguen disponibles en `docs/antecedentes/repo_ep_v3/09_datos/csv/` como referencia de las pruebas.

## Cómo se cargan

`producto/sie/db/seed.py` carga el estado del mundo antes de una fecha de corte (ADR-004): documentos del CRM con fecha ≤ corte, transacciones del ERP con fecha < corte, maestros y activos siempre. Al reiniciar la base se regenera desde estos archivos; `datos/sie.db` no se versiona.

## Supuestos de los datos nuevos

| Supuesto | Valor | Unidad o rango |
|---|---|---|
| Capacidad de ACT-LLN-01 asignada a PRD-001 para el CD Lima Norte | 60 | paquetes por día (escala didáctica del modelo, no la velocidad real de la línea) |
| Duración de la parada OT-2026-0107 | 96 | horas (03/10 06:00 a 07/10 06:00; la línea opera 24/7) |
| Capacidad perdida | 240 | paquetes (4 días × 60) |
| Traslado planta → CD | 3 | días (supuesto S-G del EP) |
| Liberación de calidad tras el arranque | hasta el 09/10 | fecha |
| Criticidad de los activos | A o B | escala A (crítica) a C |

Diccionario completo con unidad, rango observado en el seed y origen de cada columna: `datos/DICCIONARIO.csv`.
