# Brief · Bloque D · UI y entrega

**Responsable:** David Alexis Urbano Lara · **Rama:** `bloque-d/ui-entrega` · **Plazo:** miércoles 11/11/2026 (UI y documentos) y jueves 12/11/2026 (ZIP verificado)
**Por qué tú:** en el EP llevaste fuentes, declaración de IA, límites y el repositorio. Este bloque es lo que el docente abre primero: la guía, el README y el ZIP.

## Qué entregas

| Archivo | Contenido |
|---|---|
| `producto/sie/ui/app.py` | Interfaz Streamlit (abajo). Se lanza con `python -m sie ui` |
| `README.md` | Propósito, alcance (PC3 y siguientes incrementos), integrantes con nombre completo, pasos de reproducción (`python -m sie demo normal` y `excepcion`), enlace a la guía, aviso de datos sintéticos |
| `entrega/GUIA_DESPLIEGUE.md` | Secciones: Requisitos previos · Instalación · Configuración (`.env.example`, `AGENT_MODE`) · Ejecución de la demo · Resultados esperados · Diagnóstico y recuperación (`python -m sie diagnostico`) · Dependencias y licencias · Accesos seguros · Ficha del agente (enlace a `agentes/comercial/FICHA.md`) |
| `fuentes/BIBLIOGRAFIA.md`, `fuentes/LICENCIAS.md`, `fuentes/DECLARACION_IA.md` | Fuentes con fecha de acceso (parte del EP + nuevas), licencias (código MIT de `LICENSE`, dependencias, material del curso, datos sintéticos) y uso de IA con validación humana, por integrante |
| `entrega/armar_zip.py` | `construir` y `verificar` (abajo) |

## Interfaz Streamlit

- Título "Agente SIE · G2 · Coca-Cola / ACL" y aviso visible de datos sintéticos.
- Pestañas: **Caso normal**, **Excepción**, **Bitácora**, **Agentes**.
- Cada caso: botón "Ejecutar" → `preparar_base` + `construir_sistema` + `orquestador.despachar` con los datos de `sie.demo.CASOS`. Muestra la entrada, C1–C5 (entradas de la bitácora con `agente="erp"`), el código, la cadena OT-2026-0107 → −240 → ATP 380 de 600 → promesa, y el escalamiento.
- Excepción: botones "El cliente acepta" / "El cliente rechaza" (Preventista 2) que envían `decision_humana`; al final, la tabla de `sie.demo.verificar` (esperado frente a observado).
- **No dupliques lógica de negocio:** todo sale de `sie.sistema`, `sie.demo` y la bitácora.
- SQLite no comparte conexiones entre hilos: no guardes la conexión en `st.session_state`; reábrela en cada ejecución con `conectar(config.ruta_db)`. Sí puedes guardar el `ResultadoAgente` del intento 1.

## ZIP

- Nombre `GE703_PC3_Agente_G2_CocaCola.zip` (`NOMBRE` en el archivo), dentro de `entrega/salida/` por defecto.
- **Lista de permitidos**, no de exclusión: `README.md`, `LICENSE`, `requirements.txt`, `pyproject.toml`, `.env.example`, `arquitectura/`, `procesos/`, `datos/` (sin `*.db`), `producto/`, `pruebas/`, `fuentes/`, `agentes/`, `entrega/` (sin `salida/`), `docs/antecedentes/`.
- Nunca: `.env`, `*.db`, `logs/`, `.venv/`, `.git/`, `__pycache__/`, `*.pyc`, otros `.zip`. Rutas internas de 150 caracteres como máximo. Ningún archivo de texto con `sk-ant-`.
- `verificar`: extrae en una carpeta temporal, repite esos controles y, con `ejecutar_demo=True`, corre `python -m sie demo normal` y `python -m sie demo excepcion --acepta` desde la copia extraída, **sin `.env`**, y exige código de salida 0. Devuelve la lista de problemas.

## Cómo trabajar

```powershell
git fetch origin; git switch bloque-d/ui-entrega
py -3.11 -m venv .venv; .venv\Scripts\activate; pip install -r requirements.txt
python -m pytest pruebas/aceptacion/test_bloque_d.py
cd producto; python -m sie ui
```

README, guía y fuentes no dependen de nadie: empieza por ahí. La UI y el ZIP verificado necesitan B y C; cuando suban avances, `git merge origin/bloque-b/datos-erp origin/bloque-c/agente-comercial` en tu rama. Commits pequeños **con tu propia identidad**; si usas IA, decláralo. Pull request a `main` cuando esté verde.

## Terminado cuando

- `python -m pytest pruebas/aceptacion/test_bloque_d.py` da **0 pendientes y 0 fallas**.
- Un compañero sigue la guía en otra PC, desde el ZIP, sin tu ayuda, y la demo sale conforme.
- Puedes explicar en 1 minuto cómo el docente ejecuta el paquete, qué hacer si falla y qué datos son sintéticos.
