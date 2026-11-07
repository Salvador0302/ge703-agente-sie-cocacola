# ADR-004 · Seed por fecha de corte y reloj de negocio

**Estado:** aceptada · 07/11/2026 · Salvador Barrionuevo

## Contexto

- Los CSV del EP muestran el estado al 11/10/2026: ya contienen PED-002 y PED-003. Si se cargan tal cual, el agente recibiría `DUPLICADO` en vez de crear esos pedidos.
- Los datos son de octubre de 2026 y las cotizaciones vencen el 08/10 y el 15/10. Si las reglas usaran la fecha del sistema, todo saldría como cotización vencida.
- Los agentes de la PC4 deben seguir trabajando con los mismos datos.

## Decisión

1. `seed.crear_base(conn, corte)` carga el mundo tal como estaba antes del corte: documentos del CRM con fecha ≤ corte; transacciones del ERP con fecha < corte; maestros y datos sintéticos de activos siempre. Restaura los estados previos de los casos de la demo (OPP-002 y OPP-003 en `Propuesta`; CLI-003 `No usa`).
2. `seed.avanzar(conn, fecha)` agrega lo ocurrido hasta esa fecha sin pisar lo que creó el ERP simulado (`INSERT OR IGNORE`).
3. Las reglas usan la fecha del mensaje (`fecha_envio`), nunca la del sistema. La bitácora guarda las dos: `fecha_negocio` y `ts` (hora real).
4. Cada demo reinicia la base al corte de su caso, así que es repetible; la tabla `bitacora` no se borra.

## Consecuencias

- Los pedidos que crea el ERP simulado deben ser idénticos a los del EP, para que al avanzar la fecha se enlacen ENT-002, FAC-002, ENT-003, FAC-003 y PAG-002 (base de la PC4). Lo verifica la prueba de regresión del bloque B.
- Para el examen final se puede correr una sola línea de tiempo desde el 02/10 avanzando la fecha entre casos.
