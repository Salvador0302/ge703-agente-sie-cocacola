# Agente SIE · Coca-Cola / ACL · GE703 G2

Sistema de agentes de IA, uno por proceso y coordinados por un orquestador, que ejecuta y controla el flujo de un pedido del canal tradicional desde la venta hasta las finanzas operativas.

| | |
|---|---|
| Curso | GE703 Sistemas Integrados Empresariales · UNI / FIIS · 2026-2 |
| Grupo | G2 |
| Empresa | Coca-Cola, a través de Arca Continental Lindley (ACL), Perú · canal tradicional (bodegas que piden por TUALI, preventa o teléfono) |
| Integrantes | Barrionuevo Gutierrez, Salvador Jhou (líder y arquitecto) · Cornejo Palomino, José Julián · Leandro Ochoa, Gianmarco · Urbano Lara, David Alexis |
| Incremento actual | PC3: agente comercial · entrega 13/11/2026, exposición 14/11/2026 |

## Qué resuelve

En el examen parcial el comité aprobó **"un pedido, un contrato, tres canales"**: todo pedido del canal tradicional, llegue por TUALI, por preventa o por teléfono, entra al ERP (SAP ECC) por el mismo contrato CRM–ERP (I8), con las mismas cinco validaciones (C1–C5) y una respuesta codificada. El problema de fondo es la adopción de TUALI: cerca del 46 % de los clientes aún no usa la app (cálculo del equipo), y en los pedidos telefónicos el precio, el stock y el crédito se confirman a mano, con promesas que no miran la disponibilidad (hipótesis H1). El Agente SIE pone ese contrato en ejecución: recibe la solicitud, la valida con reglas, consulta la disponibilidad (ATP), responde con el código del contrato y escala a una persona cuando hace falta.

## Arquitectura

```mermaid
flowchart LR
    subgraph canales["Canales del canal tradicional"]
        T["TUALI (app)"]
        P["Preventa (AC Móvil)"]
        F["Teléfono registrado en el CRM"]
    end
    T --> O
    P --> O
    F --> O
    O["Orquestador por tipo de evento"]
    O --> A["Agente comercial"]
    A --> C["CRM simulado"]
    A --> I8["Capa I8: contrato v1.2, intentos e idempotencia"]
    I8 --> E["ERP simulado: C1 a C5, ATP y promesa"]
    E --> DB[("SQLite con datos sintéticos")]
    C --> DB
    A -->|"escala con causa y fecha límite"| H["Responsable humano"]
    H -->|"decisión con evidencia"| O
    O --> B["Bitácora: tabla y JSONL"]
    A --> B
    E --> B
    A -.->|"solo modo llm"| L["Claude API: interpreta y redacta"]
    O -.-> CS["Agente de cadena de suministro"]
    O -.-> LG["Agente de logística"]
    O -.-> FO["Agente de finanzas operativas"]
    O -.-> CEO["Agente CEO (por confirmar)"]
    classDef hecho fill:#d1fae5,stroke:#047857,color:#064e3b
    classDef curso fill:#fef3c7,stroke:#b45309,color:#78350f
    classDef previsto fill:#f3f4f6,stroke:#9ca3af,color:#4b5563,stroke-dasharray:4 3
    class O,L hecho
    class A,C,I8,E,DB,H,B curso
    class CS,LG,FO,CEO previsto
```

Verde: implementado y probado · ámbar: en construcción (interfaces y pruebas de aceptación listas) · gris punteado: previsto para incrementos siguientes.

## Caso de excepción: de la parada de mantenimiento a la promesa al cliente

Este caso une la demo del agente con el informe de la PC3 (activos, mantenimiento y cadena de suministro): una parada planificada reduce la capacidad, la capacidad perdida reduce el ATP y el ATP obliga a una promesa alternativa que solo una persona puede aceptar. Los datos de la parada son sintéticos.

```mermaid
sequenceDiagram
    autonumber
    participant MT as Mantenimiento
    participant APO as Plan de reposición (APO)
    participant P2 as Preventista 2
    participant AG as Agente comercial
    participant ERP as ERP simulado
    Note over MT,APO: Mantenimiento reduce la capacidad
    MT->>APO: OT-2026-0107 · parada planificada de la línea ACT-LLN-01 · 96 h del 03 al 07/10
    APO->>APO: −240 paquetes de Inca Kola 500 ml · el lote del 06/10 pasa al 12/10
    P2->>AG: 07/10 · Comercial Los Olivos pide por teléfono 600 paquetes (COT-002-V02, descuento aprobado)
    AG->>ERP: EV-02 · SOL-002 intento 1
    Note over ERP: La disponibilidad decide
    ERP->>ERP: C1 a C4 pasan · C5 falla · ATP 380 de 600
    ERP->>APO: consulta la causa del faltante
    APO-->>ERP: OT-2026-0107 · sin la parada el ATP sería 620
    ERP-->>AG: EV-04 · ATP-PARCIAL · 380 el 09/10 + 220 el 12/10
    Note over P2,AG: La promesa al cliente la decide una persona
    AG->>P2: escalamiento ESC-SOL-002-1 · decidir antes del 08/10
    P2->>AG: 08/10 · el cliente acepta · evidencia ACEP-SOL-002-2
    AG->>ERP: EV-05 · SOL-002 intento 2 con la aceptación
    ERP-->>AG: EV-03 · OK-PROMESA-ALT · PED-002 · 380 el 09/10 + 220 el 12/10
```

El caso normal sigue el mismo camino sin escalamiento: Bodega Don Lucho (CLI-003) acepta en TUALI la cotización COT-003-V01 → SOL-003 → `OK-ACEPTADO` → PED-003.

## Hoja de ruta

```mermaid
flowchart LR
    E0["EP · 24/10/2026<br/>Contrato I8 y decisión del comité<br/>Hecho"]
    E1["PC3 · 14/11/2026<br/>Agente comercial<br/>En construcción"]
    E2["Semanas 12 y 13<br/>Cadena de suministro y logística<br/>Previsto"]
    E3["PC4 · 05/12/2026<br/>Finanzas operativas<br/>Previsto"]
    E4["Examen final<br/>Integración de ventas a finanzas operativas<br/>Previsto"]
    E0 --> E1 --> E2 --> E3 --> E4
    classDef hecho fill:#d1fae5,stroke:#047857,color:#064e3b
    classDef curso fill:#fef3c7,stroke:#b45309,color:#78350f
    classDef previsto fill:#f3f4f6,stroke:#9ca3af,color:#4b5563,stroke-dasharray:4 3
    class E0 hecho
    class E1 curso
    class E2,E3,E4 previsto
```

Todos los incrementos usan los mismos datos: los pedidos PED-002 y PED-003 que crea el agente en la PC3 son los que la PC4 llevará a entrega, factura, cobro y conciliación.

## Estado del avance al 07/11/2026

| Componente | Estado | Evidencia |
|---|---|---|
| Contrato I8 v1.2 tipado | Hecho | `producto/sie/contrato.py` · 8 pruebas pasan (reproduce los 12 mensajes del EP y el catálogo de 9 códigos) · `arquitectura/contrato_i8/CONTRATO_I8.md` |
| Orquestador | Hecho | `producto/sie/orquestador.py` · 8 pruebas pasan · ADR-006 |
| Configuración | Hecho | `producto/sie/config.py` · 6 pruebas pasan · ADR-002 |
| CLI y diagnóstico | Hecho; la demo completa espera los componentes en construcción | `producto/sie/cli.py` · 8 pruebas pasan |
| Modo LLM (Claude API) | Hecho, probado con una simulación de la API (sin API key) | `producto/sie/llm/` · 14 pruebas pasan · ADR-001 |
| Datos y ERP simulado | En curso: interfaz y 22 pruebas de aceptación definidas | `producto/sie/erp/`, `producto/sie/db/` · ADR-004 |
| Agente comercial y bitácora | En curso: interfaz y 13 pruebas de aceptación definidas | `producto/sie/agentes/comercial/` · ADR-003, ADR-005 |
| Interfaz (Streamlit) | Pendiente: 1 prueba de aceptación definida | `producto/sie/ui/app.py` |
| Paquete de entrega (guía y ZIP) | Pendiente: 5 pruebas de aceptación definidas | `entrega/` |

Total: 44 pruebas pasan y 41 pruebas de aceptación esperan los componentes en curso. Plan del incremento: [`arquitectura/PLAN_PC3.md`](arquitectura/PLAN_PC3.md).

## Principios de diseño

- **Las reglas deciden; el LLM interpreta.** Un motor de reglas determinista decide C1–C5, el código y la promesa. El LLM solo entiende el texto del pedido con herramientas de lectura y redacta la explicación; una cifra redactada que no esté en los hechos se descarta (ADR-001).
- **El agente envía; solo el ERP crea pedidos.** El agente manda la solicitud (EV-02) por la interfaz I8, pero nunca crea pedidos, aprueba descuentos ni confirma una promesa sin una decisión humana (ADR-003).
- **Se ejecuta sin dependencias ni API key.** La demo usa solo Python 3.11 y SQLite; Streamlit, la Claude API y pytest son opcionales (ADR-002).
- **Todo queda en la bitácora, con escalamiento humano.** Cada paso se guarda con regla, código, IDs, fecha de negocio y, si se escala, a quién, por qué y hasta cuándo (ADR-005).

## Cómo probar hoy

Requisito: Python 3.11 o superior. Desde la carpeta del proyecto:

```powershell
cd producto
python -m sie diagnostico        # verifica Python, permisos y datos, y dice qué componentes ya funcionan
python -m sie agentes            # agentes previstos y su estado
python -m sie --help             # comandos disponibles
cd ..
pip install -r requirements.txt  # opcional: pytest, Streamlit y el SDK de la Claude API
python -m pytest pruebas/unitarias  # 44 pruebas del núcleo
```

Cuando la demo esté completa, `python -m sie demo normal` mostrará la traza C1–C5, `OK-ACEPTADO` y PED-003. `python -m sie demo excepcion` mostrará `ATP-PARCIAL` con la causa OT-2026-0107, pedirá la decisión de Preventista 2 y terminará en `OK-PROMESA-ALT` con PED-002. Ambas cierran con una tabla de resultado esperado frente a observado.

## Estructura del repositorio

| Carpeta | Contenido |
|---|---|
| `arquitectura/` | Plan del incremento, vistas, interfaces, versiones, decisiones (ADR) y contrato I8 v1.2 |
| `procesos/` | Reglas, tabla de decisiones, eventos y controles del agente comercial (en construcción) |
| `datos/` | Diccionario de datos, fuentes, datos de prueba (`seed/`) y tratamiento de datos sensibles (en construcción) |
| `producto/` | Código del Agente SIE (paquete `sie`): orquestador, agentes, reglas, ERP y CRM simulados, CLI e interfaz |
| `pruebas/` | Pruebas automáticas, casos, resultados esperados frente a observados e incidencias |
| `fuentes/` | Bibliografía, licencias y declaración de uso de IA (en construcción) |
| `agentes/` | Ficha de cada agente: propósito, entradas, salidas, reglas, permisos, escalamiento y bitácora (en construcción) |
| `entrega/` | Guía de despliegue y script que arma el ZIP de entrega (en construcción) |
| `docs/antecedentes/` | Material del examen parcial y de las instrucciones de la PC3 y la PC4 (solo lectura) |

## Datos

Todos los datos son **sintéticos** o vienen del modelo del examen parcial, que también es sintético: clientes marcados "(sintético)", correos `@example.com`, teléfonos `SIM-TEL-…` y documentos `SIM-RUC…`. Precios, stocks, créditos, políticas y la parada de mantenimiento son supuestos didácticos, no datos de ACL. No hay datos personales. El repositorio no contiene contraseñas ni API keys: la configuración se copia de `.env.example` a un `.env` local que git no versiona.

## Preguntas abiertas al docente

1. ¿Cumple como "agente de IA" un diseño en el que las reglas deciden y el LLM solo interpreta el pedido y redacta la explicación?
2. ¿Cómo prefiere ejecutar el modo LLM: con su propia API key, solo en modo reglas (sin clave) o con un acceso temporal que le proporcionemos?
3. ¿Acepta que el ERP (SAP ECC) y el CRM (SAP Sales Cloud) estén simulados sobre SQLite con datos sintéticos?
4. Para el examen final, ¿se exige un agente CEO o un orquestador más avanzado, o el alcance termina en finanzas operativas?

## Licencia

Código bajo licencia MIT (`LICENSE`). El material del curso en `docs/antecedentes/` pertenece a la UNI FIIS (GE703) y se incluye solo para revisión académica.
