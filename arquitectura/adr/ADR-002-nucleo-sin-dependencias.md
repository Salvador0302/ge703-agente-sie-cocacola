# ADR-002 · Núcleo con biblioteca estándar, SQLite local y sin servicios obligatorios

**Estado:** aceptada · 07/11/2026 · Salvador Barrionuevo

## Contexto

La PC3 exige que el docente pueda ejecutar el agente solo, con los archivos entregados, en un Windows con Python. El aula puede no tener internet ni permisos para instalar paquetes.

## Decisión

- Python 3.11+ y solo la biblioteca estándar para el núcleo: CLI, contrato, orquestador, ERP y CRM simulados, bitácora y lector de `.env`.
- SQLite como base local (archivo `datos/sie.db`, regenerado desde `datos/seed/` en cada demo).
- Dependencias **opcionales**, fijadas en `requirements.txt`: Streamlit (UI), `anthropic` (modo `llm`) y pytest (pruebas).
- La CLI fuerza UTF-8 en stdout y stderr: el validador del EP fallaba en Windows al redirigir la salida (incidencia I-06).
- El paquete vive en `producto/` (estructura pedida por el curso); los comandos se ejecutan desde esa carpeta y las rutas se resuelven desde el código, no desde el directorio actual.

## Alternativas descartadas

- **PostgreSQL o un servicio web:** exige instalar y levantar servidores en la PC del docente.
- **python-dotenv:** dependencia innecesaria para leer cinco variables.

## Consecuencias

- `python -m sie demo normal` funciona recién descomprimido el ZIP, sin instalar nada.
- `python -m sie diagnostico` verifica el entorno y explica cómo corregir cada falla.
