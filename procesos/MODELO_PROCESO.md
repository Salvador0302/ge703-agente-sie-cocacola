# Modelo del proceso: solicitud de pedido con el agente comercial

```mermaid
flowchart TD
    A["Solicitud de pedido: texto, canal y fecha"] --> B["Interpretar: cliente, cotización y cantidad"]
    B --> C{"¿Cotización aceptada, vigente y con la cantidad pedida? (R2)"}
    C -->|"No"| NE["NO-ENVIADA: escala al supervisor o al ejecutivo"]
    C -->|"Sí"| D["Armar EV-02 desde el CRM y consultar ATP (I3)"]
    D --> E["Enviar EV-02 por I8"]
    E --> F{"Controles del ERP: P1, P2, C1 a C5"}
    F -->|"Todo pasa"| OK["OK-ACEPTADO: el ERP crea el pedido"]
    F -->|"Falla C1 a C4 o P1, P2"| R["Rechazo con código: escala al responsable del catálogo"]
    F -->|"Falla C5"| P["ATP-PARCIAL: promesa por tramos y causa del faltante"]
    P --> H{"Decisión del ejecutivo con el cliente"}
    H -->|"Acepta"| EV5["EV-05 con evidencia"]
    EV5 --> OKP["OK-PROMESA-ALT: el ERP crea el pedido"]
    H -->|"Rechaza"| X["Cerrado sin pedido"]
    OK --> CRM["CRM: oportunidad Ganada y adopción de TUALI (R9)"]
    OKP --> CRM
```

Cada caja deja una entrada en la bitácora. El modelo de datos está en `arquitectura/PLAN_PC3.md` §5 y la tabla de decisiones en `REGLAS.md`.
