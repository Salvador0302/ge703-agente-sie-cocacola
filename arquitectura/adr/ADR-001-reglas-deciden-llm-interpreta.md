# ADR-001 · Las reglas deciden; el LLM solo interpreta y redacta

**Estado:** aceptada · 07/11/2026 · Salvador Barrionuevo

## Contexto

El agente comercial recibe pedidos en lenguaje natural ("Los Olivos pide 600 paquetes"). Las decisiones del contrato I8 (C1–C5, código, promesa, creación de pedido) deben ser reproducibles por el docente y no pueden depender de un modelo probabilístico ni de una API key.

## Decisión

1. Un motor de reglas determinista en código (`sie.erp.reglas`) decide C1–C5, el código y la promesa. Está versionado y probado contra los 12 intentos del EP.
2. El LLM (Claude, `claude-opus-5-5`, esfuerzo `low`) solo interpreta el texto con herramientas de **lectura** y redacta la explicación. No tiene herramienta de envío ni parámetros de monto: el EV-02 se arma desde la cotización aceptada del CRM.
3. Si la redacción del LLM contiene una cifra que no está en los hechos, se descarta y se usa la plantilla (`sie.llm.verificacion`).
4. `AGENT_MODE=reglas` es el modo por defecto y el de la demo en vivo. Si `llm` falla (sin key, sin red, rechazo), el agente vuelve a reglas y lo registra en la bitácora.
5. Mientras el equipo no tenga API key, el modo `llm` se prueba con un doble del SDK (`pruebas/unitarias/test_llm.py`) y así se declara.

## Alternativas descartadas

- **El LLM decide con tool use completo:** no reproducible, depende de la key y contradice la frontera "un solo sistema compromete".
- **Sin LLM:** cumple, pero pierde la interpretación de texto libre que justifica el agente; queda como modo `reglas`.

## Consecuencias

- La demo es idéntica con y sin API key en código, pedido y promesa.
- El texto del cliente se trata como dato, no como instrucción; un intento de inyección no puede crear pedidos.
- Costo del modo `llm`: unos centavos de dólar por corrida (estimado); sin costo en modo reglas.
