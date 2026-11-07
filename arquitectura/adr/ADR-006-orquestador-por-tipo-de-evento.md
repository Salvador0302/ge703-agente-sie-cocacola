# ADR-006 · Orquestador por tipo de evento con agentes previstos

**Estado:** aceptada · 07/11/2026 · Salvador Barrionuevo

## Contexto

El Agente SIE crecerá por incrementos: comercial (PC3), cadena de suministro y logística (semanas 12–13), finanzas operativas (PC4) e integración total (examen final). El curso menciona además un "agente CEO" que consume indicadores (S5 lámina 26, S6 lámina 21, contrato PC2 §6). La PC4 admite agentes adicionales si se justifican y son verificables.

## Decisión

1. El orquestador enruta por **tipo de evento** con una tabla fija (`RUTAS`): regla simple, auditable y probada.
2. Todos los agentes previstos están registrados desde ahora (`AGENTES_PREVISTOS`). Un evento de un agente aún no implementado se registra en la bitácora como "no implementado aún" y no se pierde.
3. El agente CEO queda registrado como no implementado; Salvador confirma con el docente si se exige.
4. Agregar un agente es implementar el protocolo `Agente` y registrarlo; el orquestador rechaza agentes fuera del plan o con rutas ajenas.

## Alternativas descartadas

- **Enrutamiento por LLM:** no determinista y difícil de auditar para un control de este tipo.
- **Un solo agente que hace todo:** contradice "un agente por proceso" del curso y mezcla permisos.

## Consecuencias

- `python -m sie agentes` muestra el estado de cada agente.
- Los incrementos siguientes no cambian el orquestador salvo para agregar tipos de evento nuevos.
