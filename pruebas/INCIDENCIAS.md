# Incidencias

Hallazgos sobre los datos y el material del EP. Se registran y se explica su efecto; los datos del EP no se modifican.

| # | Incidencia | Evidencia | Efecto y tratamiento |
|---|---|---|---|
| I-01 | SOL-011 registra `cantidad_atp_confirmada = 400`, pero el ATP real de PRD-001 al 09/10 es −220 (PED-002 reserva 600 desde el 08/10) | Recálculo con la fórmula del validador del EP §4 | Ninguno sobre el código: C2 (crédito bloqueado) falla antes que C5, y la respuesta sigue siendo `CRED-BLOQ`. El motor recalcula C5 = F |
| I-02 | La regla "siguiente día de ruta" reproduce 5 de las 9 fechas prometidas del EP. PED-005 y PED-006 caen fuera de la ventana de su dirección; PED-001 y PED-008 usan 2 días | `pedidos_cab.fecha_prometida` frente a `direcciones.ventana_entrega` | Las pruebas exigen las fechas de los casos de la demo (PED-002 y PED-003), que sí coinciden; las demás no se comparan |
| I-03 | C2 tiene tres redacciones: "total ≤ límite" (contrato), "límite disponible" (catálogo) y "exposición total abierta" (diccionario) | `CONTRATO_CRM_ERP.md`, `codigos_respuesta.csv`, `DICCIONARIO_DATOS.csv` | La PC3 aplica total cotizado ≤ límite (como el validador del EP). La PC4 incorporará las cuentas por cobrar abiertas |
| I-04 | Dominios del diccionario del EP que no cubren los datos: adopción de TUALI con texto libre, CLI-005 con 7 días de pago, CAMP-004 y LEAD-013 con valores fuera de lista, descuento máximo 15 % frente al 12 % de R3 | `DICCIONARIO_DATOS.csv` frente a los CSV | El seed normaliza la adopción a Digital, Híbrido o No usa; `datos/DICCIONARIO.csv` corrige los dominios |
| I-05 | El ejemplo de EV-05 no trae la evidencia de aceptación que exige `eventos_contrato.csv` | `EPX_SOL-002_intento2_solicitud.json` | El contrato v1.2 agrega el bloque `aceptacion` |
| I-06 | El validador del EP falla en Windows al redirigir su salida (`UnicodeEncodeError` por el carácter `→` en cp1252) | `python validar_contrato.py > salida.txt` | La CLI del Agente SIE fuerza UTF-8; `pruebas/unitarias/test_cli.py` lo verifica con salida redirigida |
| I-07 | El EP redondea como Excel (mitad hacia arriba): el descuento de 15 × 19.50 × 5 % es 14.63; `round()` de Python da 14.62 | `pedidos_det` de PED-003, línea 3 | `producto/sie/erp/importes.py` usa `Decimal` con `ROUND_HALF_UP`; los 9 pedidos coinciden al céntimo con el EP |
