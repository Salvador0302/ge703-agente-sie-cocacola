#!/usr/bin/env python3
"""
GE703 · Examen Parcial (EP) · G2 · Coca-Cola / ACL · v3.0
Validador independiente del contrato CRM–ERP ("un pedido, un contrato, tres canales").

Recalcula, a partir de los CSV de 09_datos/csv (exportados del modelo maestro),
las validaciones C1–C5 de cada solicitud de creación de pedido y el código de
respuesta esperado, y lo compara con lo registrado en la bitácora
(Solicitudes_pedido) y con la hoja Prueba_contrato del Excel.

Además verifica integridad referencial, reglas de negocio, importes,
idempotencia, el ATP de la excepción prioritaria e indicadores.

Uso:   python 10_pruebas/validar_contrato.py
Requisitos: Python 3.8+ (solo biblioteca estándar).
Datos sintéticos: ningún valor corresponde a ACL.
"""
import csv, os, sys
from collections import defaultdict
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(BASE, '..', '09_datos')
CSV = os.path.join(DATOS, 'csv')

def leer(nombre, carpeta=CSV):
    with open(os.path.join(carpeta, nombre), encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def num(x): return float(x) if x not in ('', None) else 0.0
def fecha(x): return date.fromisoformat(x) if x else None
def idx(rows, key): return {r[key]: r for r in rows}

T = {n[:-4]: leer(n) for n in sorted(os.listdir(CSV)) if n.endswith('.csv')}
REL = leer('RELACIONES.csv', DATOS)

fallas = []
def check(cond, msg):
    if not cond: fallas.append(msg)
    return cond

out = []
def p(s=''): out.append(s)

p('GE703 · EP · G2 · Validación independiente del contrato CRM–ERP (ACL) · v3.0')
p('=' * 74)

# ---------------------------------------------------------------- 1. Contrato C1–C5
cli = idx(T['Clientes'], 'id_cliente')
cab = idx(T['Cotizaciones_cab'], 'id_cotizacion')
det = defaultdict(list)
for d in T['Cotizaciones_det']: det[d['id_cotizacion']].append(d)
reglas = idx(T['Reglas_descuento'], 'id_regla_descuento')
precios = idx(T['Listas_precios'], 'id_precio')
opp = idx(T['Oportunidades'], 'id_oportunidad')
prueba_xlsx = idx(T['Prueba_contrato'], 'solicitud_intento')

def evaluar(s):
    c = cli[s['id_cliente']]
    q = cab[s['id_cotizacion']]
    lineas = det[s['id_cotizacion']]
    envio = fecha(s['fecha_envio'])
    c1 = c['estado_cliente'] == 'Activo' and c['estado_sincronizacion'] == 'Sincronizado'
    if c['estado_credito'] == 'Bloqueado': c2 = False
    elif num(c['condicion_pago_dias']) == 0: c2 = True          # contado
    else: c2 = num(q['importe_total']) <= num(c['limite_credito'])
    # C3: el precio de cada línea debe estar vigente en el ERP a la fecha de envío
    c3 = all(fecha(precios[l['id_precio']]['vigente_desde']) <= envio <= fecha(precios[l['id_precio']]['vigente_hasta'])
             for l in lineas)
    # C4: si alguna línea requiere aprobación (regla EXC), la versión debe estar Aprobada
    req = any(reglas[l['id_regla_descuento']]['requiere_aprobacion'] == 'TRUE' for l in lineas)
    c4 = (not req) or q['estado_descuento'] == 'Aprobado'
    c5 = num(s['cantidad_solicitada']) <= num(s['cantidad_atp_confirmada'])
    if not c1: cod = 'CLI-NO-VALIDO'
    elif not c2: cod = 'CRED-BLOQ'
    elif not c3: cod = 'PRECIO-NO-VIG'
    elif not c4: cod = 'DESC-SIN-APROB'
    elif c5: cod = 'OK-ACEPTADO'
    elif s['tipo_mensaje'] == 'Confirmación promesa' and s['acepta_entrega_parcial'] == 'Si': cod = 'OK-PROMESA-ALT'
    else: cod = 'ATP-PARCIAL'
    return (c1, c2, c3, c4, c5), cod

p('\n1. Prueba del contrato (C1 cliente · C2 crédito · C3 precio vigente · C4 descuento · C5 ATP)')
p(f"{'solicitud-intento':<18}{'C1':>4}{'C2':>4}{'C3':>4}{'C4':>4}{'C5':>4}  {'esperado':<16}{'registrado':<16}{'Excel':<16}resultado")
conformes = 0
B = lambda b: 'V' if b else 'F'
for s in T['Solicitudes_pedido']:
    cs, esperado = evaluar(s)
    key = f"{s['id_solicitud']}-{s['intento']}"
    xl = prueba_xlsx.get(key, {}).get('codigo_esperado', '—')
    ok = esperado == s['codigo_respuesta'] == xl
    conformes += ok
    check(ok, f'{key}: esperado {esperado}, registrado {s["codigo_respuesta"]}, Excel {xl}')
    p(f"{key:<18}" + ''.join(f'{B(c):>4}' for c in cs) + f"  {esperado:<16}{s['codigo_respuesta']:<16}{xl:<16}{'Conforme' if ok else 'NO CONFORME'}")
p(f'→ {conformes} de {len(T["Solicitudes_pedido"])} intentos conformes (Python = bitácora = Excel).')

# ---------------------------------------------------------------- 2. Integridad referencial
p('\n2. Integridad referencial (hoja Relaciones del modelo)')
pk = {}
def claves(tabla, campos):
    return {tuple(r[c] for c in campos) for r in T[tabla]}
n_rel = 0
for r in REL:
    hijo, campos, padre, ref, vacio = r['Tabla hija'], r['Campo(s)'].split(' + '), r['Tabla padre'], r['Clave de referencia'].split(' + '), r['Admite vacío']
    existentes = claves(padre, ref)
    for fila in T[hijo]:
        if hijo == 'Prueba_contrato':
            val = tuple(fila['solicitud_intento'].rsplit('-', 1))
        else:
            val = tuple(fila[c] for c in campos)
        if all(v == '' for v in val):
            check(vacio == 'Si', f'{hijo}.{"+".join(campos)} vacío y la relación no lo admite')
            continue
        check(val in existentes, f'{hijo}.{"+".join(campos)}={val} no existe en {padre}')
    n_rel += 1
p(f'→ {n_rel} relaciones revisadas; {sum("no existe" in f or "vacío" in f for f in fallas)} huérfanos.')

# ---------------------------------------------------------------- 3. Reglas de negocio
p('\n3. Reglas de negocio del escenario')
leads = T['Leads']
r1 = [l for l in leads if l['estado_lead'] == 'Convertido']
check(all(l['consentimiento_comunicaciones'] == 'TRUE' and l['id_cliente'] for l in r1), 'R1: lead convertido sin consentimiento o sin cliente')
check(all(l['estado_lead'] == 'Descartado' and l['motivo_descarte'] for l in leads if l['consentimiento_comunicaciones'] == 'FALSE'), 'R1: lead sin consentimiento no descartado')
docs_cli = {c['numero_documento_fiscal']: c['id_cliente'] for c in T['Clientes']}
dup = [l for l in leads if l['numero_documento_fiscal'] in docs_cli and l['estado_lead'] == 'Descartado']
check(all(l['id_cliente'] == docs_cli[l['numero_documento_fiscal']] for l in dup), 'R1: duplicado no enlazado al cliente existente')
p(f'R1 Calificación: {len(r1)} convertidos con consentimiento; {len(dup)} duplicado(s) enlazado(s) a su cliente; leads sin consentimiento descartados.')
enviadas = {s['id_cotizacion'] for s in T['Solicitudes_pedido']}
check(all(cab[c]['estado_cotizacion'] == 'Aceptada' for c in enviadas), 'R2: se envió una cotización no Aceptada')
p(f'R2 Cotización solicitable: las {len(enviadas)} cotizaciones enviadas están Aceptadas; ninguna versión Rechazada se envió.')
for d in T['Cotizaciones_det']:
    g = num(d['descuento_pct']); rg = reglas[d['id_regla_descuento']]
    check(num(rg['descuento_desde']) <= g <= num(rg['descuento_hasta']) or (g == 0 and num(rg['descuento_desde']) == 0),
          f"R3: {d['id_cotizacion']} línea {d['numero_linea']} con {g:.0%} fuera de la regla {rg['id_regla_descuento']}")
    check(g <= 0.12, f"R3: {d['id_cotizacion']} supera 12%")
p('R3 Descuento: todas las líneas caen en su tramo (≤5% preventista; 5–12% Supervisor).')
p('R4 Precio vigente: verificado en C3 (ver SOL-005 intento 1).')
p('R5 Crédito: verificado en C2 (ver SOL-011).')
# R7 idempotencia
peds = T['Pedidos_cab']
porcot = defaultdict(list)
for x in peds: porcot[x['id_cotizacion']].append(x['id_pedido'])
check(all(len(v) == 1 for v in porcot.values()), 'R7: una cotización tiene más de un pedido')
intentos = defaultdict(list)
for s in T['Solicitudes_pedido']: intentos[s['id_solicitud']].append(int(s['intento']))
check(all(sorted(v) == list(range(1, len(v) + 1)) for v in intentos.values()), 'R7: intentos no correlativos')
okp = [s for s in T['Solicitudes_pedido'] if s['codigo_respuesta'].startswith('OK')]
check(all(s['id_pedido'] for s in okp) and all(not s['id_pedido'] for s in T['Solicitudes_pedido'] if not s['codigo_respuesta'].startswith('OK')),
      'R7: pedido creado sin OK o OK sin pedido')
p(f'R7 Idempotencia: {len(intentos)} solicitudes, {len(T["Solicitudes_pedido"])} intentos correlativos; un solo pedido por cotización; pedido solo con código OK.')

# ---------------------------------------------------------------- 4. ATP de la excepción prioritaria
p('\n4. ATP de PRD-001 en el CD Lima Norte al momento de SOL-002 (07/10/2026)')
corte = date(2026, 10, 7)
mov = [m for m in T['Movimientos_inventario'] if m['id_producto'] == 'PRD-001' and m['id_almacen'] == 'ALM-001' and fecha(m['fecha_movimiento']) < corte]
fisico = sum(num(m['cantidad_entrada']) - num(m['cantidad_salida']) for m in mov)
pedcab = idx(peds, 'id_pedido')
ent = idx(T['Entregas_cab'], 'id_entrega')
reservado = 0
for d in T['Pedidos_det']:
    if d['id_producto'] != 'PRD-001' or fecha(pedcab[d['id_pedido']]['fecha_confirmacion']) >= corte: continue
    entregado = sum(num(e['cantidad_entregada']) for e in T['Entregas_det']
                    if e['id_pedido'] == d['id_pedido'] and e['numero_linea_pedido'] == d['numero_linea'] and fecha(ent[e['id_entrega']]['fecha_entrega']) < corte)
    reservado += num(d['cantidad']) - entregado
atp = fisico - reservado
sol2 = next(s for s in T['Solicitudes_pedido'] if s['id_solicitud'] == 'SOL-002' and s['intento'] == '1')
check(atp == num(sol2['cantidad_atp_confirmada']), f'ATP calculado {atp} ≠ ATP registrado {sol2["cantidad_atp_confirmada"]}')
p(f'Físico antes del 07/10: {fisico:.0f} · reservado por pedidos confirmados sin entregar: {reservado:.0f} · ATP = {atp:.0f}')
p(f'Solicitado: {num(sol2["cantidad_solicitada"]):.0f} · ATP registrado por el ERP: {num(sol2["cantidad_atp_confirmada"]):.0f} · pendiente: {num(sol2["cantidad_solicitada"]) - atp:.0f} en reposición (prevista 12/10)')
inv = next(i for i in T['Inventario_actual'] if i['id_producto'] == 'PRD-001')
p(f'Al corte (11/10): stock físico {num(inv["stock_fisico"]):.0f}, en reposición {num(inv["cantidad_en_reposicion"]):.0f} ({inv["estado_reposicion"]}).')

# ---------------------------------------------------------------- 5. Importes
p('\n5. Importes (IGV 18%, redondeo a 2 decimales)')
def total_lineas(lineas, qcol='cantidad'):
    base = sum(round(round(num(l[qcol]) * num(l['precio_unitario']), 2) - round(round(num(l[qcol]) * num(l['precio_unitario']), 2) * num(l['descuento_pct']), 2), 2) for l in lineas)
    return round(base, 2)
n_imp = 0
for nombre_cab, nombre_det, k, qcol in [('Cotizaciones_cab', 'Cotizaciones_det', 'id_cotizacion', 'cantidad'), ('Pedidos_cab', 'Pedidos_det', 'id_pedido', 'cantidad'), ('Facturas_cab', 'Facturas_det', 'id_factura', 'cantidad')]:
    g = defaultdict(list)
    for d in T[nombre_det]: g[d[k]].append(d)
    for h in T[nombre_cab]:
        b = total_lineas(g[h[k]], qcol)
        check(abs(b - num(h['base_imponible'])) < 0.011, f'{h[k]}: base {b} ≠ {h["base_imponible"]}')
        n_imp += 1
p(f'→ {n_imp} documentos con base imponible recalculada desde sus líneas.')
p(f"COT-003-V01 (escenario normal): base {cab['COT-003-V01']['base_imponible']} + IGV {cab['COT-003-V01']['importe_igv']} = total S/ {cab['COT-003-V01']['importe_total']}")
p(f"COT-002-V02 (excepción): base {cab['COT-002-V02']['base_imponible']} + IGV {cab['COT-002-V02']['importe_igv']} = total S/ {cab['COT-002-V02']['importe_total']}")

# ---------------------------------------------------------------- 6. Trazabilidad
p('\n6. Cadenas de trazabilidad (de la factura hacia la campaña)')
fac = T['Facturas_cab']
lead_i = idx(leads, 'id_lead')
def cadena(id_fac):
    f = next(x for x in fac if x['id_factura'] == id_fac)
    pe = pedcab[f['id_pedido']]; q = cab[pe['id_cotizacion']]; o = opp[q['id_oportunidad']]
    sols = [f"{s['id_solicitud']}-{s['intento']} {s['codigo_respuesta']}" for s in T['Solicitudes_pedido'] if s['id_pedido'] == pe['id_pedido'] or (s['id_cotizacion'] == pe['id_cotizacion'])]
    ents = [e['id_entrega'] for e in T['Entregas_cab'] if e['id_pedido'] == pe['id_pedido']]
    pag = [x['id_pago'] for x in T['Pagos'] if x['id_factura'] == id_fac]
    partes = [o['id_campana'] or '(sin campaña)', o['id_lead'] or '(cliente existente)', o['id_cliente'], o['id_oportunidad'], q['id_cotizacion'],
              ' / '.join(dict.fromkeys(sols)), pe['id_pedido'], ', '.join(ents), id_fac] + pag
    return ' → '.join(partes)
p('Normal (Don Lucho, TUALI):      ' + cadena('FAC-003'))
p('Excepción (Los Olivos, tel.):   ' + cadena('FAC-002'))
p('Complementaria (bodega nueva): ' + cadena('FAC-001'))
check('CAMP-004 → LEAD-013 → CLI-003 → OPP-003 → COT-003-V01' in cadena('FAC-003'), 'Cadena del escenario normal incompleta')
check('CAMP-002 → (cliente existente) → CLI-002 → OPP-002 → COT-002-V02' in cadena('FAC-002'), 'Cadena de la excepción incompleta')

# ---------------------------------------------------------------- 7. Indicadores
p('\n7. Indicadores del contrato (datos de prueba, no de ACL)')
i1 = [s for s in T['Solicitudes_pedido'] if s['intento'] == '1']
ok1 = sum(s['codigo_respuesta'] == 'OK-ACEPTADO' for s in i1)
atpp = sum(s['codigo_respuesta'] == 'ATP-PARCIAL' for s in i1)
conv = sum(l['estado_lead'] == 'Convertido' for l in leads); desc = sum(l['estado_lead'] == 'Descartado' for l in leads)
p(f'Aceptación al primer envío: {ok1}/{len(i1)} = {ok1/len(i1):.1%}')
p(f'Pedidos con promesa alternativa: {atpp}/{len(i1)} = {atpp/len(i1):.1%}')
p(f'Conversión de leads cerrados: {conv}/{conv+desc} = {conv/(conv+desc):.1%}')
check((ok1, len(i1), atpp, conv, desc) == (7, 10, 1, 6, 3), 'Indicadores distintos a los declarados en el contrato')


# ---------------------------------------------------------------- 8. Un contrato, tres canales
p('\n8. Mismo contrato, tres canales (las reglas C1–C5 no dependen del canal de origen)')
p(f"{'canal':<10}{'solicitudes':>12}{'intentos':>10}{'conformes':>11}{'OK 1.er envío':>15}{'con código de excepción':>25}")
tot = [0, 0, 0, 0, 0]
for canal in ['TUALI', 'Preventa', 'Teléfono']:
    ss = [s for s in T['Solicitudes_pedido'] if s['canal_origen'] == canal]
    nsol = len({s['id_solicitud'] for s in ss})
    conf = sum(evaluar(s)[1] == s['codigo_respuesta'] for s in ss)
    ok1c = sum(s['intento'] == '1' and s['codigo_respuesta'] == 'OK-ACEPTADO' for s in ss)
    exc = sum(not s['codigo_respuesta'].startswith('OK') for s in ss)
    for i, v in enumerate([nsol, len(ss), conf, ok1c, exc]): tot[i] += v
    p(f"{canal:<10}{nsol:>12}{len(ss):>10}{conf:>11}{ok1c:>15}{exc:>25}")
p(f"{'Total':<10}{tot[0]:>12}{tot[1]:>10}{tot[2]:>11}{tot[3]:>15}{tot[4]:>25}")
check(all(s['canal_origen'] in ('TUALI', 'Preventa', 'Teléfono') for s in T['Solicitudes_pedido']), 'Solicitud sin canal de origen válido')
# Ningún pedido comprometido por encima del ATP sin aceptación del cliente
sobre = [s for s in T['Solicitudes_pedido'] if s['codigo_respuesta'] == 'OK-ACEPTADO' and num(s['cantidad_solicitada']) > num(s['cantidad_atp_confirmada'])]
check(not sobre, 'Pedido aceptado por encima del ATP')
parc = [s for s in T['Solicitudes_pedido'] if s['codigo_respuesta'] == 'OK-PROMESA-ALT' and s['acepta_entrega_parcial'] != 'Si']
check(not parc, 'Promesa alternativa sin aceptación del cliente')
p('Control: 0 pedidos aceptados por encima del ATP; 0 promesas parciales sin aceptación registrada del cliente.')
sin_resp = [s for s in T['Solicitudes_pedido'] if not (s['codigo_respuesta'] and s['responsable'] and s['siguiente_paso'])]
check(not sin_resp, 'Respuesta sin código, responsable o siguiente paso')
p(f'Control: {len(T["Solicitudes_pedido"]) - len(sin_resp)} de {len(T["Solicitudes_pedido"])} respuestas con código, responsable y siguiente paso.')

# ---------------------------------------------------------------- 9. Prueba EP: esperado vs observado
p('\n9. Prueba del EP: resultado esperado vs. resultado observado')
def fila(caso, esperado, observado):
    ok = esperado == observado
    check(ok, f'{caso}: esperado {esperado} / observado {observado}')
    p(f"  {caso:<44} esperado: {esperado:<28} observado: {observado:<28} {'Conforme' if ok else 'NO CONFORME'}")
    return ok
sol = {f"{s['id_solicitud']}-{s['intento']}": s for s in T['Solicitudes_pedido']}
p('EP-N · Escenario normal · Bodega Don Lucho (pedía por teléfono) acepta su cotización en TUALI')
n1 = sol['SOL-003-1']
fila('Canal de origen', 'TUALI', n1['canal_origen'])
fila('C1–C5 recalculadas', 'V V V V V', ' '.join(B(c) for c in evaluar(n1)[0]))
fila('Código de respuesta (EV-03)', 'OK-ACEPTADO', n1['codigo_respuesta'])
fila('Pedido creado', 'PED-003', n1['id_pedido'])
fila('Descuento aplicado (sin aprobación)', '5% ≤ 5% preventista', f"{max(num(d['descuento_pct']) for d in det['COT-003-V01']):.0%} ≤ 5% preventista")
fila('Responsable / escalamiento', 'Preventista 1 / ninguno', n1['responsable'] + ' / ninguno')
p('EP-X · Excepción prioritaria · Comercial Los Olivos (híbrido) pide por teléfono 600 paquetes en promoción')
x1, x2 = sol['SOL-002-1'], sol['SOL-002-2']
fila('Canal de origen', 'Teléfono', x1['canal_origen'])
fila('Versión con 10% enviada al ERP', 'No (C4 preventivo)', 'Sí' if 'COT-002-V01' in enviadas else 'No (C4 preventivo)')
fila('Versión enviada', 'COT-002-V02 (8%, Aprobado)', f"{x1['id_cotizacion']} ({max(num(d['descuento_pct']) for d in det[x1['id_cotizacion']]):.0%}, {cab[x1['id_cotizacion']]['estado_descuento']})")
fila('ATP recalculado al 07/10 (§4)', '380', f'{atp:.0f}')
fila('Intento 1: código', 'ATP-PARCIAL', x1['codigo_respuesta'])
fila('Intento 1: pedido creado', 'Ninguno', x1['id_pedido'] or 'Ninguno')
fila('Intento 2: tipo de mensaje (EV-05)', 'Confirmación promesa', x2['tipo_mensaje'])
fila('Intento 2: código', 'OK-PROMESA-ALT', x2['codigo_respuesta'])
fila('Pedido y estado', 'PED-002 · Entrega parcial', f"{x2['id_pedido']} · {pedcab[x2['id_pedido']]['estado_pedido']}")
ent2 = sum(num(e['cantidad_entregada']) for e in T['Entregas_det'] if e['id_pedido'] == 'PED-002')
fila('Entregado / pendiente al corte', '380 / 220', f"{ent2:.0f} / {num(inv['cantidad_en_reposicion']):.0f}")
fila('Escala a', 'Planeamiento CD → Preventista 2', x1['responsable'].replace(' → ', ' → '))

# ---------------------------------------------------------------- Resultado
p('\n' + '=' * 74)
if fallas:
    p(f'RESULTADO: {len(fallas)} observación(es)')
    for f in fallas: p('  - ' + f)
else:
    p('RESULTADO: todas las verificaciones conformes.')
print('\n'.join(out))
sys.exit(1 if fallas else 0)
