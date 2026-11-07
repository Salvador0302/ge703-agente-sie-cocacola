# Ficha del agente comercial · Agente SIE v4.0 (PC3)

| Campo | Descripción |
|---|---|
| **Propósito** | Recibir una solicitud de pedido del canal tradicional (TUALI, preventa o teléfono), identificar la cotización aceptada, enviarla al ERP por el contrato I8 y responder con el código del contrato. Cuando el ERP no puede cumplir lo pedido, escalar a la persona responsable con la causa, la propuesta y una fecha límite |
| **Proceso** | O2C, tramo comercial: de la cotización aceptada al pedido confirmado (contrato CRM–ERP I8 v1.2) |
| **Entradas** | Evento `pedido`: texto libre de la solicitud, canal de origen y fecha de negocio. Evento `decision_humana`: ID del escalamiento, acepta o rechaza, quién registra, medio y evidencia |
| **Salidas** | Código del contrato (`OK-ACEPTADO`, `OK-PROMESA-ALT`, `ATP-PARCIAL`, rechazos) o `NO-ENVIADA`; IDs de solicitud, intento, cotización, pedido y causa (OT); promesa alternativa por tramos; escalamiento; explicación en español; entradas de bitácora |
| **Fuentes de datos** | CRM simulado: clientes (sin datos de contacto), oportunidades, cotizaciones y solicitudes. ERP simulado: ATP y causa del faltante (consulta no vinculante, I3). Todos sintéticos (`datos/FUENTES_DATOS.md`) |
| **Herramientas** | Modo `reglas`: intérprete determinista y plantillas. Modo `llm`: Claude (`claude-opus-5-5`) con cuatro herramientas de **solo lectura**: `buscar_cliente`, `listar_cotizaciones`, `ver_cotizacion`, `consultar_atp` |
| **Reglas** | R2 cotización solicitable; R6 promesa alternativa con aceptación; R7 idempotencia; R8 el canal no cambia las reglas; R9 adopción de TUALI. El ERP aplica P1, P2 y C1–C5 (`procesos/REGLAS.md`) |
| **Permisos** | Puede leer el CRM, consultar el ATP y la causa del faltante, enviar EV-02 por I8 y enviar EV-05 solo tras una `decision_humana`. **No puede** crear pedidos (solo el ERP), aprobar descuentos, cambiar datos maestros ni confirmar una promesa por su cuenta (ADR-003) |
| **Responsable humano** | Ejecutivo de la cuenta (Preventista 1 o 2): decide con el cliente la promesa alternativa. Según el código: Supervisor de ventas (descuento), Créditos y cobranzas (crédito), Analista de precios RGM (precio), Analista de datos maestros (cliente), Soporte de integración (duplicado). Planeamiento del CD propone la reposición |
| **Escalamiento** | Todo rechazo, `ATP-PARCIAL` o `NO-ENVIADA` crea un escalamiento con objeto, causa, responsable, opciones, estado y fecha límite (un día de negocio). `ATP-PARCIAL` deja el flujo en espera hasta la decisión humana (ADR-005) |
| **Bitácora** | Cada paso del orquestador, del agente y del ERP queda en la tabla `bitacora` y en `logs/bitacora.jsonl`: hora real, fecha de negocio, run, agente, paso, regla, código, resultado, IDs, escalado a, motivo, fecha límite, respuesta humana y modo. Sin datos personales ni el texto libre del cliente (solo su longitud y un hash) |
| **Límites** | Datos sintéticos; ERP y CRM simulados sobre SQLite; un solo CD (ALM-001); promesas por tramos para el producto con faltante. El modo `llm` está probado con una simulación de la API |
| **Cómo se ejecuta** | `cd producto` · `python -m sie demo normal` · `python -m sie demo excepcion` · `python -m sie bitacora --run <run>` (guía completa: `entrega/GUIA_DESPLIEGUE.md`) |
| **Evidencia** | `pruebas/aceptacion/test_bloque_c.py` (13 pruebas) y `pruebas/aceptacion/test_bloque_b.py` (22 pruebas del ERP que usa) |
