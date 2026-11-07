# Brief · Bloque B · Datos y ERP simulado

**Responsable:** Gianmarco Leandro Ochoa · **Rama:** `bloque-b/datos-erp` · **Plazo:** lunes 09/11/2026, 23:59
**Por qué tú:** en el EP defendiste el contrato y los datos maestros. Este bloque convierte ese contrato en el único código que compromete pedidos.

## Qué entregas

| Archivo | Contenido |
|---|---|
| `datos/seed/*.csv` | Copia de los 21 CSV del EP (`docs/antecedentes/repo_ep_v3/09_datos/csv/`), con nombre de tabla en minúsculas (`clientes.csv`, `pedidos_det.csv`…), **sin cambiar valores**. Más `activos.csv`, `ordenes_trabajo.csv` y `plan_reposicion.csv` (sintéticos, plan §5.3) |
| `producto/sie/db/esquema.sql` | Todas las tablas: las del EP con sus columnas, claves primarias (`INDICE_MODELO.csv`) y foráneas (`RELACIONES.csv`), y las nuevas de `INTERFACES.md` §5 |
| `producto/sie/db/seed.py` | `crear_base` y `avanzar` (reemplaza el `NotImplementedError`) |
| `producto/sie/erp/atp.py`, `causas.py`, `reglas.py`, `promesa.py`, `servicio.py` | ERP simulado y capa I8 |
| `datos/DICCIONARIO.csv` | Diccionario del EP + columnas `unidad`, `rango` y `origen` (HECHO / SINTÉTICO / SUPUESTO) + tablas nuevas |
| `datos/FUENTES_DATOS.md`, `datos/DATOS_SENSIBLES.md` | Origen de cada tabla y tratamiento de datos sensibles (marcas "(sintético)", `example.com`, `SIM-…`) |
| `pruebas/INCIDENCIAS.md` | Incidencias I-01 a I-04 del plan (§11), con su efecto |

Las firmas ya están en los archivos (`producto/sie/...`) y en `arquitectura/INTERFACES.md`. **No las cambies sin avisar a Salvador.**

## Reglas exactas

**Seed (ADR-004).** CRM (campañas, leads, oportunidades, cotizaciones) con fecha ≤ corte; ERP (solicitudes, pedidos, movimientos, entregas, facturas, pagos) con fecha < corte; maestros y activos siempre. Una oportunidad solo está `Ganada` si su pedido existe al corte; si no, `Propuesta`. CLI-003 está `No usa` antes de su primer pedido por TUALI (PED-003) e `Híbrido` después. Normaliza `estado_adopcion_tuali` a `Digital`, `Híbrido` o `No usa`. `crear_base` recrea todo menos la tabla `bitacora`. `avanzar` usa `INSERT OR IGNORE` y es idempotente.

**ATP.** Fórmula del validador del EP §4: físico = Σ(entrada − salida) con fecha < f; reservado = Σ(cantidad de pedidos confirmados antes de f − lo entregado antes de f); disponible = físico − reservado. Control: PRD-001 al 07/10 → 402 − 22 = 380.

**Orden en `ServicioERP.recibir`:** P1 `sol.faltantes()` → `DATO-OBLIG`; P2 mismo `id_solicitud + intento` ya procesado → devuelve la misma respuesta (`respuesta_json`); la solicitud o cotización ya tiene pedido → `DUPLICADO` con ese `id_pedido`; luego C1–C5 (se evalúan las cinco; decide la primera que falla):

| Control | Pasa si |
|---|---|
| C1 | El cliente del mensaje existe, está `Activo`, `Sincronizado` y tiene código ERP |
| C2 | Crédito no `Bloqueado` y (contado: `condicion_pago_dias = 0`, o total cotizado ≤ `limite_credito`) |
| C3 | Cada `id_precio` existe, es del producto, está `Activa` y vigente a `fecha_envio` |
| C4 | Cada línea: descuento ≤ 5 %; o entre 5 % y 12 % con `estado_descuento = Aprobado`, aprobador y fecha de aprobación ≤ envío. Más de 12 % siempre falla |
| C5 | Cada línea: cantidad ≤ ATP a `fecha_envio`. Si falla en EV-05 con `aceptacion.acepta` y ATP ≥ tramo 1 → `OK-PROMESA-ALT`; si no → `ATP-PARCIAL` |

**Respuestas (deben coincidir con `arquitectura/contrato_i8/ejemplos/`; la prueba compara campo por campo, salvo `causa`):**

| Código | `responsable_siguiente_paso` | `siguiente_paso` | Pedido |
|---|---|---|---|
| `OK-ACEPTADO` | ejecutivo de la cuenta del cliente (CLI-003 → "Preventista 1") | "Seguimiento de entrega" | Confirmado; prometida = siguiente día de ventana |
| `OK-PROMESA-ALT` | ejecutivo de la cuenta ("Preventista 2") | "Seguimiento de la reposición de 220 paquetes" | Confirmado; prometida 09/10; revisión 12/10 |
| `ATP-PARCIAL` | "Planeamiento CD → Preventista 2" | "Confirmar con el cliente 380 el 09/10 y 220 el 12/10" | Ninguno |
| Rechazos | "Quién corrige" del catálogo (`CATALOGO`) | "Siguiente paso" del catálogo | Ninguno |

**Promesa (EV-04).** Tramo 1: ATP disponible, fecha = `fecha_entrega(dirección, fecha_envio + 1 día)`, origen "ALM-001 CD Lima Norte". Tramo 2: faltante, fecha de la próxima reposición del plan, origen "Reposición desde ALM-002 (planta) · plan APO (I2)". Fecha de entrega: siguiente día dentro de la ventana de `direcciones.ventana_entrega` ("Lun-Sáb", "Lun-Vie").

**Pedido.** ID `PED-NNN` (`contrato.id_pedido_para`), `fecha_confirmacion = fecha_envio`, líneas copiadas del mensaje. Importes con el redondeo del validador del EP: bruto = round(cantidad × precio, 2); descuento = round(bruto × %, 2); base = bruto − descuento; IGV = round(base × 0,18, 2); total = base + IGV; la cabecera suma las líneas. Deben dar exactamente los importes de `Pedidos_cab` del EP (PED-003: 1,589.02; PED-002: 13,287.74).

**Bitácora.** Cada control C1–C5 es una entrada (`agente="erp"`, `regla="C1"`…, `resultado` con el dato que decide, `codigo` en la que decide). Si hay faltante, una entrada con `ids["id_ot"]` de la causa. Siempre con `fecha_negocio = fecha_envio` y el `run_id` recibido.

**Causa del faltante.** `plan_reposicion` con `id_ot_causa` cuya fecha original sea anterior a la fecha y la reprogramada posterior. `atp_sin_parada = atp_con_parada + cantidad del lote` (380 + 240 = 620).

## Cómo trabajar

```powershell
git fetch origin; git switch bloque-b/datos-erp
py -3.11 -m venv .venv; .venv\Scripts\activate; pip install -r requirements.txt
python -m pytest pruebas/aceptacion/test_bloque_b.py      # al inicio: 22 pendientes
```

- Haz commits pequeños **con tu propia identidad** (`git config user.name` / `user.email`), por ejemplo: seed → esquema → ATP y causas → reglas → promesa y servicio.
- Si usas IA, decláralo en `fuentes/DECLARACION_IA.md` (qué parte y para qué) y revisa todo lo que genere.
- `git push origin bloque-b/datos-erp` y abre un pull request a `main` cuando esté verde.

## Terminado cuando

- `python -m pytest pruebas/aceptacion/test_bloque_b.py` da **0 pendientes y 0 fallas**, y `python -m pytest pruebas/unitarias` sigue en verde.
- `cd producto; python -m sie diagnostico` muestra el bloque B en `OK`.
- Puedes explicar en 1 minuto por qué ATP = 380, por qué sin la parada sería 620 y por qué el seed se carga por fecha de corte.
