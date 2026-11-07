# Controles

| Control | Riesgo que previene | Dónde actúa | Evidencia (prueba) |
|---|---|---|---|
| R2 cotización solicitable | Enviar una versión rechazada o vencida, o una cantidad no cotizada | Agente, antes de EV-02 | `test_no_enviada_si_la_cotizacion_fue_rechazada`, `test_no_enviada_si_la_cantidad_no_coincide_con_la_cotizacion` |
| P1 datos obligatorios | Pedido con datos incompletos | Capa I8 | `test_dato_obligatorio_y_ev05_sin_aceptacion` |
| P2 idempotencia y duplicado | Dos pedidos para una misma cotización | Capa I8 | `test_idempotencia_y_duplicado` |
| C1 cliente | Pedido sobre una identidad no válida | ERP | `test_cliente_sin_alta_es_cli_no_valido` |
| C2 crédito | Venta a cliente bloqueado o sobre su límite | ERP | `test_credito_bloqueado_cambia_el_codigo` |
| C3 precio vigente | Precio o promoción no cargados en el ERP | ERP | Regresión del EP: SOL-005 intento 1 `PRECIO-NO-VIG` |
| C4 descuento | Descuento fuera de política | ERP | `test_descuento_sobre_12_por_ciento_nunca_pasa` |
| C5 ATP | Promesa sin stock (hipótesis H1) | ERP | `test_excepcion_intento_1_propone_promesa_y_no_crea_pedido` |
| Aceptación humana (EV-05) | Entrega parcial no acordada con el cliente | Agente + ERP (C5b) | `test_el_texto_no_puede_confirmar_la_promesa`, `test_excepcion_rechazada_no_crea_pedido` |
| Solo el ERP crea pedidos | Que el agente o el LLM comprometan stock | Diseño (ADR-003) | `test_herramientas_del_llm_son_de_solo_lectura_y_estrictas` |
| Cifras del LLM | Que una redacción invente cantidades, fechas o importes | Redactor LLM | `test_redaccion_con_cifra_inventada_se_descarta` |
| Canal neutro (R8) | Reglas distintas según el canal | Todo el flujo | `test_el_canal_no_cambia_el_resultado` (B y C) |
| Bitácora sin datos personales | Exposición de datos de contacto | Bitácora | `test_bitacora_en_tabla_y_jsonl_sin_datos_personales` |

Las pruebas están en `pruebas/aceptacion/` y `pruebas/unitarias/`; se ejecutan con `python -m pytest pruebas`.
