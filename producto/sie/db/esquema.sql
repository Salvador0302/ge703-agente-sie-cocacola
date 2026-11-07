-- Esquema de la base local del Agente SIE · v4.0 (PC3) · SQLite
-- Tablas del modelo del EP (mismas columnas; nombres en minúsculas), con las claves primarias de
-- INDICE_MODELO.csv y las claves foráneas de RELACIONES.csv. Más las tablas nuevas de la PC3
-- (arquitectura/INTERFACES.md §5). Datos sintéticos. Fechas como texto ISO (AAAA-MM-DD).
-- Inventario_actual (foto al 11/10) y Prueba_contrato (fórmulas) no se cargan: el ATP se calcula
-- desde movimientos y pedidos (erp/atp.py), y la prueba del contrato la hace el código.

CREATE TABLE IF NOT EXISTS campanas (
    id_campana TEXT NOT NULL,
    nombre_campana TEXT,
    tipo_campana TEXT,
    canal TEXT,
    sistema_origen TEXT,
    fecha_inicio TEXT,
    fecha_fin TEXT,
    objetivo TEXT,
    responsable TEXT,
    estado_campana TEXT,
    PRIMARY KEY (id_campana)
);

CREATE TABLE IF NOT EXISTS clientes (
    id_cliente TEXT NOT NULL,
    id_cuenta_crm TEXT,
    codigo_cliente_erp TEXT,
    tipo_cliente TEXT,
    razon_social TEXT,
    nombre_comercial TEXT,
    tipo_documento_fiscal TEXT,
    numero_documento_fiscal TEXT,
    estado_cliente TEXT,
    segmento_cliente TEXT,
    sector_economico TEXT,
    pais TEXT,
    estado_credito TEXT,
    limite_credito REAL,
    moneda_credito TEXT,
    condicion_pago_dias INTEGER,
    ejecutivo_cuenta TEXT,
    fuente_maestro TEXT,
    estado_sincronizacion TEXT,
    fecha_ultima_verificacion TEXT,
    fecha_ultima_sincronizacion TEXT,
    canal_pedido_habitual TEXT,
    estado_adopcion_tuali TEXT,
    PRIMARY KEY (id_cliente)
);

CREATE TABLE IF NOT EXISTS contactos (
    id_contacto TEXT NOT NULL,
    id_cliente TEXT,
    nombre_completo TEXT,
    rol_contacto TEXT,
    email TEXT,
    telefono TEXT,
    canal_preferido TEXT,
    consentimiento_comunicaciones TEXT,
    finalidad_consentimiento TEXT,
    fecha_consentimiento TEXT,
    fecha_fin_consentimiento TEXT,
    evidencia_consentimiento TEXT,
    estado_contacto TEXT,
    fecha_actualizacion TEXT,
    PRIMARY KEY (id_contacto),
    FOREIGN KEY (id_cliente) REFERENCES clientes (id_cliente)
);

CREATE TABLE IF NOT EXISTS direcciones (
    id_direccion TEXT NOT NULL,
    id_cliente TEXT,
    tipo_direccion TEXT,
    direccion TEXT,
    pais TEXT,
    departamento TEXT,
    provincia TEXT,
    distrito TEXT,
    ventana_entrega TEXT,
    restriccion_entrega TEXT,
    estado_direccion TEXT,
    PRIMARY KEY (id_direccion),
    FOREIGN KEY (id_cliente) REFERENCES clientes (id_cliente)
);

CREATE TABLE IF NOT EXISTS productos (
    id_producto TEXT NOT NULL,
    sku TEXT,
    descripcion TEXT,
    tipo_producto TEXT,
    familia TEXT,
    unidad_medida TEXT,
    configuracion TEXT,
    especificacion_tecnica TEXT,
    categoria_impuesto TEXT,
    tasa_igv REAL,
    costo_unitario_referencia REAL,
    vendible TEXT,
    estado_producto TEXT,
    PRIMARY KEY (id_producto)
);

CREATE TABLE IF NOT EXISTS listas_precios (
    id_precio TEXT NOT NULL,
    id_lista_precio TEXT,
    id_producto TEXT,
    segmento_cliente TEXT,
    moneda TEXT,
    precio_unitario REAL,
    vigente_desde TEXT,
    vigente_hasta TEXT,
    descuento_max_sin_aprobacion REAL,
    condicion_facturacion TEXT,
    estado_lista TEXT,
    PRIMARY KEY (id_precio),
    FOREIGN KEY (id_producto) REFERENCES productos (id_producto)
);

CREATE TABLE IF NOT EXISTS reglas_descuento (
    id_regla_descuento TEXT NOT NULL,
    id_lista_precio TEXT,
    descuento_desde REAL,
    descuento_hasta REAL,
    autoridad TEXT,
    requiere_aprobacion TEXT,
    vigente_desde TEXT,
    vigente_hasta TEXT,
    PRIMARY KEY (id_regla_descuento)
);

CREATE TABLE IF NOT EXISTS almacenes (
    id_almacen TEXT NOT NULL,
    nombre_almacen TEXT,
    ubicacion TEXT,
    tipo_almacen TEXT,
    estado_almacen TEXT,
    PRIMARY KEY (id_almacen)
);

CREATE TABLE IF NOT EXISTS leads (
    id_lead TEXT NOT NULL,
    id_campana TEXT,
    fecha_captura TEXT,
    canal_captura TEXT,
    nombre_negocio TEXT,
    tipo_documento_fiscal TEXT,
    numero_documento_fiscal TEXT,
    distrito TEXT,
    consentimiento_comunicaciones TEXT,
    evidencia_consentimiento TEXT,
    estado_lead TEXT,
    criterio_calificacion TEXT,
    motivo_descarte TEXT,
    id_cliente TEXT,
    responsable TEXT,
    fecha_calificacion TEXT,
    PRIMARY KEY (id_lead),
    FOREIGN KEY (id_campana) REFERENCES campanas (id_campana),
    FOREIGN KEY (id_cliente) REFERENCES clientes (id_cliente)
);

CREATE TABLE IF NOT EXISTS oportunidades (
    id_oportunidad TEXT NOT NULL,
    id_cliente TEXT,
    id_contacto TEXT,
    necesidad TEXT,
    origen TEXT,
    etapa TEXT,
    probabilidad REAL,
    valor_estimado REAL,
    moneda TEXT,
    fecha_apertura TEXT,
    fecha_cierre_estimada TEXT,
    fecha_cierre_real TEXT,
    responsable TEXT,
    motivo_perdida TEXT,
    id_campana TEXT,
    id_lead TEXT,
    PRIMARY KEY (id_oportunidad),
    FOREIGN KEY (id_cliente) REFERENCES clientes (id_cliente),
    FOREIGN KEY (id_contacto) REFERENCES contactos (id_contacto),
    FOREIGN KEY (id_campana) REFERENCES campanas (id_campana),
    FOREIGN KEY (id_lead) REFERENCES leads (id_lead)
);

CREATE TABLE IF NOT EXISTS cotizaciones_cab (
    id_cotizacion TEXT NOT NULL,
    numero_cotizacion TEXT,
    version INTEGER,
    id_oportunidad TEXT,
    id_direccion_entrega TEXT,
    fecha_emision TEXT,
    vigente_hasta TEXT,
    estado_cotizacion TEXT,
    estado_descuento TEXT,
    aprobador TEXT,
    fecha_aprobacion TEXT,
    acepta_entrega_parcial TEXT,
    condicion_facturacion TEXT,
    moneda TEXT,
    motivo_excepcion TEXT,
    base_imponible REAL,
    importe_igv REAL,
    importe_total REAL,
    PRIMARY KEY (id_cotizacion),
    FOREIGN KEY (id_oportunidad) REFERENCES oportunidades (id_oportunidad),
    FOREIGN KEY (id_direccion_entrega) REFERENCES direcciones (id_direccion)
);

CREATE TABLE IF NOT EXISTS cotizaciones_det (
    id_cotizacion TEXT NOT NULL,
    numero_linea INTEGER NOT NULL,
    id_producto TEXT,
    cantidad INTEGER,
    id_precio TEXT,
    precio_unitario REAL,
    descuento_pct REAL,
    id_regla_descuento TEXT,
    tasa_igv REAL,
    importe_bruto REAL,
    importe_descuento REAL,
    base_imponible REAL,
    importe_igv REAL,
    importe_total REAL,
    precio_vigente_desde TEXT,
    requiere_aprobacion TEXT,
    PRIMARY KEY (id_cotizacion, numero_linea),
    FOREIGN KEY (id_cotizacion) REFERENCES cotizaciones_cab (id_cotizacion),
    FOREIGN KEY (id_producto) REFERENCES productos (id_producto),
    FOREIGN KEY (id_precio) REFERENCES listas_precios (id_precio),
    FOREIGN KEY (id_regla_descuento) REFERENCES reglas_descuento (id_regla_descuento)
);

CREATE TABLE IF NOT EXISTS pedidos_cab (
    id_pedido TEXT NOT NULL,
    id_cotizacion TEXT,
    id_direccion_entrega TEXT,
    fecha_confirmacion TEXT,
    fecha_prometida TEXT,
    fecha_revision_promesa TEXT,
    estado_pedido TEXT,
    resultado_credito TEXT,
    acepta_entrega_parcial TEXT,
    condicion_facturacion TEXT,
    moneda TEXT,
    responsable_excepcion TEXT,
    causa_excepcion TEXT,
    base_imponible REAL,
    importe_igv REAL,
    importe_total REAL,
    PRIMARY KEY (id_pedido),
    FOREIGN KEY (id_cotizacion) REFERENCES cotizaciones_cab (id_cotizacion),
    FOREIGN KEY (id_direccion_entrega) REFERENCES direcciones (id_direccion)
);

CREATE TABLE IF NOT EXISTS pedidos_det (
    id_pedido TEXT NOT NULL,
    numero_linea INTEGER NOT NULL,
    id_producto TEXT,
    cantidad INTEGER,
    id_precio TEXT,
    precio_unitario REAL,
    descuento_pct REAL,
    id_regla_descuento TEXT,
    tasa_igv REAL,
    importe_bruto REAL,
    importe_descuento REAL,
    base_imponible REAL,
    importe_igv REAL,
    importe_total REAL,
    PRIMARY KEY (id_pedido, numero_linea),
    FOREIGN KEY (id_pedido) REFERENCES pedidos_cab (id_pedido),
    FOREIGN KEY (id_producto) REFERENCES productos (id_producto),
    FOREIGN KEY (id_precio) REFERENCES listas_precios (id_precio),
    FOREIGN KEY (id_regla_descuento) REFERENCES reglas_descuento (id_regla_descuento)
);

CREATE TABLE IF NOT EXISTS solicitudes_pedido (
    id_solicitud TEXT NOT NULL,
    intento INTEGER NOT NULL,
    tipo_mensaje TEXT,
    id_cotizacion TEXT,
    id_cliente TEXT,
    sistema_origen TEXT,
    fecha_envio TEXT,
    cantidad_solicitada INTEGER,
    cantidad_atp_confirmada INTEGER,
    fecha_promesa_propuesta TEXT,
    acepta_entrega_parcial TEXT,
    codigo_respuesta TEXT,
    estado_solicitud TEXT,
    id_pedido TEXT,
    responsable TEXT,
    siguiente_paso TEXT,
    canal_origen TEXT,
    causa TEXT,
    respuesta_json TEXT,
    PRIMARY KEY (id_solicitud, intento),
    FOREIGN KEY (id_cotizacion) REFERENCES cotizaciones_cab (id_cotizacion),
    FOREIGN KEY (id_pedido) REFERENCES pedidos_cab (id_pedido)
);

CREATE TABLE IF NOT EXISTS entregas_cab (
    id_entrega TEXT NOT NULL,
    id_pedido TEXT,
    id_direccion_entrega TEXT,
    id_almacen TEXT,
    fecha_despacho TEXT,
    fecha_entrega TEXT,
    estado_entrega TEXT,
    prueba_entrega TEXT,
    receptor TEXT,
    observacion TEXT,
    PRIMARY KEY (id_entrega),
    FOREIGN KEY (id_pedido) REFERENCES pedidos_cab (id_pedido),
    FOREIGN KEY (id_direccion_entrega) REFERENCES direcciones (id_direccion),
    FOREIGN KEY (id_almacen) REFERENCES almacenes (id_almacen)
);

CREATE TABLE IF NOT EXISTS entregas_det (
    id_entrega TEXT NOT NULL,
    numero_linea INTEGER NOT NULL,
    id_pedido TEXT,
    numero_linea_pedido INTEGER,
    id_producto TEXT,
    cantidad_entregada INTEGER,
    lote TEXT,
    unidad_medida TEXT,
    PRIMARY KEY (id_entrega, numero_linea),
    FOREIGN KEY (id_entrega) REFERENCES entregas_cab (id_entrega),
    FOREIGN KEY (id_pedido, numero_linea_pedido) REFERENCES pedidos_det (id_pedido, numero_linea),
    FOREIGN KEY (id_producto) REFERENCES productos (id_producto)
);

CREATE TABLE IF NOT EXISTS facturas_cab (
    id_factura TEXT NOT NULL,
    numero_documento TEXT,
    id_pedido TEXT,
    fecha_emision TEXT,
    fecha_vencimiento TEXT,
    moneda TEXT,
    estado_factura TEXT,
    base_imponible REAL,
    importe_igv REAL,
    importe_total REAL,
    PRIMARY KEY (id_factura),
    FOREIGN KEY (id_pedido) REFERENCES pedidos_cab (id_pedido)
);

CREATE TABLE IF NOT EXISTS facturas_det (
    id_factura TEXT NOT NULL,
    numero_linea INTEGER NOT NULL,
    id_entrega TEXT,
    numero_linea_entrega INTEGER,
    id_producto TEXT,
    cantidad INTEGER,
    precio_unitario REAL,
    descuento_pct REAL,
    tasa_igv REAL,
    importe_bruto REAL,
    importe_descuento REAL,
    base_imponible REAL,
    importe_igv REAL,
    importe_total REAL,
    PRIMARY KEY (id_factura, numero_linea),
    FOREIGN KEY (id_factura) REFERENCES facturas_cab (id_factura),
    FOREIGN KEY (id_entrega, numero_linea_entrega) REFERENCES entregas_det (id_entrega, numero_linea),
    FOREIGN KEY (id_producto) REFERENCES productos (id_producto)
);

CREATE TABLE IF NOT EXISTS pagos (
    id_pago TEXT NOT NULL,
    id_factura TEXT,
    fecha_pago TEXT,
    fecha_aplicacion TEXT,
    medio_pago TEXT,
    moneda TEXT,
    importe_aplicado REAL,
    referencia_bancaria TEXT,
    estado_pago TEXT,
    responsable_aplicacion TEXT,
    PRIMARY KEY (id_pago),
    FOREIGN KEY (id_factura) REFERENCES facturas_cab (id_factura)
);

CREATE TABLE IF NOT EXISTS movimientos_inventario (
    id_movimiento_inventario TEXT NOT NULL,
    id_producto TEXT,
    id_almacen TEXT,
    fecha_movimiento TEXT,
    tipo_movimiento TEXT,
    cantidad_entrada INTEGER,
    cantidad_salida INTEGER,
    id_entrega TEXT,
    numero_linea_entrega INTEGER,
    lote TEXT,
    referencia TEXT,
    PRIMARY KEY (id_movimiento_inventario),
    FOREIGN KEY (id_producto) REFERENCES productos (id_producto),
    FOREIGN KEY (id_almacen) REFERENCES almacenes (id_almacen),
    FOREIGN KEY (id_entrega, numero_linea_entrega) REFERENCES entregas_det (id_entrega, numero_linea)
);

-- ---------------------------------------------------------------- Tablas nuevas de la PC3 (sintéticas)

CREATE TABLE IF NOT EXISTS activos (
    id_activo TEXT NOT NULL PRIMARY KEY,
    nombre TEXT NOT NULL,
    tipo TEXT,
    id_almacen TEXT REFERENCES almacenes (id_almacen),
    criticidad TEXT CHECK (criticidad IN ('A', 'B', 'C')),
    enfoque_mantenimiento TEXT,
    capacidad_paq_dia INTEGER,          -- paquetes/día asignados al CD Lima Norte (escala didáctica)
    id_producto_principal TEXT REFERENCES productos (id_producto),
    sintetico INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS ordenes_trabajo (
    id_ot TEXT NOT NULL PRIMARY KEY,
    id_activo TEXT NOT NULL REFERENCES activos (id_activo),
    tipo TEXT,
    planificada TEXT,                   -- Si / No
    inicio TEXT,                        -- AAAA-MM-DDTHH:MM
    fin TEXT,
    horas_parada INTEGER,
    responsable TEXT,
    estado TEXT,
    sintetico INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS plan_reposicion (
    id_reposicion TEXT NOT NULL PRIMARY KEY,
    id_producto TEXT NOT NULL REFERENCES productos (id_producto),
    id_almacen_origen TEXT REFERENCES almacenes (id_almacen),
    id_almacen_destino TEXT REFERENCES almacenes (id_almacen),
    cantidad INTEGER,
    fecha_plan_original TEXT,
    fecha_reprogramada TEXT,
    id_ot_causa TEXT REFERENCES ordenes_trabajo (id_ot),
    estado TEXT,
    sintetico INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS promesa_tramos (
    id_solicitud TEXT NOT NULL,
    intento INTEGER NOT NULL,
    numero_tramo INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    fecha TEXT,
    origen TEXT,
    PRIMARY KEY (id_solicitud, intento, numero_tramo),
    FOREIGN KEY (id_solicitud, intento) REFERENCES solicitudes_pedido (id_solicitud, intento)
);

CREATE TABLE IF NOT EXISTS escalamientos (
    id_escalamiento TEXT NOT NULL PRIMARY KEY,
    run_id TEXT,
    id_solicitud TEXT,
    intento INTEGER,
    objeto TEXT,
    causa TEXT,
    responsable TEXT,
    fecha_limite TEXT,
    estado TEXT,                        -- Pendiente / Resuelto
    opciones_json TEXT,
    datos_json TEXT,
    respuesta_humana TEXT,
    fecha_respuesta TEXT,
    evidencia TEXT
);

-- La bitácora no se borra al reiniciar la base (seed.crear_base la conserva).
CREATE TABLE IF NOT EXISTS bitacora (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    fecha_negocio TEXT,
    run_id TEXT,
    agente TEXT NOT NULL,
    paso TEXT NOT NULL,
    regla TEXT,
    codigo TEXT,
    resultado TEXT,
    entrada_json TEXT,
    ids_json TEXT,
    escalado_a TEXT,
    motivo TEXT,
    fecha_limite TEXT,
    respuesta_humana TEXT,
    modo TEXT,
    detalle_json TEXT
);
CREATE INDEX IF NOT EXISTS ix_bitacora_run ON bitacora (run_id);

CREATE TABLE IF NOT EXISTS esquema_version (
    version TEXT NOT NULL PRIMARY KEY,
    fecha TEXT NOT NULL,
    descripcion TEXT
);
