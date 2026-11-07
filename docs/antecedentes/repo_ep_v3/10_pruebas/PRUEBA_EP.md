# Prueba del EP · escenario normal y excepción

**Tipo:** prueba de escritorio con datos sintéticos [SUPUESTO — equipo; 23/10/2026]. Las validaciones C1–C5 se recalculan de dos formas independientes: fórmulas del Excel (`Prueba_contrato`) y `validar_contrato.py`. No se ejecuta un SAP real.
**Cómo se obtiene el resultado observado:** `python 10_pruebas/validar_contrato.py` (secciones 1, 4, 8 y 9). Salida guardada en `RESULTADO_VALIDACION.txt`.

## EP-N · Escenario normal: Bodega Don Lucho acepta su cotización en TUALI

| Elemento | Registro |
|---|---|
| Precondiciones | CLI-003 activo y sincronizado, al contado, canal habitual teléfono. CAMP-004 activa. PRE-BOD-001/003/006 vigentes desde 01/10. Regla REG-BOD-STD hasta 5 % sin aprobación. Stock suficiente en el CD Lima Norte |
| Pasos | 1) Visita con demostración de TUALI; LEAD-013 calificado (30/09). 2) COT-003-V01 (65 paquetes, 5 %) aceptada en TUALI (01/10). 3) El CRM envía SOL-003 intento 1 con `canal_origen = TUALI` (EV-02, 02/10). 4) El ERP evalúa C1–C5. 5) El ERP responde (EV-03) |
| Resultado esperado | C1–C5 verdaderas; `OK-ACEPTADO`; PED-003 confirmado con promesa al 03/10; sin escalamiento |
| Resultado observado | C1–C5 = V V V V V; `OK-ACEPTADO`; PED-003; descuento 5 % ≤ 5 %; responsable Preventista 1 |
| Conformidad | **6 de 6 verificaciones conformes** (validador §9) |
| Evidencia | `05_arquitectura/ejemplos_mensajes/EPN_SOL-003_intento1_*.json`; `09_datos/csv/Solicitudes_pedido.csv`; cadena de §6: CAMP-004 → LEAD-013 → CLI-003 → OPP-003 → COT-003-V01 → SOL-003-1 → PED-003 → ENT-003 → FAC-003 → PAG-002 |
| Responsable / escalamiento | Preventista 1; sin escalamiento |

## EP-X · Excepción prioritaria: mayorista híbrido pide por teléfono volumen promocional sin ATP suficiente

| Elemento | Registro |
|---|---|
| Precondiciones | CLI-002 mayorista híbrido, crédito aprobado de S/ 20,000 a 15 días. CAMP-002 activa. COT-002-V01 (10 %) rechazada por el supervisor; COT-002-V02 (8 %) aprobada el 07/10. Pide 600 paquetes de PRD-001; el CD tiene 380 disponibles |
| Pasos | 1) Llamada del 06/10 registrada en el CRM. 2) V1 rechazada; la V2 sale con 8 % aprobado. 3) SOL-002 intento 1 (07/10) con `canal_origen = Teléfono`. 4) C1–C4 pasan y C5 falla. 5) EV-04 propone 380 el 09/10 y 220 el 12/10. 6) El cliente acepta por medio del preventista. 7) SOL-002 intento 2, confirmación de promesa (EV-05, 08/10) |
| Resultado esperado | Intento 1: `ATP-PARCIAL`, sin pedido. Intento 2: `OK-PROMESA-ALT`, PED-002 en entrega parcial. ATP = 380. La V1 con 10 % nunca llega al ERP. Al corte: 380 entregados y 220 en reposición |
| Resultado observado | Igual al esperado en las 11 verificaciones. ATP recalculado desde movimientos: físico 402 − reservado 22 = 380 |
| Conformidad | **11 de 11 verificaciones conformes** (validador §4 y §9) |
| Cómo se detecta | En el ERP, con C5 (ATP por CD) al momento del envío, y no en la llamada |
| Cómo se contiene | No se crea pedido en el intento 1; la entrega parcial exige aceptación registrada (EV-05); la V1 fuera de política no sale del CRM (C4 preventivo) |
| Quién decide o escala | Planeamiento del CD propone la promesa; Preventista 2 la gestiona con el cliente; el supervisor de ventas decide el descuento. Si la reposición se atrasa: EV-06 y caso de atención |
| Evidencia | `EPX_SOL-002_intento1_*.json` y `EPX_SOL-002_intento2_*.json`; `Cotizaciones_cab` (V01 rechazada, V02 aprobada); `Pedidos_cab` (PED-002); `Inventario_actual`; `Movimientos_inventario` |

## Mismo contrato, tres canales (validador §8)

| Canal | Solicitudes | Intentos | Conformes | OK al primer envío | Con código de excepción |
|---|---|---|---|---|---|
| TUALI | 2 | 2 | 2 | 2 | 0 |
| Preventa | 4 | 5 | 5 | 3 | 1 |
| Teléfono | 4 | 5 | 5 | 2 | 2 |
| **Total** | **10** | **12** | **12** | **7** | **3** |

Controles transversales: 0 pedidos aceptados por encima del ATP; 0 promesas parciales sin aceptación; 12 de 12 respuestas con código, responsable y siguiente paso.

## Cómo comprobar que la prueba depende de las reglas

En el Excel, cambiar `estado_credito` de CLI-002 a `Bloqueado`: el código esperado de SOL-002 pasa a `CRED-BLOQ` y el resultado a "No conforme". En el CSV, el mismo cambio hace que el validador termine con observaciones (código de salida 1).
