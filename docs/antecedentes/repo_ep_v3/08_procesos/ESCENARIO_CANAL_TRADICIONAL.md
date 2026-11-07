# Escenario comercial · canal tradicional de Lima Norte · v3.0

## Contexto

- ACL embotella y comercializa las marcas de Coca-Cola en Perú; declara 6 plantas, más de 4,500 colaboradores y más de 370 mil clientes [HECHO: F01, acceso 23/10/2026].
- TUALI permite hacer pedidos, ver promociones y revisar el portafolio. ACL reporta unos 200 mil bodegueros en la app, casi 4 de cada 10 bodegas del país sobre una base de unos 535 mil [HECHO: F03, acceso 23/10/2026].
- Cerca del 46 % de los clientes de ACL aún no usa TUALI (200 mil sobre 370 mil) [SUPUESTO: cálculo del equipo; estar registrado no equivale a pedir siempre por la app].
- En el canal tradicional se vende también por preventa y por teléfono [HECHO: S07 para preventa; SUPUESTO para la proporción telefónica].

## Actores

| Actor | Rol |
|---|---|
| Marketing trade | Campañas de captación y de adopción (CAMP-001, CAMP-004) |
| RGM | Promociones y precios (CAMP-002), cargados en ECC por I10 |
| Bodeguero / mayorista | Pide por TUALI, por el preventista o por teléfono |
| Preventista | Califica leads, cotiza y registra en el CRM los pedidos de AC Móvil y del teléfono |
| Supervisor de ventas | Aprueba descuentos de más de 5 % y hasta 12 % |
| Analista de datos maestros | Crea o fusiona clientes |
| Créditos y cobranzas | Resuelve créditos bloqueados o excedidos |
| Planeamiento del CD | Propone promesas alternativas cuando falta ATP |

## Escenario normal (EP-N): Bodega Don Lucho pasa a TUALI

Don Lucho (CLI-003) pedía por teléfono todas las semanas. Responde a "Pásate a TUALI" (CAMP-004) en la visita del preventista, acepta en la app una cotización con 5 % y su pedido entra al ERP por el contrato sin llamadas de confirmación: `OK-ACEPTADO`, PED-003. Su estado de adopción pasa de "No usa" a "Híbrido". Recorrido completo en `MAPA_O2C_P2P.md`.

## Excepción prioritaria (EP-X): mayorista híbrido pide por teléfono

Comercial Los Olivos (CLI-002) usa TUALI para reposiciones pequeñas y llama para los volúmenes grandes. El 06/10 pide por teléfono 600 paquetes de Inca Kola 500 ml en promoción con 10 %. El preventista lo registra en el CRM. El supervisor rechaza la V1 (10 %) y aprueba la V2 (8 %). El ERP encuentra 380 de 600 (`ATP-PARCIAL`) y propone 380 el 09/10 y 220 el 12/10. El cliente acepta y el pedido nace con `OK-PROMESA-ALT` (PED-002). Es la hipótesis H1 del PC1 vista desde el canal. Detalle en `../10_pruebas/PRUEBA_EP.md`.

## Pruebas complementarias

| Caso | Canal | Código |
|---|---|---|
| SOL-001: bodega nueva captada por TUALI | TUALI | `OK-ACEPTADO` |
| SOL-005: precio de Powerade no vigente y reintento | Preventa | `PRECIO-NO-VIG` → `OK-ACEPTADO` |
| SOL-011: crédito bloqueado | Teléfono | `CRED-BLOQ` |
| LEAD-003: duplicado · LEAD-007: sin consentimiento | TUALI | Descartados |

## Reglas de negocio

Ver `REGLAS_NEGOCIO.csv` (R1–R9). R8 y R9 se agregan en el EP.

## Fuera de alcance

Pedido operativo, entrega, facturación y posventa (S7 en adelante, backlog B19).
