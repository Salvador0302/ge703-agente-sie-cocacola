# Roles del equipo · PC3

**Decisión del 07/11/2026 (Salvador Barrionuevo):** todo el código del Agente SIE lo implementa Salvador con asistencia de IA (declarada en `fuentes/DECLARACION_IA.md`), para asegurar calidad y plazos. Los demás integrantes no hacen commits de código. Cada uno tiene un aporte verificable no técnico, con su propia identidad.

**Para todos:** el docente elige al azar a dos integrantes para exponer. Cada uno debe poder ejecutar la demo (`entrega/GUIA_DESPLIEGUE.md`) y explicar las reglas, los controles, la trazabilidad y el escalamiento. Ensayo cronometrado: jueves 12/11/2026.

| Integrante | Aporte verificable | Evidencia | Plazo |
|---|---|---|---|
| Barrionuevo Gutierrez, Salvador Jhou | Líder y arquitecto. Plan, decisiones de diseño (ADR), implementación de los bloques A a D, integración, paquete de entrega y demo; consolidación del informe y la presentación de la PC3 con asistencia de IA (13/11/2026) | Commits y pull requests #1 a #4 | 12/11 |
| Leandro Ochoa, Gianmarco | Resultados esperados de los casos calculados a mano y revisión del PR del bloque B | Su commit de `pruebas/CASOS.csv` y su revisión en el PR #2 | 10/11 |
| Cornejo Palomino, José Julián | Recorrido O2C y escenario de quiebre del EP: casos EP-N y EP-X que el agente ejecuta en la PC3 | `docs/antecedentes/repo_ep_v3/08_procesos/`, `10_pruebas/` y `11_comite/MATRIZ_INTEGRANTES.md` | EP |
| Urbano Lara, David Alexis | Recomendación del comité, backlog, fuentes con fecha de acceso y declaración de IA del EP; datos transaccionales de prueba que usa la demo | `docs/antecedentes/repo_ep_v3/04_backlog/`, `02_fuentes/`, `06_ia_etica/`, `09_datos/README.md` | EP |

## Gianmarco · resultados esperados y revisión del bloque B

**1. Calcular a mano**, sin ejecutar el agente, los resultados esperados de estos casos, con los datos de `datos/seed/` (o del Excel del EP):

| Caso | Qué calcular |
|---|---|
| EP-N · SOL-003 intento 1 (02/10, TUALI) | C1 a C5, total con IGV, código y pedido |
| EP-X · SOL-002 intento 1 (07/10, teléfono) | ATP de PRD-001 al 07/10 (físico − reservado), C1 a C5, código, tramos de la promesa |
| EP-X · SOL-002 intento 2 (08/10, EV-05) | ATP al 08/10, código, pedido, fechas prometida y de revisión |
| C-02 · SOL-005 intento 1 (08/10, preventa) | Qué control falla y por qué |
| C-03 · SOL-011 intento 1 (09/10, teléfono) | Qué control falla y por qué |
| R2 · COT-002-V01 | Por qué no se envía al ERP |

**2. Registrarlos** en `pruebas/CASOS.csv`, en un commit con su propia identidad de git, con estas columnas: `id_caso, solicitud_intento, fecha, canal, c1, c2, c3, c4, c5, atp_a_mano, total_con_igv, codigo_esperado, pedido_esperado, promesa_esperada, responsable_esperado, calculado_por, fecha_calculo`. Luego ejecutar la demo y anotar en `pruebas/ESPERADO_VS_OBSERVADO.md` si su cálculo coincide con lo observado.

**3. Revisar el PR #2 (bloque B)** en GitHub: comparar sus cálculos con las pruebas y con `procesos/REGLAS.md`, y dejar la revisión (aprobar o pedir cambios con comentarios). El PR #2 no se fusiona sin su revisión.

## José · informe de la PC3

Redactar el informe sobre activos y mantenimiento, cadena de suministro parte I y la relación mantenimiento → disponibilidad → continuidad de la cadena, según la plantilla del curso. El esqueleto con las secciones de la plantilla y los datos disponibles está en `docs/informe_pc3/ESQUELETO_INFORME_PC3.md`. El informe no exige secciones técnicas del agente.

## David · por confirmar

Su aporte está pendiente de definir por Salvador.


## Actualización del 13/11/2026

El informe y la presentación de la PC3 los consolidó Salvador con asistencia de IA (declarada en `fuentes/DECLARACION_IA.md`) a partir de los datos y salidas del repositorio; están en `docs/entregables_pc3/`. La tabla de contribuciones del informe (sección 2) registra, para cada integrante, su aporte del EP que la PC3 reutiliza. Todos preparan la defensa completa con las notas del expositor del `.pptx`.
