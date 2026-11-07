# CHANGELOG

## v3.0 · 23/10/2026 · Examen Parcial
- **Decisión del comité:** contrato único CRM–ERP para los tres canales del canal tradicional (TUALI, preventa y teléfono), con TUALI como canal preferente.
- **Arquitectura:** el teléfono/WhatsApp deja de ser un canal fuera del sistema; el pedido telefónico se registra en el CRM y entra por I8. I4 e I9 se actualizan (`05_arquitectura/interfaces.csv`). Nueva figura `arquitectura_v3.png`.
- **Contrato v1.1:** se agrega el dato mínimo `canal_origen` a EV-02; las reglas C1–C5 no cambian y no dependen del canal. Se agrega la regla R8 (todo pedido telefónico se registra en el CRM) y R9 (adopción de TUALI).
- **Macroprocesos:** se agrega el mapa integrado O2C–P2P con la transacción que los conecta: el pedido confirmado consume ATP y el faltante (220 paquetes de PED-002) genera el requerimiento que APO/MRP convierte en solicitud de compra.
- **Datos (modelo v3):** columnas `canal_pedido_habitual` y `estado_adopcion_tuali` en Clientes; `canal_origen` en Solicitudes_pedido; campaña CAMP-004 "Pásate a TUALI" y LEAD-013. El escenario normal pasa a ser Bodega Don Lucho (CLI-003), que pedía por teléfono y acepta su cotización en TUALI: COT-003-V01 sube de 3 % a 5 % (3 % promoción + 2 % bono TUALI) y se recalculan PED-003, FAC-003 y PAG-002.
- **Normalización de IDs con la PC2 v2.1:** COT-01 V1 → COT-003-V01; CAMP-01 → CAMP-004; CAMP-02 → CAMP-002; LEAD-01 → LEAD-013; OPP-01 → OPP-003; COT-02 V1/V2 → COT-002-V01/V02. Las fechas del caso de Don Lucho se alinean con el modelo (30/09–02/10).
- **Prueba:** `validar_contrato.py` agrega §8 (mismo contrato, tres canales) y §9 (esperado vs. observado del EP). Resultado: 12 de 12 intentos conformes; 6 de 6 y 11 de 11 verificaciones del escenario normal y de la excepción.
- **Fuentes:** se reverifican F01, F03 y F16 el 23/10/2026. F03 respalda ahora el dato "casi 4 de cada 10 bodegueros del país" (base de 535 mil bodegas), que en la PC2 v2.1 quedó pendiente de fuente.
- **Comité:** se agregan el panel de decisión, la matriz de integrantes, el guion de 15 minutos y el registro del vocal (en blanco: lo designa el docente).

## v2.1 · 16/10/2026 · PC2 (versión entregada)
- La rúbrica de la PC2 se actualizó: alcance hasta la cotización aceptada, sin contrato técnico; expone una persona.
- Se precisa el problema: parte de los clientes pide por teléfono o espera la visita del preventista en lugar de usar TUALI. El reto es migrar a quien aún no suelta el teléfono, incluidos los clientes híbridos.
- Escenario normal: Bodega Don Lucho pasa a TUALI. Excepción: mayorista híbrido pide por teléfono 600 paquetes con 10 % y solo hay 380.

## v2.0 · 11/10/2026 · PC2 (versión de trabajo)
- Se incorpora SAP Sales Cloud como CRM [SUPUESTO] y el contrato de transición CRM–ERP: eventos EV-01 a EV-07, validaciones C1–C5, nueve códigos de respuesta e idempotencia por `id_solicitud + intento`.
- Se agregan I8, I9 e I10; se modifican I3 e I4. Modelo maestro adaptado a ACL (23 tablas sintéticas) y validador en Python.

## v1.0 · 25/09/2026 · PC1
- SAP ECC/APO como backbone, complementado por Anaplan (RGM), AC Móvil/TUALI y WMS/TMS; interfaces I1–I7; hipótesis H1; backlog B01–B12.
