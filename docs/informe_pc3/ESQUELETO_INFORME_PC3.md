# Esqueleto del informe PC3 · G2 · Coca-Cola / ACL

Para: José Cornejo, que redacta el informe. Sigue las secciones de la plantilla oficial (`docs/antecedentes/GE703_PC3_PC4_Plantilla_Informe_General_Agente_SIE.docx`). En cada sección hay qué pide la rúbrica y qué datos ya existen en el repositorio. El texto lo escribe José; este archivo solo ordena el material.

**Entregable:** `GE703_PC3_Informe_G2_CocaCola.pdf`, hasta el 13/11/2026 a las 17:00. Vale el 30 % de la nota académica, con cinco criterios de 4 puntos: alcance y proceso; activos y mantenimiento; datos y fuentes; análisis y evidencia documental; calidad y ética. **No exige las secciones técnicas del agente.**

## 1. Identificación del grupo y la empresa

Evaluación PC3 · G2 · Coca-Cola (Arca Continental Lindley) · fecha · versión · enlace al repositorio · enlace al paquete del agente (`entrega/GUIA_DESPLIEGUE.md`) · expositores (si el docente los designa antes).

## 2. Integrantes y contribuciones

Una contribución verificable por integrante. Fuente: `arquitectura/ROLES_EQUIPO.md`.

## 3. Resumen ejecutivo

[Completar al final] El problema, el análisis, la decisión principal, los resultados y los límites, en un párrafo.

## 4. Problema empresarial y alcance

[Completar] Partir de la continuidad con el EP: "un pedido, un contrato, tres canales" y la hipótesis H1 del PC1 (promociones desincronizadas de la planificación y la disponibilidad). Alcance PC3: activos y mantenimiento + cadena de suministro parte I. Límites: datos sintéticos, sin datos internos de ACL.

Material: `README.md` (Qué resuelve), `docs/antecedentes/repo_ep_v3/README.md`.

## 5. Procesos y análisis de la empresa

**5.1 Activos y mantenimiento** (criterio "Activos y mantenimiento"): activos relevantes, función, criticidad, disponibilidad y enfoque de mantenimiento.

| Dato disponible | Dónde |
|---|---|
| Cuatro activos sintéticos con tipo, ubicación, criticidad (A/B) y enfoque de mantenimiento | `datos/seed/activos.csv` |
| Orden de trabajo OT-2026-0107: preventivo mayor planificado, 96 h | `datos/seed/ordenes_trabajo.csv` |
| Disponibilidad de la línea ACT-LLN-01 en octubre: (744 − 96) / 744 = 87,1 % | `procesos/PARADA_ATP.md` |

[Completar] Ampliar con lo visto en clase (tipos de mantenimiento, criticidad, disponibilidad) y con fuentes públicas sobre el embotellado, si las hay, citadas con fecha de acceso.

**5.2 Cadena de suministro parte I**: actores y flujo de abastecimiento, demanda, inventarios, capacidad, disponibilidad y nivel de servicio.

| Dato disponible | Dónde |
|---|---|
| Flujo planta (ALM-002) → CD Lima Norte (ALM-001) → bodegas; plan de reposición APO (I2) | `docs/antecedentes/repo_ep_v3/08_procesos/MAPA_O2C_P2P.md`, `datos/seed/plan_reposicion.csv` |
| Movimientos de inventario e ATP (402 físicos − 22 reservados = 380 al 07/10) | `datos/seed/movimientos_inventario.csv`, `procesos/PARADA_ATP.md` |
| Capacidad asignada: 60 paquetes/día de PRD-001 para el CD | `datos/seed/activos.csv` |
| Nivel de servicio de PED-002 en la fecha prometida: 380 / 600 = 63,3 % | `procesos/PARADA_ATP.md` |

**5.3 Efecto del mantenimiento sobre la continuidad de la cadena** (criterio "Análisis y evidencia documental"): la cadena OT-2026-0107 → −240 paquetes → ATP 380 de 600 → promesa 380 + 220 → pedido PED-002 con aceptación del cliente. Tabla completa en `procesos/PARADA_ATP.md`. La demo del agente lo muestra en vivo (`python -m sie demo excepcion`).

[Completar] El problema, sus efectos y la decisión sustentada. La propuesta de `procesos/PARADA_ATP.md` es coordinar el calendario de mantenimiento con el de promociones (S&OP). José puede tomarla, ajustarla o proponer otra.

## 6. Datos, fuentes y supuestos

Distinguir información verificada de datos sintéticos; para los sintéticos, supuestos, unidades y rangos.

| Material | Dónde |
|---|---|
| Fuentes con fecha de acceso | `fuentes/BIBLIOGRAFIA.md` |
| Origen y supuestos de cada dato | `datos/FUENTES_DATOS.md` |
| Unidad, rango y origen por columna | `datos/DICCIONARIO.csv` |
| Tratamiento de datos sensibles | `datos/DATOS_SENSIBLES.md` |
| Incidencias de calidad de los datos del EP | `pruebas/INCIDENCIAS.md` |

## 7. Evidencias y decisión sustentada

Tabla "Hallazgo y decisión · Evidencia o enlace · Responsable". Evidencias ejecutables: `pruebas/evidencia/` (salidas de la demo) y `pruebas/ESPERADO_VS_OBSERVADO.md`.

## 8. Resultados, conclusiones y límites

Diferenciar resultados observados (salidas de la demo, cálculos sobre los datos) de supuestos (la parada, la capacidad, los plazos). Límites: datos sintéticos; ERP y CRM simulados; un solo CD; pendientes del backlog del EP (B01, B13, B15, B16).

## 9. Fuentes y uso de IA

Fuentes y fecha de acceso; herramientas de IA usadas y propósito (`fuentes/DECLARACION_IA.md`, más lo que use José al redactar); validación humana; datos sensibles excluidos; límites y pendientes.

## 10. Anexos

Diagramas del README (arquitectura y secuencia de la excepción), tabla de la cadena causal y salida de la demo.
