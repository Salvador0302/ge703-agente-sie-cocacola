"""Interfaz Streamlit de la demo. Se lanza con `python -m sie ui` (desde `producto/`).

Reutiliza `sie.sistema`, `sie.demo` y la bitácora: no contiene lógica de negocio. Usa su propia base
(`datos/sie_ui.db`) para no bloquear la de la CLI. SQLite no comparte conexiones entre hilos, así que la
conexión se abre en cada ejecución del script y solo se guardan los resultados en `st.session_state`.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):  # `streamlit run app.py` directo: hace importable el paquete `sie`
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

from sie.agentes.base import EstadoResultado, Evento, ResultadoAgente, nuevo_run_id
from sie.bitacora.persistente import BitacoraPersistente
from sie.config import Config, cargar
from sie.db import seed
from sie.db.conexion import conectar
from sie.demo import CASOS, CasoDemo, verificar
from sie.orquestador import AGENTES_PREVISTOS, RUTAS
from sie.sistema import construir_sistema, preparar_base

CONTROLES = ("C1", "C2", "C3", "C4", "C5")


def _config(modo: str) -> Config:
    return cargar(modo=modo)


def _ruta_db(config: Config) -> Path:
    return config.ruta_db.with_name("sie_ui.db")


def _entradas(config: Config, run_id: str):
    conn = conectar(_ruta_db(config))
    try:
        return BitacoraPersistente(conn, config.ruta_bitacora).leer(run_id=run_id)
    finally:
        conn.close()


def _ejecutar_pedido(config: Config, caso: CasoDemo) -> dict:
    conn = preparar_base(config, caso.corte, ruta=_ruta_db(config))
    try:
        sistema = construir_sistema(config, conn)
        run_id = nuevo_run_id()
        r1 = sistema.orquestador.despachar(Evento(tipo="pedido", fecha_negocio=caso.fecha, origen="ui", run_id=run_id,
                                                  datos={"texto": caso.texto, "canal": caso.canal}))
    finally:
        conn.close()
    return {"run_id": run_id, "resultados": [r1], "acepta": True}


def _decidir(config: Config, caso: CasoDemo, estado: dict, acepta: bool) -> None:
    r1: ResultadoAgente = estado["resultados"][0]
    conn = conectar(_ruta_db(config))
    try:
        seed.avanzar(conn, caso.fecha_decision)
        sistema = construir_sistema(config, conn)
        r2 = sistema.orquestador.despachar(Evento(
            tipo="decision_humana", fecha_negocio=caso.fecha_decision, origen="ui", run_id=estado["run_id"],
            datos={"id_escalamiento": r1.escalamiento.id_escalamiento, "acepta": acepta, **caso.decision}))
    finally:
        conn.close()
    estado["resultados"].append(r2)
    estado["acepta"] = acepta


def _mostrar_resultado(r: ResultadoAgente) -> None:
    texto = f"**{r.codigo or r.estado}** · {r.ids.get('id_solicitud', '')} intento {r.ids.get('intento', '—')}"
    if r.ids.get("id_pedido"):
        texto += f" · pedido **{r.ids['id_pedido']}**"
    if r.estado == EstadoResultado.COMPLETADO:
        st.success(texto)
    elif r.estado == EstadoResultado.ESPERA_HUMANO:
        st.warning(texto + " · espera la decisión humana")
    else:
        st.error(texto + f" · {r.estado}")
    st.write(r.mensaje)
    for aviso in r.detalle.get("avisos", []):
        st.caption(f"Aviso: {aviso}")


def _mostrar_controles(entradas) -> None:
    filas = [{"Control": e.regla, "Resultado": e.resultado} for e in entradas
             if e.agente == "erp" and e.regla in CONTROLES]
    if filas:
        st.markdown("**Controles del ERP (contrato I8)**")
        st.table(filas[:5])


def _mostrar_excepcion(r: ResultadoAgente) -> None:
    causa = r.detalle.get("causa")
    if causa:
        st.markdown("**Cadena causal: mantenimiento → disponibilidad → promesa** (datos sintéticos)")
        cols = st.columns(4)
        cols[0].metric("Parada", causa["id_ot"], f"{causa['horas_parada']} h en {causa['id_activo']}",
                       delta_color="off")
        cols[1].metric("Capacidad perdida", f"−{causa['paquetes_perdidos']} paq", "lote del 06/10 al 12/10",
                       delta_color="off")
        cols[2].metric("ATP al 07/10", f"{causa['atp_con_parada']} de 600",
                       f"sin la parada: {causa['atp_sin_parada']}", delta_color="off")
        promesa = r.detalle.get("promesa") or {}
        tramos = " + ".join(f"{t['cantidad']} el {t['fecha'][8:10]}/{t['fecha'][5:7]}" for t in promesa.get("tramos", []))
        cols[3].metric("Promesa propuesta", tramos or "—", "requiere aceptación del cliente", delta_color="off")
    if r.escalamiento:
        e = r.escalamiento
        st.info(f"Escalamiento **{e.id_escalamiento}** a **{e.responsable}** · fecha límite "
                f"{e.fecha_limite.strftime('%d/%m/%Y')} · {e.estado}\n\nCausa: {e.causa}")


def _mostrar_verificacion(clave: str, estado: dict) -> None:
    filas = verificar(clave, estado["resultados"], estado["acepta"])
    st.markdown("**Resultado esperado frente a observado**")
    st.table([{"Verificación": f.nombre, "Esperado": f.esperado, "Observado": f.observado,
               "Resultado": "Conforme" if f.conforme else "NO CONFORME"} for f in filas])
    conformes = sum(f.conforme for f in filas)
    (st.success if conformes == len(filas) else st.error)(f"{conformes} de {len(filas)} verificaciones conformes")


def _pestana_caso(config: Config, clave: str) -> None:
    caso = CASOS[clave]
    st.subheader(caso.titulo)
    st.markdown(f"**{caso.fecha.strftime('%d/%m/%Y')} · canal {caso.canal}** · “{caso.texto}”")
    if st.button("Ejecutar caso", key=f"ejecutar_{clave}", type="primary"):
        st.session_state[clave] = _ejecutar_pedido(config, caso)
    estado = st.session_state.get(clave)
    if not estado:
        st.caption("La base se reinicia al corte del caso en cada ejecución.")
        return
    r1 = estado["resultados"][0]
    _mostrar_resultado(r1)
    _mostrar_controles(_entradas(config, estado["run_id"]))
    _mostrar_excepcion(r1)
    if r1.estado == EstadoResultado.ESPERA_HUMANO and len(estado["resultados"]) == 1:
        st.markdown(f"**Decisión de {caso.decision['registrada_por']}** "
                    f"({caso.fecha_decision.strftime('%d/%m/%Y')}, evidencia {caso.decision['evidencia']})")
        a, b = st.columns(2)
        if a.button("El cliente acepta la promesa (EV-05)", key=f"acepta_{clave}"):
            _decidir(config, caso, estado, True)
            st.rerun()
        if b.button("El cliente rechaza", key=f"rechaza_{clave}"):
            _decidir(config, caso, estado, False)
            st.rerun()
        return
    if len(estado["resultados"]) > 1:
        st.markdown("**Después de la decisión humana**")
        _mostrar_resultado(estado["resultados"][1])
    _mostrar_verificacion(clave, estado)


def _pestana_bitacora(config: Config) -> None:
    runs = {clave: st.session_state[clave]["run_id"] for clave in CASOS if clave in st.session_state}
    if not runs:
        st.caption("Ejecute un caso para ver su bitácora.")
        return
    clave = st.radio("Caso", list(runs), format_func=lambda c: CASOS[c].titulo.split("·")[0].strip(), horizontal=True)
    entradas = _entradas(config, runs[clave])
    st.caption(f"run {runs[clave]} · {len(entradas)} entradas · también en {config.ruta_bitacora}")
    st.dataframe([{"Fecha de negocio": e.fecha_negocio.isoformat() if e.fecha_negocio else "", "Agente": e.agente,
                   "Paso": e.paso, "Regla": e.regla or "", "Código": e.codigo or "", "Resultado": e.resultado,
                   "Escala a": e.escalado_a or "", "Límite": e.fecha_limite.isoformat() if e.fecha_limite else "",
                   "Respuesta humana": e.respuesta_humana or ""} for e in entradas],
                 width="stretch", hide_index=True)


def _pestana_agentes() -> None:
    st.table([{"Agente": a.nombre, "Proceso": a.proceso, "Incremento": a.incremento,
               "Estado": "implementado" if a.nombre == "comercial" else "no implementado aún",
               "Eventos": ", ".join(sorted(t for t, n in RUTAS.items() if n == a.nombre))} for a in AGENTES_PREVISTOS])


def main() -> None:
    st.set_page_config(page_title="Agente SIE · G2", layout="wide")
    st.title("Agente SIE · G2 · Coca-Cola / ACL")
    st.caption("GE703 · PC3 · agente comercial sobre el contrato CRM–ERP I8 · "
               "**Datos sintéticos**: ningún valor corresponde a ACL")
    modo = st.sidebar.radio("Modo del agente", ["reglas", "llm"],
                            help="reglas: sin internet ni API key. llm: Claude interpreta y redacta; las reglas deciden.")
    config = _config(modo)
    st.sidebar.markdown(f"Modo efectivo: **{config.modo}**")
    for aviso in config.avisos:
        st.sidebar.warning(aviso)
    st.sidebar.caption("Un pedido, un contrato, tres canales: TUALI, preventa y teléfono entran por el contrato I8 "
                       "con las mismas validaciones C1–C5.")
    normal, excepcion, bitacora, agentes = st.tabs(["Caso normal", "Excepción", "Bitácora", "Agentes"])
    with normal:
        _pestana_caso(config, "normal")
    with excepcion:
        _pestana_caso(config, "excepcion")
    with bitacora:
        _pestana_bitacora(config)
    with agentes:
        _pestana_agentes()


if __name__ == "__main__":
    main()
