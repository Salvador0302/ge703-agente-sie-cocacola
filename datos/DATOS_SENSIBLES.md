# Tratamiento de datos sensibles

| Dato | Tratamiento |
|---|---|
| Clientes | Nombres con la marca "(sintético)"; documentos `SIM-RUC10-…` y `SIM-RUC20-…`, que no son RUC válidos |
| Contactos | "Contacto ficticio N-N", correos del dominio reservado `@example.com`, teléfonos `SIM-TEL-…` |
| Direcciones | "Jr. Simulado …"; los distritos reales solo dan contexto geográfico |
| Consentimiento | Un lead sin consentimiento se descarta y no se conservan más datos (LEAD-007), según la Ley 29733 |
| Responsables | Roles ("Preventista 2", "Supervisor de ventas"), nunca personas |
| Activos y mantenimiento | Activos, OT y plan de reposición sintéticos, marcados con `sintetico = 1` |
| Bitácora | Guarda IDs, códigos, reglas y cifras. No guarda nombres de contacto, correos, teléfonos, documentos ni el texto libre del cliente (solo su longitud y un hash) |
| Datos enviados a la Claude API (modo `llm`) | Solo el texto del pedido y resultados de consultas sobre datos sintéticos |
| Credenciales | `ANTHROPIC_API_KEY` solo en `.env` local o en el entorno; `.env` está en `.gitignore` y fuera del ZIP; la clave no aparece en `repr()` ni en la bitácora |
| Datos de ACL | No se usa información interna ni confidencial |
