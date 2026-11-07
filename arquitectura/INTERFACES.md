# Interfaces entre módulos · Agente SIE v4.0 (PC3)

Contrato interno entre los bloques. **No cambie una firma de este documento sin acordarlo con Salvador**; si hace falta, se actualiza aquí primero. Las interfaces externas (I1–I10) están en `contrato_i8/interfaces.csv`.

## 1. Módulos y dueños

| Módulo (`producto/sie/`) | Responsabilidad | Bloque |
|---|---|---|
| `contrato.py` | Tipos de EV-02/03/04/05, catálogo de nueve códigos, convenciones de IDs | A |
| `config.py` | Configuración desde entorno y `.env`; rutas | A |
| `db/conexion.py` | `conectar(ruta)` con claves foráneas y filas por nombre | A |
| `agentes/base.py` | `Evento`, `ResultadoAgente`, `Escalamiento`, `Herramienta`, protocolo `Agente` | A |
| `bitacora/__init__.py` | `EntradaBitacora`, protocolo `Bitacora`, `BitacoraMemoria` | A |
| `orquestador.py` | Enrutamiento por tipo de evento; agentes previstos | A |
| `llm/`, `agentes/comercial/interprete_llm.py` | Modo `llm` (Claude API) con respaldo a reglas | A |
| `agentes/comercial/intencion.py` | `Intencion`, protocolos `Interprete` y `Redactor` | A |
| `sistema.py` | `construir_sistema(config, conn, bitacora=None, cliente_llm=None)` y `preparar_base(config, corte)` | A |
| `demo.py`, `cli.py`, `__main__.py` | Casos de la demo, esperado frente a observado, CLI | A |
| `db/esquema.sql`, `db/seed.py` | Esquema y seed por fecha de corte | B |
| `erp/atp.py`, `erp/causas.py`, `erp/reglas.py`, `erp/promesa.py`, `erp/servicio.py` | ERP simulado y capa I8 | B |
| `crm/consultas.py` | CRM simulado (lectura y registro tras EV-03) | C |
| `agentes/comercial/agente.py`, `herramientas.py`, `interprete_reglas.py`, `redaccion.py` | Agente comercial | C |
| `bitacora/persistente.py` | Bitácora en tabla y JSONL | C |
| `ui/app.py` | Interfaz Streamlit | D |
| `entrega/armar_zip.py` (fuera del paquete) | Armado y verificación del ZIP | D |

Regla de dependencia: `contrato`, `agentes.base` y `bitacora` no importan nada del proyecto; `erp` no importa `agentes` ni `crm`; el agente comercial habla con el ERP solo a través de `ServicioERP`.

## 2. Firmas públicas

```python
# Bloque B
seed.crear_base(conn, corte: date) -> None
seed.avanzar(conn, hasta: date) -> int
atp.calcular(conn, id_producto: str, fecha: date, id_almacen="ALM-001") -> DetalleATP
causas.explicar_faltante(conn, id_producto: str, fecha: date, id_almacen="ALM-001") -> CausaFaltante | None
reglas.evaluar(conn, sol: SolicitudPedido) -> Evaluacion
promesa.fecha_entrega(conn, id_direccion: str, desde: date) -> date
promesa.proponer(conn, sol: SolicitudPedido, evaluacion: Evaluacion) -> PromesaAlternativa
ServicioERP(conn, bitacora=None)
    .recibir(sol: SolicitudPedido, run_id="") -> RespuestaERP     # único punto que crea pedidos
    .consultar_atp(id_producto, fecha) -> DetalleATP               # I3, no vinculante
    .explicar_faltante(id_producto, fecha) -> CausaFaltante | None

# Bloque C
ConsultasCRM(conn)
    .buscar_clientes(texto) -> list[dict]
    .cotizaciones_del_cliente(id_cliente, fecha) -> list[dict]
    .cotizacion(id_cotizacion) -> dict | None                      # cabecera + "lineas"
    .construir_solicitud(id_cotizacion, canal, fecha_envio, intento=1, tipo=..., aceptacion=None) -> SolicitudPedido
    .registrar_respuesta(respuesta: RespuestaERP, canal, fecha) -> None
BitacoraPersistente(conn, ruta_jsonl).registrar(entrada) / .leer(run_id=None, id_solicitud=None, ultimas=None)
InterpreteReglas(crm).interpretar(texto, fecha_negocio, canal=None) -> Intencion
RedactorPlantilla().redactar(hechos: dict) -> str
herramientas_lectura(crm, erp) -> list[Herramienta]   # nombres: buscar_cliente, listar_cotizaciones, ver_cotizacion, consultar_atp
AgenteComercial(erp, crm, interprete, redactor, bitacora, modo="reglas").manejar(evento) -> ResultadoAgente

# Bloque D
armar_zip.construir(destino: Path, incremento="PC3") -> Path
armar_zip.verificar(ruta_zip: Path, ejecutar_demo=True) -> list[str]   # lista de problemas; vacía = correcto
```

## 3. Eventos del orquestador

| Tipo | Agente | `datos` |
|---|---|---|
| `pedido` | comercial | `{"texto": str, "canal": "TUALI" \| "Preventa" \| "Teléfono"}`; `fecha_negocio` = fecha de envío |
| `decision_humana` | comercial | `{"id_escalamiento": str, "acepta": bool, "registrada_por": str, "medio": str, "evidencia": str}` |
| `abastecimiento`, `reposicion`, `inventario` | cadena_suministro | por definir (semana 12) |
| `entrega`, `transporte` | logistica | por definir (semana 13) |
| `factura`, `cobro`, `pago_proveedor`, `conciliacion` | finanzas_operativas | por definir (PC4) |
| `indicadores` | ceo | por confirmar con el docente |

## 4. Convenciones de `ResultadoAgente` (agente comercial)

| Campo | Contenido |
|---|---|
| `estado` | `COMPLETADO` (pedido creado), `ESPERA_HUMANO` (ATP-PARCIAL), `ESCALADO` (otro rechazo del ERP), `NO_ENVIADA` (R2/P3), `CERRADO_SIN_PEDIDO` (el cliente rechazó), `ERROR` |
| `codigo` | Código del contrato, `NO-ENVIADA` o `None` |
| `ids` | `id_solicitud`, `intento`, `id_cotizacion`, `id_cliente`, `id_pedido` (si hay), `id_ot` (si el faltante tiene causa) |
| `escalamiento` | Obligatorio en `ESPERA_HUMANO`, `ESCALADO` y `NO_ENVIADA`. ID `ESC-<id_solicitud>-<intento>`; fecha límite = fecha de negocio + 1 día |
| `detalle` | `respuesta` (`RespuestaERP.a_dict()`), `promesa` (`PromesaAlternativa.a_dict()`, si hay), `causa` (dict de `CausaFaltante`, si hay), `avisos` (lista de textos) |
| `mensaje` | Explicación redactada (plantilla o LLM verificado) |

## 5. Tablas nuevas (las crea B en `esquema.sql`; las escribe quien se indica)

| Tabla | Columnas | Escribe |
|---|---|---|
| `activos` | id_activo PK, nombre, tipo, id_almacen, criticidad, enfoque_mantenimiento, capacidad_paq_dia, id_producto_principal, sintetico | seed |
| `ordenes_trabajo` | id_ot PK, id_activo, tipo, planificada, inicio, fin, horas_parada, responsable, estado, sintetico | seed |
| `plan_reposicion` | id_reposicion PK, id_producto, id_almacen_origen, id_almacen_destino, cantidad, fecha_plan_original, fecha_reprogramada, id_ot_causa, estado, sintetico | seed |
| `promesa_tramos` | id_solicitud, intento, numero_tramo, cantidad, fecha, origen · PK (id_solicitud, intento, numero_tramo) | ERP (B) |
| `escalamientos` | id_escalamiento PK, run_id, id_solicitud, intento, objeto, causa, responsable, fecha_limite, estado, opciones_json, datos_json, respuesta_humana, fecha_respuesta, evidencia | agente (C) |
| `bitacora` | id PK autoincremental, ts, fecha_negocio, run_id, agente, paso, regla, codigo, resultado, entrada_json, ids_json, escalado_a, motivo, fecha_limite, respuesta_humana, modo, detalle_json | bitácora (C); no se borra al reiniciar |
| `esquema_version` | version, fecha, descripcion | seed |

`solicitudes_pedido` conserva las columnas del EP y agrega `causa` y `respuesta_json` (la respuesta completa, para devolverla igual si llega de nuevo el mismo `id_solicitud + intento`). Fechas como texto ISO (`AAAA-MM-DD`; fecha y hora `AAAA-MM-DDTHH:MM`).
