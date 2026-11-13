# Declaración de uso de IA · PC3

## Herramienta usada en el desarrollo

| Campo | Registro |
|---|---|
| Herramienta | Claude Code (Anthropic), modelo Claude Opus 5.5 |
| Quién la usó | Salvador Barrionuevo Gutierrez (líder y arquitecto), en su computadora y con su cuenta de git |
| Periodo | Desde el 07/11/2026 |
| Propósito | Lectura y síntesis de los antecedentes (EP, PC2, PC3, PC4), propuesta del plan y de la arquitectura, implementación del código del Agente SIE (bloques A, B, C y D), pruebas automáticas, diagramas y documentación del repositorio |
| Datos entregados a la IA | Solo material del curso, trabajo previo del grupo y datos sintéticos. Ningún dato real de ACL, de clientes ni de personas |
| Evidencia | Cada commit hecho con asistencia de IA lleva la línea `Co-Authored-By: Claude Opus 5.5` en el historial de git |

## Apoyo de IA en el informe y la presentación de la PC3

| Campo | Registro |
|---|---|
| Herramienta | Claude (Anthropic), modelo Claude Opus 5.5 |
| Fecha | 13/11/2026 |
| Propósito | Redacción del informe y de la presentación a partir de los datos, la evidencia y las salidas de la demo del repositorio; búsqueda de fuentes públicas sobre ACL (plantas y centros de distribución), citadas con fecha de acceso |
| Validación humana | Salvador Barrionuevo revisa las cifras contra la salida de la demo y los CSV antes de entregar |

## Validación humana

| Integrante | Validación |
|---|---|
| Barrionuevo Gutierrez, Salvador Jhou | Decidió el plan y las ocho decisiones de diseño, revisó y aprobó cada pull request y ejecutó la demo |
| Leandro Ochoa, Gianmarco | Calcula a mano los resultados esperados de los casos (`pruebas/CASOS.csv`) y revisa el PR del bloque B (datos y ERP simulado) |
| Cornejo Palomino, José Julián | Autor del recorrido O2C y de los casos EP-N y EP-X del EP que el agente reproduce |
| Urbano Lara, David Alexis | Ver `arquitectura/ROLES_EQUIPO.md` |

Además de la revisión humana, el código se valida con pruebas independientes de la IA que la produjo:

- **Contra el EP:** los 12 intentos del EP se reproducen con los mismos códigos y pedidos al céntimo.
- **Contra el contrato:** las respuestas coinciden con los mensajes de ejemplo del contrato.
- **Recorrido completo:** la demo cierra con una tabla de resultado esperado frente a observado.

## IA dentro del producto (modo `llm`)

En modo `llm`, el agente usa Gemini (Google AI Studio, nivel gratuito, `gemini-2.5-flash`) o la Claude API (`claude-opus-5-5`), según `LLM_PROVEEDOR`, solo para interpretar el texto del pedido y redactar la explicación. Las decisiones (códigos, cantidades, importes, promesas) las toma un motor de reglas determinista. Una redacción con cifras que no estén en los hechos se descarta (ADR-001). El modo por defecto y de la demo es `reglas`, sin IA. A la fecha, el modo `llm` está probado con una simulación de la API, no contra la API real.

## Límites

La salida de la IA no es fuente primaria. Las afirmaciones sobre ACL se sostienen en las fuentes de `fuentes/BIBLIOGRAFIA.md`; lo que no tiene fuente se marca como SUPUESTO o PENDIENTE.
