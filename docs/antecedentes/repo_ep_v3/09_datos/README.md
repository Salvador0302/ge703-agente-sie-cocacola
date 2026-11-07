# Datos · modelo maestro CRM–ERP adaptado a ACL · v3.0

**Fuente:** `00_entregables/GE703_EP_G2_Modelo_CRM_ERP_ACL_v3.xlsx`, adaptado del modelo maestro Andina de la Semana 6 (C02).  
**Corte:** 11/10/2026 (datos); versión del modelo 23/10/2026.  
**Naturaleza:** datos **sintéticos**. Ningún cliente, precio, stock, política ni importe es un dato de ACL.

## Contenido

| Archivo | Qué es |
|---|---|
| `csv/*.csv` | Una tabla por hoja del modelo, con los valores ya calculados por las fórmulas del Excel (UTF-8, fechas AAAA-MM-DD, booleanos TRUE/FALSE) |
| `DICCIONARIO_DATOS.csv` | Descripción, tipo, ejemplo, valores permitidos y regla de calidad de cada columna (293 columnas) |
| `RELACIONES.csv` | Claves foráneas entre tablas, cardinalidad y si admiten vacío (40 relaciones) |
| `INDICE_MODELO.csv` | Granularidad, clave primaria, sistema de registro y número de filas de cada tabla |

Los CSV se verificaron contra el Excel celda por celda (0 diferencias numéricas). `10_pruebas/validar_contrato.py` los usa para reproducir la prueba sin Excel.

## Cambios del EP (v3.0)

- `Clientes`: nuevas columnas `canal_pedido_habitual` y `estado_adopcion_tuali` (Digital, Híbrido, No usa).
- `Solicitudes_pedido`: nueva columna `canal_origen` (TUALI, Preventa, Teléfono).
- `Campanas`: CAMP-004 "Pásate a TUALI". `Leads`: LEAD-013 (Don Lucho, cliente existente).
- `Cotizaciones_det`, `Pedidos_det`, `Facturas_det`: Don Lucho pasa de 3 % a 5 % (3 % promoción + 2 % bono TUALI); los importes se recalculan con las fórmulas del Excel.
- `Prueba_contrato`: columna `canal_origen` y resumen por canal.

## Tablas por sistema de registro

| Sistema | Tablas |
|---|---|
| CRM (SAP Sales Cloud) [SUPUESTO] | Campanas, Contactos, Leads, Oportunidades, Cotizaciones_cab, Cotizaciones_det |
| Bitácora de integración [SUPUESTO] | Solicitudes_pedido |
| ERP (SAP ECC) | Clientes, Direcciones, Productos, Listas_precios, Reglas_descuento, Almacenes, Pedidos_cab/det, Entregas_cab/det, Facturas_cab/det, Pagos, Movimientos_inventario, Inventario_actual |
| Evidencia de prueba | Prueba_contrato (calculada con fórmulas) |

## Cambios respecto del modelo Andina

- Se agregan **Campanas** y **Leads**, que no existían en Andina.
- Contactos y direcciones quedan en tablas propias; Clientes conserva identidad, segmento y crédito.
- Se agrega **Solicitudes_pedido** como bitácora del contrato: cada intento conserva código, estado, responsable y siguiente paso.
- Se agrega **Prueba_contrato**, que recalcula C1–C5 y el código esperado.
- Productos en paquetes (CJ), importes en PEN, IGV didáctico 18%, dos listas de precios (Bodega y Mayorista) y reglas de descuento por rol.

## Identidad sintética y privacidad

- Nombres con la marca "(sintético)" o "Contacto ficticio".
- Correos `@example.com`, teléfonos `SIM-TEL-…`, documentos `SIM-RUC10-…` y `SIM-RUC20-…`.
- Distritos reales solo como referencia geográfica.
- Una celda vacía significa "no aplica" o "aún no ocurrió". No se rellena con IDs ficticios ni con ceros.

## Contribuciones

- Datos maestros (Clientes, Contactos, Direcciones, Productos, Listas_precios, Reglas_descuento): Leandro Ochoa, Gianmarco.
- Datos transaccionales de prueba (Campanas, Leads, Oportunidades, Cotizaciones, Solicitudes_pedido): Urbano Lara, David Alexis.
- Campos de canal y adopción del EP (v3.0): Leandro Ochoa, Gianmarco; consolidación del modelo v3: Barrionuevo Gutierrez, Salvador Jhou.
