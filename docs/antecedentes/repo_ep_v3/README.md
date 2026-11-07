# GE703 · Sistemas Integrados Empresariales · Examen Parcial · G2 · Coca-Cola / ACL

**Entrega:** Examen Parcial (EP) · Semana 8 · comité del sábado 24/10/2026
**Empresa / unidad de análisis:** Coca-Cola, a través de Arca Continental Lindley (ACL), Perú
**Proceso:** canal tradicional de Lima Norte, desde la campaña y el lead hasta la solicitud de creación de pedido y sus respuestas (aceptación, rechazo o promesa)
**Versión:** v3.0 (integra la arquitectura ERP base del PC1, los macroprocesos de la S5 y el tramo comercial de la PC2)
**Panel de decisión:** https://claude.ai/artifact/9vgf6ER4u2Njc4u7gwM4A6 · copia sin conexión en `00_entregables/panel_decision/comite_decision_acl.html`

## Decisión que el comité debe aprobar

> **Un pedido, un contrato, tres canales.** Todo pedido del canal tradicional, llegue por TUALI, por preventa (AC Móvil) o por teléfono, entra a SAP ECC por el mismo contrato CRM–ERP (I8), con las mismas cinco validaciones (C1–C5) y una respuesta codificada. TUALI queda como canal preferente para migrar a los clientes telefónicos e híbridos.

**Reto de negocio.** ACL declara más de 370 mil clientes (F01) y 200 mil bodegueros en TUALI, casi 4 de cada 10 bodegas del país (F03). Cerca del 46 % de sus clientes aún no está en la app (SUPUESTO: cálculo del equipo). En los pedidos por teléfono, el precio, el stock y el crédito se confirman a mano y la promesa sale sin mirar el ATP (hipótesis H1 del PC1).

**Criterio de éxito verificable en este paquete:**

| Criterio | Resultado | Evidencia |
|---|---|---|
| Ningún pedido se crea sin pasar C1–C5 | 12 de 12 intentos conformes | `10_pruebas/RESULTADO_VALIDACION.txt` §1 |
| Toda respuesta trae código, responsable y siguiente paso | 12 de 12 | §8 |
| Ninguna promesa por encima del ATP sin aceptación del cliente | 0 casos | §8 |
| El resultado no depende del canal | TUALI, preventa y teléfono con las mismas reglas | §8 |
| Escenario normal y excepción: esperado = observado | 6 de 6 y 11 de 11 verificaciones | §9 · `10_pruebas/PRUEBA_EP.md` |

**Recomendación del comité:** aprobar con condiciones (piloto en el CD Lima Norte). Ver `11_comite/GUION_COMITE.md`, momento 6.

## Cómo reproducir la prueba

**Sin Excel** (Python 3.8+, solo biblioteca estándar), desde la raíz del repositorio:

```bash
python 10_pruebas/validar_contrato.py
```

Termina con código 0 y escribe `RESULTADO: todas las verificaciones conformes`. La salida esperada está en `10_pruebas/RESULTADO_VALIDACION.txt`.

**En Excel:** abrir `00_entregables/GE703_EP_G2_Modelo_CRM_ERP_ACL_v3.xlsx`, hoja `Prueba_contrato`. Al cambiar un dato maestro (por ejemplo, `estado_credito` de CLI-002 a `Bloqueado`), el código esperado de SOL-002 pasa a `CRED-BLOQ` y el resultado a "No conforme". Debajo de la tabla está el resumen por canal.

## Estructura

```text
GE703_EP_G2_CocaCola_REPOSITORIO_v3/
├── README.md · CHANGELOG.md
├── 00_entregables/     plantilla EP llena, panel sin conexión, modelo Excel v3, diagramas
├── 01_evidencias/      instrucciones del EP, PC1, avance S5, PC2 v2.0 y material del curso
├── 02_fuentes/         inventario de fuentes con URL y fecha de acceso
├── 03_trazabilidad/    matriz HECHO / SUPUESTO / PENDIENTE (T01–T70)
├── 04_backlog/         pendientes priorizados (B01–B27)
├── 05_arquitectura/    arquitectura v3.0, registro de cambios desde PC1, interfaces, contrato, mensajes
├── 06_ia_etica/        uso de IA, datos sensibles, supuestos y límites
├── 07_revision/        lista de verificación del EP
├── 08_procesos/        mapa O2C–P2P, escenario y reglas de negocio
├── 09_datos/           modelo exportado a CSV, diccionario y relaciones
├── 10_pruebas/         prueba del EP (normal y excepción), casos, validador y resultado
└── 11_comite/          matriz de integrantes, guion de 15 minutos y registro del vocal
```

| Evidencia obligatoria del EP | Dónde está |
|---|---|
| Panel de decisión en una sola vista | enlace arriba · `00_entregables/panel_decision/` |
| Arquitectura ERP base actualizada y registro de cambios desde PC1 | `05_arquitectura/ARQUITECTURA_v3.md` · `REGISTRO_CAMBIOS_DESDE_PC1.md` |
| Mapa integrado O2C–P2P con la transacción que conecta | `08_procesos/MAPA_O2C_P2P.md` |
| Contrato CRM–ERP | `05_arquitectura/CONTRATO_CRM_ERP.md` y CSV asociados |
| Prueba de un escenario normal y de una excepción | `10_pruebas/PRUEBA_EP.md` |
| Matriz de integrantes, contribuciones y decisión defendida | `11_comite/MATRIZ_INTEGRANTES.md` |
| Registro del vocal invitado, su pregunta y la respuesta | `11_comite/REGISTRO_VOCAL.md` (se completa el día del comité) |
| Fuentes, fecha de acceso, IA, datos sensibles, supuestos y límites | `02_fuentes/` · `06_ia_etica/` |

## Integrantes

| Integrante | Momento del comité | Decisión que defiende |
|---|---|---|
| Barrionuevo Gutierrez, Salvador Jhou | 1 · Decisión ejecutiva (0–1′) y 2 · Arquitectura base (1–4′) | Aprobar el contrato único; SAP ECC sigue siendo el único sistema que compromete |
| Cornejo Palomino, José Julián | 3 · Recorrido O2C (4–6′) y 5 · Escenario de quiebre (9–11′) | El pedido confirmado consume ATP y conecta con P2P; ante ATP insuficiente, promesa alternativa con aceptación |
| Leandro Ochoa, Gianmarco | 4 · Contrato CRM–ERP (6–9′) | Datos mínimos, cinco validaciones en orden y respuesta codificada para todo canal |
| Urbano Lara, David Alexis | 6 · Recomendación final (11–14′) | Aprobar con condiciones: piloto, riesgos aceptados y pendientes priorizados |

El vocero y el vocal invitado los designa el docente el día del comité. Huamani Vargas, Angel Sebastián se retiró del curso y no registra contribución. El detalle está en `11_comite/MATRIZ_INTEGRANTES.md`.

## Convención de trazabilidad

**HECHO:** respaldado por una fuente identificable · **SUPUESTO:** decisión de diseño o dato didáctico por validar con ACL · **PENDIENTE:** evidencia aún no disponible · **ND:** no determinado · **DECISIÓN:** elección del equipo justificada.

## Datos y privacidad

Todos los datos del modelo son **sintéticos**: nombres con la marca "(sintético)", correos `example.com`, teléfonos `SIM-TEL-…` y documentos `SIM-RUC10/20-…`. Precios, stocks, políticas e importes son supuestos didácticos y no son datos de ACL.

## Alcance

El EP integra arquitectura base, macroprocesos y el tramo comercial hasta la solicitud de creación de pedido y sus respuestas (hasta la sesión 6). No se desarrolla la ejecución operativa del pedido, la entrega, la facturación ni la posventa: aparecen solo como continuidad en el mapa y en el backlog.

## Versiones anteriores

- PC1 v1.0: https://drive.google.com/drive/folders/1Dq2FQ79LhB3MpWMnFBt0HBE3bXjXT03Y?usp=sharing
- PC2 (v2.0 y v2.1): carpeta del repositorio del G2 en Drive, https://drive.google.com/drive/folders/17P-ot4uLSmdB-U3gF8FgSIXztHumbpYt
