# Licencias, propiedad intelectual y atribución

## Código

El código del Agente SIE (`producto/`, `entrega/armar_zip.py`, `pruebas/`) se distribuye bajo licencia **MIT** (`LICENSE`, © 2026 Salvador Barrionuevo Gutierrez).

## Dependencias

| Componente | Versión | Licencia | Uso | ¿Se distribuye en el ZIP? |
|---|---|---|---|---|
| Python y su biblioteca estándar (incluye `sqlite3`) | 3.11+ | PSF License | Núcleo | No: lo instala el usuario |
| SQLite | incluido en Python | Dominio público | Base local | No |
| Streamlit | 1.67.0 | Apache-2.0 | Interfaz web (opcional) | No: `pip install -r requirements.txt` |
| anthropic (SDK de la Claude API) | 2.6.0 | Apache-2.0 | Modo `llm` (opcional) | No |
| pytest | 9.2.0 | MIT | Pruebas (opcional) | No |
| Mermaid | renderizado por GitHub | MIT | Diagramas del README y de `arquitectura/` | No |

Las licencias de las dependencias se verificaron con los metadatos de los paquetes instalados (07/11/2026). Streamlit instala además pandas (BSD-3-Clause) y pyarrow (Apache-2.0), entre otros.

## Material de terceros incluido

| Material | Titular | Tratamiento |
|---|---|---|
| Instrucciones, rúbricas, plantillas y presentaciones del curso (`docs/antecedentes/`) | UNI FIIS, GE703 | Se incluyen solo para revisión académica del docente |
| Marcas Coca-Cola, Inca Kola, Fanta, Powerade, San Luis, Frugos del Valle, TUALI, AC Móvil, SAP, Anaplan | Sus titulares | Solo para identificación académica; sin logotipos |
| Datos públicos de ACL (F01, F03) | Arca Continental Lindley | Citados con URL y fecha de acceso; no se copian contenidos |

## Datos

Todos los datos de `datos/seed/` son sintéticos, elaborados por el grupo (EP v3 y PC3). No representan a ACL ni a personas reales. Ver `datos/FUENTES_DATOS.md` y `datos/DATOS_SENSIBLES.md`.
